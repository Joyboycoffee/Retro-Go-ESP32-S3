// =============================================================================
//  Retro Handheld S3 - Web Browser & AI Answers   (fixed for MicroQuickJS)
//
//  WHY THE OLD VERSION CRASHED
//    "TypeError: not a function at draw_browser (browser.js:127:32)"
//    Bruce's JS engine (MicroQuickJS) is ES5-style and has NO String.prototype.startsWith /
//    endsWith / includes / padStart / repeat and NO encodeURIComponent. Every one of those
//    calls throws "not a function".  This file uses only indexOf / slice / charAt / charCodeAt.
//    It also read wifi.httpFetch() as a string; the real return value is an object whose text
//    is in `.body` (plus .status / .ok).
//
//  CONTROLS (matched to the Retro Handheld S3 key map)
//    A ............ search / ask a question
//    X or Y ....... switch mode  (AI answer  <->  Wikipedia search)
//    UP / DOWN .... scroll (hold to auto-repeat)      LEFT / RIGHT ... page up / down
//    B or MENU .... exit
//    (SELECT is wired to "Esc" by the firmware, so it exits too - it cannot be used as "OK".)
// =============================================================================

var display = require("display");
var keyboard = require("keyboard");

var wifi = null;
try { wifi = require("wifi"); } catch (errW) {}

var gpio = null;
try { gpio = require("gpio"); } catch (errG) {}

var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var CYAN = display.color(0, 240, 255);
var YELLOW = display.color(255, 220, 50);
var GRAY = display.color(70, 75, 90);
var DARK_BLUE = display.color(15, 25, 45);
var ACCENT_BLUE = display.color(30, 110, 230);
var GREEN = display.color(50, 230, 90);
var RED = display.color(255, 60, 60);

var displayWidth = display.width();
var displayHeight = display.height();

// Board pins (active LOW) - see boards/retro-handheld-s3/interface.cpp
var PIN_UP = 41;
var PIN_DOWN = 42;
var PIN_X = 45;
var PIN_Y = 48;

var mode = 0;              // 0 = AI answer, 1 = Wikipedia search
var pageLines = [];
var scrollOffset = 0;
var lineHeight = 21;
var maxVisibleLines = Math.floor((displayHeight - 34) / lineHeight);
if (maxVisibleLines < 4) maxVisibleLines = 4;
var CHARS_PER_LINE = 34;   // font size 1, leaves room for the scrollbar

// ---------------------------------------------------------------- string helpers
// startsWith replacement
function hasPrefix(str, prefix) {
    return str.indexOf(prefix) === 0;
}

// Keep printable ASCII only (the built-in font has no emoji / curly quotes / etc.)
function toAscii(text) {
    var out = "";
    for (var i = 0; i < text.length; i++) {
        var c = text.charCodeAt(i);
        if (c === 10 || c === 13 || (c >= 32 && c < 127)) {
            out += text.charAt(i);
        } else if (c === 0x2018 || c === 0x2019) {
            out += "'";
        } else if (c === 0x201C || c === 0x201D) {
            out += '"';
        } else if (c === 0x2013 || c === 0x2014) {
            out += "-";
        } else if (c === 9) {
            out += " ";
        } else if (c > 127) {
            out += "?";
        }
    }
    return out;
}

// encodeURIComponent replacement (UTF-8 safe)
var HEX = "0123456789ABCDEF";
function pct(b) {
    return "%" + HEX.charAt((b >> 4) & 15) + HEX.charAt(b & 15);
}
function urlEncode(str) {
    var out = "";
    for (var i = 0; i < str.length; i++) {
        var c = str.charCodeAt(i);
        var ch = str.charAt(i);
        if ((c >= 48 && c <= 57) || (c >= 65 && c <= 90) || (c >= 97 && c <= 122) ||
            c === 45 || c === 95 || c === 46 || c === 126) {
            out += ch;
        } else if (c < 128) {
            out += pct(c);
        } else if (c < 2048) {
            out += pct(192 | (c >> 6)) + pct(128 | (c & 63));
        } else {
            out += pct(224 | (c >> 12)) + pct(128 | ((c >> 6) & 63)) + pct(128 | (c & 63));
        }
    }
    return out;
}

// Light markdown clean-up for AI answers
function stripMarkdown(text) {
    var t = text;
    t = t.split("**").join("");
    t = t.split("__").join("");
    t = t.split("`").join("");
    t = t.split("\n### ").join("\n");
    t = t.split("\n## ").join("\n");
    t = t.split("\n# ").join("\n");
    t = t.split("\r").join("");
    return t;
}

// Word wrap into lines that fit the screen
function wrapText(text, maxChars) {
    if (!maxChars) maxChars = CHARS_PER_LINE;
    var result = [];
    var paragraphs = text.split("\n");
    for (var p = 0; p < paragraphs.length; p++) {
        var words = paragraphs[p].split(" ");
        var curLine = "";
        for (var w = 0; w < words.length; w++) {
            var word = words[w];
            if (word.length === 0) continue;
            while (word.length > maxChars) {           // very long token (URLs etc.)
                if (curLine.length > 0) { result.push(curLine); curLine = ""; }
                result.push(word.slice(0, maxChars));
                word = word.slice(maxChars);
            }
            if (curLine.length + word.length + 1 <= maxChars) {
                curLine += (curLine.length === 0 ? "" : " ") + word;
            } else {
                if (curLine.length > 0) result.push(curLine);
                curLine = word;
            }
        }
        if (curLine.length > 0) result.push(curLine);
        if (p < paragraphs.length - 1 && result.length > 0 && result[result.length - 1] !== "") {
            result.push("");
        }
    }
    return result;
}

// ---------------------------------------------------------------- pages
function loadHomePage() {
    pageLines = [
        "RETRO BROWSER",
        "================================",
        "Mode: " + (mode === 0 ? "[ AI Answer ]" : "[ Wikipedia Search ]"),
        "",
        "Controls:",
        "- Press [A] to search / ask",
        "- Press [X] or [Y] to switch mode",
        "- [UP]/[DOWN] scroll, [B] exit",
        "",
        "Quick prompts to try:",
        "1. What is quantum computing?",
        "2. Explain ESP32-S3 architecture",
        "3. Best retro games of all time",
        "4. Tell me a sci-fi hacker story"
    ];
    scrollOffset = 0;
}

function isOnline() {
    try {
        if (wifi && typeof wifi.connected === "function") return wifi.connected();
    } catch (errCheck) {}
    return false;
}

// ---------------------------------------------------------------- drawing
function drawHeader() {
    display.drawFillRect(0, 0, displayWidth, 26, DARK_BLUE);
    display.drawLine(0, 26, displayWidth, 26, ACCENT_BLUE);

    display.setTextAlign("left", "middle");
    display.setTextSize(1);
    display.setTextColor(CYAN, DARK_BLUE);
    display.drawText(mode === 0 ? "AI ANSWER" : "WIKIPEDIA SEARCH", 10, 13);

    display.setTextAlign("right", "middle");
    var online = isOnline();
    display.setTextColor(online ? GREEN : RED, DARK_BLUE);
    display.drawText(online ? "ONLINE" : "OFFLINE", displayWidth - 10, 13);
}

function lineColor(line) {
    if (hasPrefix(line, "RETRO") || hasPrefix(line, "=====") || hasPrefix(line, "Topic:")) return CYAN;
    if (hasPrefix(line, "Mode:") || hasPrefix(line, "Quick") || hasPrefix(line, "Prompt:") ||
        hasPrefix(line, "Controls:")) return YELLOW;
    if (hasPrefix(line, "1.") || hasPrefix(line, "2.") || hasPrefix(line, "3.") || hasPrefix(line, "4.")) return GREEN;
    if (hasPrefix(line, "[ERROR]") || hasPrefix(line, "WiFi") || hasPrefix(line, "Network")) return RED;
    return WHITE;
}

function drawBrowser() {
    drawHeader();
    display.drawFillRect(0, 27, displayWidth, displayHeight - 27, BLACK);
    display.setTextAlign("left", "top");
    display.setTextSize(1);

    for (var i = 0; i < maxVisibleLines; i++) {
        var idx = scrollOffset + i;
        if (idx >= pageLines.length) break;
        display.setTextColor(lineColor(pageLines[idx]), BLACK);
        display.drawText(pageLines[idx], 10, 32 + i * lineHeight);
    }

    if (pageLines.length > maxVisibleLines) {
        var barTotalH = displayHeight - 34;
        var barThumbH = Math.max(16, Math.floor((maxVisibleLines / pageLines.length) * barTotalH));
        var span = pageLines.length - maxVisibleLines;
        var barThumbY = 30 + Math.floor((scrollOffset / span) * (barTotalH - barThumbH));
        display.drawFillRect(displayWidth - 5, 28, 4, barTotalH, GRAY);
        display.drawFillRect(displayWidth - 5, barThumbY, 4, barThumbH, CYAN);
    }
}

function showStatus(title, sub, color) {
    display.drawFillRect(0, 27, displayWidth, displayHeight - 27, BLACK);
    display.setTextAlign("center", "middle");
    display.setTextSize(1);
    display.setTextColor(color, BLACK);
    display.drawText(title, displayWidth / 2, displayHeight / 2 - 12);
    display.setTextColor(WHITE, BLACK);
    var shown = sub.length > 38 ? sub.slice(0, 35) + "..." : sub;
    display.drawText('"' + shown + '"', displayWidth / 2, displayHeight / 2 + 12);
}

// ---------------------------------------------------------------- network
// Returns { ok:boolean, status:number, text:string, err:string }
function fetchText(url, timeoutMs) {
    var out = { ok: false, status: 0, text: "", err: "" };
    if (!wifi || typeof wifi.httpFetch !== "function") {
        out.err = "WiFi module not available";
        return out;
    }
    try {
        var res = wifi.httpFetch(url, { method: "GET", responseType: "string" });
        if (typeof res === "string") {
            out.ok = res.length > 0;
            out.status = 200;
            out.text = res;
        } else if (res) {
            out.status = res.status || res.response || 0;
            out.ok = (res.ok === true) || (out.status >= 200 && out.status < 300);
            if (typeof res.body === "string") out.text = res.body;
            else if (res.body) out.text = JSON.stringify(res.body);
            if (!out.ok && out.status) out.err = "HTTP " + out.status;
        }
        if (out.ok && out.text.length === 0) { out.ok = false; out.err = "empty response"; }
    } catch (e) {
        out.err = (e && e.message) ? e.message : "request failed";
    }
    return out;
}

function netErrorPage(prompt, r) {
    pageLines = [
        "Prompt: " + prompt,
        "================================",
        "",
        "Network request failed.",
        "Connect WiFi in Bruce settings,",
        "then try again.",
        "",
        "Detail: " + (r.err || "no response")
    ];
}

function fetchAI(prompt) {
    showStatus("Asking AI...", prompt, CYAN);
    // https:// directly - Bruce's HTTP client does not follow http->https redirects.
    var r = fetchText("https://text.pollinations.ai/" + urlEncode(prompt), 30000);
    if (r.ok) {
        var body = stripMarkdown(toAscii(r.text));
        pageLines = ["Prompt: " + prompt, "================================", ""]
            .concat(wrapText(body, CHARS_PER_LINE));
        pageLines.push("");
        pageLines.push("[ Press A to ask another question ]");
    } else {
        netErrorPage(prompt, r);
    }
    scrollOffset = 0;
}

function fetchWiki(query) {
    showStatus("Searching Wikipedia...", query, YELLOW);
    var topic = urlEncode(query.split(" ").join("_"));
    var r = fetchText("https://en.wikipedia.org/api/rest_v1/page/summary/" + topic, 20000);
    var parsed = null;
    if (r.ok) {
        try { parsed = JSON.parse(r.text); } catch (e) { parsed = null; }
    }
    if (parsed && parsed.extract) {
        pageLines = ["Topic: " + toAscii(parsed.title || query), "================================", ""]
            .concat(wrapText(toAscii(parsed.extract), CHARS_PER_LINE));
        pageLines.push("");
        pageLines.push("[ Press A to search again ]");
        scrollOffset = 0;
    } else {
        // No article (404) or network trouble -> let the AI answer instead
        fetchAI("Define and summarize: " + query);
    }
}

// ---------------------------------------------------------------- input
var prevDown = {};
function readPin(pin) {
    try { return gpio.digitalRead(pin) === 0; } catch (e) {}
    return false;
}
function edge(pin) {                 // true once per press
    var d = readPin(pin);
    var was = prevDown[pin] === true;
    prevDown[pin] = d;
    return d && !was;
}
function scrollBy(n) {
    var maxOff = Math.max(0, pageLines.length - maxVisibleLines);
    var next = scrollOffset + n;
    if (next < 0) next = 0;
    if (next > maxOff) next = maxOff;
    if (next !== scrollOffset) {
        scrollOffset = next;
        drawBrowser();
    }
}

if (gpio) {
    var pins = [PIN_UP, PIN_DOWN, PIN_X, PIN_Y];
    for (var pi = 0; pi < pins.length; pi++) {
        try { gpio.pinMode(pins[pi], "input", "up"); } catch (errPm) {}
    }
}

// ---------------------------------------------------------------- main loop
loadHomePage();
drawBrowser();

var repeatAt = 0;
while (true) {
    if (keyboard.getEscPress()) break;                       // B / MENU / SELECT

    // Mode switch: X or Y
    if (edge(PIN_X) || edge(PIN_Y)) {
        mode = (mode === 0) ? 1 : 0;
        loadHomePage();
        drawBrowser();
    }

    // Scroll: UP/DOWN with auto-repeat, LEFT/RIGHT page
    var up = readPin(PIN_UP);
    var down = readPin(PIN_DOWN);
    var tNow = now();
    if ((up || down) && tNow >= repeatAt) {
        scrollBy(up ? -1 : 1);
        repeatAt = tNow + 90;
    }
    if (!up && !down) repeatAt = 0;
    if (keyboard.getPrevPress()) scrollBy(-maxVisibleLines + 1);
    if (keyboard.getNextPress()) scrollBy(maxVisibleLines - 1);

    // A (SelPress) = ask / search
    if (keyboard.getSelPress()) {
        var title = (mode === 0) ? "Ask the AI:" : "Wikipedia search:";
        var input = keyboard.keyboard(60, title, "");
        if (input && input.length > 0) {
            if (mode === 0) fetchAI(input); else fetchWiki(input);
        }
        drawBrowser();
        prevDown = {};
    }

    delay(30);
}

display.fill(BLACK);
