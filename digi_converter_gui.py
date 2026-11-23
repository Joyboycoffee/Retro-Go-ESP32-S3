import os
import sys
import glob
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# ==============================================================================
# KEY & MODIFIER MAPPINGS FOR DUCKY SCRIPT
# ==============================================================================

KEY_MAP = {
    'KEY_ENTER': 'ENTER',
    'KEY_RETURN': 'ENTER',
    'KEY_TAB': 'TAB',
    'KEY_SPACE': 'SPACE',
    'KEY_ESC': 'ESC',
    'KEY_ESCAPE': 'ESC',
    'KEY_BACKSPACE': 'BACKSPACE',
    'KEY_DELETE': 'DELETE',
    'KEY_ARROW_LEFT': 'LEFT',
    'KEY_ARROW_RIGHT': 'RIGHT',
    'KEY_ARROW_UP': 'UP',
    'KEY_ARROW_DOWN': 'DOWN',
    'KEY_PAGE_UP': 'PAGEUP',
    'KEY_PAGE_DOWN': 'PAGEDOWN',
    'KEY_HOME': 'HOME',
    'KEY_END': 'END',
    'KEY_CAPS_LOCK': 'CAPSLOCK',
    '81': 'DOWN',          # HID scan code 0x51 for Down Arrow
    '70': 'PRINTSCREEN',   # HID scan code 0x46 for PrintScreen
}

# Function keys F1 - F24
for i in range(1, 25):
    KEY_MAP[f'KEY_F{i}'] = f'F{i}'

# Letters KEY_A - KEY_Z
for c in range(ord('A'), ord('Z') + 1):
    char = chr(c)
    KEY_MAP[f'KEY_{char}'] = char.lower()

MOD_MAP = {
    'MOD_GUI_LEFT': 'GUI',
    'MOD_GUI_RIGHT': 'GUI',
    'MOD_CONTROL_LEFT': 'CTRL',
    'MOD_CONTROL_RIGHT': 'CTRL',
    'MOD_ALT_LEFT': 'ALT',
    'MOD_ALT_RIGHT': 'ALT',
    'MOD_SHIFT_LEFT': 'SHIFT',
    'MOD_SHIFT_RIGHT': 'SHIFT',
}

# ==============================================================================
# CONVERSION ENGINE LOGIC
# ==============================================================================

def unescape_c_string(s):
    """Unescapes C/C++ string literal escape sequences into literal characters."""
    s = s.strip()
    if s.startswith('F(') and s.endswith(')'):
        s = s[2:-1].strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
        
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

def parse_keystroke(args_str):
    """Converts DigiKeyboard.sendKeyStroke(...) args to DuckyScript commands."""
    parts = [p.strip() for p in args_str.split(',')]
    
    if len(parts) == 1:
        arg = parts[0]
        if arg == '0':
            return None  # Key release
        if arg in KEY_MAP:
            mapped = KEY_MAP[arg]
            if len(mapped) == 1:
                return f"STRING {mapped}"
            return mapped
        return f"REM Key: {arg}"

    elif len(parts) >= 2:
        part1, part2 = parts[0], parts[1]
        
        # Check argument ordering: (key, mod) vs (mod, key)
        if 'MOD_' in part1 and 'MOD_' not in part2:
            mod_part, key_part = part1, part2
        else:
            key_part, mod_part = part1, part2
            
        # Handle "0, MOD_GUI_LEFT | KEY_R"
        if key_part == '0' and '|' in mod_part:
            for sub in mod_part.split('|'):
                sub = sub.strip()
                if 'KEY_' in sub:
                    key_part = sub
                elif 'MOD_' in sub:
                    mod_part = sub

        # Extract all modifiers (can be joined by + or |)
        mods = []
        for token in re.split(r'[\+\|]', mod_part):
            token = token.strip()
            if token in MOD_MAP:
                mods.append(MOD_MAP[token])

        # Resolve the key
        key_str = ""
        if key_part == '0':
            if mods:
                return mods[0]
            return None
        elif key_part in KEY_MAP:
            key_str = KEY_MAP[key_part]
        else:
            key_str = key_part

        if not mods:
            if len(key_str) == 1:
                return f"STRING {key_str}"
            return key_str
        elif len(mods) == 1:
            return f"{mods[0]} {key_str}"
        elif len(mods) == 2:
            return f"{mods[0]}-{mods[1]} {key_str}"
        else:
            return f"{'-'.join(mods)} {key_str}"

    return f"REM Unhandled Keystroke: {args_str}"

def convert_ino_file(source_path):
    """Converts a single .ino file content into Bruce-compatible DuckyScript string."""
    with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    lines = content.splitlines()
    out = []
    
    # Track C char variables (e.g. char mode[] = "..."; char separator[] = "...";)
    variables = {}
    for line in lines:
        var_match = re.search(r'char\s+([A-Za-z0-9_]+)\[\]\s*=\s*"([^"]+)";', line)
        if var_match:
            variables[var_match.group(1)] = var_match.group(2)

    base_name = os.path.basename(source_path)
    out.append("REM ========================================================")
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
                cpart = sline[:sline.find('*/')].strip()
                if cpart:
                    out.append(f"REM {cpart}")
            else:
                out.append(f"REM {sline}")
            continue
            
        if sline.startswith('/*'):
            in_block_comment = True
            cpart = sline[2:]
            if '*/' in cpart:
                in_block_comment = False
                cpart = cpart[:cpart.find('*/')]
            if cpart.strip():
                out.append(f"REM {cpart.strip()}")
            continue
            
        # Line comments
        if sline.startswith('//'):
            out.append(f"REM {sline[2:].strip()}")
            continue
            
        # Skip Arduino setup/loop/pin boilerplate
        if (sline.startswith('#include') or 
            sline.startswith('void setup') or 
            sline.startswith('void loop') or 
            sline.startswith('pinMode') or
            sline.startswith('digitalWrite') or
            sline == '{' or sline == '}' or sline == '' or
            'for(;;)' in sline or 'for (;;)' in sline):
            continue

        # DigiKeyboard.delay(...)
        delay_m = re.search(r'DigiKeyboard\.delay\(([0-9]+)\);', sline)
        if delay_m:
            out.append(f"DELAY {delay_m.group(1)}")
            continue

        # DigiKeyboard.sendKeyStroke(...)
        stroke_m = re.search(r'DigiKeyboard\.sendKeyStroke\(([^;]+)\);', sline)
        if stroke_m:
            cmd = parse_keystroke(stroke_m.group(1))
            if cmd:
                out.append(cmd)
            continue

        # DigiKeyboard.print(...) / println(...)
        print_m = re.search(r'DigiKeyboard\.(print|println)\((.+)\);', sline)
        if print_m:
            is_ln = (print_m.group(1) == 'println')
            raw_arg = print_m.group(2).strip()
            
            if raw_arg in variables:
                text = variables[raw_arg]
            else:
                text = unescape_c_string(raw_arg)
                
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

        # Note any untranslated code for user transparency
        if sline and not sline.startswith('//'):
            out.append(f"REM [Code] {sline}")

    return "\n".join(out) + "\n"

# ==============================================================================
# TKINTER GUI APPLICATION
# ==============================================================================

class DigiConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DigiSpark to Bruce BadUSB Converter")
        self.root.geometry("740x580")
        self.root.minsize(680, 500)
        
        # Color Scheme (Modern Dark Theme)
        self.BG_COLOR = "#1e1e2e"
        self.SURFACE_COLOR = "#2a2b3d"
        self.TEXT_COLOR = "#cdd6f4"
        self.ACCENT_COLOR = "#89b4fa"
        self.SUCCESS_COLOR = "#a6e3a1"
        self.BTN_COLOR = "#313244"
        self.BTN_HOVER = "#45475a"
        self.CONSOLE_BG = "#181825"
        self.CONSOLE_FG = "#a6adc8"
        
        self.root.configure(bg=self.BG_COLOR)
        
        self.source_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready. Select a folder to begin.")
        
        self._setup_styles()
        self._build_ui()
        
    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Progressbar styling
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=self.CONSOLE_BG,
            background=self.ACCENT_COLOR,
            darkcolor=self.ACCENT_COLOR,
            lightcolor=self.ACCENT_COLOR,
            bordercolor=self.CONSOLE_BG
        )

    def _build_ui(self):
        # Header Frame
        header = tk.Frame(self.root, bg=self.BG_COLOR, padx=20, pady=15)
        header.pack(fill=tk.X)
        
        title_lbl = tk.Label(
            header,
            text="DigiSpark (.ino) ➔ Bruce BadUSB (.txt)",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_COLOR,
            fg=self.ACCENT_COLOR
        )
        title_lbl.pack(anchor="w")
        
        sub_lbl = tk.Label(
            header,
            text="Recursively converts DigiKeyboard Arduino scripts into DuckyScript .txt files ready for your ESP32-S3 SD card (/badusb/).",
            font=("Segoe UI", 9),
            bg=self.BG_COLOR,
            fg="#9399b2"
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        # Main Card Frame
        card = tk.Frame(self.root, bg=self.SURFACE_COLOR, padx=18, pady=15, relief=tk.FLAT)
        card.pack(fill=tk.X, padx=20, pady=5)
        
        # Source Folder Input
        src_lbl = tk.Label(card, text="Source Folder (containing .ino files):", font=("Segoe UI", 10, "bold"), bg=self.SURFACE_COLOR, fg=self.TEXT_COLOR)
        src_lbl.pack(anchor="w")
        
        src_row = tk.Frame(card, bg=self.SURFACE_COLOR)
        src_row.pack(fill=tk.X, pady=(5, 12))
        
        self.src_entry = tk.Entry(
            src_row,
            textvariable=self.source_folder,
            font=("Consolas", 10),
            bg=self.CONSOLE_BG,
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR,
            relief=tk.FLAT,
            bd=5
        )
        self.src_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(
            src_row,
            text="📂 Browse...",
            font=("Segoe UI", 9, "bold"),
            bg=self.BTN_COLOR,
            fg=self.TEXT_COLOR,
            activebackground=self.BTN_HOVER,
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.browse_source
        )
        browse_btn.pack(side=tk.RIGHT)

        # Destination Folder Preview
        dest_lbl = tk.Label(card, text="Destination Folder (will be created as 'converted'):", font=("Segoe UI", 9), bg=self.SURFACE_COLOR, fg="#9399b2")
        dest_lbl.pack(anchor="w")
        
        self.dest_entry = tk.Entry(
            card,
            textvariable=self.dest_folder,
            font=("Consolas", 9),
            bg=self.CONSOLE_BG,
            fg="#6c7086",
            state="readonly",
            relief=tk.FLAT,
            bd=5
        )
        self.dest_entry.pack(fill=tk.X, pady=(4, 5))

        # Action Buttons Row
        btn_row = tk.Frame(self.root, bg=self.BG_COLOR, padx=20, pady=8)
        btn_row.pack(fill=tk.X)
        
        self.convert_btn = tk.Button(
            btn_row,
            text="⚡ Start Conversion",
            font=("Segoe UI", 11, "bold"),
            bg="#89b4fa",
            fg="#11111b",
            activebackground="#b4befe",
            activeforeground="#11111b",
            relief=tk.FLAT,
            padx=20,
            pady=6,
            cursor="hand2",
            command=self.start_conversion
        )
        self.convert_btn.pack(side=tk.LEFT)
        
        self.open_btn = tk.Button(
            btn_row,
            text="📁 Open 'converted' Folder",
            font=("Segoe UI", 10),
            bg=self.BTN_COLOR,
            fg=self.TEXT_COLOR,
            activebackground=self.BTN_HOVER,
            activeforeground=self.TEXT_COLOR,
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            state=tk.DISABLED,
            command=self.open_converted_folder
        )
        self.open_btn.pack(side=tk.LEFT, padx=12)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, style="Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill=tk.X, padx=20, pady=(5, 5))

        # Status Label
        self.status_lbl = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "italic"),
            bg=self.BG_COLOR,
            fg=self.ACCENT_COLOR
        )
        self.status_lbl.pack(anchor="w", padx=20, pady=(0, 5))

        # Console Log Frame
        log_frame = tk.Frame(self.root, bg=self.CONSOLE_BG, padx=8, pady=8)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.log_text = tk.Text(
            log_frame,
            font=("Consolas", 9),
            bg=self.CONSOLE_BG,
            fg=self.CONSOLE_FG,
            insertbackground=self.TEXT_COLOR,
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview, bg=self.SURFACE_COLOR)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tags for colored console log output
        self.log_text.tag_config("info", foreground="#89b4fa")
        self.log_text.tag_config("success", foreground="#a6e3a1")
        self.log_text.tag_config("warn", foreground="#f9e2af")
        self.log_text.tag_config("error", foreground="#f38ba8")
        
        self.log("Welcome to DigiSpark to Bruce BadUSB Converter!", "info")
        self.log("Select a source folder to scan for .ino files.\n", "info")

    def log(self, text, tag=None):
        self.log_text.insert(tk.END, text + "\n", tag)
        self.log_text.see(tk.END)

    def browse_source(self):
        folder = filedialog.askdirectory(title="Select Folder Containing .ino Files")
        if folder:
            self.source_folder.set(folder)
            dest = os.path.join(folder, "converted")
            self.dest_folder.set(dest)
            
            # Count .ino files in folder
            ino_files = glob.glob(os.path.join(folder, "**", "*.ino"), recursive=True)
            self.log(f"Selected: {folder}", "info")
            self.log(f"Found {len(ino_files)} .ino file(s) in selected directory.", "success" if ino_files else "warn")
            self.status_var.set(f"Ready: Found {len(ino_files)} .ino file(s).")
            self.open_btn.config(state=tk.NORMAL if os.path.exists(dest) else tk.DISABLED)

    def open_converted_folder(self):
        dest = self.dest_folder.get()
        if os.path.exists(dest):
            os.startfile(dest)
        else:
            messagebox.showinfo("Folder Not Found", "Converted folder has not been created yet.")

    def start_conversion(self):
        src = self.source_folder.get().strip()
        if not src or not os.path.isdir(src):
            messagebox.showwarning("Invalid Folder", "Please select a valid source folder first.")
            return

        self.convert_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self._run_conversion_worker, args=(src,), daemon=True)
        thread.start()

    def _run_conversion_worker(self, src):
        dest_root = os.path.join(src, "converted")
        self.log(f"\n--- Starting Conversion ---", "info")
        self.log(f"Source: {src}", "info")
        self.log(f"Target: {dest_root}\n", "info")
        
        ino_files = glob.glob(os.path.join(src, "**", "*.ino"), recursive=True)
        
        # Exclude any files already inside 'converted' folder if re-running
        ino_files = [f for f in ino_files if os.path.abspath(f) != os.path.abspath(dest_root) and not os.path.abspath(f).startswith(os.path.abspath(dest_root) + os.sep)]
        
        total = len(ino_files)
        if total == 0:
            self.log("No .ino files found to convert!", "warn")
            self.status_var.set("No .ino files found.")
            self.convert_btn.config(state=tk.NORMAL)
            return

        converted_count = 0
        for idx, file_path in enumerate(ino_files, start=1):
            rel_path = os.path.relpath(file_path, src)
            rel_dir = os.path.dirname(rel_path)
            file_name = os.path.basename(file_path)
            
            # Clean filename (e.g. replace Greek kappa or non-ascii with K)
            clean_name = file_name.replace('Κ', 'K').replace('?', 'K')
            txt_name = os.path.splitext(clean_name)[0] + ".txt"
            
            target_dir = os.path.join(dest_root, rel_dir)
            os.makedirs(target_dir, exist_ok=True)
            target_file = os.path.join(target_dir, txt_name)
            
            self.status_var.set(f"Converting [{idx}/{total}]: {file_name}...")
            self.log(f"[{idx}/{total}] Converting: {rel_path} ➔ {os.path.join(rel_dir, txt_name)}")
            
            try:
                ducky_content = convert_ino_file(file_path)
                with open(target_file, 'w', encoding='utf-8') as out_f:
                    out_f.write(ducky_content)
                converted_count += 1
            except Exception as e:
                self.log(f"  ❌ Error converting {file_name}: {e}", "error")
                
            progress_pct = (idx / total) * 100
            self.progress['value'] = progress_pct
            self.root.update_idletasks()

        self.log(f"\n🎉 Successfully converted {converted_count}/{total} files!", "success")
        self.log(f"All files saved in: {dest_root}", "success")
        self.log("You can now copy the folders inside 'converted' directly to your SD card under /badusb/.\n", "info")
        
        self.status_var.set(f"Completed! {converted_count} files converted successfully.")
        self.convert_btn.config(state=tk.NORMAL)
        self.open_btn.config(state=tk.NORMAL)
        
        # Notify user
        messagebox.showinfo(
            "Conversion Complete",
            f"Successfully converted {converted_count} files!\n\nSaved inside:\n{dest_root}"
        )

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = DigiConverterApp(root)
    root.mainloop()
