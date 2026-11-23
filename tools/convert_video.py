"""
Retro Handheld Video Converter (MP4/MKV to 320x240 MJPEG AVI)
Produces 24 FPS Motion JPEG video with synchronized 16kHz mono 16-bit PCM audio,
optimized for silky-smooth hardware playback on the ESP32-S3 handheld.
"""

import sys, os, subprocess

def convert(input_path, output_path=None):
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found!")
        sys.exit(1)

    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = base + "_handheld.avi"

    # FFmpeg command:
    # 1. Scale with aspect ratio kept + letterbox pad to exactly 320x240
    # 2. MJPEG video @ 24 fps with quality 5 (optimal compression vs decode speed)
    # 3. 16-bit signed PCM audio @ 16000 Hz, 1 channel (MAX98357A I2S native)
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", "scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "mjpeg",
        "-q:v", "5",
        "-r", "24",
        "-c:a", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]

    print(f"Converting '{input_path}' -> '{output_path}'...")
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\n[SUCCESS] Conversion complete! File size: {size_mb:.2f} MB")
        print(f"Copy '{output_path}' to your MicroSD card and play it on your handheld!\n")
    else:
        print("\n[ERROR] FFmpeg conversion failed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_video.py <input_video.mp4> [output.avi]")
        sys.exit(1)
    in_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert(in_file, out_file)
