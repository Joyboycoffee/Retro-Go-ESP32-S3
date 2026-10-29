import serial
import time
import sys

port = 'COM10'
baud = 115200

try:
    s = serial.Serial(port, baud, timeout=1)
    print(f"Connected to {port}! Listening for button presses...\n", flush=True)
    while True:
        line = s.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print(line, flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
