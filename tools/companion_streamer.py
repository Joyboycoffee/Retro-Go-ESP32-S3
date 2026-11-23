"""
Retro Handheld PC Companion & Streamer Server
Features:
- High-Speed PC Screen Streaming (320x240 MJPEG @ 25-30 FPS)
- Remote PC Mouse & Keyboard Control from ESP32 Handheld
- YouTube Downloader & Transcoder to 320x240 AVI (SD Card Video Player)
- Web Browser Proxy & Visual Snapshot for Handheld
"""

import os
import io
import time
import subprocess
import threading
from flask import Flask, Response, request, jsonify, render_template_string
import mss
import pyautogui
from PIL import Image, ImageDraw

pyautogui.FAILSAFE = False
app = Flask(__name__)

# Video & Stream Settings
TARGET_WIDTH = 320
TARGET_HEIGHT = 240
JPEG_QUALITY = 72

sct = mss.mss()

def capture_screen_frame():
    """Captures desktop, scales to 320x240, renders cursor, returns JPEG bytes."""
    monitor = sct.monitors[1] # Primary monitor
    sct_img = sct.grab(monitor)
    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    # Draw mouse pointer
    mx, my = pyautogui.position()
    draw = ImageDraw.Draw(img)
    draw.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=(255, 0, 0), outline=(255, 255, 255))
    draw.line([mx - 10, my, mx + 10, my], fill=(255, 255, 255), width=2)
    draw.line([mx, my - 10, mx, my + 10], fill=(255, 255, 255), width=2)

    # Resize to handheld resolution
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.BILINEAR)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()

def generate_mjpeg_stream():
    """MJPEG stream generator for ESP32 and web browsers."""
    while True:
        frame = capture_screen_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033) # ~30 FPS

@app.route("/")
def index():
    return """
    <html>
    <head><title>Retro Handheld PC Companion</title></head>
    <body style="font-family: sans-serif; background: #121212; color: #eee; text-align: center; padding: 20px;">
        <h2>🎮 Retro Handheld PC Companion & Streamer</h2>
        <p>Live Desktop Stream (320x240):</p>
        <img src="/stream" style="border: 2px solid #00f0ff; width: 640px; height: 480px; image-rendering: pixelated;"><br><br>
        <div style="background: #222; max-width: 600px; margin: auto; padding: 15px; border-radius: 8px;">
            <h3>Endpoints for ESP32 Handheld:</h3>
            <p><b>Screen MJPEG Stream:</b> <code>/stream</code></p>
            <p><b>Single JPEG Frame:</b> <code>/frame.jpg</code></p>
            <p><b>Remote Mouse Control:</b> <code>/mouse?dx=10&dy=0&click=left</code></p>
            <p><b>YouTube Transcode to SD AVI:</b> <code>/youtube/download?url=...</code></p>
            <p><b>Web Browser Proxy:</b> <code>/browse?url=https://...</code></p>
        </div>
    </body>
    </html>
    """

@app.route("/stream")
def video_feed():
    return Response(generate_mjpeg_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/frame.jpg")
def single_frame():
    frame = capture_screen_frame()
    return Response(frame, mimetype='image/jpeg')

@app.route("/mouse")
def control_mouse():
    """
    Handle remote mouse commands from the handheld.
    Query params:
      dx, dy: relative movement (-50 to +50)
      click: 'left', 'right', 'double'
      scroll: 'up', 'down'
    """
    dx = int(request.args.get("dx", 0))
    dy = int(request.args.get("dy", 0))
    click = request.args.get("click", "")
    scroll = request.args.get("scroll", "")

    if dx != 0 or dy != 0:
        pyautogui.moveRel(dx, dy)

    if click == "left":
        pyautogui.click()
    elif click == "right":
        pyautogui.rightClick()
    elif click == "double":
        pyautogui.doubleClick()

    if scroll == "up":
        pyautogui.scroll(120)
    elif scroll == "down":
        pyautogui.scroll(-120)

    return jsonify({"status": "ok", "pos": pyautogui.position()})

@app.route("/youtube/download")
def download_youtube_video():
    """
    Downloads any YouTube video, downscales to 320x240 @ 24fps MJPEG AVI with 16kHz mono audio,
    ready to copy onto the handheld SD card!
    """
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "Missing url parameter"}), 400

    output_dir = os.path.join(os.path.expanduser("~"), "RetroHandheldVideos")
    os.makedirs(output_dir, exist_ok=True)
    out_avi = os.path.join(output_dir, f"video_{int(time.time())}.avi")

    def run_transcode():
        cmd = f'yt-dlp -f "best[height<=720]" -o - "{url}" | ffmpeg -i - -vf "scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2" -c:v mjpeg -q:v 5 -r 24 -c:a pcm_s16le -ar 16000 -ac 1 -y "{out_avi}"'
        subprocess.run(cmd, shell=True)

    t = threading.Thread(target=run_transcode)
    t.start()

    return jsonify({
        "status": "transcoding_started",
        "destination": out_avi,
        "instructions": "Copy this .avi file to your MicroSD card to play at silky-smooth 24 FPS with I2S audio!"
    })

@app.route("/browse")
def web_proxy():
    """
    Fetches any webpage, strips scripts/ads, extracts text and headings,
    and returns a clean readable format tailored for the 320x240 screen.
    """
    target = request.args.get("url", "https://news.ycombinator.com")
    import urllib.request
    from urllib.parse import urlparse
    try:
        req = urllib.request.Request(target, headers={'User-Agent': 'Mozilla/5.0 (RetroHandheld Browser)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw_html = resp.read().decode('utf-8', errors='ignore')

        import re
        # Strip script, style, tags
        raw_html = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL)
        raw_html = re.sub(r'<style.*?</style>', '', raw_html, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', raw_html)
        text = re.sub(r'\s+', ' ', text).strip()

        return jsonify({
            "url": target,
            "text": text[:2000] # First 2000 chars for handheld display
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()

    print(f"\n=======================================================")
    print(f"  🎮 RETRO HANDHELD PC COMPANION STREAMER RUNNING")
    print(f"  IP Address: http://{local_ip}:5000")
    print(f"  Desktop Stream: http://{local_ip}:5000/stream")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=5000, threaded=True)
