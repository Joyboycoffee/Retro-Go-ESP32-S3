#!/usr/bin/env python3
"""
Clean GB/GBC separation and mismatched ROM organization script:
1. Separates GB and GBC:
   - roms/gb: strictly monochrome Game Boy (.gb) games (removes .gbc files and moves GBC-only DX hacks to gbc)
   - roms/gbc: strictly Game Boy Color (.gbc) games (removes duplicate monochrome .gb files, includes colorized DX hacks)
2. Moves 11 .sms (Sega Master System) games accidentally placed in roms/gg to roms/sms
3. Converts roms/md/Berzerk.smd (interleaved Super Magic Drive format) into standard roms/md/Berzerk.gen and removes .smd
4. Cleans image/audio junk files (.png, .jpg, .mp3, .ogg) from roms/gg, roms/md, roms/gw
5. Renames roms/gw/*.mgw to *.gw so Retro-Go's Game & Watch launcher (configured for 'gw') immediately recognizes them
"""

import os
import shutil

def deinterleave_smd(input_path, output_path):
    with open(input_path, 'rb') as f:
        f.seek(512) # skip SMD header
        data = f.read()
    
    out = bytearray(len(data))
    for i in range(0, len(data), 16384):
        block = data[i:i+16384]
        half = len(block) // 2
        part1 = block[:half]
        part2 = block[half:]
        for j in range(half):
            out[i + j*2] = part2[j]
            out[i + j*2 + 1] = part1[j]
            
    with open(output_path, 'wb') as f:
        f.write(out)

def clean_rom_folder(base_dir):
    print(f"\nProcessing directory: {base_dir}")
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist, skipping.")
        return

    # 1. Clean junk files from gg, md, gw
    junk_patterns = {
        'gg': ['.png', '.jpg', '.jpeg'],
        'md': ['.png', '.jpg', '.jpeg'],
        'gw': ['.png', '.jpg', '.jpeg', '.mp3', '.ogg']
    }
    for sub, exts in junk_patterns.items():
        dir_path = os.path.join(base_dir, sub)
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                if any(f.lower().endswith(x) for x in exts):
                    fp = os.path.join(dir_path, f)
                    print(f"  [Junk] Removing {sub}/{f}")
                    os.remove(fp)

    # 2. Move .sms files from gg/ to sms/
    gg_dir = os.path.join(base_dir, 'gg')
    sms_dir = os.path.join(base_dir, 'sms')
    if os.path.exists(gg_dir) and os.path.exists(sms_dir):
        for f in os.listdir(gg_dir):
            if f.lower().endswith('.sms'):
                src = os.path.join(gg_dir, f)
                dst = os.path.join(sms_dir, f)
                print(f"  [Move] Moving {f} from gg/ to sms/")
                shutil.move(src, dst)

    # 3. Convert Berzerk.smd to Berzerk.gen in md/
    md_dir = os.path.join(base_dir, 'md')
    if os.path.exists(md_dir):
        smd_path = os.path.join(md_dir, 'Berzerk.smd')
        gen_path = os.path.join(md_dir, 'Berzerk.gen')
        if os.path.exists(smd_path):
            print(f"  [Convert] Deinterleaving Berzerk.smd -> Berzerk.gen")
            deinterleave_smd(smd_path, gen_path)
            os.remove(smd_path)

    # 4. Rename *.mgw to *.gw in gw/
    gw_dir = os.path.join(base_dir, 'gw')
    if os.path.exists(gw_dir):
        for f in os.listdir(gw_dir):
            if f.lower().endswith('.mgw'):
                old_p = os.path.join(gw_dir, f)
                new_p = os.path.join(gw_dir, os.path.splitext(f)[0] + '.gw')
                print(f"  [Rename] {f} -> {os.path.basename(new_p)}")
                if os.path.exists(new_p):
                    os.remove(new_p)
                os.rename(old_p, new_p)

    # 5. Separate GB and GBC
    gb_dir = os.path.join(base_dir, 'gb')
    gbc_dir = os.path.join(base_dir, 'gbc')

    if os.path.exists(gb_dir) and os.path.exists(gbc_dir):
        # A. Remove all .gbc files from gb/
        for f in os.listdir(gb_dir):
            if f.lower().endswith('.gbc'):
                fp = os.path.join(gb_dir, f)
                # Ensure it exists in gbc/
                dst = os.path.join(gbc_dir, f)
                if not os.path.exists(dst):
                    shutil.copy2(fp, dst)
                os.remove(fp)
        print("  [GB] Removed all .gbc files from gb/")

        # B. Identify GBC-only games (CGB flag 0xC0) in gb/ that were misnamed .gb
        for f in list(os.listdir(gb_dir)):
            if f.lower().endswith('.gb'):
                fp = os.path.join(gb_dir, f)
                is_cgb_only = False
                try:
                    with open(fp, 'rb') as rom_file:
                        rom_file.seek(0x143)
                        b = rom_file.read(1)
                        if b and b[0] == 0xC0:
                            is_cgb_only = True
                except Exception:
                    pass

                if is_cgb_only:
                    base_name = os.path.splitext(f)[0]
                    gbc_name = base_name + '.gbc'
                    target_path = os.path.join(gbc_dir, gbc_name)
                    print(f"  [GBC-Only DX Hack] Moving {f} -> gbc/{gbc_name}")
                    shutil.copy2(fp, target_path)
                    os.remove(fp)

        # C. Remove all monochrome .gb files from gbc/
        for f in list(os.listdir(gbc_dir)):
            if f.lower().endswith('.gb'):
                fp = os.path.join(gbc_dir, f)
                os.remove(fp)
        print("  [GBC] Removed monochrome .gb files from gbc/")

if __name__ == '__main__':
    # 1. Clean local source directory
    local_roms = os.path.abspath('copy to SD card/roms')
    clean_rom_folder(local_roms)

    # 2. Clean SD card directory
    sd_roms = 'F:\\roms'
    if os.path.exists(sd_roms):
        clean_rom_folder(sd_roms)
    else:
        print(f"Note: SD Card at {sd_roms} not detected.")
    
    print("\nCleanup and organization complete!")
