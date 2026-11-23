import os
import shutil

src_root = os.path.abspath("copy to SD card")
dst_root = "F:\\"

print(f"Copying files from '{src_root}' to '{dst_root}' (excluding 'roms')...")

for item in os.listdir(src_root):
    if item.lower() == "roms":
        print(f"Skipping '{item}' as requested (user is adding games manually).")
        continue

    s = os.path.join(src_root, item)
    d = os.path.join(dst_root, item)

    if os.path.isdir(s):
        print(f"Copying folder: {item} ...", end="", flush=True)
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(s, d)
        print(" OK")
    else:
        print(f"Copying file: {item} ({os.path.getsize(s):,} bytes) ...", end="", flush=True)
        shutil.copy2(s, d)
        print(" OK")

# Ensure empty roms directory exists on F:
roms_dir = os.path.join(dst_root, "roms")
if not os.path.exists(roms_dir):
    os.makedirs(roms_dir, exist_ok=True)
    print("Created empty 'F:\\roms' directory ready for game ROMs.")

print("\n=== Drive F: Copy Complete ===")
for root, dirs, files in os.walk(dst_root):
    level = root.replace(dst_root, '').count(os.sep)
    indent = ' ' * 4 * level
    rel = os.path.relpath(root, dst_root)
    if rel != ".":
        print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        if f.lower() not in ["desktop.ini", "thumbs.db"]:
            print(f"{subindent}{f}")
