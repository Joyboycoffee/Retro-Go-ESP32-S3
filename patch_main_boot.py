with open('bruce/src/main.cpp', 'r', encoding='utf-8') as f:
    code = f.read()

target = '''void boot_screen_anim() {
    // If Instant Boot / Fast Boot is enabled: show static shark for 1 second, then proceed
    if (bruceConfig.instantBoot) {
        bool drawn = false;
        if (sdcardMounted && SD.exists("/boot.jpg")) {
            showJpeg(SD, "/boot.jpg", 0, 0, true);
            drawn = true;
        } else if (LittleFS.exists("/boot.jpg")) {
            showJpeg(LittleFS, "/boot.jpg", 0, 0, true);
            drawn = true;
        }
        if (!drawn) {
            showJpeg(boot_shark_jpg, boot_shark_jpg_len, 0, 0, true);
        }
        delay(1000);
        tft.fillScreen(bruceConfig.bgColor);
        return;
    }

    // Normal Boot (Fast Startup OFF): Full 4-5 second colored boot animation!
    bool animated = false;
    if (sdcardMounted && SD.exists("/boot.gif")) {
        animated = showGif(&SD, "/boot.gif", 0, 0, true, 4500, true);
    } else if (LittleFS.exists("/boot.gif")) {
        animated = showGif(&LittleFS, "/boot.gif", 0, 0, true, 4500, true);
    }

    if (!animated) {
        // Fallback if boot.gif not found: display color shark screen for 4 seconds
        tft.fillScreen(bruceConfig.bgColor);
        if (sdcardMounted && SD.exists("/boot.jpg")) {
            showJpeg(SD, "/boot.jpg", 0, 0, true);
        } else if (LittleFS.exists("/boot.jpg")) {
            showJpeg(LittleFS, "/boot.jpg", 0, 0, true);
        } else {
            showJpeg(boot_shark_jpg, boot_shark_jpg_len, 0, 0, true);
        }
        long start = millis();
        while (millis() - start < 4000) {
            if (check(AnyKeyPress)) break;
            delay(50);
        }
    }

    // Clear splash screen
    tft.fillScreen(bruceConfig.bgColor);
}'''

replacement = '''void boot_screen_anim() {
    // If Instant Boot / Fast Boot is enabled: show static shark for 1 second, then proceed
    if (bruceConfig.instantBoot) {
        bool drawn = false;
        if (sdcardMounted && SD.exists("/boot.jpg")) {
            showJpeg(SD, "/boot.jpg", 0, 0, true);
            drawn = true;
        } else if (LittleFS.exists("/boot.jpg")) {
            showJpeg(LittleFS, "/boot.jpg", 0, 0, true);
            drawn = true;
        }
        if (!drawn) {
            showJpeg(boot_shark_jpg, boot_shark_jpg_len, 0, 0, true);
        }
        delay(1000);
        tft.fillScreen(bruceConfig.bgColor);
        return;
    }

    // Normal Boot (Fast Startup OFF): High-FPS boot animation with audio & Button Y skip
    int anim = bruceConfig.bootAnim;
    bool animated = false;

    if (anim == 1) { // Cybernetic (Audio + 40fps animation)
        if (sdcardMounted && SD.exists("/boot_anims/cybernetic.wav")) {
            playAudioFile(&SD, "/boot_anims/cybernetic.wav", PLAYBACK_ASYNC);
        }
        if (sdcardMounted && SD.exists("/boot_anims/cybernetic.gif")) {
            animated = showGif(&SD, "/boot_anims/cybernetic.gif", 0, 0, true, 5000, true, true);
        }
    } else if (anim == 2) { // Shark Genesis (Audio + animation)
        if (sdcardMounted && SD.exists("/boot_anims/gemini_shark.wav")) {
            playAudioFile(&SD, "/boot_anims/gemini_shark.wav", PLAYBACK_ASYNC);
        }
        if (sdcardMounted && SD.exists("/boot_anims/gemini_shark.gif")) {
            animated = showGif(&SD, "/boot_anims/gemini_shark.gif", 0, 0, true, 5000, true, true);
        }
    } else if (anim == 3) { // Static Splash
        tft.fillScreen(bruceConfig.bgColor);
        if (sdcardMounted && SD.exists("/boot.jpg")) {
            showJpeg(SD, "/boot.jpg", 0, 0, true);
        } else {
            showJpeg(boot_shark_jpg, boot_shark_jpg_len, 0, 0, true);
        }
        long start = millis();
        while (millis() - start < 3000) {
            #if defined(RETRO_HANDHELD_S3)
            if (digitalRead(48) == LOW) break; // Button Y (GPIO 48)
            #else
            if (check(AnyKeyPress)) break;
            #endif
            delay(50);
        }
        animated = true;
    } else { // 0: Bruce 40FPS Main (Default)
        if (sdcardMounted && SD.exists("/boot_anims/bruce_boot.gif")) {
            animated = showGif(&SD, "/boot_anims/bruce_boot.gif", 0, 0, true, 5000, true, true);
        } else if (sdcardMounted && SD.exists("/boot.gif")) {
            animated = showGif(&SD, "/boot.gif", 0, 0, true, 5000, true, true);
        } else if (LittleFS.exists("/boot.gif")) {
            animated = showGif(&LittleFS, "/boot.gif", 0, 0, true, 5000, true, true);
        }
    }

    if (!animated) {
        // Fallback if SD animation is missing: display high-res shark screen
        tft.fillScreen(bruceConfig.bgColor);
        if (sdcardMounted && SD.exists("/boot.jpg")) {
            showJpeg(SD, "/boot.jpg", 0, 0, true);
        } else if (LittleFS.exists("/boot.jpg")) {
            showJpeg(LittleFS, "/boot.jpg", 0, 0, true);
        } else {
            showJpeg(boot_shark_jpg, boot_shark_jpg_len, 0, 0, true);
        }
        long start = millis();
        while (millis() - start < 3500) {
            #if defined(RETRO_HANDHELD_S3)
            if (digitalRead(48) == LOW) break; // Button Y (GPIO 48)
            #else
            if (check(AnyKeyPress)) break;
            #endif
            delay(50);
        }
    }

    // Stop async boot audio if still playing
    stopAudioPlayback();

    // Clear splash screen
    tft.fillScreen(bruceConfig.bgColor);
}'''

assert target in code, "target not found in main.cpp"
code = code.replace(target, replacement)

with open('bruce/src/main.cpp', 'w', encoding='utf-8') as f:
    f.write(code)
print("main.cpp patched successfully")
