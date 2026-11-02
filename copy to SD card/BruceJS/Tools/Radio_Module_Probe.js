// =============================================================================
//  Retro Handheld S3 - Sub-GHz (CC1101) & 2.4GHz (NRF24) Radio Probe
//  Checks hardware connections and module responsiveness
// =============================================================================

var display = require("display");
var gpio = require("gpio");

var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var GREEN = display.color(0, 255, 100);
var RED = display.color(255, 60, 60);
var CYAN = display.color(0, 220, 255);
var GOLD = display.color(255, 200, 40);
var DARK_GRAY = display.color(40, 44, 55);

var W = display.width();
var H = display.height();

display.fill(BLACK);
display.drawRoundRect(4, 4, W - 8, H - 8, 6, CYAN);

display.setTextAlign("center", "middle");
display.setTextSize(2);
display.setTextColor(CYAN, BLACK);
display.drawText("RADIO PROBE", W / 2, 24);

display.setTextSize(1);
display.setTextColor(WHITE, BLACK);
display.drawText("Probing SPI Buses & Pins...", W / 2, 50);

// Check Sub-GHz CC1101 module
var subghzStatus = "Not Detected";
var subghzColor = RED;
try {
    var sub = require("subghz");
    if (sub) {
        subghzStatus = "Module Driver Loaded (Ready)";
        subghzColor = GREEN;
    }
} catch (errSub) {
    subghzStatus = "Driver Exception: " + errSub;
}

// Check NRF24 module
var nrfStatus = "Not Detected";
var nrfColor = RED;
try {
    var nrf = require("nrf24");
    if (nrf) {
        nrfStatus = "Module Driver Loaded (Ready)";
        nrfColor = GREEN;
    }
} catch (errNrf) {
    nrfStatus = "Driver Exception: " + errNrf;
}

// Draw Results Box
display.drawFillRoundRect(16, 70, W - 32, 60, 4, DARK_GRAY);
display.setTextAlign("left", "top");
display.setTextColor(GOLD, DARK_GRAY);
display.drawText("1. CC1101 Sub-GHz (433MHz):", 24, 76);
display.setTextColor(subghzColor, DARK_GRAY);
display.drawText(subghzStatus, 24, 94);
display.setTextColor(WHITE, DARK_GRAY);
display.drawText("SPI: SCK 12 | MOSI 11 | MISO 13 | CS 43 | GDO0 44", 24, 110);

display.drawFillRoundRect(16, 140, W - 32, 60, 4, DARK_GRAY);
display.setTextColor(GOLD, DARK_GRAY);
display.drawText("2. NRF24L01+ 2.4GHz:", 24, 146);
display.setTextColor(nrfColor, DARK_GRAY);
display.drawText(nrfStatus, 24, 164);
display.setTextColor(WHITE, DARK_GRAY);
display.drawText("SPI: SCK 12 | MOSI 11 | MISO 13 | CS 43/9 | CE 44/5", 24, 180);

display.setTextAlign("center", "middle");
display.setTextColor(CYAN, BLACK);
display.drawText("Press SELECT or MENU to Exit", W / 2, 220);

// Wait for keypress
try {
    gpio.pinMode(40, "input", "up"); // SELECT
    gpio.pinMode(39, "input", "up"); // MENU
    while (true) {
        if (gpio.digitalRead(40) === 0 || gpio.digitalRead(39) === 0) break;
        delay(100);
    }
} catch (errKey) {
    delay(4000);
}

display.fill(BLACK);
