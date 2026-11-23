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

def list_files(path):
    res = api_call('list', path)
    return {f['name']: f for f in res.get('files', [])}

converted_dir = os.path.abspath("digispark_scripts/converted")
files = glob.glob(os.path.join(converted_dir, "**", "*.txt"), recursive=True)

targets = [
    "/sd/BadUSB and BlueDucky",
    "/sd/badusb"
]

print(f"Starting sync of {len(files)} scripts to {BASE_URL}...")

for base in targets:
    print(f"\n=======================================================")
    print(f"Target: {base}")
    print(f"=======================================================")
    
    # Ensure root target exists
    api_call('mkdir', base)
    
    for idx, f in enumerate(files, start=1):
        rel = os.path.relpath(f, converted_dir).replace('\\', '/')
        subfolder = rel.split('/')[0]
        filename = rel.split('/')[-1]
        
        remote_dir = f"{base}/{subfolder}"
        remote_path = f"{base}/{rel}"
        
        # Ensure subfolder exists
        api_call('mkdir', remote_dir)
        
        # Check if already uploaded
        existing = list_files(remote_dir)
        if filename in existing and existing[filename]['size'] > 0:
            print(f"[{idx}/{len(files)}] [EXISTS] {remote_path} ({existing[filename]['size']} bytes)")
        else:
            print(f"[{idx}/{len(files)}] [UPLOADING] {remote_path}...")
            ok = upload_file(f, remote_path)
            if ok:
                print(f"[{idx}/{len(files)}] [OK] {remote_path}")
            else:
                print(f"[{idx}/{len(files)}] [RETRYING] {remote_path}...")
                time.sleep(0.5)
                ok = upload_file(f, remote_path)
                print(f"[{idx}/{len(files)}] [{'OK' if ok else 'FAIL'}] {remote_path}")
                
        time.sleep(0.05)

print("\n=======================================================")
print("FINAL VERIFICATION:")
print("=======================================================")
for base in targets:
    root_items = list_files(base)
    folders = [k for k, v in root_items.items() if v.get('is_dir')]
    print(f"\n{base}: {len(folders)} folders found:")
    total_txt = 0
    for folder in sorted(folders):
        sub_items = list_files(f"{base}/{folder}")
        txts = [k for k, v in sub_items.items() if k.endswith('.txt')]
        total_txt += len(txts)
        print(f"  📁 {folder}: {', '.join(txts)}")
    print(f"Total .txt payloads in {base}: {total_txt}/19")
