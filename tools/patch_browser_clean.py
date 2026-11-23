for path in ['copy to SD card/BruceJS/Tools/Browser.js', 'copy to SD card/browser_bruce.js']:
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    # Replace top module declarations
    old_top = """var display = require("display");
var keyboard = require("keyboard");

var wifi = null;
try { wifi = require("wifi"); } catch (errW) {}

var gpio = null;
try { gpio = require("gpio"); } catch (errG) {}"""

    new_top = """var display = (typeof display !== "undefined" && display) ? display : require("display");
var keyboard = (typeof keyboard !== "undefined" && keyboard) ? keyboard : require("keyboard");

function getWifi() {
    try {
        if (typeof wifi !== "undefined" && wifi) return wifi;
        if (typeof require === "function") {
            var w = require("wifi");
            if (w) return w;
        }
    } catch (e) {}
    return null;
}

function getGpio() {
    try {
        if (typeof gpio !== "undefined" && gpio) return gpio;
        if (typeof require === "function") {
            var g = require("gpio");
            if (g) return g;
        }
    } catch (e) {}
    return null;
}"""

    if old_top in c:
        c = c.replace(old_top, new_top)
        print('Patched top in', path)
    else:
        print('Warning: old_top not found in', path)

    # Replace isOnline
    old_online = """function isOnline() {
    try {
        if (wifi) {
            if (typeof wifi.connected === "function" && wifi.connected()) return true;
            if (typeof wifi.getIPAddress === "function") {
                var ip = wifi.getIPAddress();
                if (ip && ip !== "0.0.0.0") return true;
            }
        }
    } catch (errCheck) {}
    return false;
}"""

    new_online = """function isOnline() {
    try {
        var w = getWifi();
        if (w) {
            if (typeof w.connected === "function" && w.connected()) return true;
            if (typeof w.getIPAddress === "function") {
                var ip = w.getIPAddress();
                if (ip && ip !== "0.0.0.0") return true;
            }
        }
    } catch (errCheck) {}
    return false;
}"""

    if old_online in c:
        c = c.replace(old_online, new_online)
        print('Patched isOnline in', path)
    else:
        print('Warning: old_online not found in', path)

    # Replace fetchText
    old_fetch = """function fetchText(url, timeoutMs) {
    var out = { ok: false, status: 0, text: "", err: "" };
    if (!wifi || typeof wifi.httpFetch !== "function") {
        out.err = "WiFi module not available";
        return out;
    }
    try {
        var res = wifi.httpFetch(url, { method: "GET", responseType: "string" });"""

    new_fetch = """function fetchText(url, timeoutMs) {
    var out = { ok: false, status: 0, text: "", err: "" };
    var w = getWifi();
    if (!w || typeof w.httpFetch !== "function") {
        out.err = "WiFi module not available";
        return out;
    }
    try {
        var res = w.httpFetch(url, { method: "GET", responseType: "string" });"""

    if old_fetch in c:
        c = c.replace(old_fetch, new_fetch)
        print('Patched fetchText in', path)
    else:
        print('Warning: old_fetch not found in', path)

    # Replace gpio usage
    old_gpio1 = "if (gpio && typeof gpio.digitalRead === 'function')"
    old_gpio2 = 'if (gpio && typeof gpio.digitalRead === "function")'
    new_gpio = 'var _g = getGpio(); if (_g && typeof _g.digitalRead === "function")'
    if old_gpio1 in c: c = c.replace(old_gpio1, new_gpio)
    if old_gpio2 in c: c = c.replace(old_gpio2, new_gpio)
    c = c.replace('gpio.digitalRead', '_g.digitalRead')

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(c)
print('Browser scripts updated')
