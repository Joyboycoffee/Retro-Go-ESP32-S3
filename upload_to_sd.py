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
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"API Error ({cmd}, {arg1}): {e}")
        return {'success': False, 'error': str(e)}

def ensure_dir(path):
    # Splits path e.g. /sd/BadUSB and BlueDucky/Create_Account into hierarchy
    parts = [p for p in path.strip('/').split('/')]
    curr = ""
    for p in parts:
        curr += "/" + p
        if curr in ["/sd", ""]:
            continue
        api_call('mkdir', curr)

def upload_file(local_path, remote_path):
    # remote_path: e.g. /sd/BadUSB and BlueDucky/Create_Account/Create_Account.txt
    encoded_path = urllib.parse.quote(remote_path)
    url = f"{BASE_URL}{encoded_path}"
    
    with open(local_path, 'rb') as f:
        data = f.read()
        
    req = urllib.request.Request(url, data=data, method='PUT')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Upload error {remote_path}: {e}")
        return False

# Source directory
converted_dir = os.path.abspath("digispark_scripts/converted")
files = glob.glob(os.path.join(converted_dir, "**", "*.txt"), recursive=True)

print(f"Found {len(files)} converted scripts to upload to {BASE_URL}")

# Targets:
# 1. /sd/BadUSB and BlueDucky/<rel_path>
# 2. /sd/badusb/<rel_path>

targets = [
    "/sd/BadUSB and BlueDucky",
    "/sd/badusb"
]

for base_dest in targets:
    print(f"\n==========================================")
    print(f"Uploading to SD target: {base_dest}")
    print(f"==========================================")
    ensure_dir(base_dest)
    
    success_count = 0
    for idx, f in enumerate(files, start=1):
        rel = os.path.relpath(f, converted_dir).replace('\\', '/')
        remote_path = f"{base_dest}/{rel}"
        remote_dir = "/".join(remote_path.split('/')[:-1])
        
        ensure_dir(remote_dir)
        ok = upload_file(f, remote_path)
        if ok:
            success_count += 1
            print(f"[{idx}/{len(files)}] Uploaded: {remote_path}")
        else:
            print(f"[{idx}/{len(files)}] FAILED: {remote_path}")
        time.sleep(0.05)
        
    print(f"Finished {base_dest}: {success_count}/{len(files)} files uploaded.")

print("\n--- Verifying uploads on SD card ---")
for base_dest in targets:
    res = api_call('list', base_dest)
    dirs = [item['name'] for item in res.get('files', []) if item.get('is_dir')]
    print(f"{base_dest} contains {len(dirs)} folders: {', '.join(dirs[:5])}...")
