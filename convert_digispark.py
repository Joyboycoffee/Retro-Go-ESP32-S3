import os
import glob
import re

# Destination folder for converted BadUSB scripts
OUTPUT_DIR = os.path.join(os.getcwd(), "badusb_payloads")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Key code mappings
KEY_MAP = {
    'KEY_ENTER': 'ENTER',
    'KEY_TAB': 'TAB',
    'KEY_SPACE': 'SPACE',
    'KEY_ARROW_LEFT': 'LEFT',
    'KEY_ARROW_RIGHT': 'RIGHT',
    'KEY_ARROW_UP': 'UP',
    'KEY_ARROW_DOWN': 'DOWN',
    '81': 'DOWN',
    '70': 'PRINTSCREEN',
    'KEY_F1': 'F1',
    'KEY_F2': 'F2',
    'KEY_F3': 'F3',
    'KEY_F4': 'F4',
    'KEY_F5': 'F5',
    'KEY_F6': 'F6',
    'KEY_F7': 'F7',
    'KEY_F8': 'F8',
    'KEY_F9': 'F9',
    'KEY_F10': 'F10',
    'KEY_F11': 'F11',
    'KEY_F12': 'F12',
    'KEY_A': 'a',
    'KEY_B': 'b',
    'KEY_C': 'c',
    'KEY_D': 'd',
    'KEY_E': 'e',
    'KEY_F': 'f',
    'KEY_G': 'g',
    'KEY_H': 'h',
    'KEY_I': 'i',
    'KEY_J': 'j',
    'KEY_K': 'k',
    'KEY_L': 'l',
    'KEY_M': 'm',
    'KEY_N': 'n',
    'KEY_O': 'o',
    'KEY_P': 'p',
    'KEY_Q': 'q',
    'KEY_R': 'r',
    'KEY_S': 's',
    'KEY_T': 't',
    'KEY_U': 'u',
    'KEY_V': 'v',
    'KEY_W': 'w',
    'KEY_X': 'x',
    'KEY_Y': 'y',
    'KEY_Z': 'z',
}

MOD_MAP = {
    'MOD_GUI_LEFT': 'GUI',
    'MOD_CONTROL_LEFT': 'CTRL',
    'MOD_ALT_LEFT': 'ALT',
    'MOD_SHIFT_LEFT': 'SHIFT',
}

def unescape_c_string(s):
    # If the string was wrapped in F("...") or ("...")
    s = s.strip()
    if s.startswith('F(') and s.endswith(')'):
        s = s[2:-1].strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    
    # Unescape C escapes
    # Replace escaped quotes and backslashes
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            nxt = s[i+1]
            if nxt == '"':
                result.append('"')
                i += 2
            elif nxt == "'":
                result.append("'")
                i += 2
            elif nxt == '\\':
                result.append('\\')
                i += 2
            elif nxt == 'n':
                result.append('\n')
                i += 2
            elif nxt == 'r':
                result.append('\r')
                i += 2
            elif nxt == 't':
                result.append('\t')
                i += 2
            else:
                result.append(s[i:i+2])
                i += 2
        else:
            result.append(s[i])
            i += 1
    return "".join(result)

def parse_keystroke_args(args_str):
    parts = [p.strip() for p in args_str.split(',')]
    
    # Handle cases like "0" or "0, MOD_GUI_LEFT"
    if len(parts) == 1:
        arg = parts[0]
        if arg == '0':
            return None # Release / clear
        if arg in KEY_MAP:
            mapped = KEY_MAP[arg]
            if len(mapped) == 1:
                return f"STRING {mapped}"
            else:
                return mapped
        return f"REM Unknown key: {arg}"

    elif len(parts) == 2:
        part1, part2 = parts[0], parts[1]
        
        # Check if part1 or part2 has combined modifiers, or reversed args
        key_part = None
        mod_part = None
        
        # Identify key vs modifier
        # Note: sometimes it's (MOD_ALT_LEFT, KEY_Y)
        if 'MOD_' in part1 and 'MOD_' not in part2:
            mod_part, key_part = part1, part2
        else:
            key_part, part2 = part1, part2
            mod_part = part2
            
        # If key_part is "0", check if mod_part has a key combined with |
        # e.g. "0, MOD_GUI_LEFT | KEY_R"
        if key_part == '0' and '|' in mod_part:
            subparts = [p.strip() for p in mod_part.split('|')]
            for sp in subparts:
                if 'KEY_' in sp:
                    key_part = sp
                elif 'MOD_' in sp:
                    mod_part = sp

        # Parse modifiers
        mods = []
        # Could be "MOD_CONTROL_LEFT + MOD_SHIFT_LEFT" or "MOD_CONTROL_LEFT | MOD_SHIFT_LEFT"
        mod_tokens = re.split(r'[\+\|]', mod_part)
        for token in mod_tokens:
            token = token.strip()
            if token in MOD_MAP:
                mods.append(MOD_MAP[token])
                
        # Parse key
        key_str = ""
        if key_part == '0':
            # Just modifier key
            if mods:
                return f"{mods[0]}"
            return None
        elif key_part in KEY_MAP:
            key_str = KEY_MAP[key_part]
        else:
            key_str = key_part
            
        if len(mods) == 0:
            if len(key_str) == 1:
                return f"STRING {key_str}"
            return key_str
        elif len(mods) == 1:
            return f"{mods[0]} {key_str}"
        elif len(mods) == 2:
            return f"{mods[0]}-{mods[1]} {key_str}"
        else:
            return f"{'-'.join(mods)} {key_str}"

    return f"REM Unhandled sendKeyStroke: {args_str}"

def convert_ino_to_ducky(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    lines = content.splitlines()
    out = []
    
    # Track defined variables
    variables = {}
    
    # First pass: find char variable definitions like:
    # char mode[] = "powershell -nop -win h -noni -exec bypass";
    # char separator[] = "exit";
    for line in lines:
        var_match = re.search(r'char\s+([A-Za-z0-9_]+)\[\]\s*=\s*"([^"]+)";', line)
        if var_match:
            variables[var_match.group(1)] = var_match.group(2)

    out.append("REM ========================================================")
    base_name = os.path.basename(file_path)
    out.append(f"REM Payload: {base_name}")
    out.append("REM Converted from DigiKeyboard (.ino) to DuckyScript (.txt)")
    out.append("REM Compatible with Bruce BadUSB (USB HID & BLE HID)")
    out.append("REM ========================================================\n")
    
    in_block_comment = False
    
    for line in lines:
        sline = line.strip()
        
        # Block comments
        if in_block_comment:
            if '*/' in sline:
                in_block_comment = False
                comment_part = sline[:sline.find('*/')]
                if comment_part.strip():
                    out.append(f"REM {comment_part.strip()}")
            else:
                out.append(f"REM {sline}")
            continue
            
        if sline.startswith('/*'):
            in_block_comment = True
            comment_part = sline[2:]
            if '*/' in comment_part:
                in_block_comment = False
                comment_part = comment_part[:comment_part.find('*/')]
            if comment_part.strip():
                out.append(f"REM {comment_part.strip()}")
            continue
            
        # Line comments
        if sline.startswith('//'):
            out.append(f"REM {sline[2:].strip()}")
            continue
            
        # Ignore boilerplate
        if (sline.startswith('#include') or 
            sline.startswith('void setup') or 
            sline.startswith('void loop') or 
            sline.startswith('pinMode') or
            sline.startswith('digitalWrite') or
            sline == '{' or sline == '}' or sline == '' or
            'for(;;)' in sline or 'for (;;)' in sline):
            continue

        # DigiKeyboard.delay(N)
        delay_match = re.search(r'DigiKeyboard\.delay\(([0-9]+)\);', sline)
        if delay_match:
            ms = delay_match.group(1)
            out.append(f"DELAY {ms}")
            continue

        # DigiKeyboard.sendKeyStroke(...)
        stroke_match = re.search(r'DigiKeyboard\.sendKeyStroke\(([^;]+)\);', sline)
        if stroke_match:
            cmd = parse_keystroke_args(stroke_match.group(1))
            if cmd:
                out.append(cmd)
            continue

        # DigiKeyboard.print(...) and println(...)
        print_match = re.search(r'DigiKeyboard\.(print|println)\((.+)\);', sline)
        if print_match:
            is_ln = (print_match.group(1) == 'println')
            raw_arg = print_match.group(2).strip()
            
            # Check if variable
            if raw_arg in variables:
                text = variables[raw_arg]
            else:
                text = unescape_c_string(raw_arg)
                
            # If text has newlines (\n), split into multiple STRING / ENTER lines
            if '\n' in text:
                sublines = text.split('\n')
                for i, sub in enumerate(sublines):
                    if sub:
                        out.append(f"STRING {sub}")
                    if i < len(sublines) - 1:
                        out.append("ENTER")
                if is_ln:
                    out.append("ENTER")
            else:
                if is_ln:
                    out.append(f"STRINGLN {text}")
                else:
                    out.append(f"STRING {text}")
            continue

        # Any inline comment at end of line
        # If there's an unhandled statement:
        if sline and not sline.startswith('//'):
            out.append(f"REM [Note] {sline}")

    return "\n".join(out)

# Process all .ino files
ino_files = sorted(glob.glob('digispark_scripts/**/*.ino', recursive=True))
print(f"Found {len(ino_files)} .ino files.")

converted_count = 0
for file_path in ino_files:
    folder_name = os.path.basename(os.path.dirname(file_path))
    file_name = os.path.basename(file_path)
    
    # Clean up name: handle non-ascii like Κeylogger -> Keylogger
    clean_file_name = file_name.replace('Κ', 'K').replace('?', 'K')
    txt_name = os.path.splitext(clean_file_name)[0] + ".txt"
    
    # Destination
    out_file = os.path.join(OUTPUT_DIR, txt_name)
    
    ducky_code = convert_ino_to_ducky(file_path)
    with open(out_file, 'w', encoding='utf-8') as out_f:
        out_f.write(ducky_code)
        
    converted_count += 1
    print(f"[{converted_count}/{len(ino_files)}] Converted: {file_name} -> {txt_name}")

print(f"\nSuccessfully converted all {converted_count} scripts to: {OUTPUT_DIR}")
