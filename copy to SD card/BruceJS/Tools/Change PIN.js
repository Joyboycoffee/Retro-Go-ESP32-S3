// =============================================================================
//  Retro Handheld S3 - Change Lock Device PIN Tool
// =============================================================================

var display = require("display");
var keyboard = require("keyboard");
var storage = require("storage");

var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var RED = display.color(255, 50, 50);
var GREEN = display.color(50, 255, 50);
var CYAN = display.color(0, 240, 255);
var DARK_GRAY = display.color(35, 38, 50);

var displayWidth = display.width();
var displayHeight = display.height();

var fileSystem = "sd";
try {
    var conf = storage.read({ fs: "sd", path: "/bruce.conf" });
    if (!conf) fileSystem = "littlefs";
} catch (errFs) {
    fileSystem = "littlefs";
}

var CONFIG_FILE = "/BruceJS/Tools/Lock Device.json";
var config = {
    password: "1234",
    baseTimeout: 10000,
    maxTimeout: 120000
};

try {
    var data = storage.read({ fs: fileSystem, path: CONFIG_FILE });
    if (data) {
        var parsed = JSON.parse(data);
        if (parsed && parsed.password) config = parsed;
    }
} catch (e) {}

display.fill(BLACK);
display.drawRoundRect(6, 6, displayWidth - 12, displayHeight - 12, 6, CYAN);
display.setTextAlign("center", "middle");
display.setTextSize(2);
display.setTextColor(CYAN, BLACK);
display.drawText("CHANGE PIN", displayWidth / 2, 50);

display.setTextSize(1);
display.setTextColor(WHITE, BLACK);
display.drawText("Enter Current PIN:", displayWidth / 2, 85);

var current = keyboard.numKeyboard(10, "Current PIN:", true);
if (current !== config.password && config.password !== null) {
    display.fill(BLACK);
    display.setTextColor(RED, BLACK);
    display.setTextSize(2);
    display.drawText("WRONG PIN!", displayWidth / 2, 100);
    delay(2000);
} else {
    display.fill(BLACK);
    display.setTextColor(CYAN, BLACK);
    display.setTextSize(2);
    display.drawText("NEW PIN", displayWidth / 2, 50);

    display.setTextSize(1);
    display.setTextColor(WHITE, BLACK);
    display.drawText("Enter New 4-6 Digit PIN:", displayWidth / 2, 85);

    var newPin = keyboard.numKeyboard(10, "New PIN:", true);
    if (newPin && newPin.length >= 4) {
        config.password = newPin;
        try {
            storage.write({ fs: fileSystem, path: CONFIG_FILE }, JSON.stringify(config));
            display.fill(BLACK);
            display.setTextColor(GREEN, BLACK);
            display.setTextSize(2);
            display.drawText("PIN UPDATED!", displayWidth / 2, 100);
            display.setTextSize(1);
            display.setTextColor(WHITE, BLACK);
            display.drawText("New PIN: " + newPin, displayWidth / 2, 140);
            delay(2500);
        } catch (errW) {
            display.fill(BLACK);
            display.setTextColor(RED, BLACK);
            display.drawText("SAVE ERROR", displayWidth / 2, 100);
            delay(2000);
        }
    } else {
        display.fill(BLACK);
        display.setTextColor(RED, BLACK);
        display.setTextSize(2);
        display.drawText("CANCELLED", displayWidth / 2, 100);
        delay(1500);
    }
}

display.fill(BLACK);
