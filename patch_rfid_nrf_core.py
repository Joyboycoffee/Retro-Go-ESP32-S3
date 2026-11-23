import os

# 1. Patch bruce/boards/retro-handheld-s3/interface.cpp
interface_path = r"bruce/boards/retro-handheld-s3/interface.cpp"
with open(interface_path, "r", encoding="utf-8") as f:
    code = f.read()

# Replace _setup_gpio
old_setup = """void _setup_gpio() {
    // 1. Explicitly detach GPIO 43 (CS) and 44 (RST) from UART0 peripheral matrix
    gpio_reset_pin(GPIO_NUM_43);
    pinMode(43, OUTPUT);
    digitalWrite(43, HIGH); // RC522 CS deselected (HIGH)

    gpio_reset_pin(GPIO_NUM_44);
    pinMode(44, OUTPUT);
    digitalWrite(44, HIGH); // RC522 RST awake and active (HIGH)

    gpio_reset_pin(GPIO_NUM_10);
    pinMode(10, OUTPUT);
    digitalWrite(10, HIGH); // MicroSD CS deselected (HIGH)

    // Clear UART/GPS buses so no peripheral touches pins 43 & 44
    bruceConfigPins.uart_bus.rx = GPIO_NUM_NC;
    bruceConfigPins.uart_bus.tx = GPIO_NUM_NC;
    bruceConfigPins.gps_bus.rx = GPIO_NUM_NC;
    bruceConfigPins.gps_bus.tx = GPIO_NUM_NC;

    if (bruceConfigPins.rfidModule == M5_RFID2_MODULE) {
        bruceConfigPins.rfidModule = RC522_SPI_MODULE;
    }"""

new_setup = """void _setup_gpio() {
    // 1. Explicitly initialize expansion socket GPIOs:
    // GPIO 35: Expansion SPI CS (SDA for RC522, CSN for NRF24)
    // GPIO 44: Expansion CE (CE for NRF24, hard-shorted RST on RC522)
    // GPIO 10: MicroSD CS
    gpio_reset_pin(GPIO_NUM_35);
    pinMode(35, OUTPUT);
    digitalWrite(35, HIGH); // Expansion CS deselected (HIGH)

    gpio_reset_pin(GPIO_NUM_44);
    pinMode(44, OUTPUT);
    digitalWrite(44, LOW);  // NRF24 CE idle / standby (LOW)

    gpio_reset_pin(GPIO_NUM_10);
    pinMode(10, OUTPUT);
    digitalWrite(10, HIGH); // MicroSD CS deselected (HIGH)

    // Detach pin 43 from UART peripheral matrix
    gpio_reset_pin(GPIO_NUM_43);
    pinMode(43, INPUT);

    // Enforce NRF24 hardware pins for the Retro Handheld S3
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
    }"""

old_post_setup = """void _post_setup_gpio() {
    _setBrightness(bruceConfig.bright);

    // Ensure expansion CS, RST, and SD CS remain driven HIGH
    digitalWrite(43, HIGH);
    digitalWrite(44, HIGH);
    digitalWrite(10, HIGH);

    // Guarantee Retro-Go launcher (ota_0) is restored as default boot partition for next reboot
    const esp_partition_t *launcher_part = esp_partition_find_first(
        ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_APP_OTA_0, "launcher");
    if (launcher_part) {
        esp_ota_set_boot_partition(launcher_part);
    }
}"""

new_post_setup = """void _post_setup_gpio() {
    _setBrightness(bruceConfig.bright);

    // Ensure expansion CS and SD CS remain driven HIGH
    digitalWrite(35, HIGH);
    digitalWrite(10, HIGH);

    // Enforce and persist NRF24 pinout if changed
    if (bruceConfigPins.NRF24_bus.cs != (gpio_num_t)35 || bruceConfigPins.NRF24_bus.io0 != (gpio_num_t)44) {
        bruceConfigPins.NRF24_bus.sck  = (gpio_num_t)12;
        bruceConfigPins.NRF24_bus.miso = (gpio_num_t)13;
        bruceConfigPins.NRF24_bus.mosi = (gpio_num_t)11;
        bruceConfigPins.NRF24_bus.cs   = (gpio_num_t)35;
        bruceConfigPins.NRF24_bus.io0  = (gpio_num_t)44;
        bruceConfigPins.NRF24_bus.io2  = GPIO_NUM_NC;
        bruceConfigPins.saveFile();
    }

    // Guarantee Retro-Go launcher (ota_0) is restored as default boot partition for next reboot
    const esp_partition_t *launcher_part = esp_partition_find_first(
        ESP_PARTITION_TYPE_APP, ESP_PARTITION_SUBTYPE_APP_OTA_0, "launcher");
    if (launcher_part) {
        esp_ota_set_boot_partition(launcher_part);
    }
}"""

# Normalize CRLF
code = code.replace("\r\n", "\n")
old_setup = old_setup.replace("\r\n", "\n")
new_setup = new_setup.replace("\r\n", "\n")
old_post_setup = old_post_setup.replace("\r\n", "\n")
new_post_setup = new_post_setup.replace("\r\n", "\n")

if old_setup in code and old_post_setup in code:
    code = code.replace(old_setup, new_setup)
    code = code.replace(old_post_setup, new_post_setup)
    with open(interface_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(code)
    print("interface.cpp patched successfully!")
else:
    print("interface.cpp: pattern mismatch!")

# 2. Patch bruce/src/main.cpp (pre-load MIFARE keys at boot)
main_path = r"bruce/src/main.cpp"
with open(main_path, "r", encoding="utf-8") as f:
    code = f.read().replace("\r\n", "\n")

target_storage = """    bool checkFS = setupSdCard();
    bruceConfig.fromFile(checkFS);
    bruceConfigPins.fromFile(checkFS);
}"""

replacement_storage = """    bool checkFS = setupSdCard();
    bruceConfig.fromFile(checkFS);
    bruceConfigPins.fromFile(checkFS);
    bruceConfig.ensureMifareKeysLoaded();
}"""

if target_storage in code:
    code = code.replace(target_storage, replacement_storage)
    with open(main_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(code)
    print("main.cpp patched successfully!")
else:
    print("main.cpp: target_storage not found or already patched")

# 3. Patch bruce/src/core/mifare_keys_manager.cpp
mifare_path = r"bruce/src/core/mifare_keys_manager.cpp"
with open(mifare_path, "r", encoding="utf-8") as f:
    code = f.read().replace("\r\n", "\n")

target_ensure = """void MifareKeysManager::ensureLoaded(std::set<String> &keys) {
    if (!keys.empty()) return; // Already loaded

    // Try loading from file (SD priority)
    if ((setupSdCard() && SD.exists(KEYS_PATH)) || LittleFS.exists(KEYS_PATH)) {
        loadFromFile(keys);
    } else {
        createDefaultFile(keys);
    }
}"""

replacement_ensure = """void MifareKeysManager::ensureLoaded(std::set<String> &keys) {
    if (!keys.empty()) return; // Already loaded

    // Always pre-populate standard default keys immediately
    keys.insert("FFFFFFFFFFFF");
    keys.insert("A0A1A2A3A4A5");
    keys.insert("D3F7D3F7D3F7");

    // Try loading additional custom keys from file if filesystem is ready
    if ((sdcardMounted && SD.exists(KEYS_PATH)) || LittleFS.exists(KEYS_PATH)) {
        loadFromFile(keys);
    }
}"""

if target_ensure in code:
    code = code.replace(target_ensure, replacement_ensure)
    with open(mifare_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(code)
    print("mifare_keys_manager.cpp patched successfully!")
else:
    print("mifare_keys_manager.cpp: target_ensure not found or already patched")

# 4. Patch bruce/src/modules/NRF24/nrf_common.cpp
nrf_common_path = r"bruce/src/modules/NRF24/nrf_common.cpp"
with open(nrf_common_path, "r", encoding="utf-8") as f:
    code = f.read().replace("\r\n", "\n")

target_nrf_start = """    if (!CHECK_NRF_SPI(mode)) return result;

    // Always re-assert CE LOW and CS HIGH before begin() — these pins
    // may have been left in an indeterminate state by the previous session,
    // especially after stopConstCarrier() which can leave CE HIGH internally.
    pinMode(bruceConfigPins.NRF24_bus.cs, OUTPUT);
    digitalWrite(bruceConfigPins.NRF24_bus.cs, HIGH);
    pinMode(bruceConfigPins.NRF24_bus.io0, OUTPUT);
    digitalWrite(bruceConfigPins.NRF24_bus.io0, LOW);
    delay(5); // Let pins settle before SPI traffic

    NRFSPI =
        acquireSPIBus(bruceConfigPins.NRF24_bus.sck, bruceConfigPins.NRF24_bus.miso, bruceConfigPins.NRF24_bus.mosi);
    if (!NRFSPI) {
        Serial.println("No hardware SPI bus available for NRF24, falling back to default SPI");
        NRFSPI = &SPI;
    }
    delay(10);"""

replacement_nrf_start = """    if (!CHECK_NRF_SPI(mode)) return result;

    // Deselect MicroSD card on shared SPI bus
#if defined(SDCARD_CS) && SDCARD_CS != -1
    pinMode(SDCARD_CS, OUTPUT);
    digitalWrite(SDCARD_CS, HIGH);
#endif

    // Always re-assert CE LOW and CS HIGH before begin() — these pins
    // may have been left in an indeterminate state by the previous session,
    // especially after stopConstCarrier() which can leave CE HIGH internally.
    pinMode(bruceConfigPins.NRF24_bus.cs, OUTPUT);
    digitalWrite(bruceConfigPins.NRF24_bus.cs, HIGH);
    pinMode(bruceConfigPins.NRF24_bus.io0, OUTPUT);
    digitalWrite(bruceConfigPins.NRF24_bus.io0, LOW);
    delay(5); // Let pins settle before SPI traffic

    NRFSPI =
        acquireSPIBus(bruceConfigPins.NRF24_bus.sck, bruceConfigPins.NRF24_bus.miso, bruceConfigPins.NRF24_bus.mosi);
    if (!NRFSPI) {
        Serial.println("No hardware SPI bus available for NRF24, falling back to default SPI");
        NRFSPI = &SPI;
    } else {
        // Clock dummy bytes with CS HIGH to clear any shared SPI line contention
        NRFSPI->beginTransaction(SPISettings(1000000u, MSBFIRST, SPI_MODE0));
        for (int i = 0; i < 4; i++) NRFSPI->transfer(0xFF);
        NRFSPI->endTransaction();
    }
    delay(10);"""

if target_nrf_start in code:
    code = code.replace(target_nrf_start, replacement_nrf_start)
    with open(nrf_common_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(code)
    print("nrf_common.cpp patched successfully!")
else:
    print("nrf_common.cpp: target_nrf_start not found or already patched")
