import subprocess, sys, os

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

cmd = [
    r"C:\Users\Gourav\.platformio\penv\Scripts\python.exe",
    "-m",
    "esptool",
    "--chip",
    "esp32s3",
    "--port",
    "COM10",
    "--baud",
    "921600",
    "--before",
    "usb-reset",
    "--after",
    "hard-reset",
    "write-flash",
    "0x10000",
    r"retro_go_build_latest\launcher.bin",
    "0x500000",
    r"bruce\.pio\build\retro-handheld-s3\firmware.bin"
]

print("Flashing Retro-Go (0x10000) and Bruce (0x500000) to COM10...")
p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
for line in p.stdout:
    sys.stdout.buffer.write(line.encode("ascii", errors="replace"))
    sys.stdout.buffer.flush()
p.wait()
print(f"\nesptool finished with return code {p.returncode}")
sys.exit(p.returncode)
