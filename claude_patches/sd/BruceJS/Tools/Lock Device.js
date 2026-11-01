// =============================================================================
//  Retro Handheld S3 - Professional Rock-Solid Lock Screen
//  Features:
//   - ZERO Flickering: Static elements rendered ONCE, no full-screen clearing
//   - 12-Hour AM/PM Time (Hours:Minutes) updating smoothly without seconds
//   - Top Status Bar with Live 12hr Time & Smoothed Battery %
//   - Clear Interactive Instruction: "PRESS [SELECT] TO ENTER PIN"
//   - 20 Curated Inspirational & Hacker Quotes updating on every boot/lock
//   - ONLY the SELECT button (GPIO 40) opens the PIN pad. A / START / B / D-pad do nothing.
//   - Battery % comes from Bruce's calibrated curve (device.getBatteryCharge, >= 3.96V = 100%)
// =============================================================================

var display = require("display");
var keyboard = require("keyboard");
var storage = require("storage");

var device = null;
try {
    device = require("device");
} catch (errDev) {}

var gpio = null;
try {
    gpio = require("gpio");
} catch (errGpio) {}

// Color Palette
var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var RED = display.color(255, 50, 50);
var GREEN = display.color(50, 255, 50);
var CYAN = display.color(0, 240, 255);
var GOLD = display.color(255, 205, 50);
var DARK_BG = display.color(20, 22, 32);
var DARK_GRAY = display.color(35, 38, 50);
var LIGHT_GRAY = display.color(160, 165, 180);
var MUTED_BLUE = display.color(70, 95, 130);

var displayWidth = display.width();
var displayHeight = display.height();

// Storage selection
var fileSystem = "sd";
try {
    var conf = storage.read({ fs: "sd", path: "/bruce.conf" });
    if (!conf) fileSystem = "littlefs";
} catch (errFs) {
    fileSystem = "littlefs";
}

var CONFIG_FILE = "/BruceJS/Tools/Lock Device.json";
var config = {
    password: null,
    baseTimeout: 10000,
    maxTimeout: 120000
};

function loadConfig() {
    try {
        var data = storage.read({ fs: fileSystem, path: CONFIG_FILE });
        if (data) {
            var parsed = JSON.parse(data);
            if (parsed && parsed.password) config.password = parsed.password;
        }
    } catch (errLoad) {}
}

function saveConfig() {
    try {
        storage.write({ fs: fileSystem, path: CONFIG_FILE }, JSON.stringify(config));
    } catch (errSave) {}
}

loadConfig();

// Format 12-hour AM/PM Time (Hours and Minutes only - no flickering seconds)
function get12HourComponents() {
    var nowMs = Date.now();
    var totalSec = Math.floor(nowMs / 1000);
    var totalMin = Math.floor(totalSec / 60);
    var min = totalMin % 60;
    var totalHours = Math.floor(totalMin / 60);
    var hour = totalHours % 24;
    var ampm = (hour >= 12) ? "PM" : "AM";
    var h12 = hour % 12;
    if (h12 === 0) h12 = 12;
    var mStr = (min < 10) ? ("0" + min) : ("" + min);
    return {
        h12: h12,
        min: mStr,
        ampm: ampm,
        timeShort: h12 + ":" + mStr + " " + ampm,
        clockDisplay: h12 + ":" + mStr,
        minuteKey: totalMin
    };
}

// Battery level from Bruce's own calibrated curve (>= 3.96V = 100%, EMA-smoothed in firmware).
// NOTE: the JS API name is device.getBatteryCharge() - there is NO device.getBattery().
// The old code called getBattery(), hit the catch block and always showed the hard-coded 77.
// Returns -1 when the value is unavailable so the UI shows "--%" instead of a fake number.
function getBatteryLevel() {
    try {
        if (device && typeof device.getBatteryCharge === "function") {
            var bat = device.getBatteryCharge();
            if (typeof bat === "number" && bat >= 0 && bat <= 100) return Math.round(bat);
        }
    } catch (errBat) {}
    try {
        if (device && typeof device.getBatteryDetailed === "function") {
            var det = device.getBatteryDetailed();
            if (det && typeof det.battery_percent === "number" &&
                det.battery_percent >= 0 && det.battery_percent <= 100) {
                return Math.round(det.battery_percent);
            }
        }
    } catch (errBat2) {}
    return -1;
}

// Draw Top Status Bar (Only updates coordinates without clearing screen)
function drawStatusBar(timeStr, bat) {
    display.drawFillRect(0, 0, displayWidth, 24, BLACK);
    display.drawLine(6, 24, displayWidth - 6, 24, DARK_GRAY);

    // Left: 12-Hour Time
    display.setTextAlign("left", "middle");
    display.setTextSize(1);
    display.setTextColor(WHITE, BLACK);
    display.drawText(timeStr, 12, 12);

    // Center badge
    display.setTextAlign("center", "middle");
    display.setTextColor(CYAN, BLACK);
    display.drawText("RETRO S3", displayWidth / 2, 12);

    // Right: Battery % and Icon
    display.setTextAlign("right", "middle");
    var batKnown = (bat >= 0);
    var batColor = (batKnown && bat < 20) ? RED : CYAN;
    display.setTextColor(batColor, BLACK);
    display.drawText(batKnown ? (bat + "%") : "--%", displayWidth - 44, 12);

    var bx = displayWidth - 40;
    var by = 6;
    var bw = 28;
    var bh = 12;
    display.drawRoundRect(bx, by, bw, bh, 2, DARK_GRAY);
    display.drawFillRect(bx + bw, by + 3, 2, bh - 6, DARK_GRAY);

    var numBars = batKnown ? Math.floor(bat / 20) : 0;
    if (batKnown && bat > 0 && numBars === 0) numBars = 1;
    if (batKnown && bat >= 96) numBars = 5;   // 100% must show a completely full cell
    for (var b = 0; b < numBars; b++) {
        display.drawFillRect(bx + 2 + b * 5, by + 2, 3, bh - 4, batColor);
    }
}

// Curated Greetings Collection (Rotating Gourav and JoiBoi)
var GREETINGS = [
    "Welcome back, Gourav!",
    "Welcome back, JoiBoi!",
    "System Unlocked. Hello Gourav!",
    "Ready to hack, JoiBoi!",
    "Greetings, Gourav! Have fun!",
    "Session Active: Welcome JoiBoi!",
    "Access Authorized for Gourav.",
    "Console Armed & Ready, JoiBoi!",
    "Welcome back, Captain Gourav!",
    "Great to see you again, JoiBoi!",
    "Welcome aboard, Gourav!",
    "Cyberdeck Activated. Hey JoiBoi!",
    "Good day, Gourav! Systems Nominal.",
    "Security Cleared. Go for it, JoiBoi!",
    "Welcome back, Legendary Gourav!",
    "Console Online. Welcome JoiBoi!"
];
var greetingIndex = Math.floor(Math.random() * GREETINGS.length);

// Curated Quotes Collection
var QUOTES = [
    { text: "Stay hungry, stay foolish.", author: "Steve Jobs" },
    { text: "The best way to predict the future is to invent it.", author: "Alan Kay" },
    { text: "Talk is cheap. Show me the code.", author: "Linus Torvalds" },
    { text: "It's dangerous to go alone! Take this.", author: "The Legend of Zelda" },
    { text: "Do or do not. There is no try.", author: "Master Yoda" },
    { text: "Simplicity is prerequisite for reliability.", author: "Edsger W. Dijkstra" },
    { text: "There is no place like 127.0.0.1.", author: "Hacker Culture" },
    { text: "The quieter you become, the more you can hear.", author: "Kali Linux" },
    { text: "Creativity is intelligence having fun.", author: "Albert Einstein" },
    { text: "Hardware makes it fast; software makes it slow.", author: "Craig Bruce" },
    { text: "The only way to do great work is to love it.", author: "Steve Jobs" },
    { text: "Reality is broken. Game designers can fix it.", author: "Jane McGonigal" },
    { text: "Knowledge is power, but curiosity is the key.", author: "Retro Go" },
    { text: "Hack the planet!", author: "The Plague (1995)" },
    { text: "Press Start to continue your journey.", author: "Arcade Classic" },
    { text: "Code is like humor. When you explain it, it's bad.", author: "Cory House" },
    { text: "Never stop exploring.", author: "BruceOS" },
    { text: "In the middle of difficulty lies opportunity.", author: "Albert Einstein" },
    { text: "Make it work, make it right, make it fast.", author: "Kent Beck" },
    { text: "The future belongs to those who learn more.", author: "Bruce Handheld" }
];

// Draw formatted quote centered
function drawQuote(quote, baseY) {
    var quoteText = '"' + quote.text + '"';
    var authorText = "- " + quote.author;

    display.setTextAlign("center", "middle");
    display.setTextSize(1);

    if (quoteText.length > 38) {
        var split = quoteText.lastIndexOf(" ", 36);
        if (split === -1) split = 34;
        var p1 = quoteText.substring(0, split);
        var p2 = quoteText.substring(split + 1);

        display.setTextColor(WHITE, BLACK);
        display.drawText(p1, displayWidth / 2, baseY);
        display.drawText(p2, displayWidth / 2, baseY + 13);

        display.setTextColor(GOLD, BLACK);
        display.drawText(authorText, displayWidth / 2, baseY + 28);
    } else {
        display.setTextColor(WHITE, BLACK);
        display.drawText(quoteText, displayWidth / 2, baseY + 4);

        display.setTextColor(GOLD, BLACK);
        display.drawText(authorText, displayWidth / 2, baseY + 22);
    }
}

// Initial PIN setup if not present
if (!config.password) {
    display.fill(BLACK);
    drawStatusBar(get12HourComponents().timeShort, getBatteryLevel());
    display.setTextAlign("center", "middle");
    display.setTextSize(2);
    display.setTextColor(CYAN, BLACK);
    display.drawText("SETUP PIN", displayWidth / 2, 60);

    display.setTextSize(1);
    display.setTextColor(WHITE, BLACK);
    display.drawText("Choose a 4-6 digit unlock PIN:", displayWidth / 2, 95);

    var newPin = keyboard.numKeyboard(10, "Create PIN:", true);
    if (newPin && newPin.length >= 4) {
        config.password = newPin;
        saveConfig();
        display.setTextColor(GREEN, BLACK);
        display.drawText("PIN SAVED!", displayWidth / 2, 160);
        delay(800);
    } else {
        config.password = "1234";
        saveConfig();
    }
}

// USER REQUIREMENT: ONLY the physical SELECT button (GPIO 40, active LOW) opens the PIN pad.
//
// Do NOT use keyboard.getSelPress() here: on this board the firmware maps SelPress to
// A *or* START (see boards/retro-handheld-s3/interface.cpp), which is why pressing A used to
// open the keypad. Reading GPIO 40 directly ignores every other key.
var SELECT_PIN = 40;
try { gpio.pinMode(SELECT_PIN, "input", "up"); } catch (errPin) {}

function selectIsDown() {
    try {
        return gpio.digitalRead(SELECT_PIN) === 0;
    } catch (errRead) {}
    return false;
}

// Debounced press: SELECT must read LOW on two reads 30ms apart.
function isUnlockRequested() {
    if (!selectIsDown()) return false;
    delay(30);
    return selectIsDown();
}

// The PIN pad treats SELECT as "cancel", so wait until the finger is off the button
// before opening it (otherwise the pad would close the instant it opens).
function waitSelectReleased() {
    var guard = 0;
    while (selectIsDown() && guard < 100) { // max ~2s
        delay(20);
        guard++;
    }
    delay(40);
}

// Swallow any key flags that piled up while the keypad / penalty screen was active.
function drainKeys() {
    try {
        for (var i = 0; i < 3; i++) {
            if (keyboard.getAnyPress) keyboard.getAnyPress();
        }
    } catch (errDrain) {}
}

// Render the entire static lock screen (ONLY called once on entry/reload)
function renderStaticScreen(quote) {
    display.fill(BLACK);

    // Outer stylish border
    display.drawRoundRect(3, 3, displayWidth - 6, displayHeight - 6, 6, MUTED_BLUE);

    // Security Status Pill
    display.drawRoundRect(displayWidth / 2 - 45, 30, 90, 16, 4, DARK_GRAY);
    display.setTextAlign("center", "middle");
    display.setTextSize(1);
    display.setTextColor(CYAN, BLACK);
    display.drawText("LOCKED", displayWidth / 2, 38);

    // Instruction Pill
    var pillY = 96;
    display.drawFillRect(28, pillY, displayWidth - 56, 26, DARK_BG);
    display.drawRoundRect(28, pillY, displayWidth - 56, 26, 6, CYAN);

    display.setTextSize(1);
    display.setTextColor(WHITE, DARK_BG);
    display.drawText("PRESS [SELECT] TO ENTER PIN", displayWidth / 2, pillY + 13);

    display.setTextColor(LIGHT_GRAY, BLACK);
    display.drawText("[ SELECT BUTTON ONLY ]", displayWidth / 2, 131);

    // Divider
    display.drawLine(35, 145, displayWidth - 35, 145, DARK_GRAY);

    // Quote
    drawQuote(quote, 162);

    // Bottom hint
    display.setTextColor(DARK_GRAY, BLACK);
    display.setTextSize(1);
    display.drawText("Retro Go Dual-Boot  v1.0", displayWidth / 2, 222);
}

// Redraw ONLY the clock without clearing the screen (100% flicker-free)
function updateClockOnly(tc) {
    // Clear only the clock area
    display.drawFillRect(60, 52, displayWidth - 120, 36, BLACK);

    // Big 12-Hour Digital Clock (Hours:Minutes)
    display.setTextAlign("center", "middle");
    display.setTextSize(3);
    display.setTextColor(WHITE, BLACK);
    display.drawText(tc.clockDisplay, displayWidth / 2 - 16, 68);

    // AM/PM badge
    display.setTextSize(1);
    display.setTextColor(CYAN, BLACK);
    display.drawText(tc.ampm, displayWidth / 2 + 56, 68);
}

// Main Lock Loop
var unlocked = false;
var failedAttempts = 0;
var lastRenderMin = -1;
var lastBatMs = 0;
var quoteIndex = Math.floor(Math.random() * QUOTES.length);

// Initial Static Render
renderStaticScreen(QUOTES[quoteIndex]);

while (!unlocked) {
    var tc = get12HourComponents();

    // Only update clock when the MINUTE changes (zero flickering!)
    if (tc.minuteKey !== lastRenderMin) {
        lastRenderMin = tc.minuteKey;

        // Update status bar time and battery
        drawStatusBar(tc.timeShort, getBatteryLevel());

        // Update central clock
        updateClockOnly(tc);
    }

    // Refresh the battery readout every 10s (it used to update only when the minute changed)
    var nowMs = now();
    if (nowMs - lastBatMs > 10000) {
        lastBatMs = nowMs;
        drawStatusBar(tc.timeShort, getBatteryLevel());
    }

    // ONLY the SELECT button opens the PIN pad
    if (isUnlockRequested()) {
        waitSelectReleased();
        display.fill(BLACK);
        drawStatusBar(tc.timeShort, getBatteryLevel());

        display.setTextAlign("center", "middle");
        display.setTextSize(2);
        display.setTextColor(CYAN, BLACK);
        display.drawText("ENTER PIN", displayWidth / 2, 60);

        display.setTextSize(1);
        display.setTextColor(LIGHT_GRAY, BLACK);
        display.drawText("Default: 1234", displayWidth / 2, 85);

        // Open PIN keypad
        var entered = keyboard.numKeyboard(10, "Enter PIN:", true);
        drainKeys();

        if (entered === config.password) {
            unlocked = true;

            // Success Screen
            display.fill(BLACK);
            display.drawRoundRect(6, 6, displayWidth - 12, displayHeight - 12, 6, GREEN);
            display.setTextAlign("center", "middle");
            display.setTextSize(2);
            display.setTextColor(GREEN, BLACK);
            display.drawText("ACCESS GRANTED", displayWidth / 2, displayHeight / 2 - 16);

            display.setTextSize(1);
            display.setTextColor(WHITE, BLACK);
            var welcomeMsg = GREETINGS[greetingIndex];
            display.drawText(welcomeMsg, displayWidth / 2, displayHeight / 2 + 14);

            display.setTextColor(CYAN, BLACK);
            display.drawText("Authenticating BruceOS Session...", displayWidth / 2, displayHeight / 2 + 34);

            // Display welcome screen for 3 full seconds as requested
            delay(3000);
            break;
        } else if (entered && entered.length > 0) {
            failedAttempts++;
            display.fill(BLACK);
            drawStatusBar(tc.timeShort, getBatteryLevel());

            display.setTextAlign("center", "middle");
            display.setTextSize(2);
            display.setTextColor(RED, BLACK);
            display.drawText("INCORRECT PIN", displayWidth / 2, 70);

            var penaltySec = Math.min(2 * failedAttempts, 12);
            display.setTextSize(1);
            display.setTextColor(WHITE, BLACK);
            display.drawText("Attempts: " + failedAttempts, displayWidth / 2, 105);

            for (var s = penaltySec; s > 0; s--) {
                display.drawFillRect(30, 135, displayWidth - 60, 30, BLACK);
                display.setTextColor(RED, BLACK);
                display.drawText("Penalty wait: " + s + "s", displayWidth / 2, 150);
                delay(1000);
            }

            // Update quote and re-render static screen
            quoteIndex = (quoteIndex + 1) % QUOTES.length;
            renderStaticScreen(QUOTES[quoteIndex]);
            lastRenderMin = -1; // force clock update
        } else {
            // Cancelled out of keypad (empty string / ESC)
            quoteIndex = (quoteIndex + 1) % QUOTES.length;
            renderStaticScreen(QUOTES[quoteIndex]);
            lastRenderMin = -1; // force clock update
            waitSelectReleased(); // SELECT cancels the pad; don't instantly re-open it
            drainKeys();
        }
    }

    delay(50);
}

// Exit cleanly
display.fill(BLACK);
