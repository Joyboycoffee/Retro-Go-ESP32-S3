with open('bruce/src/modules/bjs_interpreter/wifi_js.cpp', 'rb') as f:
    data = f.read()

target = b'    http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);\r\n    http.setTimeout(15000);'
replacement = b'''    http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
    uint32_t httpTimeoutMs = 35000;
    if (argc > 1 && JS_IsObject(ctx, argv[1])) {
        JSValue jsvTimeout = JS_GetPropertyStr(ctx, argv[1], "timeout");
        if (JS_IsNumber(ctx, jsvTimeout)) {
            int toVal = 0;
            JS_ToInt32(ctx, &toVal, jsvTimeout);
            if (toVal > 0) httpTimeoutMs = (uint32_t)toVal;
        }
    }
    http.setTimeout(httpTimeoutMs);'''.replace(b'\n', b'\r\n')

if target not in data:
    target = target.replace(b'\r\n', b'\n')
    replacement = replacement.replace(b'\r\n', b'\n')

assert target in data, 'Target not found!'
data = data.replace(target, replacement, 1)

target2 = b'const unsigned long timeoutMillis = 30000;'
replacement2 = b'const unsigned long timeoutMillis = httpTimeoutMs + 5000;'
assert target2 in data, 'Target2 not found!'
data = data.replace(target2, replacement2, 1)

with open('bruce/src/modules/bjs_interpreter/wifi_js.cpp', 'wb') as f:
    f.write(data)
print('Successfully patched wifi_js.cpp!')
