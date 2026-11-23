import os
import glob
import json
import urllib.request
import urllib.parse
import time

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
        print(f"  API Error ({cmd}, {arg1}): {e}")
        return {'success': False, 'error': str(e)}

def upload_file(local_path, remote_path):
    encoded_path = urllib.parse.quote(remote_path)
    url = f"{BASE_URL}{encoded_path}"
    with open(local_path, 'rb') as f:
        data = f.read()
    req = urllib.request.Request(url, data=data, method='PUT')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  Upload error ({remote_path}): {e}")
        return False

# Ensure /sd/BruceJS/Games and /sd/BruceJS/Tools exist
api_call('mkdir', '/sd/BruceJS')
api_call('mkdir', '/sd/BruceJS/Games')
api_call('mkdir', '/sd/BruceJS/Tools')

# Upload Games
games = glob.glob("copy to SD card/BruceJS/Games/*.js")
print(f"Uploading {len(games)} Games to /sd/BruceJS/Games/...")
for g in games:
    fname = os.path.basename(g)
    target = f"/sd/BruceJS/Games/{fname}"
    ok = upload_file(g, target)
    print(f"  {'[OK]' if ok else '[FAIL]'} {fname}")
    time.sleep(0.05)

# Upload Tools
tools = glob.glob("copy to SD card/BruceJS/Tools/*.js")
print(f"\nUploading {len(tools)} Tools to /sd/BruceJS/Tools/...")
for t in tools:
    fname = os.path.basename(t)
    target = f"/sd/BruceJS/Tools/{fname}"
    ok = upload_file(t, target)
    print(f"  {'[OK]' if ok else '[FAIL]'} {fname}")
    time.sleep(0.05)

# Verification
print("\n--- Verifying /sd/BruceJS ---")
res_games = api_call('list', '/sd/BruceJS/Games')
print("Games installed on SD:")
for f in res_games.get('files', []):
    print(f"  🎮 {f['name']} ({f['size']} bytes)")

res_tools = api_call('list', '/sd/BruceJS/Tools')
print("\nTools installed on SD:")
for f in res_tools.get('files', []):
    print(f"  🛠️  {f['name']} ({f['size']} bytes)")
