import os
import sys
import re
import shutil

# Japanese -> English known title map for common cross-regional duplicates
JP_TO_EN = {
    'rockman': 'mega man',
    'bare knuckle': 'streets of rage',
    'super donkey kong': 'donkey kong country',
    'makaimura': 'ghosts n goblins',
    'daimakaimura': 'ghouls n ghosts',
    'chou makaimura': 'super ghouls n ghosts',
    'akumajou dracula': 'castlevania',
    'vampire killer': 'castlevania bloodlines',
    'strider hiryu': 'strider',
    'starwing': 'star fox',
    'yossy island': 'yoshi s island',
    'panel de pon': 'tetris attack',
    'hokuto no ken': 'fist of the north star',
    'biohazard': 'resident evil'
}

SUPPORTED_NES_MAPPERS = {
    0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 15, 16, 18, 19, 20, 21, 22, 23, 24,
    30, 31, 32, 33, 34, 40, 41, 42, 46, 50, 64, 65, 66, 70, 71, 73, 74,
    75, 76, 78, 79, 85, 87, 93, 94, 119, 160, 162, 176, 185, 191, 192,
    193, 194, 195, 206, 228, 229, 231
}

def normalize_title(fname):
    t = os.path.splitext(fname)[0]
    t = re.sub(r'\[.*?\]', '', t)
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'[^a-zA-Z0-9]+', ' ', t).strip().lower()
    for jp, en in JP_TO_EN.items():
        if t.startswith(jp):
            t = t.replace(jp, en, 1).strip()
    return t

def score_rom(fname):
    score = 0
    fn = fname.lower()

    # Bad dumps, overdumps, hacks, trainers
    if re.search(r'\[b\d*\]', fn): score -= 10000
    if re.search(r'\[o\d*\]', fn): score -= 6000
    if re.search(r'\[t\d*\]', fn): score -= 4000
    if re.search(r'\[h\d*c?\]', fn) or 'hack' in fn: score -= 5000
    if re.search(r'\[f\d*\]', fn): score -= 1000
    if re.search(r'\[a\d*\]', fn): score -= 800

    # Foreign language translations (non-English)
    if re.search(r'\[t\+(?!eng)[a-z]+', fn) or re.search(r'\[t\-(?!eng)[a-z]+', fn): score -= 8000

    # Development builds / dated daily betas
    if re.search(r'\(\d{4}\-\d{2}\-\d{2}\)', fn): score -= 8000
    if '(beta' in fn or '(proto' in fn or '(sample' in fn or '(demo' in fn: score -= 3000

    # Verified good dump
    if '[!]' in fname: score += 2000

    # Language / Region ranking (English USA first)
    if '(usa' in fn or '(u)' in fn: score += 1500
    elif '(world' in fn: score += 1400
    elif '(europe' in fn or '(e)' in fn: score += 1000
    elif '[t+eng' in fn or '[t-eng' in fn: score += 1200 # English translation of Japanese game
    elif '(japan' in fn or '(j)' in fn: score -= 500

    # Revision
    if '(v1.2)' in fn or '(rev 2)' in fn or '(rev b)' in fn: score += 60
    elif '(v1.1)' in fn or '(rev 1)' in fn or '(rev a)' in fn: score += 30

    return score

def is_bad_nes(path):
    sz = os.path.getsize(path)
    if sz > 0x200000: # 2MB limit in nofrendo
        return True, "Oversized (>2MB)"
    try:
        with open(path, 'rb') as fp:
            head = fp.read(16)
            if len(head) < 16 or head[:4] != b'NES\x1a':
                return True, "Bad/Missing iNES header"
            m = (head[7] & 0xF0) | (head[6] >> 4)
            if head[15] != 0:
                m &= 0x0F
            if m not in SUPPORTED_NES_MAPPERS:
                return True, f"Unsupported mapper {m}"
    except Exception as e:
        return True, str(e)
    return False, ""

def process_directory(roms_root, apply_deletions=True):
    print(f"\n==========================================")
    print(f"Processing ROM directory: {roms_root}")
    print(f"Apply deletions: {apply_deletions}")
    print(f"==========================================\n")

    systems = ['nes', 'snes', 'md', 'sms', 'gg', 'pce', 'gb', 'gbc', 'lnx']
    files_to_remove = []

    # 1. NES Hardware Error Filter
    nes_dir = os.path.join(roms_root, 'nes')
    if os.path.isdir(nes_dir):
        nes_bad_count = 0
        for root, dirs, files in os.walk(nes_dir):
            for f in files:
                if f.lower().endswith('.nes'):
                    p = os.path.join(root, f)
                    is_bad, reason = is_bad_nes(p)
                    if is_bad:
                        files_to_remove.append((p, f, 'nes', f'NES Error: {reason}'))
                        nes_bad_count += 1
        print(f"Found {nes_bad_count} NES ROMs with hardware mapper/size errors.")

    # 2. Intra-system clean English deduplication
    kept_by_sys = {}
    for s in systems:
        s_dir = os.path.join(roms_root, s)
        if not os.path.isdir(s_dir):
            continue
        all_files = []
        for root, dirs, files in os.walk(s_dir):
            for f in files:
                p = os.path.join(root, f)
                # Skip if already marked for removal in NES check
                if any(p == r[0] for r in files_to_remove):
                    continue
                all_files.append((p, f))

        groups = {}
        for p, f in all_files:
            norm = normalize_title(f)
            groups.setdefault(norm, []).append((p, f))

        s_kept = {}
        for norm, variants in groups.items():
            sorted_v = sorted(variants, key=lambda x: score_rom(x[1]), reverse=True)
            s_kept[norm] = sorted_v[0]
            for p, f in sorted_v[1:]:
                files_to_remove.append((p, f, s, 'Duplicate/inferior version'))

        kept_by_sys[s] = s_kept

    # 3. Cross-system: SMS vs GG (Master System runs full-screen 256x192 at 60fps)
    if 'sms' in kept_by_sys and 'gg' in kept_by_sys:
        sms_titles = set(kept_by_sys['sms'].keys())
        gg_cross_count = 0
        for norm in list(kept_by_sys['gg'].keys()):
            if norm in sms_titles:
                p, f = kept_by_sys['gg'].pop(norm)
                files_to_remove.append((p, f, 'gg', 'Duplicate of Master System (play full-screen on SMS)'))
                gg_cross_count += 1
        print(f"Removed {gg_cross_count} Game Gear duplicates that exist on Master System.")

    # 4. Cross-system: Genesis (MD) vs SNES (Genesis runs smooth 60fps on ESP32-S3)
    if 'md' in kept_by_sys and 'snes' in kept_by_sys:
        md_titles = set(kept_by_sys['md'].keys())
        snes_cross_count = 0
        for norm in list(kept_by_sys['snes'].keys()):
            if norm in md_titles:
                p, f = kept_by_sys['snes'].pop(norm)
                files_to_remove.append((p, f, 'snes', 'Duplicate of Mega Drive (play at 60 FPS on MD)'))
                snes_cross_count += 1
        print(f"Removed {snes_cross_count} SNES multiplatform games that exist on Genesis (60 FPS on MD).")

    print(f"\nTotal files marked for removal: {len(files_to_remove):,}")

    if apply_deletions:
        print("Deleting files from disk...")
        deleted_count = 0
        for p, f, s, reason in files_to_remove:
            if os.path.exists(p):
                try:
                    os.remove(p)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {p}: {e}")
        print(f"Successfully deleted {deleted_count:,} redundant/bad ROMs.")

    print("\n--- Remaining Clean Library Counts ---")
    for s in systems:
        if s in kept_by_sys:
            print(f"  {s:4s}: {len(kept_by_sys[s]):5d} games")

if __name__ == '__main__':
    apply = True
    target = r'C:\Users\Gourav\Documents\GitHub\Retro Go\copy to SD card\roms'
    if len(sys.argv) > 1:
        target = sys.argv[1]
    process_directory(target, apply_deletions=apply)
