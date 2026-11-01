# ANTIGRAVITY EXECUTION PROMPT

You are executing a pre-written, pre-tested patch set on the Edgehax Retro Handheld S3 repo.
Repo root: `C:\Users\Gourav\Documents\GitHub\Retro Go`  (patch set: `claude_patches\`)
Rules: do not redesign anything; apply, build, flash, verify. If a build step fails, fix ONLY the compile error (smallest possible edit), re-run, and report what you changed. Never touch `partitions`, `platformio.ini` env names, or the flash offsets. Use PowerShell. Stop and report if serial shows a boot loop.

## 0. Branch + safety
```powershell
cd "C:\Users\Gourav\Documents\GitHub\Retro Go"
git status --short
git checkout -b claude/ui-clock-boot-fixes
git add claude_patches; git commit -m "Add Claude patch set (not yet applied)"
```

## 1. Retro-Go: beige 3-arc Wi-Fi icon + vertical battery with visible % (tasks A1, A2)
```powershell
python claude_patches\retro-go\apply_status_icons.py
git diff --stat retro-go\components\retro-go\rg_gui.c      # expect ONE file, only rg_gui_draw_icons() region changed
```
(The script keeps CRLF, is idempotent, and writes `rg_gui.c.bak_before_status_icons`.)

## 2. Bruce firmware sources (tasks A3, B1-B3, C1, C2)
```powershell
Copy-Item claude_patches\bruce\src\core\desk_clock.cpp                bruce\src\core\desk_clock.cpp -Force
Copy-Item claude_patches\bruce\src\core\boot_gif.h                    bruce\src\core\ -Force
Copy-Item claude_patches\bruce\src\core\boot_gif.cpp                  bruce\src\core\ -Force
Copy-Item claude_patches\bruce\src\modules\others\alarm_audio.h       bruce\src\modules\others\ -Force
Copy-Item claude_patches\bruce\src\modules\others\alarm_audio.cpp     bruce\src\modules\others\ -Force
python claude_patches\bruce\apply_boot_patch.py  bruce\src\main.cpp
python claude_patches\bruce\apply_audio_fix.py   bruce\src\modules\others\audio.cpp
git diff --stat bruce
```
New files are picked up automatically (`build_src_filter = +<*>`).

## 3. SD-card scripts (tasks D1, D2, E)
```powershell
Copy-Item "claude_patches\sd\BruceJS\Tools\Lock Device.js" "copy to SD card\BruceJS\Tools\Lock Device.js" -Force
Copy-Item "claude_patches\sd\BruceJS\Tools\Browser.js"     "copy to SD card\BruceJS\Tools\Browser.js" -Force
Copy-Item "claude_patches\sd\browser_bruce.js"             "copy to SD card\browser_bruce.js" -Force
```

## 4. Build Bruce (env `retro-handheld-s3`)
```powershell
cd bruce
& "C:\Users\Gourav\.platformio\penv\Scripts\pio.exe" run -e retro-handheld-s3 2>&1 | Tee-Object ..\build_bruce.log
cd ..
```
Likely-only compile issues and their minimal fixes:
* `desk_clock.cpp`: if `(GFX &)*g_fb` fails ("invalid cast") change `typedef TFT_eSPI GFX;` to the actual base class of `tft_sprite`/`tft_logger` (look at `include/tftLogger.h`).
* `alarm_audio.cpp`: if `SetOutputModeMono`/`SetRate` are missing in the installed ESP8266Audio, delete those two lines and keep the rest.
* `boot_gif.cpp`: if `gif->open(uint8_t*,int,cb)` is ambiguous, cast: `(GIF_DRAW_CALLBACK *)drawLine`.
Success = `.pio\build\retro-handheld-s3\firmware.bin` exists and is newer than the sources.

## 5. Build Retro-Go launcher
Use the exact same command/procedure you used for the last Retro-Go build (it produces `retro_go_build_latest\launcher.bin`). Confirm the file timestamp is new.

## 6. Flash both partitions (COM10, 921600)
```powershell
python flash_both.py
```
(esptool: Retro-Go `launcher.bin` @ 0x10000, Bruce `firmware.bin` @ 0x500000.) Wait for `Hard resetting via RTS pin...` and return code 0.

## 7. Update the SD card over Wi-Fi (device must be on 192.168.1.39)
```powershell
Invoke-RestMethod -Uri http://192.168.1.39/api -Method Post -ContentType application/json -Body '{"cmd":"ls","arg1":"/sd","arg2":""}'   # connectivity check
python upload_to_sd.py
```
`upload_to_sd.py` PUTs `Lock Device.js`, `Browser.js`, `browser_bruce.js` and the boot GIFs to `/sd/...`. Missing `.wav` files are expected now (boot audio was removed) - those lines may report failure; ignore them.
Verify the upload: `Invoke-WebRequest "http://192.168.1.39/sd/BruceJS/Tools/Browser.js" | Select -Expand Content | Select-String "hasPrefix"` must match.

## 8. Verify on serial (115200, COM10) and on the device
```powershell
& "C:\Users\Gourav\.platformio\penv\Scripts\python.exe" -m serial.tools.miniterm COM10 115200
```
Check and report each line PASS/FAIL:
1. Retro-Go launcher: status bar shows beige vertical battery + "NN%" to its LEFT with a gap, 3-arc beige Wi-Fi icon, nothing overlapping the "Super Nintendo" title.
2. Bruce boots straight into animation with NO sound; serial prints `[bootgif] /boot_anims/bruce_boot.gif: 152 frames in ~5100 ms` (frames must equal the GIF frame count; time ~5.0-5.5 s, NOT 5000 exactly). Press Y during boot -> animation skips.
3. Switch boot animation 1 and 2 (Settings): `cybernetic.gif` (143 frames) and `gemini_shark.gif` (144 frames) play to the end, silent.
4. Clock menu: faces cycle with LEFT/RIGHT (8 faces, no flip clock). Temperature shows like `18°C` with a ring degree sign. A opens "Clock Suite": faces, alarms, timer, stopwatch, display settings.
5. Alarm: set alarm 1 two minutes ahead (Alarms -> 1 -> Time), tune "Morning Bell". At the minute it must ring smoothly (no crackle between notes), get louder over ~10 s, A = snooze, B = stop. Run "Test sound" for each of the 6 tunes.
6. Lock Device.js (run from Bruce JS menu): battery shows the same percent as the Bruce status bar (NOT 77). Press A, START, B, D-pad: nothing happens. Press SELECT: PIN pad opens. Wrong PIN -> penalty screen; correct PIN -> unlock.
7. Browser.js: opens with no TypeError; press A, type a query, result is word-wrapped, UP/DOWN scrolls, X/Y switches AI/Wikipedia mode, B exits. If the AI/Wikipedia call fails the screen must show "Network request failed ... Detail: <reason>" (not crash) - report the Detail text.

## 9. Commit
```powershell
git add -A
git commit -m "Status bar icons, desk clock suite, alarm audio engine, smooth silent boot GIFs, lock/browser JS fixes" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01Fq4hc3VQNasxucHafAPM3y"
```
Report: build log tail, esptool result, the serial lines from step 8, and PASS/FAIL for items 1-7. If any FAIL, paste the exact serial/UI evidence - do not attempt redesigns.
