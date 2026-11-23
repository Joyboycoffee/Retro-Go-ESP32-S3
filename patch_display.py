with open('bruce/src/core/display.cpp', 'r', encoding='utf-8') as f:
    c = f.read()

target = """bool showGif(
    FS *fs, const char *filename, int x, int y, bool center, int playDurationMs, bool resetButtonStatus
) {
    if (!fs->exists(filename)) return false;

    Gif gif;
    bool success = gif.openGIF(fs, filename);
    if (!success) { return false; }

    if (center) {
        x = x + (tftWidth - gif.getCanvasWidth()) / 2;
        y = y + (tftHeight - gif.getCanvasHeight()) / 2;
    }

    int result = 0;
    long timeStart = millis();
    do {
        result = gif.playFrame(x, y);
        if (result == -1) log_e("GIF playFrame error: %d\\n", gif.getLastError());

        if (check(AnyKeyPress, resetButtonStatus)) break;

        if (playDurationMs > 0 && (millis() - timeStart) > playDurationMs) break;
        if (playDurationMs == 0 && result == 0) break;
    } while (result >= 0);

    return true;
}"""

replacement = """bool showGif(
    FS *fs, const char *filename, int x, int y, bool center, int playDurationMs, bool resetButtonStatus, bool skipOnlyOnY
) {
    if (!fs->exists(filename)) return false;

    Gif gif;
    bool success = gif.openGIF(fs, filename);
    if (!success) { return false; }

    if (center) {
        x = x + (tftWidth - gif.getCanvasWidth()) / 2;
        y = y + (tftHeight - gif.getCanvasHeight()) / 2;
    }

    int result = 0;
    long timeStart = millis();
    do {
        result = gif.playFrame(x, y);
        if (result == -1) log_e("GIF playFrame error: %d\\n", gif.getLastError());

        if (skipOnlyOnY) {
            #if defined(RETRO_HANDHELD_S3)
            if (digitalRead(48) == LOW) break; // Button Y (GPIO 48, active LOW)
            #else
            if (check(AnyKeyPress, resetButtonStatus)) break;
            #endif
        } else {
            if (check(AnyKeyPress, resetButtonStatus)) break;
        }

        if (playDurationMs > 0 && (millis() - timeStart) > playDurationMs) break;
        if (playDurationMs == 0 && result == 0) break;
    } while (result >= 0);

    return true;
}"""

assert target in c, "target not in display.cpp"
c = c.replace(target, replacement)
with open('bruce/src/core/display.cpp', 'w', encoding='utf-8') as f:
    f.write(c)
print("display.cpp SUCCESS")
