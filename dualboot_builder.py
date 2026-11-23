#!/usr/bin/env python3
"""
Dual-Boot Image Builder for ESP32-S3 Handheld Console
Combines Retro-Go (Default boot) + Bruce (Hold Y button on boot)
"""

import os
import struct
import hashlib

PARTITION_MAGIC = b"\xAA\x50"
PARTITION_MD5_MAGIC = b"\xEB\xEB\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"

# Partition table definition for 16MB Flash
# (type, subtype, offset, size, label)
# Types: 0 = app, 1 = data
# Subtypes:
#   app: 0x10 = ota_0, 0x11 = ota_1, ... 0x20 = test
#   data: 0x00 = ota, 0x01 = phy, 0x02 = nvs, 0x03 = coredump, 0x82 = spiffs
PARTITIONS = [
    (1, 0x02, 0x009000, 0x004000, "nvs"),
    (1, 0x00, 0x00D000, 0x002000, "otadata"),
    (1, 0x01, 0x00F000, 0x001000, "phy_init"),
    (0, 0x10, 0x010000, 0x100000, "launcher"),    # 1.0 MB (Retro-Go Launcher)
    (0, 0x11, 0x110000, 0x100000, "retro-core"),  # 1.0 MB (NES, GB, GBC, SMS, GG, PCE)
    (0, 0x12, 0x210000, 0x0D0000, "prboom-go"),   # 832 KB (DOOM)
    (0, 0x13, 0x2E0000, 0x100000, "gwenesis"),    # 1.0 MB (Sega Genesis / Mega Drive)
    (0, 0x14, 0x3E0000, 0x0A0000, "fmsx"),        # 640 KB (MSX)
    (0, 0x15, 0x500000, 0x500000, "bruce"),       # 5.0 MB (Bruce Firmware - OTA_5)
    (1, 0x82, 0xA00000, 0x200000, "spiffs"),      # 2.0 MB (Storage for Bruce LittleFS)
    (1, 0x03, 0xFF0000, 0x010000, "coredump"),    # 64 KB
]

def generate_partition_table_bin():
    table_bin = b""
    for partype, subtype, offset, size, label in PARTITIONS:
        # struct format: <2sBBLL16sL (magic, type, subtype, offset, size, label, flags)
        label_bytes = label.encode("utf-8")[:16].ljust(16, b"\x00")
        table_bin += struct.pack("<2sBBLL16sL", PARTITION_MAGIC, partype, subtype, offset, size, label_bytes, 0)
    
    table_bin += PARTITION_MD5_MAGIC + hashlib.md5(table_bin).digest()
    table_bin += b"\xFF" * (0xC00 - len(table_bin))  # Pad to 3KB
    return table_bin

def build_combined_image(retro_go_img_path, bruce_bin_path, output_img_path):
    print("Reading Retro-Go image:", retro_go_img_path)
    with open(retro_go_img_path, "rb") as f:
        retro_data = f.read()

    print("Generating Dual-Boot Partition Table...")
    ptable_bin = generate_partition_table_bin()

    # Total 16MB image
    flash_size = 16 * 1024 * 1024
    image = bytearray(b"\xFF" * flash_size)

    # 1. Bootloader (0x0 to 0x8000)
    bootloader_len = 0x8000
    image[0:bootloader_len] = retro_data[0:bootloader_len]
    print(f"  Bootloader placed at 0x0 (size: {bootloader_len})")

    # 2. Partition Table (0x8000)
    image[0x8000 : 0x8000 + len(ptable_bin)] = ptable_bin
    print(f"  Partition Table placed at 0x8000 (size: {len(ptable_bin)})")

    # 3. Retro-Go apps
    retro_apps = ["launcher", "retro-core", "prboom-go", "gwenesis", "fmsx"]
    for partype, subtype, offset, size, label in PARTITIONS:
        if label in retro_apps:
            app_data = retro_data[offset : offset + size]
            image[offset : offset + size] = app_data
            actual_size = len(app_data.rstrip(b"\xFF"))
            print(f"  Retro-Go '{label}' placed at {hex(offset)} ({actual_size:,} bytes)")

    # 4. Bruce firmware
    if os.path.exists(bruce_bin_path):
        print("Reading Bruce binary:", bruce_bin_path)
        with open(bruce_bin_path, "rb") as f:
            bruce_data = f.read()
        bruce_offset = 0x500000
        image[bruce_offset : bruce_offset + len(bruce_data)] = bruce_data
        print(f"  Bruce placed at {hex(bruce_offset)} ({len(bruce_data):,} bytes)")
    else:
        print(f"WARNING: Bruce binary '{bruce_bin_path}' not found yet!")

    print(f"Writing combined dual-boot image: {output_img_path}")
    with open(output_img_path, "wb") as f:
        f.write(image)
    print(f"Successfully generated {output_img_path} ({len(image):,} bytes / 16MB)!")

if __name__ == "__main__":
    import sys
    retro_img = "retro_go_build_latest/retro-go_1.46_esp32-s3-devkit.img"
    bruce_bin = "bruce/.pio/build/retro-handheld-s3/firmware.bin"
    output = "dualboot_retro-go_bruce_16mb.img"
    build_combined_image(retro_img, bruce_bin, output)
