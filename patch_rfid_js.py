import os

path = "bruce/src/modules/bjs_interpreter/rfid_js.cpp"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target = """JSValue native_rfidReadUID(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv) {
    // usage: rfidReadUID(timeout_in_seconds : number = 5);
    // returns: string (UID) or empty string on timeout

    int timeout = 5;
    if (argc > 0 && JS_IsNumber(ctx, argv[0])) { JS_ToInt32(ctx, &timeout, argv[0]); }

    TagOMatic tagReader(true);
    String uid = tagReader.read_uid_headless(timeout);

    return JS_NewString(ctx, uid.c_str());
}"""

replacement = """JSValue native_rfidReadUID(JSContext *ctx, JSValue *this_val, int argc, JSValue *argv) {
    // usage: rfidReadUID(timeout_in_seconds : number = 5);
    // returns: string (UID) or empty string on timeout
    // if timeout <= 0: returns hardware diagnostic string e.g. 'OK:0x82:FM17522'

    int timeout = 5;
    if (argc > 0 && JS_IsNumber(ctx, argv[0])) { JS_ToInt32(ctx, &timeout, argv[0]); }

    if (timeout <= 0) {
        TagOMatic tagReader(true);
        RFIDInterface *rfid = tagReader.getRFIDInterface();
        byte ver = 0xFF;
        if (rfid) { ver = rfid->raw_version; }
        char diag[32];
        if (ver == 0x82) {
            snprintf(diag, sizeof(diag), "OK:0x%02X:FM17522", ver);
        } else if (ver == 0x92) {
            snprintf(diag, sizeof(diag), "OK:0x%02X:RC522v2", ver);
        } else if (ver == 0x91) {
            snprintf(diag, sizeof(diag), "OK:0x%02X:RC522v1", ver);
        } else if (ver == 0x00 || ver == 0xFF) {
            snprintf(diag, sizeof(diag), "ERR:0x%02X:DISCONNECTED", ver);
        } else {
            snprintf(diag, sizeof(diag), "OK:0x%02X:CHIP", ver);
        }
        return JS_NewString(ctx, diag);
    }

    TagOMatic tagReader(true);
    String uid = tagReader.read_uid_headless(timeout);

    return JS_NewString(ctx, uid.c_str());
}"""

if target in c:
    c = c.replace(target, replacement)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(c)
    print("SUCCESS: rfid_js.cpp updated!")
else:
    print("ERROR: Target not found in rfid_js.cpp")
