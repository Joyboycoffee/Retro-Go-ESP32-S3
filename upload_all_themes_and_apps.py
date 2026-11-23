import os
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
        return {'success': False, 'error': str(e)}

def upload_file(local_path, remote_path):
    encoded_path = urllib.parse.quote(remote_path)
    url = f"{BASE_URL}{encoded_path}"
    with open(local_path, 'rb') as f:
        data = f.read()
    req = urllib.request.Request(url, data=data, method='PUT')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    return True
        except Exception as e:
            time.sleep(0.3)
    return False

def ensure_remote_dir(remote_dir):
    parts = remote_dir.strip('/').split('/')
    curr = ""
    for p in parts:
        curr += "/" + p
        api_call('mkdir', curr)

print("Starting Upload of Apps and Themes to SD Card...")

# 1. Upload Apps
apps = [
    ("Musicstreaming_Handheld.js", "/sd/BruceJS/Audio/Musicstreaming.js"),
    ("Morse_Code_Handheld.js", "/sd/BruceJS/Utilities/Morse Code.js"),
    ("Theme_Switcher.js", "/sd/BruceJS/Tools/Theme Switcher.js"),
    ("App_Store_Patched.js", "/sd/BruceJS/Tools/App Store.js")
]

print("\n--- Uploading Community Apps ---")
for local_file, remote_path in apps:
    remote_dir = os.path.dirname(remote_path)
    ensure_remote_dir(remote_dir)
    ok = upload_file(local_file, remote_path)
    status = "OK" if ok else "FAILED"
    print(f"[{status}] {local_file} -> {remote_path}")

# 2. Upload Themes
themes_base_local = r"c:\Users\Gourav\Documents\GitHub\Retro Go\themes_sd_ready"
theme_names = [d for d in os.listdir(themes_base_local) if os.path.isdir(os.path.join(themes_base_local, d))]

print(f"\n--- Uploading {len(theme_names)} 320x240 Themes ---")
ensure_remote_dir("/sd/Themes")

total_theme_files = 0
uploaded_theme_files = 0

for tname in theme_names:
    t_local_dir = os.path.join(themes_base_local, tname)
    t_remote_dir = f"/sd/Themes/{tname}"
    ensure_remote_dir(t_remote_dir)
    print(f"\nUploading Theme: {tname}")

    files = os.listdir(t_local_dir)
    for fname in files:
        flocal = os.path.join(t_local_dir, fname)
        if os.path.isfile(flocal):
            fremote = f"{t_remote_dir}/{fname}"
            total_theme_files += 1
            ok = upload_file(flocal, fremote)
            if ok:
                uploaded_theme_files += 1
                print(f"  + {fname} ({os.path.getsize(flocal)} B)")
            else:
                print(f"  ! FAILED: {fname}")

print(f"\nUpload complete! Uploaded {uploaded_theme_files}/{total_theme_files} theme files.")
