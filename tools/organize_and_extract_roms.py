import os
import sys
import shutil
import zipfile
import subprocess
import hashlib
import re
from pathlib import Path

ROMS_DIR = r"C:\Users\Gourav\Documents\GitHub\Retro Go\copy to SD card\roms"

SYSTEM_EXTENSIONS = {
    "nes": {".nes", ".fc", ".fds", ".nsf"},
    "snes": {".sfc", ".smc", ".fig"},
    "gb": {".gb", ".gbc"},
    "gbc": {".gbc", ".gb"},
    "gba": {".gba"},
    "sms": {".sms", ".sg"},
    "gg": {".gg"},
    "md": {".md", ".gen", ".bin", ".smd"},
    "pce": {".pce"},
    "col": {".col", ".rom"},
    "lnx": {".lnx"},
    "doom": {".wad"},
    "msx": {".rom", ".mx1", ".mx2", ".dsk"},
    "gw": {".gw", ".mgw"}
}

ALL_ROM_EXTS = set().union(*SYSTEM_EXTENSIONS.values())

def get_file_hash(filepath):
    """Calculates MD5 hash of first 512KB + file size for fast deduplication."""
    h = hashlib.md5()
    size = os.path.getsize(filepath)
    h.update(str(size).encode())
    with open(filepath, "rb") as f:
        chunk = f.read(524288)
        h.update(chunk)
        if size > 1048576:
            f.seek(-524288, os.SEEK_END)
            h.update(f.read(524288))
    return h.hexdigest()

def clean_game_title(filename):
    """Extracts base normalized title without region/revision tags."""
    stem = Path(filename).stem
    # Remove bracketed and parenthesized tags: e.g. (USA), [T-Eng], (Rev 1), etc.
    cleaned = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", stem)
    cleaned = re.sub(r"[\._\-\s]+", " ", cleaned).strip().lower()
    return cleaned

def get_region_score(filename):
    """Higher score = higher preference."""
    name = filename.upper()
    if "(USA)" in name or "(U)" in name or "USA" in name:
        return 100
    if "(WORLD)" in name:
        return 95
    if "[T-ENG" in name or "(EN" in name or "(ENGLISH" in name:
        return 90
    if "(EUROPE)" in name or "(E)" in name:
        return 80
    if "(JAPAN)" in name or "(J)" in name or "(JA)" in name:
        return 70
    return 50

def extract_archives(roms_dir):
    print("=== Step 1: Extracting all .zip and .7z archives ===")
    extracted_count = 0
    errors_count = 0

    for root, dirs, files in os.walk(roms_dir):
        rel = os.path.relpath(root, roms_dir)
        top_system = rel.split(os.sep)[0].lower()
        valid_exts = SYSTEM_EXTENSIONS.get(top_system, ALL_ROM_EXTS)

        for file in list(files):
            ext = os.path.splitext(file)[1].lower()
            if ext not in [".zip", ".7z"]:
                continue
            file_path = os.path.join(root, file)

            if ext == ".zip":
                try:
                    with zipfile.ZipFile(file_path, "r") as z:
                        members = z.namelist()
                        rom_members = [m for m in members if os.path.splitext(m)[1].lower() in valid_exts]
                        if not rom_members:
                            # Try any valid ROM extension
                            rom_members = [m for m in members if os.path.splitext(m)[1].lower() in ALL_ROM_EXTS]

                        for m in rom_members:
                            # Extract flat to root
                            target_name = os.path.basename(m)
                            target_path = os.path.join(root, target_name)
                            with z.open(m) as src, open(target_path, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            extracted_count += 1
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error extracting ZIP {file_path}: {e}")
                    errors_count += 1

            elif ext == ".7z":
                try:
                    cmd_extract = ["tar", "-xf", file_path, "-C", root]
                    res = subprocess.run(cmd_extract, capture_output=True, text=True)
                    if res.returncode == 0:
                        extracted_count += 1
                        os.remove(file_path)
                    else:
                        print(f"Error extracting 7Z {file_path}: {res.stderr.strip()}", flush=True)
                        errors_count += 1
                except Exception as e:
                    print(f"Exception extracting 7Z {file_path}: {e}", flush=True)
                    errors_count += 1

            if extracted_count > 0 and extracted_count % 200 == 0:
                print(f"Extracted {extracted_count} archives...", flush=True)

    print(f"Extraction complete: {extracted_count} ROMs extracted, {errors_count} errors.\n")

def flatten_pack_directories(roms_dir):
    print("=== Step 2: Flattening pack subdirectories ===")
    pack_folders = [
        os.path.join(roms_dir, "snes", "gameplay-snes"),
        os.path.join(roms_dir, "gb", "game-boy-and-game-boy-color-complete-collection"),
        os.path.join(roms_dir, "gbc", "game-boy-and-game-boy-color-complete-collection"),
        os.path.join(roms_dir, "gg", "sega-game-gear-romset-ultra-us"),
        os.path.join(roms_dir, "sms", "nointro.ms-mkiii"),
        os.path.join(roms_dir, "pce", "nointro.tg-16"),
        os.path.join(roms_dir, "gw", "GameWatchRomCollectionByGhostware"),
        os.path.join(roms_dir, "md", "sega-genesis-romset-ultra-usa"),
    ]

    moved_count = 0
    for pf in pack_folders:
        if os.path.exists(pf):
            parent = os.path.dirname(pf)
            for root, dirs, files in os.walk(pf, topdown=False):
                for f in files:
                    src = os.path.join(root, f)
                    dst = os.path.join(parent, f)
                    if os.path.exists(dst):
                        # Keep larger or newer
                        if os.path.getsize(src) > os.path.getsize(dst):
                            os.remove(dst)
                            shutil.move(src, dst)
                        else:
                            os.remove(src)
                    else:
                        shutil.move(src, dst)
                    moved_count += 1
            # Remove empty directory
            try:
                shutil.rmtree(pf)
            except Exception:
                pass
    print(f"Flattening complete: {moved_count} ROMs moved to main system folders.\n")

def deduplicate_roms(roms_dir):
    print("=== Step 3: Deduplicating ROMs ===")
    removed_exact = 0
    removed_region = 0

    for system in os.listdir(roms_dir):
        sys_dir = os.path.join(roms_dir, system)
        if not os.path.isdir(sys_dir):
            continue

        valid_exts = SYSTEM_EXTENSIONS.get(system.lower(), ALL_ROM_EXTS)
        
        # 1. Exact hash deduplication
        hashes = {}
        for root, dirs, files in os.walk(sys_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in valid_exts:
                    continue
                path = os.path.join(root, f)
                try:
                    f_hash = get_file_hash(path)
                    if f_hash in hashes:
                        # Duplicate exact ROM!
                        existing_path = hashes[f_hash]
                        # Prefer keeping USA or higher scored path
                        if get_region_score(f) > get_region_score(os.path.basename(existing_path)):
                            os.remove(existing_path)
                            hashes[f_hash] = path
                        else:
                            os.remove(path)
                        removed_exact += 1
                    else:
                        hashes[f_hash] = path
                except Exception as e:
                    pass

        # 2. Regional duplicate deduplication within same system
        title_map = {}
        for root, dirs, files in os.walk(sys_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in valid_exts:
                    continue
                path = os.path.join(root, f)
                title = clean_game_title(f)
                score = get_region_score(f)
                
                # Group by (title, ext)
                key = (title, ext)
                if key not in title_map:
                    title_map[key] = (score, path)
                else:
                    prev_score, prev_path = title_map[key]
                    # If this is significantly higher score (e.g. USA vs Europe/Japan)
                    if score > prev_score:
                        try:
                            os.remove(prev_path)
                            removed_region += 1
                        except Exception:
                            pass
                        title_map[key] = (score, path)
                    elif score < prev_score:
                        try:
                            os.remove(path)
                            removed_region += 1
                        except Exception:
                            pass

    print(f"Deduplication complete: {removed_exact} exact duplicates removed, {removed_region} regional duplicates removed.\n")

def cleanup_junk(roms_dir):
    print("=== Step 4: Cleaning junk and non-ROM files ===")
    junk_exts = {".txt", ".nfo", ".xml", ".sqlite", ".log", ".diz", ".db", ".ds_store"}
    removed_junk = 0

    for root, dirs, files in os.walk(roms_dir, topdown=False):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in junk_exts or f.lower() in {"thumbs.db", ".ds_store", "desktop.ini"}:
                try:
                    os.remove(os.path.join(root, f))
                    removed_junk += 1
                except Exception:
                    pass
        # Remove empty directories
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except Exception:
                pass

    print(f"Junk cleanup complete: {removed_junk} files removed.\n")

if __name__ == "__main__":
    print("Starting ROM Organization and Extraction Pipeline...")
    print(f"Target directory: {ROMS_DIR}")
    extract_archives(ROMS_DIR)
    flatten_pack_directories(ROMS_DIR)
    deduplicate_roms(ROMS_DIR)
    cleanup_junk(ROMS_DIR)
    print("ALL ROM PROCESSING COMPLETED SUCCESSFULLY!")
