import os

path = r'C:\Users\Gourav\Documents\GitHub\Retro Go\retro-go\retro-core\main\main_snes.c'
with open(path, 'rb') as f:
    content = f.read()

old_keymap = b'''static const keymap_t KEYMAPS[] = {\r
\t{"Type A", {\r
\t\t{SNES_A_MASK, RG_KEY_A, 0},\r
\t\t{SNES_B_MASK, RG_KEY_B, 0},\r
\t\t{SNES_X_MASK, RG_KEY_START, 0},\r
\t\t{SNES_Y_MASK, RG_KEY_SELECT, 0},\r
\t\t{SNES_TL_MASK, RG_KEY_B, RG_KEY_MENU},\r
\t\t{SNES_TR_MASK, RG_KEY_A, RG_KEY_MENU},\r
\t\t{SNES_START_MASK, RG_KEY_START, RG_KEY_MENU},\r
\t\t{SNES_SELECT_MASK, RG_KEY_SELECT, RG_KEY_MENU},\r
\t\t{SNES_UP_MASK, RG_KEY_UP, 0},\r
\t\t{SNES_DOWN_MASK, RG_KEY_DOWN, 0},\r
\t\t{SNES_LEFT_MASK, RG_KEY_LEFT, 0},\r
\t\t{SNES_RIGHT_MASK, RG_KEY_RIGHT, 0},\r
\t}},'''

new_keymap = b'''static const keymap_t KEYMAPS[] = {\r
\t{"Standard 6-Btn", {\r
\t\t{SNES_A_MASK, RG_KEY_A, 0},\r
\t\t{SNES_B_MASK, RG_KEY_B, 0},\r
\t\t{SNES_X_MASK, RG_KEY_X, 0},\r
\t\t{SNES_Y_MASK, RG_KEY_Y, 0},\r
\t\t{SNES_TL_MASK, RG_KEY_B, RG_KEY_MENU},\r
\t\t{SNES_TR_MASK, RG_KEY_A, RG_KEY_MENU},\r
\t\t{SNES_START_MASK, RG_KEY_START, 0},\r
\t\t{SNES_SELECT_MASK, RG_KEY_SELECT, 0},\r
\t\t{SNES_UP_MASK, RG_KEY_UP, 0},\r
\t\t{SNES_DOWN_MASK, RG_KEY_DOWN, 0},\r
\t\t{SNES_LEFT_MASK, RG_KEY_LEFT, 0},\r
\t\t{SNES_RIGHT_MASK, RG_KEY_RIGHT, 0},\r
\t}},\r
\t{"Legacy 4-Btn", {\r
\t\t{SNES_A_MASK, RG_KEY_A, 0},\r
\t\t{SNES_B_MASK, RG_KEY_B, 0},\r
\t\t{SNES_X_MASK, RG_KEY_START, 0},\r
\t\t{SNES_Y_MASK, RG_KEY_SELECT, 0},\r
\t\t{SNES_TL_MASK, RG_KEY_B, RG_KEY_MENU},\r
\t\t{SNES_TR_MASK, RG_KEY_A, RG_KEY_MENU},\r
\t\t{SNES_START_MASK, RG_KEY_START, RG_KEY_MENU},\r
\t\t{SNES_SELECT_MASK, RG_KEY_SELECT, RG_KEY_MENU},\r
\t\t{SNES_UP_MASK, RG_KEY_UP, 0},\r
\t\t{SNES_DOWN_MASK, RG_KEY_DOWN, 0},\r
\t\t{SNES_LEFT_MASK, RG_KEY_LEFT, 0},\r
\t\t{SNES_RIGHT_MASK, RG_KEY_RIGHT, 0},\r
\t}},'''

if old_keymap in content:
    content = content.replace(old_keymap, new_keymap)
    with open(path, 'wb') as f:
        f.write(content)
    print("Successfully patched main_snes.c with Standard 6-Button layout!")
else:
    print("Pattern not found in main_snes.c")
