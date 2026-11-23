// =============================================================================
//  Retro Handheld S3 - BruceJS File Editor
//  Edit configuration files directly on your console without a PC
// =============================================================================

var display = require("display");
var keyboard = require("keyboard");
var storage = require("storage");
var gpio = require("gpio");

var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var GREEN = display.color(0, 255, 100);
var CYAN = display.color(0, 220, 255);
var GOLD = display.color(255, 200, 40);
var RED = display.color(255, 60, 60);
var DARK_GRAY = display.color(35, 40, 52);

var W = display.width();
var H = display.height();

var fileSystem = "sd";
try {
    var conf = storage.read({ fs: "sd", path: "/bruce.conf" });
    if (!conf) fileSystem = "littlefs";
} catch (errFs) {
    fileSystem = "littlefs";
}

var QUICK_FILES = [
    "/BruceJS/Tools/Lock Device.json",
    "/retro-go/config/wifi.json",
    "/bruce.conf"
];

display.fill(BLACK);
display.setTextAlign("center", "middle");
display.setTextSize(2);
display.setTextColor(CYAN, BLACK);
display.drawText("FILE EDITOR", W / 2, 25);

display.setTextSize(1);
display.setTextColor(WHITE, BLACK);
display.drawText("1. Edit Lock Device.json", W / 2, 70);
display.drawText("2. Edit wifi.json", W / 2, 100);
display.drawText("3. Custom File Path", W / 2, 130);
display.setTextColor(GOLD, BLACK);
display.drawText("Press 1, 2, or 3 (or A to pick)", W / 2, 175);
display.setTextColor(DARK_GRAY, BLACK);
display.drawText("Press MENU or B to cancel", W / 2, 210);

var choice = keyboard.keyboard(30, "File (1=Lock, 2=WiFi, or path):", "1");
var targetPath = "";

if (choice === "1" || choice === "lock") {
    targetPath = "/BruceJS/Tools/Lock Device.json";
} else if (choice === "2" || choice === "wifi") {
    targetPath = "/retro-go/config/wifi.json";
} else if (choice && choice.length > 2) {
    targetPath = choice;
}

if (targetPath.length > 0) {
    var content = "";
    try {
        content = storage.read({ fs: fileSystem, path: targetPath });
        if (!content) content = "";
    } catch (errR) {
        content = "";
    }

    display.fill(BLACK);
    display.setTextAlign("center", "middle");
    display.setTextSize(1);
    display.setTextColor(CYAN, BLACK);
    display.drawText("Editing: " + targetPath, W / 2, 30);
    display.setTextColor(WHITE, BLACK);
    display.drawText("Current content: " + content.slice(0, 35), W / 2, 70);

    var newContent = keyboard.keyboard(120, "Edit Text:", content);
    if (newContent && newContent.length > 0) {
        try {
            storage.write({ fs: fileSystem, path: targetPath }, newContent);
            display.fill(BLACK);
            display.setTextColor(GREEN, BLACK);
            display.setTextSize(2);
            display.drawText("FILE SAVED!", W / 2, H / 2 - 10);
            display.setTextSize(1);
            display.setTextColor(WHITE, BLACK);
            display.drawText(targetPath, W / 2, H / 2 + 20);
            delay(2000);
        } catch (errW) {
            display.fill(BLACK);
            display.setTextColor(RED, BLACK);
            display.setTextSize(2);
            display.drawText("SAVE FAILED!", W / 2, H / 2);
            delay(2000);
        }
    }
}

display.fill(BLACK);
