import os
import json
import urllib.request
import urllib.parse
import shutil

IP = "192.168.1.35"
BASE_URL = f"http://{IP}"

def api_call(cmd, arg1, arg2=''):
    url = f"{BASE_URL}/api"
    data = json.dumps({'cmd': cmd, 'arg1': arg1, 'arg2': arg2}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'success': False, 'error': str(e)}

def upload_content(data_bytes, remote_path):
    encoded_path = urllib.parse.quote(remote_path)
    url = f"{BASE_URL}{encoded_path}"
    req = urllib.request.Request(url, data=data_bytes, method='PUT')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
    return False

# 1. Update local copy
local_dest = r"c:\Users\Gourav\Documents\GitHub\Retro Go\copy to SD card\BruceJS\Tools\AllPlayer.js"
shutil.copy("AllPlayer_Fixed.js", local_dest)
print(f"Updated local: {local_dest}")

# 2. Upload fixed AllPlayer.js to SD card
with open("AllPlayer_Fixed.js", "rb") as f:
    js_data = f.read()

remote_js = "/sd/BruceJS/Tools/AllPlayer.js"
ok_js = upload_content(js_data, remote_js)
print(f"Upload {remote_js}: {'SUCCESS' if ok_js else 'FAILED'}")

# 3. Create /sd/rttts/ on SD card and upload sample melodies
api_call('mkdir', '/sd/rttts')

melodies = {
    "Super Mario.txt": "Super Mario:d=4,o=5,b=100:16e6,16e6,32p,8e6,16c6,8e6,8g6,8p,8g,8p,8c6,16p,8g,16p,8e,16p,8a,8b,16a#,8a,16g,16e6,16g6,8a6,16f6,8g6,8e6,16c6,16d6,8b",
    "Tetris.txt": "Tetris:d=4,o=5,b=160:e6,8b,8c6,8d6,16e6,16d6,8c6,8b,a,8a,8c6,e6,8d6,8c6,b,8b,8c6,d6,e6,c6,a,2a",
    "Star Wars.txt": "StarWars:d=4,o=5,b=45:32p,32f#,32f#,32f#,8b.,8f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32e6,8c#.6",
    "Nokia.txt": "Nokia:d=4,o=5,b=225:8e6,8d6,f#,g#,8c#6,8b,d,e,8b,8a,c#,e,2a"
}

for name, tune in melodies.items():
    remote_path = f"/sd/rttts/{name}"
    ok = upload_content(tune.encode('utf-8'), remote_path)
    print(f"Uploaded melody {name}: {'SUCCESS' if ok else 'FAILED'}")

print("\nAllPlayer fix and sample RTTTL tunes deployed successfully!")
