p = 'bruce/boards/retro-handheld-s3/interface.cpp'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old_code = '''    // Full charge clamp: when battery is within 110mV of 4.07V (>= 3.96V), clamp to 100%
    if (batteryVolts >= 3.96f || currentPercent >= 96.0f) {
        currentPercent = 100.0f;
    }

    // 3. Exponential Moving Average Filter
    if (smoothedPercent < 0.0f) {
        smoothedPercent = currentPercent;
        cachedDisplayedPercent = (int)(currentPercent + 0.5f);
    } else {
        smoothedPercent = smoothedPercent * 0.85f + currentPercent * 0.15f;
        int candidate = (int)(smoothedPercent + 0.5f);
        if (candidate >= 97) candidate = 100;

        // 1.5% hysteresis deadband to prevent integer toggling
        if (abs(candidate - cachedDisplayedPercent) >= 1) {
            if (fabsf(smoothedPercent - (float)cachedDisplayedPercent) >= 1.5f) {
                cachedDisplayedPercent = candidate;
            }
        }
    }

    if (cachedDisplayedPercent >= 97) cachedDisplayedPercent = 100;
    if (cachedDisplayedPercent < 0) cachedDisplayedPercent = 0;
    if (cachedDisplayedPercent > 100) cachedDisplayedPercent = 100;'''

new_code = '''    // 3. Exponential Moving Average Filter (matches Retro-Go 3.30V=0%, 4.07V=100%)
    if (smoothedPercent < 0.0f) {
        smoothedPercent = currentPercent;
        cachedDisplayedPercent = (int)(currentPercent + 0.5f);
    } else {
        smoothedPercent = smoothedPercent * 0.85f + currentPercent * 0.15f;
        int candidate = (int)(smoothedPercent + 0.5f);

        // 1.0% hysteresis deadband to prevent integer toggling
        if (abs(candidate - cachedDisplayedPercent) >= 1) {
            if (fabsf(smoothedPercent - (float)cachedDisplayedPercent) >= 1.0f) {
                cachedDisplayedPercent = candidate;
            }
        }
    }

    if (cachedDisplayedPercent < 0) cachedDisplayedPercent = 0;
    if (cachedDisplayedPercent > 100) cachedDisplayedPercent = 100;'''

if old_code in c:
    c = c.replace(old_code, new_code)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(c)
    print('interface.cpp battery clamp removed')
else:
    print('old_code not found in interface.cpp')
