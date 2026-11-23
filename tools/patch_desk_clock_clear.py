p = 'bruce/src/core/desk_clock.cpp'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add clearCanvas helper right after present()
old_present = '''static void present() {
    if (g_fb) g_fb->pushSprite(0, 0);
}'''

new_present = '''static void present() {
    if (g_fb) g_fb->pushSprite(0, 0);
}
static void clearCanvas(uint16_t color = 0x0000) {
    if (g_fb) {
        g_fb->fillScreen(color);
    } else {
        tft.fillScreen(color);
    }
}'''

c = c.replace(old_present, new_present)

# 2. In face0..face7, replace g.fillScreen with clearCanvas
c = c.replace('static void face0(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    g.fillScreen(K(0x0000));',
              'static void face0(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    clearCanvas(K(0x0000));')

c = c.replace('static void face1(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    const int cx = 160, cy = 108, R = 92;\n    uint16_t bg = K(0x0824);\n    g.fillScreen(bg);',
              'static void face1(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    const int cx = 160, cy = 108, R = 92;\n    uint16_t bg = K(0x0824);\n    clearCanvas(bg);')

c = c.replace('static void face2(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    uint16_t bg = K(0x1186);\n    g.fillScreen(bg);',
              'static void face2(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    uint16_t bg = K(0x1186);\n    clearCanvas(bg);')

c = c.replace('static void face3(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    const int cx = 160, cy = 112;\n    uint16_t bg = K(0x0000);\n    g.fillScreen(bg);',
              'static void face3(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    const int cx = 160, cy = 112;\n    uint16_t bg = K(0x0000);\n    clearCanvas(bg);')

c = c.replace('static void face4(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    const int cx = 108, cy = 120, R = 100;\n    uint16_t bg = K(0x0000);\n    g.fillScreen(bg);',
              'static void face4(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    const int cx = 108, cy = 120, R = 100;\n    uint16_t bg = K(0x0000);\n    clearCanvas(bg);')

c = c.replace('static void face5(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    uint16_t bg = K(0x0841);\n    g.fillScreen(bg);',
              'static void face5(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    uint16_t bg = K(0x0841);\n    clearCanvas(bg);')

c = c.replace('static void face6(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    g.fillScreen(K(0x0000));',
              'static void face6(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    clearCanvas(K(0x0000));')

c = c.replace('static void face7(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    g.fillScreen(K(0x0000));',
              'static void face7(GFX &g, const tm &ti, float secF, int bat) {\n    TP p;\n    fmtTime(ti, p);\n    clearCanvas(K(0x0000));')

# 3. In runStopwatch
c = c.replace('        if (running) elapsed = millis() - start;\n        GFX &g = canvas();\n        g.fillScreen(K(0x0000));',
              '        if (running) elapsed = millis() - start;\n        clearCanvas(K(0x0000));\n        GFX &g = canvas();')

# 4. In pickTime
c = c.replace('        keepAwake();\n        GFX &g = canvas();\n        g.fillScreen(K(0x0000));',
              '        keepAwake();\n        clearCanvas(K(0x0000));\n        GFX &g = canvas();')

# 5. In main loop before kFaces
old_draw = '''            int bat = (int)getBattery();
            if (bat < 0) bat = 0;
            if (bat > 100) bat = 100;
            kFaces[cfg.theme](canvas(), ti, secF, bat);'''

new_draw = '''            int bat = (int)getBattery();
            if (bat < 0) bat = 0;
            if (bat > 100) bat = 100;
            clearCanvas(0x0000);
            kFaces[cfg.theme](canvas(), ti, secF, bat);'''

c = c.replace(old_draw, new_draw)

with open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)

print('desk_clock.cpp patched with clearCanvas')
