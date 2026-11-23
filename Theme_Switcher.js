// Theme Switcher for Bruce Firmware (320x240 Handheld Console)
// Quickly preview and activate custom themes directly from the JS Interpreter!

var display = require("display");
var keyboard = require("keyboard");
var storage = require("storage");
var dialog = require("dialog");

var W = display.width();
var H = display.height();

var THEMES = [
  {
    name: "Default (Original Bruce)",
    path: "",
    onSd: 0,
    priColor: "a80f",
    secColor: "880f",
    bgColor: "0000",
    desc: "Classic neon magenta Bruce theme"
  },
  {
    name: "Modern UI 2",
    path: "/Themes/Modern UI 2/theme.json",
    onSd: 2,
    priColor: "ffff",
    secColor: "c618",
    bgColor: "0000",
    desc: "Sleek modern white/grey icon grid"
  },
  {
    name: "Cyberpunk 2077",
    path: "/Themes/Cyberpunk 2077/theme.json",
    onSd: 2,
    priColor: "96fe",
    secColor: "f9ff",
    bgColor: "0000",
    desc: "High-tech neon cyan and bright yellow"
  },
  {
    name: "Watch Dogs",
    path: "/Themes/Watch Dogs/theme.json",
    onSd: 2,
    priColor: "ffff",
    secColor: "8c71",
    bgColor: "0000",
    desc: "DedSec hacker terminal aesthetic"
  },
  {
    name: "Flipper Color",
    path: "/Themes/Flipper Color/theme.json",
    onSd: 2,
    priColor: "0000",
    secColor: "0000",
    bgColor: "fc45",
    desc: "Vibrant Flipper Zero dolphin orange"
  },
  {
    name: "Dark Mode",
    path: "/Themes/Dark Mode/theme.json",
    onSd: 2,
    priColor: "ffff",
    secColor: "8410",
    bgColor: "0000",
    desc: "Minimalist OLED deep black & white"
  },
  {
    name: "Mad Shark",
    path: "/Themes/Mad Shark/theme.json",
    onSd: 2,
    priColor: "ffff",
    secColor: "ffff",
    bgColor: "0000",
    desc: "Fierce shark illustrations"
  },
  {
    name: "SciFi 2",
    path: "/Themes/SciFi 2/theme.json",
    onSd: 2,
    priColor: "07ff",
    secColor: "03ef",
    bgColor: "0000",
    desc: "Futuristic spaceship command deck"
  },
  {
    name: "Shark Blue",
    path: "/Themes/Shark Blue/theme.json",
    onSd: 2,
    priColor: "001f",
    secColor: "52aa",
    bgColor: "0000",
    desc: "Deep oceanic blue styling"
  }
];

function hexToRgb565(hexStr) {
  var v = parseInt(hexStr.replace("0x", ""), 16);
  return v;
}

function hexToDisplayColor(hexStr) {
  var v = parseInt(hexStr.replace("0x", ""), 16);
  var r = Math.floor(((v >> 11) & 0x1F) * 255 / 31);
  var g = Math.floor(((v >> 5) & 0x3F) * 255 / 63);
  var b = Math.floor((v & 0x1F) * 255 / 31);
  return display.color(r, g, b);
}

function applyTheme(theme) {
  try {
    var confStr = "";
    try {
      confStr = String(storage.read({ fs: "sd", path: "/bruce.conf" }));
    } catch (e1) {
      try {
        confStr = String(storage.read({ fs: "littlefs", path: "/bruce.conf" }));
      } catch (e2) {}
    }

    var conf = {};
    if (confStr && confStr.length > 5) {
      try { conf = JSON.parse(confStr); } catch (e3) { conf = {}; }
    }

    conf.themeFile = theme.path;
    conf.themeOnSd = theme.onSd;
    conf.priColor = theme.priColor;
    conf.secColor = theme.secColor;
    conf.bgColor = theme.bgColor;

    var outJson = JSON.stringify(conf, null, 2);
    try { storage.write({ fs: "sd", path: "/bruce.conf" }, outJson, "write"); } catch (e4) {}
    try { storage.write({ fs: "littlefs", path: "/bruce.conf" }, outJson, "write"); } catch (e5) {}

    dialog.info("Theme Saved!\n\n" + theme.name + "\n\nReboot Bruce to activate completely.", true);
  } catch (err) {
    dialog.error("Error applying theme: " + err.message, true);
  }
}

function run() {
  var sel = 0;
  var dirty = true;

  while (true) {
    if (dirty) {
      var t = THEMES[sel];
      var priC = hexToDisplayColor(t.priColor);
      var secC = hexToDisplayColor(t.secColor);
      var bgC = hexToDisplayColor(t.bgColor);

      display.fill(display.color(15, 15, 20));

      // Header Banner
      display.drawFillRect(0, 0, W, 26, display.color(30, 30, 45));
      display.drawRect(0, 0, W, 26, display.color(70, 70, 100));
      display.setTextSize(1);
      display.setTextColor(display.color(0, 255, 255));
      display.drawString("[ THEME SWITCHER ] - 320x240", 12, 8);

      display.setTextColor(display.color(180, 180, 180));
      display.drawString((sel + 1) + "/" + THEMES.length, W - 45, 8);

      // Card Container
      var cardY = 36;
      var cardH = 150;
      display.drawFillRoundRect(10, cardY, W - 20, cardH, 8, display.color(24, 24, 32));
      display.drawRoundRect(10, cardY, W - 20, cardH, 8, priC);
      display.drawRoundRect(11, cardY + 1, W - 22, cardH - 2, 7, priC);

      // Theme Title
      display.setTextSize(2);
      display.setTextColor(display.color(255, 255, 255));
      display.drawString(t.name, 22, cardY + 12);

      // Description
      display.setTextSize(1);
      display.setTextColor(display.color(160, 160, 175));
      display.drawString(t.desc, 22, cardY + 38);

      // Path
      display.setTextColor(display.color(100, 180, 255));
      display.drawString("File: " + (t.path ? t.path : "(Built-in ROM Default)"), 22, cardY + 56);

      // Palette Swatches
      display.setTextColor(display.color(220, 220, 220));
      display.drawString("Color Palette:", 22, cardY + 80);

      // Swatch 1: Primary
      display.drawFillRoundRect(22, cardY + 96, 75, 24, 4, priC);
      display.drawRoundRect(22, cardY + 96, 75, 24, 4, display.color(255, 255, 255));
      display.setTextSize(1);
      display.setTextColor(display.color(0, 0, 0));
      display.drawString("Primary", 34, cardY + 103);

      // Swatch 2: Secondary
      display.drawFillRoundRect(105, cardY + 96, 75, 24, 4, secC);
      display.drawRoundRect(105, cardY + 96, 75, 24, 4, display.color(255, 255, 255));
      display.drawString("Secondary", 112, cardY + 103);

      // Swatch 3: Background
      display.drawFillRoundRect(188, cardY + 96, 75, 24, 4, bgC);
      display.drawRoundRect(188, cardY + 96, 75, 24, 4, display.color(200, 200, 200));
      display.setTextColor(display.color(255, 255, 255));
      display.drawString("Backdrop", 198, cardY + 103);

      // Bottom Control Bar
      display.drawFillRect(0, H - 38, W, 38, display.color(20, 20, 28));
      display.drawFastHLine(0, H - 38, W, display.color(50, 50, 70));
      display.setTextSize(1);
      display.setTextColor(display.color(0, 255, 0));
      display.drawString("[A] Apply Theme", 16, H - 28);
      display.setTextColor(display.color(255, 180, 0));
      display.drawString("[D-Pad] Next / Prev", 120, H - 28);
      display.setTextColor(display.color(200, 80, 80));
      display.drawString("[B] Exit", 260, H - 28);

      dirty = false;
    }

    var up = keyboard.getUpPress && keyboard.getUpPress();
    var down = keyboard.getDownPress && keyboard.getDownPress();
    var next = keyboard.getNextPress();
    var prev = keyboard.getPrevPress();
    var selBtn = keyboard.getSelPress();
    var escBtn = keyboard.getEscPress();

    if (next || down) {
      sel = (sel + 1) % THEMES.length;
      dirty = true;
    } else if (prev || up) {
      sel = (sel - 1 + THEMES.length) % THEMES.length;
      dirty = true;
    } else if (selBtn) {
      applyTheme(THEMES[sel]);
      dirty = true;
    } else if (escBtn) {
      break;
    }

    delay(30);
  }
}

run();
