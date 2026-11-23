import os

# 1. Patch bruce/boards/retro-handheld-s3/interface.cpp
interface_path = r"bruce/boards/retro-handheld-s3/interface.cpp"
with open(interface_path, "r", encoding="utf-8") as f:
    text = f.read().replace("\r\n", "\n")

new_setup_post = """/***************************************************************************************
** Function: _setup_gpio()
***************************************************************************************/
void _setup_gpio() {
    // 0. FIRST AND FOREMOST: Guarantee Retro-Go launcher (ota_0) is armed as default boot.
    // If ANY crash, panic, or power loss occurs in Bruce, the ESP32-S3 will reboot
    // cleanly into the Retro-Go launcher instead of bootlooping!
    const esp_partition_t *launcher_part = esp_partition_find_first(
        ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_APP_OTA_0, "launcher");
    if (launcher_part) {
        esp_ota_set_boot_partition(launcher_part);
    }

    // 1. Expansion Socket GPIOs:
    // GPIO 35: Expansion SPI CS (SDA for RC522, CSN for NRF24) -> OUTPUT HIGH (deselected)
    // GPIO 44: Expansion CE / RST -> INPUT_PULLUP (DO NOT drive LOW: RC522 RST is shorted to 3.3V!)
    // GPIO 10: MicroSD CS -> OUTPUT HIGH (deselected)
    // GPIO 43: Expansion spare / UART TX -> INPUT
    gpio_reset_pin(GPIO_NUM_35);
    pinMode(35, OUTPUT);
    digitalWrite(35, HIGH); // Expansion CS deselected (HIGH)

    gpio_reset_pin(GPIO_NUM_44);
    pinMode(44, INPUT_PULLUP); // Safe high-Z input: NEVER short to 3.3V!

    gpio_reset_pin(GPIO_NUM_10);
    pinMode(10, OUTPUT);
    digitalWrite(10, HIGH); // MicroSD CS deselected (HIGH)

    gpio_reset_pin(GPIO_NUM_43);
    pinMode(43, INPUT);

    // Enforce expansion bus pins in memory for NRF24
    bruceConfigPins.NRF24_bus.sck  = (gpio_num_t)12;
    bruceConfigPins.NRF24_bus.miso = (gpio_num_t)13;
    bruceConfigPins.NRF24_bus.mosi = (gpio_num_t)11;
    bruceConfigPins.NRF24_bus.cs   = (gpio_num_t)35; // Expansion CSN
    bruceConfigPins.NRF24_bus.io0  = (gpio_num_t)44; // Expansion CE
    bruceConfigPins.NRF24_bus.io2  = GPIO_NUM_NC;

    // Clear UART/GPS buses so no peripheral touches expansion pins
    bruceConfigPins.uart_bus.rx = GPIO_NUM_NC;
    bruceConfigPins.uart_bus.tx = GPIO_NUM_NC;
    bruceConfigPins.gps_bus.rx = GPIO_NUM_NC;
    bruceConfigPins.gps_bus.tx = GPIO_NUM_NC;

    if (bruceConfigPins.rfidModule == M5_RFID2_MODULE) {
        bruceConfigPins.rfidModule = RC522_SPI_MODULE;
    }
    for (size_t i = 0; i < sizeof(BUTTON_PINS) / sizeof(BUTTON_PINS[0]); i++) {
        pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    }

    pinMode(BATTERY_PIN, INPUT);

    // Initialize display reset and backlight IMMEDIATELY so boot screen is visible
    pinMode(TFT_RST, OUTPUT);
    digitalWrite(TFT_RST, HIGH);

    pinMode(TFT_BL, OUTPUT);
    analogWrite(TFT_BL, 255); // Full brightness on startup
}

/***************************************************************************************
** Function: _post_setup_gpio()
***************************************************************************************/
void _post_setup_gpio() {
    _setBrightness(bruceConfig.bright);

    // Ensure expansion CS and SD CS remain driven HIGH
    digitalWrite(35, HIGH);
    digitalWrite(10, HIGH);

    // Ensure launcher partition is confirmed
    const esp_partition_t *launcher_part = esp_partition_find_first(
        ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_APP_OTA_0, "launcher");
    if (launcher_part) {
        esp_ota_set_boot_partition(launcher_part);
    }
}"""

# Find _setup_gpio to _post_setup_gpio end
import re
pattern = re.compile(r"/\*+\s*\*\* Function: _setup_gpio\(\).*?void _post_setup_gpio\(\) \{.*?\n\}", re.DOTALL)
if pattern.search(text):
    text = pattern.sub(new_setup_post, text)
    with open(interface_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)
    print("interface.cpp patched successfully!")
else:
    print("interface.cpp: pattern not found!")

# 2. Patch bruce/src/main.cpp: remove ensureMifareKeysLoaded from begin_storage
main_path = r"bruce/src/main.cpp"
with open(main_path, "r", encoding="utf-8") as f:
    text = f.read().replace("\r\n", "\n")

old_storage = """    bool checkFS = setupSdCard();
    bruceConfig.fromFile(checkFS);
    bruceConfigPins.fromFile(checkFS);
    bruceConfig.ensureMifareKeysLoaded();
}"""

new_storage = """    bool checkFS = setupSdCard();
    bruceConfig.fromFile(checkFS);
    bruceConfigPins.fromFile(checkFS);
}"""

if old_storage in text:
    text = text.replace(old_storage, new_storage)
    with open(main_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)
    print("main.cpp patched successfully!")
else:
    print("main.cpp: already clean")

# 3. Patch bruce/src/modules/rfid/RFID2.cpp: do NOT pull NRF24_CE_PIN LOW
rfid2_path = r"bruce/src/modules/rfid/RFID2.cpp"
with open(rfid2_path, "r", encoding="utf-8") as f:
    text = f.read().replace("\r\n", "\n")

# In constructor and begin(): don't drive NRF24_CE_PIN LOW
text = text.replace("digitalWrite(NRF24_CE_PIN, LOW);", "// pin 44 may be shorted to 3.3V on RC522; do not drive LOW")
text = text.replace("pinMode(NRF24_CE_PIN, OUTPUT);", "pinMode(NRF24_CE_PIN, INPUT_PULLUP);")

with open(rfid2_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(text)
print("RFID2.cpp patched successfully!")

# 4. Patch bruce/src/core/mifare_keys_manager.cpp: do not copy files between FS during boot
mifare_path = r"bruce/src/core/mifare_keys_manager.cpp"
with open(mifare_path, "r", encoding="utf-8") as f:
    text = f.read().replace("\r\n", "\n")

old_copy_block = """    // Sync to other filesystem - PRESERVING ORIGINAL ORDER
    if (fromSD) {
        // SD → LittleFS (copy byte-a-byte)
        copyFileToFS(&SD, &LittleFS, "LittleFS");
    } else if (setupSdCard()) {
        // LittleFS → SD (copy byte-a-byte)
        copyFileToFS(&LittleFS, &SD, "SD");
    }"""

new_copy_block = """    // File copy disabled to prevent shared SPI bus lockup at runtime"""

if old_copy_block in text:
    text = text.replace(old_copy_block, new_copy_block)
    with open(mifare_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)
    print("mifare_keys_manager.cpp patched successfully!")
else:
    print("mifare_keys_manager.cpp: copy block not found or already removed")
