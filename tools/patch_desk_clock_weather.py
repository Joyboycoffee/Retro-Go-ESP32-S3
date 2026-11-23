with open('bruce/src/core/desk_clock.cpp', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Replace weather section
idx1 = text.find('static const char *kWxPath')
idx2 = text.find('// =============================================================================\n//  DRAWING PRIMITIVES')

new_wx = '''static const char *kWxPath = "api.open-meteo.com/v1/forecast?latitude=31.1048&longitude=77.1734&elevation=1850&current_weather=true";

static bool parseTemp(const String &body, float &out) {
    int c = body.indexOf("\\\"current_weather\\\":");
    if (c < 0) c = body.indexOf("\\\"current\\\":");
    if (c < 0) return false;
    int t = body.indexOf("\\\"temperature\\\":", c);
    if (t < 0) t = body.indexOf("\\\"temperature_2m\\\":", c);
    if (t < 0) return false;
    int valStart = body.indexOf(':', t) + 1;
    while (valStart < (int)body.length() && body[valStart] == ' ') valStart++;
    int valEnd = valStart;
    while (valEnd < (int)body.length() && (isdigit(body[valEnd]) || body[valEnd] == '.' || body[valEnd] == '-')) {
        valEnd++;
    }
    if (valEnd <= valStart) return false;
    out = body.substring(valStart, valEnd).toFloat();
    return true;
}

static bool isNetConnected() {
    return wifiConnected || WiFi.isConnected() || (WiFi.status() == WL_CONNECTED) || (WiFi.localIP()[0] != 0);
}

static bool fetchWeatherOnce() {
    String body;
    float v = 0.0f;
    bool gotTemp = false;

    // 1. Try Open-Meteo via plain HTTP (elevation=1850m for Shimla city)
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

    // 2. Fallback to Open-Meteo via HTTPS if plain HTTP was blocked
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

    // 3. Fallback to wttr.in (airport station at 1546m elevation -> apply -3°C elevation correction for Shimla city at 1850m)
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
                    float airportTemp = wbody.substring(idx).toFloat();
                    v = airportTemp - 3.0f;
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
        // Check every 30 minutes (1800000 ms), or retry every 30 seconds if fetch failed
        bool due = first || (now - last >= 1800000UL) || (!g_wxValid && now - last >= 30000UL);
        if (due && isNetConnected()) {
            first = false;
            last = now;
            // Synchronize clock time via NTP whenever network is connected
            if (bruceConfig.automaticTimeUpdateViaNTP) {
                updateClockTimezone();
            }
            fetchWeatherOnce();
        }
        for (int i = 0; i < 20 && g_wxRun; i++) vTaskDelay(pdMS_TO_TICKS(100));
    }
    g_wxTask = nullptr;
    vTaskDelete(nullptr);
}

'''

text = text[:idx1] + new_wx + text[idx2:]

# 2. Add "Sync time & weather now" to displayMenu
old_disp_target = '{String("Shimla weather: ") + (cfg.showWx ? "ON" : "OFF"), [&]() { cfg.showWx = !cfg.showWx; saveCfg(p); }},'
new_disp_target = '''{String("Shimla weather: ") + (cfg.showWx ? "ON" : "OFF"), [&]() { cfg.showWx = !cfg.showWx; saveCfg(p); }},
            {"Sync time & weather now", [&]() {
                if (isNetConnected()) {
                    if (bruceConfig.automaticTimeUpdateViaNTP) updateClockTimezone();
                    fetchWeatherOnce();
                }
            }},'''

assert old_disp_target in text, 'old_disp_target not found'
text = text.replace(old_disp_target, new_disp_target, 1)

# Update the exit check in displayMenu for the extra menu item (from sel == 7 to sel == 8)
old_sel_check = 'if (sel == -1 || sel == 7) break;'
new_sel_check = 'if (sel == -1 || sel == 8) break;'
assert old_sel_check in text, 'old_sel_check not found'
text = text.replace(old_sel_check, new_sel_check, 1)

with open('bruce/src/core/desk_clock.cpp', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print('desk_clock.cpp successfully updated!')
