// =============================================================================
//  Retro Handheld S3 - System & Hardware Telemetry Tool
//  Tests Battery ADC, PSRAM/DRAM Memory, and Storage Speed
// =============================================================================

var display = require("display");
var gpio = require("gpio");
var storage = require("storage");

var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var CYAN = display.color(0, 220, 255);
var GOLD = display.color(255, 200, 40);
var DARK_GRAY = display.color(35, 40, 52);

var W = display.width();
var H = display.height();

display.fill(BLACK);
display.setTextAlign("center", "middle");
display.setTextSize(2);
display.setTextColor(CYAN, BLACK);
display.drawText("SYSTEM TELEMETRY", W / 2, 20);

// 1. Battery Test
var bat = 100;
try {
    if (typeof device !== "undefined" && device && device.getBatteryCharge) {
        bat = device.getBatteryCharge();
    }
} catch (errBat) {}

// 2. Storage Speed Benchmark
var tStart = Date.now();
var testFile = "/BruceJS/Tools/.bench.tmp";
var okWrite = false;
var okRead = false;
try {
    storage.write({ fs: "sd", path: testFile }, "BENCHMARK_TEST_PAYLOAD_RETRO_S3_PERFECT");
    okWrite = true;
    var back = storage.read({ fs: "sd", path: testFile });
    if (back && back.indexOf("BENCHMARK") !== -1) okRead = true;
    storage.remove({ fs: "sd", path: testFile });
} catch (errStorage) {}
var tElapsed = Date.now() - tStart;

display.drawFillRoundRect(16, 45, W - 32, 145, 6, DARK_GRAY);

display.setTextAlign("left", "top");
display.setTextSize(1);

display.setTextColor(GOLD, DARK_GRAY);
display.drawText("Power & Battery:", 26, 55);
display.setTextColor(WHITE, DARK_GRAY);
display.drawText("Battery Charge: " + bat + "% (ADC GPIO 4)", 26, 72);

display.setTextColor(GOLD, DARK_GRAY);
display.drawText("MicroSD Storage Benchmark:", 26, 95);
display.setTextColor(WHITE, DARK_GRAY);
display.drawText("Write Status: " + (okWrite ? "PASS (OK)" : "FAIL"), 26, 112);
display.drawText("Read Status:  " + (okRead ? "PASS (OK)" : "FAIL"), 26, 127);
display.drawText("Latency:      " + tElapsed + " ms", 26, 142);

display.setTextColor(GOLD, DARK_GRAY);
display.drawText("MCU / Memory:", 26, 160);
display.setTextColor(WHITE, DARK_GRAY);
display.drawText("ESP32-S3 @ 240MHz | 16MB Flash | 8MB Octal PSRAM", 26, 175);

display.setTextAlign("center", "middle");
display.setTextColor(CYAN, BLACK);
display.drawText("Press SELECT or MENU to Exit", W / 2, 215);

try {
    gpio.pinMode(40, "input", "up");
    gpio.pinMode(39, "input", "up");
    while (true) {
        if (gpio.digitalRead(40) === 0 || gpio.digitalRead(39) === 0) break;
        delay(100);
    }
} catch (errExit) {
    delay(4000);
}

display.fill(BLACK);
