@echo off
echo ========================================================
echo   Retro-Go Library Sync & Auto-Clean for Drive F:
echo ========================================================

if not exist F:\ (
    echo Error: Drive F: is not detected. Please plug in your SD card!
    pause
    exit /b 1
)

echo.
echo [1/3] Running ROM de-duplication and error cleanup on Drive F:...
"C:\Users\Gourav\.platformio\penv\Scripts\python.exe" "%~dp0tools\curate_and_dedup_roms.py" "F:\roms"

echo.
echo [2/3] Syncing latest configs and tools to Drive F:...
xcopy "%~dp0copy to SD card\retro-go" "F:\retro-go" /E /I /Y /Q >nul 2>&1
xcopy "%~dp0copy to SD card\BruceJS" "F:\BruceJS" /E /I /Y /Q >nul 2>&1
copy /Y "%~dp0copy to SD card\bruce.conf" "F:\bruce.conf" >nul 2>&1

echo.
echo [3/3] Done! All ROMs verified, English-only duplicates cleaned, and configs synced!
echo You can now safely eject Drive F: and plug it into your handheld.
pause
