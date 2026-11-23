// =============================================================================
//  Retro Handheld S3 - RC522 RFID & NFC Diagnostic Scanner (v2.3)
//  Pins: SDA->IO35 | RST->3.3V | SCK->12 | MOSI->11 | MISO->13 | SD_CS->10
//  Exit: Hold [B] button for 1.5 seconds (or START+SELECT)
// =============================================================================

// -----------------------------------------------------------------------------
// 1. MODULE IMPORTS & CONSTANTS
// -----------------------------------------------------------------------------
var display = (typeof globalThis !== "undefined" && globalThis.display) ? globalThis.display : require("display");
var gpio    = (typeof globalThis !== "undefined" && globalThis.gpio) ? globalThis.gpio : require("gpio");

var rfid = null;
if (typeof globalThis !== "undefined" && globalThis.rfid) {
    rfid = globalThis.rfid;
} else if (typeof rfid !== "undefined") {
    // rfid in scope
} else {
    try {
        rfid = require("rfid");
    } catch (eRfidReq) {
        rfid = null;
    }
}

var BLACK     = display.color(0, 0, 0);
var WHITE     = display.color(255, 255, 255);
var GREEN     = display.color(0, 255, 120);
var RED       = display.color(255, 60, 60);
var CYAN      = display.color(0, 220, 255);
var GOLD      = display.color(255, 200, 40);
var DARK_GRAY = display.color(28, 32, 42);
var BLUE_BG   = display.color(14, 20, 36);
var CARD_BG   = display.color(18, 48, 28);
var BAR_BG    = display.color(45, 50, 65);

var W = display.width();
var H = display.height();

// -----------------------------------------------------------------------------
// 2. HARDWARE PIN SETTLE
// -----------------------------------------------------------------------------
try {
    // MicroSD CS (pin 10) HIGH so SD card does not drive MISO
    gpio.pinMode(10, "output");
    gpio.digitalWrite(10, 1);

    // RC522 SDA/CS (pin 43) HIGH initially
    gpio.pinMode(43, "output");
    gpio.digitalWrite(43, 1);
} catch (eHwPins) {}

// Exit buttons configuration (internal pullup)
try {
    gpio.pinMode(21, "input", "up"); // B button
    gpio.pinMode(39, "input", "up"); // MENU button
    gpio.pinMode(38, "input", "up"); // START button
    gpio.pinMode(40, "input", "up"); // SELECT button
} catch (eBtnInit) {}

// -----------------------------------------------------------------------------
// 3. HELPER FUNCTIONS
// -----------------------------------------------------------------------------
var radarFrames = ["[-       ]", "[--      ]", "[---     ]", "[ ----   ]", "[  ----  ]", "[   ---- ]", "[     ---]", "[      --]", "[       -]"];

var beep = function() {
    try {
        var snd = (typeof audio !== "undefined") ? audio : require("audio");
        if (snd && snd.tone) {
            snd.tone(2500, 90);
        }
    } catch (eSnd) {}
};

var parseDiagnostic = function() {
    var info = {
        ok: false,
        raw: "",
        ver: "--",
        tx: "--",
        req: "--",
        uid: ""
    };
    if (!rfid || !rfid.readUID) {
        info.raw = "RFID module not loaded";
        return info;
    }
    try {
        var res = rfid.readUID(0);
        if (typeof res === "string" && res.length > 0) {
            info.raw = res;
            // Expected format: V:0x82|TX:0x83|REQ:3|UID:NONE
            var parts = res.split("|");
            for (var i = 0; i < parts.length; i++) {
                var kv = parts[i].split(":");
                if (kv.length >= 2) {
                    var k = kv[0];
                    var v = kv.slice(1).join(":");
                    if (k === "V") info.ver = v;
                    else if (k === "TX") info.tx = v;
                    else if (k === "REQ") info.req = v;
                    else if (k === "UID") {
                        if (v !== "NONE" && v.length > 0) info.uid = v;
                    }
                }
            }
            if (info.ver === "0x82" || info.ver === "0x92" || info.ver === "0x91" || (info.ver !== "0xFF" && info.ver !== "0x00" && info.ver !== "--")) {
                info.ok = true;
            }
        }
    } catch (eProbe) {
        info.raw = "Probe err: " + eProbe;
    }
    return info;
};

var drawStaticFrame = function(diag) {
    display.fill(BLACK);
    display.drawFillRoundRect(4, 4, W - 8, H - 8, 6, BLUE_BG);
    display.drawRoundRect(4, 4, W - 8, H - 8, 6, CYAN);

    display.setTextAlign("center", "middle");
    display.setTextSize(2);
    display.setTextColor(CYAN, BLUE_BG);
    display.drawText("RC522 RFID SCANNER", W / 2, 18);

    display.setTextSize(1);
    display.setTextColor(GOLD, BLUE_BG);
    display.drawText("13.56 MHz ISO 14443-A Diagnostic Engine", W / 2, 34);

    // Hardware Wiring Info Box
    display.drawFillRoundRect(12, 46, W - 24, 42, 4, DARK_GRAY);
    display.drawRoundRect(12, 46, W - 24, 42, 4, display.color(65, 75, 95));

    display.setTextAlign("left", "top");
    display.setTextSize(1);
    display.setTextColor(WHITE, DARK_GRAY);
    display.drawText("Pins: SDA->IO43 | RST->3.3V | SCK->12 | MOSI->11 | MISO->13", 18, 51);

    var statColor = diag.ok ? GREEN : RED;
    var chipName = (diag.ver === "0x82") ? "FM17522 (0x82)" : (diag.ver === "0x92" ? "RC522 v2 (0x92)" : "Chip " + diag.ver);
    display.setTextColor(statColor, DARK_GRAY);
    if (diag.ok) {
        display.drawText("HW:   " + chipName + " READY  |  Antenna: " + diag.tx, 18, 63);
    } else {
        display.drawText("HW:   DISCONNECTED (" + diag.ver + ")  |  Check SDA/SCK", 18, 63);
    }

    display.setTextColor(CYAN, DARK_GRAY);
    display.drawText("Bus:  Shared SPI (MicroSD CS:10 Protected HIGH)", 18, 75);
};

var drawIdleBox = function(tickCount, scanCount, diag) {
    display.drawFillRoundRect(12, 92, W - 24, 114, 4, DARK_GRAY);
    display.drawRoundRect(12, 92, W - 24, 114, 4, diag.ok ? CYAN : RED);

    display.setTextAlign("center", "middle");
    display.setTextSize(1);

    if (!diag.ok) {
        display.setTextColor(RED, DARK_GRAY);
        display.drawText("! HARDWARE COMMUNICATION CHECK !", W / 2, 108);
        display.setTextColor(WHITE, DARK_GRAY);
        display.drawText("SPI MISO returned " + diag.ver + " (No response from RC522)", W / 2, 126);
        display.setTextColor(GOLD, DARK_GRAY);
        display.drawText("Wiring: SDA->IO43, RST->3.3V, 3.3V, GND", W / 2, 142);
        display.drawText("Shared SPI: SCK->12, MOSI->11, MISO->13", W / 2, 156);
        display.setTextColor(CYAN, DARK_GRAY);
        display.drawText("Polling active... Tap card if connected", W / 2, 184);
        return;
    }

    display.setTextColor(CYAN, DARK_GRAY);
    var anim = radarFrames[tickCount % radarFrames.length];
    display.drawText("ACTIVE RF FIELD " + anim, W / 2, 110);

    display.setTextColor(WHITE, DARK_GRAY);
    display.drawText("TAP 13.56 MHz CARD, TAG, OR FOB", W / 2, 130);
    display.setTextColor(display.color(180, 190, 210), DARK_GRAY);
    display.drawText("MIFARE Classic 1K/4K, Ultralight, NTAG213/215/216", W / 2, 148);
    display.drawText("Access Badges, Keychains, Android / iOS NFC", W / 2, 162);

    display.setTextColor(GOLD, DARK_GRAY);
    display.drawText("Polls: " + tickCount + "  |  Scanned: " + scanCount + "  |  REQ: " + diag.req, W / 2, 186);
};

var drawDetectedCardBox = function(tag, scanCount) {
    display.drawFillRoundRect(12, 92, W - 24, 114, 4, CARD_BG);
    display.drawRoundRect(12, 92, W - 24, 114, 4, GREEN);

    display.setTextAlign("left", "top");
    display.setTextSize(1);

    display.setTextColor(GREEN, CARD_BG);
    display.drawText(">>> TAG DETECTED! (Scan #" + scanCount + ") <<<", 20, 100);

    display.setTextSize(2);
    display.setTextColor(WHITE, CARD_BG);
    display.drawText(String(tag.uid || "NO UID"), 20, 116);

    display.setTextSize(1);
    display.setTextColor(CYAN, CARD_BG);
    display.drawText("Type: " + String(tag.type || "ISO 14443-A (13.56 MHz)"), 20, 140);

    display.setTextColor(GOLD, CARD_BG);
    display.drawText("SAK:  0x" + String(tag.sak || "--") + "   ATQA: 0x" + String(tag.atqa || "--"), 20, 156);

    display.setTextColor(WHITE, CARD_BG);
    if (tag.totalPages) {
        display.drawText("Total Pages: " + tag.totalPages, 20, 172);
    } else {
        display.drawText("Protocol: ISO/IEC 14443-A (MIFARE/NFC)", 20, 172);
    }

    display.setTextColor(GREEN, CARD_BG);
    display.drawText("[ Remove tag to scan next ]", 20, 188);
};

var drawExitBar = function(holdCount, maxHold) {
    var pct = holdCount / maxHold;
    if (pct > 1) pct = 1;
    var barW = Math.floor((W - 32) * pct);

    display.drawFillRoundRect(16, 212, W - 32, 18, 3, BAR_BG);
    if (barW > 4) {
        display.drawFillRoundRect(16, 212, barW, 18, 3, (pct >= 1) ? GREEN : GOLD);
    }
    display.drawRoundRect(16, 212, W - 32, 18, 3, display.color(100, 110, 130));

    display.setTextAlign("center", "middle");
    display.setTextSize(1);
    display.setTextColor(WHITE, (barW > W / 2) ? display.color(30, 40, 50) : BAR_BG);
    if (holdCount > 0) {
        display.drawText("HOLDING [B] TO EXIT (" + Math.floor(pct * 100) + "%)", W / 2, 221);
    } else {
        display.drawText("Exit: Hold [B] button for 1.5 seconds", W / 2, 221);
    }
};

// -----------------------------------------------------------------------------
// 4. STARTUP INITIALIZATION
// -----------------------------------------------------------------------------
var diag = parseDiagnostic();
drawStaticFrame(diag);

var loopTicks = 0;
var scanCount = 0;
var lastUid = "";
var lastSeenTick = 0;
var exitHold = 0;
var MAX_EXIT_HOLD = 14; // ~1.4s sustained hold
var GRACE_TICKS = 25;   // ~2.5s absolute startup guard

drawIdleBox(0, 0, diag);
drawExitBar(0, MAX_EXIT_HOLD);
delay(150);

// -----------------------------------------------------------------------------
// 5. MAIN SCANNING LOOP
// -----------------------------------------------------------------------------
while (true) {
    loopTicks++;

    // Probing hardware diagnostic status (takes <2ms)
    diag = parseDiagnostic();

    // Check Exit Input with Sustained Hold
    var btnB = 1;
    var btnMenu = 1;
    var btnSel = 1;
    var btnStart = 1;

    try {
        btnB = gpio.digitalRead(21);
        btnMenu = gpio.digitalRead(39);
        btnSel = gpio.digitalRead(40);
        btnStart = gpio.digitalRead(38);
    } catch (eBtnRd) {}

    var exitPressed = (btnB === 0) || (btnMenu === 0) || (btnSel === 0 && btnStart === 0);

    // Enforce startup grace period: never exit during initial 2.5s
    if (loopTicks <= GRACE_TICKS) {
        exitPressed = false;
        exitHold = 0;
    }

    if (exitPressed) {
        exitHold++;
        drawExitBar(exitHold, MAX_EXIT_HOLD);
        if (exitHold >= MAX_EXIT_HOLD) {
            display.fill(BLACK);
            display.setTextAlign("center", "middle");
            display.setTextSize(2);
            display.setTextColor(GREEN, BLACK);
            display.drawText("EXITING SCANNER...", W / 2, H / 2);
            delay(400);
            break;
        }
    } else {
        if (exitHold > 0) {
            exitHold = 0;
            drawExitBar(0, MAX_EXIT_HOLD);
        }
    }

    // --- Check for Tag ---
    var tag = null;

    // Fast path: if diag probe already read the UID directly
    if (diag.uid && diag.uid.length > 0) {
        tag = {
            uid: diag.uid,
            type: "13.56 MHz ISO 14443-A",
            sak: "--",
            atqa: "--"
        };
    } else if (rfid) {
        // Fallback: full read metadata
        try {
            tag = rfid.read(1);
        } catch (eRead) {
            tag = null;
        }

        if ((!tag || !tag.uid) && rfid.readUID) {
            try {
                var raw = rfid.readUID(1);
                if (raw && typeof raw === "string" && raw.length > 0 &&
                    raw.indexOf("V:") === -1 && raw.indexOf("OK:") === -1 && raw.indexOf("ERR:") === -1) {
                    tag = {
                        uid: raw,
                        type: "13.56 MHz ISO 14443-A",
                        sak: "--",
                        atqa: "--"
                    };
                }
            } catch (eRaw) {
                tag = null;
            }
        }
    }

    if (tag && tag.uid && tag.uid.length > 0) {
        var isNew = (tag.uid !== lastUid) || ((loopTicks - lastSeenTick) > 18);
        if (isNew) {
            scanCount++;
            lastUid = tag.uid;
            lastSeenTick = loopTicks;
            beep();
            drawDetectedCardBox(tag, scanCount);
            drawExitBar(exitHold, MAX_EXIT_HOLD);
            delay(1200); // Hold detected card view
        }
    } else {
        // Idle polling display update
        drawIdleBox(loopTicks, scanCount, diag);
        drawExitBar(exitHold, MAX_EXIT_HOLD);
    }

    delay(75);
}

display.fill(BLACK);
