import sys

p = 'bruce/src/modules/bjs_interpreter/wifi_js.cpp'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('\r\n', '\n')

c = c.replace('#include <WiFi.h>', '#include <WiFi.h>\n#include <WiFiClientSecure.h>')

old_conn = """JSValue native_wifiConnected(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv) {
    return JS_NewBool(wifiConnected);
}"""

new_conn = """JSValue native_wifiConnected(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv) {
    bool ok = wifiConnected || WiFi.isConnected() || (WiFi.status() == WL_CONNECTED) || (WiFi.localIP()[0] != 0);
    if (ok) wifiConnected = true;
    return JS_NewBool(ok);
}"""

if old_conn not in c:
    print("ERROR: old_conn not found")
    sys.exit(1)
c = c.replace(old_conn, new_conn)

old_fetch = """    const char *url = JS_ToCString(ctx, argv[0], &stringBuffer);
    http.begin(url);"""

new_fetch = """    const char *url = JS_ToCString(ctx, argv[0], &stringBuffer);
    WiFiClientSecure secureClient;
    WiFiClient plainClient;
    bool isHttps = (url && strncmp(url, "https://", 8) == 0);
    if (isHttps) {
        secureClient.setInsecure();
        http.begin(secureClient, url);
    } else {
        http.begin(plainClient, url ? url : "");
    }
    http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
    http.setTimeout(15000);"""

if old_fetch not in c:
    print("ERROR: old_fetch not found")
    sys.exit(1)
c = c.replace(old_fetch, new_fetch)

with open(p, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(c)

print("wifi_js.cpp updated successfully!")
