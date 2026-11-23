// =============================================================================
//  Retro Handheld S3 - IR Blaster Continuous Test Tool
//  Fires continuous pulses on GPIO 43 (TX / L-R pin) to test IR LEDs via camera
// =============================================================================

var display = require("display");
var gpio = require("gpio");

var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var CYAN = display.color(0, 220, 255);
var PURPLE = display.color(180, 50, 255);
var RED = display.color(255, 60, 60);
var GREEN = display.color(50, 255, 100);
var DARK_GRAY = display.color(30, 35, 45);

var W = display.width();
var H = display.height();

var IR_PIN = 43; // Expansion TX pin / L-R trace

// Setup IR pin
try {
    gpio.pinMode(IR_PIN, "output");
    gpio.digitalWrite(IR_PIN, 0);
} catch (ePin) {}

// Setup Exit Buttons
var BTN_B = 21;
var BTN_SEL = 40;
var BTN_MENU = 39;
var BTN_A = 47;

try {
    gpio.pinMode(BTN_B, "input", "up");
    gpio.pinMode(BTN_SEL, "input", "up");
    gpio.pinMode(BTN_MENU, "input", "up");
    gpio.pinMode(BTN_A, "input", "up");
} catch (eBtn) {}

display.fill(BLACK);

// Draw Header
display.setTextAlign("center", "top");
display.setTextSize(2);
display.setTextColor(CYAN, BLACK);
display.drawText("IR BLASTER TEST", W / 2, 12);

display.setTextSize(1);
display.setTextColor(WHITE, BLACK);
display.drawText("Output: GPIO 43 (Expansion TX / L-R)", W / 2, 36);

// Instruction Card
display.drawFillRoundRect(16, 52, W - 32, 60, 6, DARK_GRAY);
display.setTextColor(PURPLE, DARK_GRAY);
display.drawText("CAMERA TEST INSTRUCTIONS:", W / 2, 60);
display.setTextColor(WHITE, DARK_GRAY);
display.drawText("Point your phone's SELFIE CAMERA at the bulb.", W / 2, 76);
display.drawText("You will see a bright PURPLE / VIOLET glow.", W / 2, 92);

// Footer
display.setTextAlign("center", "bottom");
display.setTextColor(CYAN, BLACK);
display.drawText("Press B or SELECT to Stop & Exit", W / 2, H - 10);

var count = 0;
var state = false;

while (true) {
    // Check exit buttons (Active LOW)
    try {
        if (gpio.digitalRead(BTN_B) === 0 || gpio.digitalRead(BTN_SEL) === 0 || gpio.digitalRead(BTN_MENU) === 0) {
            break;
        }
    } catch (eExit) {}

    state = !state;
    if (state) count++;

    // Pulse GPIO 43
    try {
        gpio.digitalWrite(IR_PIN, state ? 1 : 0);
    } catch (eWrite) {}

    // Draw Live Status Indicator Box
    var boxY = 122;
    var boxH = 75;
    display.drawFillRoundRect(16, boxY, W - 32, boxH, 8, DARK_GRAY);

    if (state) {
        // Glowing visual indicator
        display.drawFillCircle(W / 2, boxY + 28, 16, PURPLE);
        display.drawCircle(W / 2, boxY + 28, 20, WHITE);
        display.setTextAlign("center", "middle");
        display.setTextSize(2);
        display.setTextColor(GREEN, DARK_GRAY);
        display.drawText("FIRING (ON)", W / 2, boxY + 56);
    } else {
        // Idle visual indicator
        display.drawCircle(W / 2, boxY + 28, 16, WHITE);
        display.setTextAlign("center", "middle");
        display.setTextSize(2);
        display.setTextColor(RED, DARK_GRAY);
        display.drawText("IDLE (OFF)", W / 2, boxY + 56);
    }

    display.setTextSize(1);
    display.setTextColor(CYAN, DARK_GRAY);
    display.drawText("Pulse Count: " + count, W / 2, boxY + 70);

    delay(250); // 250ms ON, 250ms OFF = 2 Hz clean flashing
}

// Ensure LED is turned OFF on exit
try {
    gpio.digitalWrite(IR_PIN, 0);
} catch (eEnd) {}

display.fill(BLACK);
