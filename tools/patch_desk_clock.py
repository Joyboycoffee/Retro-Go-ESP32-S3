import sys

p = 'bruce/src/core/desk_clock.cpp'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Normalize newlines
c = c.replace('\r\n', '\n')

old_wx = """static bool fetchWeatherOnce() {
    String body;
    {
        HTTPClient http;
        http.setTimeout(4000);
        if (http.begin(String("http://") + kWxPath)) {
            if (http.GET() == 200) body = http.getString();
            http.end();
        }
    }
    if (body.length() == 0) { // some networks force https
        WiFiClientSecure client;
        client.setInsecure();
        HTTPClient http;
        http.setTimeout(5000);
        if (http.begin(client, String("https://") + kWxPath)) {
            if (http.GET() == 200) body = http.getString();
            http.end();
        }
    }
    float v;
    if (body.length() && parseTemp(body, v)) {
        g_wxTemp = (int)lroundf(v);
        g_wxValid = true;
        g_wxStamp = millis() | 1;
        return true;
    }
    return false;
}

static void weatherTask(void *) {
    uint32_t last = 0;
    bool first = true;
    while (g_wxRun) {
        uint32_t now = millis();
        bool due = first || (now - last > 900000UL) || (!g_wxValid && now - last > 60000UL);
        if (due && WiFi.isConnected()) {
            first = false;
            last = now;
            fetchWeatherOnce();
        }
        for (int i = 0; i < 20 && g_wxRun; i++) vTaskDelay(pdMS_TO_TICKS(100));
    }
    g_wxTask = nullptr;
    vTaskDelete(nullptr);
}"""

new_wx = """static bool isNetConnected() {
    return wifiConnected || WiFi.isConnected() || (WiFi.status() == WL_CONNECTED) || (WiFi.localIP()[0] != 0);
}

static bool fetchWeatherOnce() {
    String body;
    float v = 0.0f;
    bool gotTemp = false;

    // 1. Try Open-Meteo via plain HTTP with explicit client
    {
        HTTPClient http;
        http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
        http.setTimeout(4000);
        WiFiClient client;
        if (http.begin(client, String("http://") + kWxPath)) {
            if (http.GET() == 200) {
                body = http.getString();
                if (body.length() && parseTemp(body, v)) {
                    gotTemp = true;
                }
            }
            http.end();
        }
    }

    // 2. Fallback to wttr.in (plain HTTP, returns '+14°C', super reliable)
    if (!gotTemp) {
        HTTPClient http;
        http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
        http.setTimeout(4000);
        WiFiClient client;
        if (http.begin(client, "http://wttr.in/Shimla?format=%t")) {
            if (http.GET() == 200) {
                String wbody = http.getString();
                wbody.trim();
                int idx = 0;
                while (idx < (int)wbody.length() && (wbody[idx] == '+' || wbody[idx] == ' ')) idx++;
                if (idx < (int)wbody.length()) {
                    v = wbody.substring(idx).toFloat();
                    gotTemp = true;
                }
            }
            http.end();
        }
    }

    // 3. Fallback to Open-Meteo via HTTPS if plain HTTP was blocked
    if (!gotTemp) {
        WiFiClientSecure client;
        client.setInsecure();
        HTTPClient http;
        http.setTimeout(5000);
        if (http.begin(client, String("https://") + kWxPath)) {
            if (http.GET() == 200) {
                body = http.getString();
                if (body.length() && parseTemp(body, v)) {
                    gotTemp = true;
                }
            }
            http.end();
        }
    }

    if (gotTemp) {
        g_wxTemp = (int)lroundf(v);
        g_wxValid = true;
        g_wxStamp = millis() | 1;
        return true;
    }
    return false;
}

static void weatherTask(void *) {
    uint32_t last = 0;
    bool first = true;
    while (g_wxRun) {
        uint32_t now = millis();
        bool due = first || (now - last > 900000UL) || (!g_wxValid && now - last > 15000UL);
        if (due && isNetConnected()) {
            first = false;
            last = now;
            fetchWeatherOnce();
        }
        for (int i = 0; i < 20 && g_wxRun; i++) vTaskDelay(pdMS_TO_TICKS(100));
    }
    g_wxTask = nullptr;
    vTaskDelete(nullptr);
}"""

if old_wx not in c:
    print("ERROR: old_wx not found")
    sys.exit(1)
c = c.replace(old_wx, new_wx)

old_sw = """static void runStopwatch() {
    uint32_t elapsed = 0, start = 0;"""
new_sw = """static void runStopwatch() {
    tft.setRotation(1);
    tft.resetViewport();
    tft.fillScreen(0x0000);
    canvas().fillScreen(0x0000);
    uint32_t elapsed = 0, start = 0;"""
if old_sw not in c:
    print("ERROR: old_sw not found")
    sys.exit(1)
c = c.replace(old_sw, new_sw)

old_tm = """            o.push_back({label, [&, i]() { cfg.theme = i; saveCfg(p); }});"""
new_tm = """            o.push_back({label, [&, i]() {
                cfg.theme = i;
                saveCfg(p);
                tft.fillScreen(0x0000);
                canvas().fillScreen(0x0000);
            }});"""
if old_tm not in c:
    print("ERROR: old_tm not found")
    sys.exit(1)
c = c.replace(old_tm, new_tm)

old_runner = """    bool haveFb = fbCreate();
    tft.fillScreen(0x0000);

    int lastSec = -1;"""
new_runner = """    tft.setRotation(1);
    tft.resetViewport();
    bool haveFb = fbCreate();
    tft.fillScreen(0x0000);
    canvas().fillScreen(0x0000);

    int lastSec = -1;"""
if old_runner not in c:
    print("ERROR: old_runner not found")
    sys.exit(1)
c = c.replace(old_runner, new_runner)

c = c.replace('"wx", 8192,', '"wx", 12288,')

old_prev = """if (check(PrevPress)) { cfg.theme = (cfg.theme + NUM_THEMES - 1) % NUM_THEMES; saveCfg(prefs); redraw = true; }
        else if (check(NextPress)) { cfg.theme = (cfg.theme + 1) % NUM_THEMES; saveCfg(prefs); redraw = true; }"""
new_prev = """if (check(PrevPress)) {
            cfg.theme = (cfg.theme + NUM_THEMES - 1) % NUM_THEMES;
            saveCfg(prefs);
            tft.fillScreen(0x0000);
            canvas().fillScreen(0x0000);
            redraw = true;
        } else if (check(NextPress)) {
            cfg.theme = (cfg.theme + 1) % NUM_THEMES;
            saveCfg(prefs);
            tft.fillScreen(0x0000);
            canvas().fillScreen(0x0000);
            redraw = true;
        }"""
if old_prev not in c:
    print("ERROR: old_prev not found")
    sys.exit(1)
c = c.replace(old_prev, new_prev)

old_ret = """        else if (check(SelPress)) {
            clockMenu(prefs);
            tft.fillScreen(0x0000);
            haveFb = fbCreate();
            redraw = true;
            lastSec = -1;
        }"""
new_ret = """        else if (check(SelPress)) {
            clockMenu(prefs);
            tft.setRotation(1);
            tft.resetViewport();
            tft.fillScreen(0x0000);
            canvas().fillScreen(0x0000);
            haveFb = fbCreate();
            redraw = true;
            lastSec = -1;
        }"""
if old_ret not in c:
    print("ERROR: old_ret not found")
    sys.exit(1)
c = c.replace(old_ret, new_ret)

with open(p, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(c)

print("desk_clock.cpp updated successfully!")
