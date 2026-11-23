import os

p = r"C:\Users\Gourav\.platformio\packages\framework-arduinoespressif32\cores\esp32\Arduino.h"
with open(p, "rb") as f:
    c = f.read().decode("utf-8")
c = c.replace('#include "esp32/spiram.h"', '#if __has_include("esp32/spiram.h")\n#include "esp32/spiram.h"\n#endif')
with open(p, "wb") as f:
    f.write(c.encode("utf-8"))

p2 = r"C:\Users\Gourav\.platformio\packages\framework-arduinoespressif32\cores\esp32\esp32-hal-touch.h"
with open(p2, "rb") as f:
    c2 = f.read().decode("utf-8")
if "SOC_TOUCH_VERSION_2" not in c2:
    c2 = "#define SOC_TOUCH_VERSION_2 1\n" + c2
    with open(p2, "wb") as f:
        f.write(c2.encode("utf-8"))

print("Framework headers patched successfully!")
