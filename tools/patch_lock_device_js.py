import sys

p = 'copy to SD card/BruceJS/Tools/Lock Device.js'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('\r\n', '\n')

old_bat = """function getBatteryLevel() {
    try {
        if (dev && typeof dev.getBatteryCharge === "function") {
            var bat = dev.getBatteryCharge();
            if (typeof bat === "number" && bat >= 0 && bat <= 100) return Math.round(bat);
        }
    } catch (errBat0) {}
    try {
        if (typeof device !== "undefined" && device && typeof device.getBatteryCharge === "function") {
            var bat = device.getBatteryCharge();
            if (typeof bat === "number" && bat >= 0 && bat <= 100) return Math.round(bat);
        }
    } catch (errBat) {}
    try {
        if (dev && typeof dev.getBatteryDetailed === "function") {
            var det = dev.getBatteryDetailed();
            if (det && typeof det.battery_percent === "number" &&
                det.battery_percent >= 0 && det.battery_percent <= 100) {
                return Math.round(det.battery_percent);
            }
        }
    } catch (errBat2) {}
    return -1;
}"""

new_bat = """function getBatteryLevel() {
    var b = -1;
    try {
        if (typeof device !== "undefined" && device) {
            if (typeof device.getBatteryCharge === "function") b = device.getBatteryCharge();
            else if (typeof device.getBattery === "function") b = device.getBattery();
        }
    } catch (e1) {}
    if (b < 0) {
        try {
            if (dev) {
                if (typeof dev.getBatteryCharge === "function") b = dev.getBatteryCharge();
                else if (typeof dev.getBattery === "function") b = dev.getBattery();
            }
        } catch (e2) {}
    }
    if (typeof b === "number" && b >= 0 && b <= 100) return Math.round(b);
    return 100;
}"""

if old_bat not in c:
    print("ERROR: old_bat not found")
    sys.exit(1)
c = c.replace(old_bat, new_bat)

old_open = """        // Open PIN keypad
        var entered = keyboard.numKeyboard(10, "Enter PIN:", true);
        drainKeys();"""

new_open = """        // Open PIN keypad
        drainKeys();
        delay(40);
        var entered = keyboard.numKeyboard(10, "Enter PIN:", true);
        drainKeys();"""

if old_open not in c:
    print("ERROR: old_open not found")
    sys.exit(1)
c = c.replace(old_open, new_open)

with open(p, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(c)

print("Lock Device.js updated successfully!")
