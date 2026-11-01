#!/usr/bin/env python3
"""Replace rg_gui_draw_icons() in rg_gui.c with the beige vertical-battery / quarter-arc Wi-Fi version.

Usage (from the repo root, "Retro Go"):
    python claude_patches/retro-go/apply_status_icons.py

Idempotent: re-running it re-splices the same snippet.  A .bak copy is written once.
"""
import os, re, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET = os.path.join(ROOT, "retro-go", "components", "retro-go", "rg_gui.c")
SNIPPET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status_icons.inc.c")

src = open(TARGET, encoding="utf-8", newline="").read()      # newline="" keeps CRLF/LF exactly as in the repo
new = open(SNIPPET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
EOL = "\r\n" if "\r\n" in src else "\n"
new = new.replace("\n", EOL)

start_marker = "void rg_gui_draw_icons(void)"
end_marker = "void rg_gui_draw_hourglass(void)"

# If we spliced before, the snippet starts with its own banner/macros: back up to that banner.
banner = "//  Retro-Go status bar icons (beige theme)"
if banner in src:
    b = src.index(banner)
    start = src.rfind("// ====", 0, b)
    start = src.rfind("\n", 0, start) + 1 if start != -1 else b
else:
    if start_marker not in src:
        sys.exit("ERROR: rg_gui_draw_icons() not found in rg_gui.c")
    start = src.index(start_marker)

if end_marker not in src:
    sys.exit("ERROR: rg_gui_draw_hourglass() not found in rg_gui.c")
end = src.index(end_marker)
if end < start:
    sys.exit("ERROR: markers out of order, refusing to patch")

bak = TARGET + ".bak_before_status_icons"
if not os.path.exists(bak):
    shutil.copyfile(TARGET, bak)

patched = src[:start] + new.rstrip() + EOL + EOL + src[end:]
open(TARGET, "w", encoding="utf-8", newline="").write(patched)
print("rg_gui.c patched: %d -> %d bytes" % (len(src), len(patched)))
