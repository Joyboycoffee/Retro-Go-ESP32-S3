// =============================================================================
//  Retro Handheld S3 - Gamepad & 11-Button Diagnostic Tool
//  Tests all 11 buttons with real-time visual feedback:
//  - D-Pad: UP (41), DOWN (42), LEFT (2), RIGHT (1)
//  - Action: A (47), B (21), X (45), Y (48)
//  - System: START (38), SELECT (40), MENU (39)
//  Exit: Hold SELECT + START together for 1.5 seconds
// =============================================================================

var display = require("display");
var gpio = require("gpio");

var BLACK = display.color(0, 0, 0);
var WHITE = display.color(255, 255, 255);
var GREEN = display.color(0, 255, 100);
var CYAN = display.color(0, 220, 255);
var GOLD = display.color(255, 200, 40);
var DARK_GRAY = display.color(40, 44, 55);
var BTN_OFF = display.color(50, 55, 70);

var W = display.width();
var H = display.height();

var BUTTONS = [
    { name: "UP",     pin: 41, x: 50,  y: 80,  w: 26, h: 26 },
    { name: "DOWN",   pin: 42, x: 50,  y: 140, w: 26, h: 26 },
    { name: "LEFT",   pin: 2,  x: 20,  y: 110, w: 26, h: 26 },
    { name: "RIGHT",  pin: 1,  x: 80,  y: 110, w: 26, h: 26 },
    { name: "X",      pin: 45, x: 250, y: 80,  w: 26, h: 26 },
    { name: "B",      pin: 21, x: 250, y: 140, w: 26, h: 26 },
    { name: "Y",      pin: 48, x: 220, y: 110, w: 26, h: 26 },
    { name: "A",      pin: 47, x: 280, y: 110, w: 26, h: 26 },
    { name: "SELECT", pin: 40, x: 125, y: 120, w: 32, h: 18 },
    { name: "MENU",   pin: 39, x: 145, y: 80,  w: 30, h: 18 },
    { name: "START",  pin: 38, x: 165, y: 120, w: 32, h: 18 }
];

function initPins() {
    for (var i = 0; i < BUTTONS.length; i++) {
        try {
            gpio.pinMode(BUTTONS[i].pin, "input", "up");
        } catch (errInit) {}
    }
}

function readButtonState(pin) {
    try {
        return gpio.digitalRead(pin) === 0;
    } catch (errRead) {}
    return false;
}

initPins();

display.fill(BLACK);
display.setTextAlign("center", "middle");
display.setTextSize(2);
display.setTextColor(CYAN, BLACK);
display.drawText("BUTTON TESTER", W / 2, 22);

display.setTextSize(1);
display.setTextColor(GOLD, BLACK);
display.drawText("Hold SELECT + START to Exit", W / 2, 45);

var lastStates = [];
var exitHoldCount = 0;

while (true) {
    var selDown = false;
    var startDown = false;

    for (var b = 0; b < BUTTONS.length; b++) {
        var btn = BUTTONS[b];
        var isPressed = readButtonState(btn.pin);

        if (btn.name === "SELECT" && isPressed) selDown = true;
        if (btn.name === "START" && isPressed) startDown = true;

        if (lastStates[b] !== isPressed) {
            lastStates[b] = isPressed;

            var col = isPressed ? GREEN : BTN_OFF;
            var textCol = isPressed ? BLACK : WHITE;

            display.drawFillRoundRect(btn.x, btn.y, btn.w, btn.h, 4, col);
            display.drawRoundRect(btn.x, btn.y, btn.w, btn.h, 4, isPressed ? WHITE : DARK_GRAY);

            display.setTextAlign("center", "middle");
            display.setTextSize(1);
            display.setTextColor(textCol, col);
            display.drawText(btn.name, btn.x + btn.w / 2, btn.y + btn.h / 2);
        }
    }

    if (selDown && startDown) {
        exitHoldCount++;
        if (exitHoldCount > 15) { // ~1.5s
            display.fill(BLACK);
            display.setTextColor(GREEN, BLACK);
            display.setTextSize(2);
            display.drawText("EXITING...", W / 2, H / 2);
            delay(500);
            break;
        }
    } else {
        exitHoldCount = 0;
    }

    delay(80);
}

display.fill(BLACK);
