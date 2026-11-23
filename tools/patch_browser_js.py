import sys

files = [
    'copy to SD card/BruceJS/Tools/Browser.js',
    'copy to SD card/browser_bruce.js'
]

old_online = """function isOnline() {
    try {
        if (wifi && typeof wifi.connected === "function") return wifi.connected();
    } catch (errCheck) {}
    return false;
}"""

new_online = """function isOnline() {
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

for p in files:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()
    c = c.replace('\r\n', '\n')
    if old_online not in c:
        print(f"ERROR: old_online not found in {p}")
        sys.exit(1)
    c = c.replace(old_online, new_online)
    with open(p, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(c)
    print(f"Updated {p}")

print("Browser.js files updated successfully!")
