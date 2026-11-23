// =============================================================================
//  BRUCE HI-FI MUSIC PLAYER (BruceJS)
//  Native 320x240 Retro Handheld Audio Player
//  Compatible with: MP3, WAV, FLAC, AAC, MOD
//  Controls:
//    [A] (Pin 47)      : Play / Stop Track
//    [B] (Pin 21)      : Exit to Bruce Menu
//    [UP] (Pin 41)     : Volume Up (+10%) / Playlist Up
//    [DOWN] (Pin 42)   : Volume Down (-10%) / Playlist Down
//    [LEFT] (Pin 2)    : Previous Track
//    [RIGHT] (Pin 1)   : Next Track
//    [SELECT] (Pin 40) : Toggle Playlist / Player View
// =============================================================================

var display = typeof require !== "undefined" ? require("display") : display;
var gpio = typeof require !== "undefined" ? require("gpio") : gpio;
var storage = typeof require !== "undefined" ? require("storage") : storage;
var serial = typeof require !== "undefined" ? require("serial") : serial;

// Screen dimensions
var W = 320;
var H = 240;
try {
    if (display.width) W = display.width();
    if (display.height) H = display.height();
} catch (e) {}

// Color Palette (Cyberpunk / Hi-Fi Theme)
var COLOR_BG       = display.color(15, 18, 25);
var COLOR_PANEL    = display.color(25, 30, 42);
var COLOR_ACCENT   = display.color(0, 220, 255);    // Neon Cyan
var COLOR_ACCENT2  = display.color(255, 60, 120);   // Neon Pink
var COLOR_GOLD     = display.color(255, 200, 40);   // Gold Amber
var COLOR_GREEN    = display.color(50, 255, 120);   // Neon Green
var COLOR_WHITE    = display.color(240, 245, 255);
var COLOR_GRAY     = display.color(110, 120, 140);
var COLOR_DARKGRAY = display.color(45, 52, 68);

// Button Pin Map
var PIN_UP     = 41;
var PIN_DOWN   = 42;
var PIN_LEFT   = 2;
var PIN_RIGHT  = 1;
var PIN_A      = 47;
var PIN_B      = 21;
var PIN_SELECT = 40;
var PIN_START  = 38;

function initButtons() {
    var pins = [PIN_UP, PIN_DOWN, PIN_LEFT, PIN_RIGHT, PIN_A, PIN_B, PIN_SELECT, PIN_START];
    for (var i = 0; i < pins.length; i++) {
        try {
            gpio.pinMode(pins[i], "input", "up");
        } catch (e) {}
    }
}

function isPressed(pin) {
    try {
        return gpio.digitalRead(pin) === 0;
    } catch (e) {
        return false;
    }
}

// Volume & Playback State
var currentVolume = 80;
var isPlaying = false;
var playlist = [];
var currentTrackIdx = 0;
var viewMode = "player"; // "player" or "playlist"
var playlistScroll = 0;
var eqPhase = 0;

// Scan SD Card for Audio Files
function scanMusicLibrary() {
    var found = [];
    var searchPaths = ["/music", "/Music", "/sd/music", "/sd/Music"];
    
    for (var p = 0; p < searchPaths.length; p++) {
        var folder = searchPaths[p];
        try {
            var entries = storage.readdir(folder, { withFileTypes: true });
            if (entries && entries.length) {
                for (var i = 0; i < entries.length; i++) {
                    var item = entries[i];
                    var name = (typeof item === "object") ? item.name : item;
                    if (!name) continue;
                    var lower = name.toLowerCase();
                    if (lower.endsWith(".mp3") || lower.endsWith(".flac") || 
                        lower.endsWith(".wav") || lower.endsWith(".aac") || lower.endsWith(".mod")) {
                        var size = (typeof item === "object" && item.size) ? item.size : 0;
                        found.push({
                            filename: name,
                            path: folder + "/" + name,
                            size: size,
                            title: formatTrackTitle(name)
                        });
                    }
                }
            }
        } catch (errScan) {}
    }

    // Default Lil Peep track if readdir is empty
    if (found.length === 0) {
        found.push({
            filename: "Lil_Peep_Right_Here.mp3",
            path: "/music/Lil_Peep_Right_Here.mp3",
            size: 5665209,
            title: "Lil Peep - right here"
        });
    }

    return found;
}

function formatTrackTitle(filename) {
    var name = filename;
    var lastDot = name.lastIndexOf(".");
    if (lastDot > 0) name = name.substring(0, lastDot);
    name = name.replace(/_/g, " ");
    name = name.replace(/-/g, " - ");
    name = name.replace(/\s+/g, " ");
    return name.trim();
}

function formatSize(bytes) {
    if (!bytes) return "";
    var mb = (bytes / (1024 * 1024)).toFixed(1);
    return mb + " MB";
}

// Draw Top Header
function drawHeader() {
    display.drawFillRect(0, 0, W, 26, COLOR_PANEL);
    display.drawLine(0, 26, W, 26, COLOR_ACCENT);

    display.setTextSize(1);
    display.setTextColor(COLOR_ACCENT, COLOR_PANEL);
    display.setTextAlign("left", "middle");
    display.drawText(" BRUCE HI-FI AUDIO", 8, 13);

    // Track Counter
    display.setTextAlign("right", "middle");
    display.setTextColor(COLOR_GOLD, COLOR_PANEL);
    var countStr = (playlist.length > 0) ? (currentTrackIdx + 1) + "/" + playlist.length : "0/0";
    display.drawText(countStr + " ", W - 8, 13);
}

// Draw Animated Equalizer Spectrum
function drawEqualizer(x, y, w, h, active) {
    var barCount = 14;
    var barW = Math.floor(w / barCount) - 2;
    eqPhase += 0.3;

    for (var i = 0; i < barCount; i++) {
        var bx = x + i * (barW + 2);
        var barH = 4;
        if (active) {
            var s1 = Math.sin(eqPhase + i * 0.7);
            var s2 = Math.cos(eqPhase * 0.8 + i * 0.4);
            var norm = Math.abs(s1 * 0.6 + s2 * 0.4);
            barH = Math.floor(4 + norm * (h - 8));
        }

        var by = y + h - barH;
        var barColor = (i < 4) ? COLOR_GREEN : ((i < 10) ? COLOR_ACCENT : COLOR_ACCENT2);
        
        display.drawFillRect(bx, y, barW, h, COLOR_PANEL);
        display.drawFillRect(bx, by, barW, barH, barColor);
    }
}

// Draw Main Player View
function drawPlayerView() {
    var cur = playlist[currentTrackIdx];
    var title = cur ? cur.title : "No Track Selected";
    var filename = cur ? cur.filename : "";
    var ext = filename.substring(filename.lastIndexOf(".") + 1).toUpperCase();

    // Background Canvas
    display.drawFillRect(0, 27, W, H - 27, COLOR_BG);

    // Track Info Card
    display.drawFillRoundRect(12, 36, W - 24, 76, 6, COLOR_PANEL);
    display.drawRoundRect(12, 36, W - 24, 76, 6, COLOR_DARKGRAY);

    // Format Badge
    var badgeW = (ext.length * 8) + 12;
    display.drawFillRoundRect(22, 44, badgeW, 16, 4, COLOR_ACCENT2);
    display.setTextSize(1);
    display.setTextColor(COLOR_WHITE, COLOR_ACCENT2);
    display.setTextAlign("center", "middle");
    display.drawText(ext, 22 + (badgeW / 2), 52);

    // Size / Bitrate Info
    display.setTextColor(COLOR_GRAY, COLOR_PANEL);
    display.setTextAlign("left", "middle");
    display.drawText(formatSize(cur ? cur.size : 0) + " | Stereo 44.1kHz", 26 + badgeW, 52);

    // Track Title
    display.setTextSize(2);
    display.setTextColor(COLOR_WHITE, COLOR_PANEL);
    display.setTextAlign("left", "middle");
    var dispTitle = title;
    if (dispTitle.length > 20) dispTitle = dispTitle.substring(0, 18) + "...";
    display.drawText(dispTitle, 22, 80);

    // Equalizer & Visualizer Box
    var eqX = 12;
    var eqY = 118;
    var eqW = W - 24;
    var eqH = 46;
    display.drawFillRoundRect(eqX, eqY, eqW, eqH, 6, COLOR_PANEL);
    display.drawRoundRect(eqX, eqY, eqW, eqH, 6, isPlaying ? COLOR_ACCENT : COLOR_DARKGRAY);
    drawEqualizer(eqX + 8, eqY + 4, eqW - 16, eqH - 8, isPlaying);

    // Status Indicator & Volume Bar
    var statY = 172;
    display.setTextSize(1);
    display.setTextAlign("left", "middle");
    if (isPlaying) {
        display.setTextColor(COLOR_GREEN, COLOR_BG);
        display.drawText("▶ PLAYING", 16, statY);
    } else {
        display.setTextColor(COLOR_GOLD, COLOR_BG);
        display.drawText("⏸ READY", 16, statY);
    }

    // Volume Bar
    display.setTextAlign("right", "middle");
    display.setTextColor(COLOR_WHITE, COLOR_BG);
    display.drawText("VOL " + currentVolume + "%", W - 16, statY);

    var volBarX = 100;
    var volBarY = statY - 4;
    var volBarW = W - 100 - 80;
    var volFill = Math.floor((currentVolume / 100) * volBarW);
    display.drawFillRect(volBarX, volBarY, volBarW, 8, COLOR_PANEL);
    display.drawFillRect(volBarX, volBarY, volFill, 8, COLOR_ACCENT);
    display.drawRect(volBarX, volBarY, volBarW, 8, COLOR_DARKGRAY);

    // Bottom Controls Banner
    var ctrlY = H - 22;
    display.drawFillRect(0, ctrlY - 4, W, 26, COLOR_PANEL);
    display.drawLine(0, ctrlY - 4, W, ctrlY - 4, COLOR_DARKGRAY);
    display.setTextSize(1);
    display.setTextColor(COLOR_GRAY, COLOR_PANEL);
    display.setTextAlign("center", "middle");
    display.drawText("[A] Play  [B] Exit  [UP/DN] Vol  [L/R] Track", W / 2, ctrlY + 8);
}

// Draw Playlist View
function drawPlaylistView() {
    display.drawFillRect(0, 27, W, H - 27, COLOR_BG);

    display.setTextSize(1);
    display.setTextColor(COLOR_GOLD, COLOR_BG);
    display.setTextAlign("left", "middle");
    display.drawText(" SELECT TRACK TO PLAY:", 12, 40);

    var itemH = 26;
    var startY = 56;
    var maxVisible = 5;

    for (var i = 0; i < maxVisible; i++) {
        var idx = playlistScroll + i;
        if (idx >= playlist.length) break;

        var y = startY + i * itemH;
        var isSelected = (idx === currentTrackIdx);

        if (isSelected) {
            display.drawFillRoundRect(10, y, W - 20, itemH - 4, 4, COLOR_PANEL);
            display.drawRoundRect(10, y, W - 20, itemH - 4, 4, COLOR_ACCENT);
            display.setTextColor(COLOR_ACCENT, COLOR_PANEL);
        } else {
            display.drawFillRoundRect(10, y, W - 20, itemH - 4, 4, COLOR_PANEL);
            display.setTextColor(COLOR_WHITE, COLOR_PANEL);
        }

        display.setTextSize(1);
        display.setTextAlign("left", "middle");
        var num = (idx + 1) + ". ";
        display.drawText(num + playlist[idx].title, 18, y + (itemH / 2) - 2);

        display.setTextAlign("right", "middle");
        display.setTextColor(COLOR_GRAY, COLOR_PANEL);
        display.drawText(formatSize(playlist[idx].size), W - 18, y + (itemH / 2) - 2);
    }

    var ctrlY = H - 22;
    display.drawFillRect(0, ctrlY - 4, W, 26, COLOR_PANEL);
    display.setTextSize(1);
    display.setTextColor(COLOR_GRAY, COLOR_PANEL);
    display.setTextAlign("center", "middle");
    display.drawText("[A] Select & Play   [B] Back to Player", W / 2, ctrlY + 8);
}

// Play current track via native Bruce audio engine
function playTrack(idx) {
    if (idx < 0 || idx >= playlist.length) return;
    currentTrackIdx = idx;
    var track = playlist[currentTrackIdx];
    isPlaying = true;
    drawPlayerView();

    try {
        serial.cmd("music_player " + track.path);
    } catch (errPlay) {}

    // When blocking audio completes or user presses a key to stop:
    isPlaying = false;
    drawHeader();
    drawPlayerView();
}

// Stop current playback
function stopPlayback() {
    isPlaying = false;
    try {
        serial.cmd("tone 0 1");
    } catch (e) {}
}

// =============================================================================
//  MAIN APP ENTRY POINT
// =============================================================================
function main() {
    initButtons();
    display.fill(COLOR_BG);
    drawHeader();

    // Loading screen
    display.setTextSize(1);
    display.setTextColor(COLOR_ACCENT, COLOR_BG);
    display.setTextAlign("center", "middle");
    display.drawText("Loading Music Library...", W / 2, H / 2);

    playlist = scanMusicLibrary();
    drawHeader();
    drawPlayerView();

    var running = true;

    while (running) {
        // 1. [B] EXIT BUTTON
        if (isPressed(PIN_B)) {
            if (viewMode === "playlist") {
                viewMode = "player";
                drawHeader();
                drawPlayerView();
                delay(250);
            } else {
                stopPlayback();
                display.fill(display.color(0, 0, 0));
                running = false;
                break;
            }
        }

        // 2. [A] PLAY BUTTON
        if (isPressed(PIN_A)) {
            if (viewMode === "playlist") {
                viewMode = "player";
                playTrack(currentTrackIdx);
            } else {
                playTrack(currentTrackIdx);
            }
            delay(300);
        }

        // 3. [SELECT] TOGGLE PLAYLIST VIEW
        if (isPressed(PIN_SELECT)) {
            viewMode = (viewMode === "player") ? "playlist" : "player";
            drawHeader();
            if (viewMode === "playlist") drawPlaylistView();
            else drawPlayerView();
            delay(300);
        }

        // 4. [UP] VOLUME UP / PLAYLIST UP
        if (isPressed(PIN_UP)) {
            if (viewMode === "playlist") {
                if (currentTrackIdx > 0) currentTrackIdx--;
                if (currentTrackIdx < playlistScroll) playlistScroll = currentTrackIdx;
                drawPlaylistView();
            } else {
                currentVolume = Math.min(100, currentVolume + 5);
                drawPlayerView();
            }
            delay(150);
        }

        // 5. [DOWN] VOLUME DOWN / PLAYLIST DOWN
        if (isPressed(PIN_DOWN)) {
            if (viewMode === "playlist") {
                if (currentTrackIdx < playlist.length - 1) currentTrackIdx++;
                if (currentTrackIdx >= playlistScroll + 5) playlistScroll = currentTrackIdx - 4;
                drawPlaylistView();
            } else {
                currentVolume = Math.max(0, currentVolume - 5);
                drawPlayerView();
            }
            delay(150);
        }

        // 6. [LEFT] PREVIOUS TRACK
        if (isPressed(PIN_LEFT)) {
            if (playlist.length > 0) {
                currentTrackIdx = (currentTrackIdx - 1 + playlist.length) % playlist.length;
                drawPlayerView();
            }
            delay(250);
        }

        // 7. [RIGHT] NEXT TRACK
        if (isPressed(PIN_RIGHT)) {
            if (playlist.length > 0) {
                currentTrackIdx = (currentTrackIdx + 1) % playlist.length;
                drawPlayerView();
            }
            delay(250);
        }

        delay(30);
    }
}

main();
