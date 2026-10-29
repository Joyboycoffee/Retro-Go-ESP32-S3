#include <Arduino.h>
#include <SPI.h>
#include "driver/i2s.h"

// ==========================================
// PIN DEFINITIONS
// ==========================================
#define TFT_CS    46
#define TFT_RST   3
#define TFT_DC    8
#define TFT_MOSI  18
#define TFT_SCLK  17
#define TFT_BL    16

#define I2S_BCLK  7
#define I2S_LRC   15
#define I2S_DIN   6

// Safe button pins to scan (Internal Pull-Up enabled)
const int scanPins[] = {1, 2, 4, 5, 14, 21, 38, 39, 40, 41, 42, 45, 47, 48};
const int numScanPins = sizeof(scanPins) / sizeof(scanPins[0]);

// The 11 buttons in order
const char* buttonNames[] = {
    "D-PAD UP",
    "D-PAD DOWN",
    "D-PAD LEFT",
    "D-PAD RIGHT",
    "BUTTON A",
    "BUTTON B",
    "BUTTON X",
    "BUTTON Y",
    "SELECT",
    "MENU",
    "START"
};
const int totalButtons = sizeof(buttonNames) / sizeof(buttonNames[0]);
int recordedPins[totalButtons];

// ILI9341 Basic Commands
#define CMD_SWRESET 0x01
#define CMD_SLPOUT  0x11
#define CMD_DISPON  0x29
#define CMD_CASET   0x2A
#define CMD_PASET   0x2B
#define CMD_RAMWR   0x2C
#define CMD_MADCTL  0x36
#define CMD_PIXFMT  0x3A

#define COLOR_NAVY    0x000F
#define COLOR_GREEN   0x07E0
#define COLOR_GOLD    0xFDE0

SPIClass tftSpi(HSPI);

void sendCommand(uint8_t cmd) {
    digitalWrite(TFT_DC, LOW);
    digitalWrite(TFT_CS, LOW);
    tftSpi.transfer(cmd);
    digitalWrite(TFT_CS, HIGH);
}

void sendData(uint8_t data) {
    digitalWrite(TFT_DC, HIGH);
    digitalWrite(TFT_CS, LOW);
    tftSpi.transfer(data);
    digitalWrite(TFT_CS, HIGH);
}

void initILI9341() {
    pinMode(TFT_CS, OUTPUT);
    pinMode(TFT_DC, OUTPUT);
    pinMode(TFT_RST, OUTPUT);

    digitalWrite(TFT_RST, HIGH);
    delay(10);
    digitalWrite(TFT_RST, LOW);
    delay(20);
    digitalWrite(TFT_RST, HIGH);
    delay(120);

    sendCommand(CMD_SWRESET);
    delay(150);
    sendCommand(CMD_SLPOUT);
    delay(120);
    sendCommand(CMD_PIXFMT);
    sendData(0x55);
    sendCommand(CMD_MADCTL);
    sendData(0x48);
    sendCommand(CMD_DISPON);
    delay(50);
}

void fillScreen(uint16_t color) {
    sendCommand(CMD_CASET);
    sendData(0x00); sendData(0x00); sendData(0x00); sendData(239);
    sendCommand(CMD_PASET);
    sendData(0x00); sendData(0x00); sendData(0x01); sendData(0x3F);
    sendCommand(CMD_RAMWR);

    digitalWrite(TFT_DC, HIGH);
    digitalWrite(TFT_CS, LOW);
    uint8_t highByte = (color >> 8);
    uint8_t lowByte = (color & 0xFF);
    uint8_t lineBuffer[240 * 2];
    for (int i = 0; i < 240 * 2; i += 2) {
        lineBuffer[i] = highByte;
        lineBuffer[i + 1] = lowByte;
    }
    for (int y = 0; y < 320; y++) {
        tftSpi.transferBytes(lineBuffer, NULL, sizeof(lineBuffer));
    }
    digitalWrite(TFT_CS, HIGH);
}

void initI2S() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = 22050,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 256,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_BCLK,
        .ws_io_num = I2S_LRC,
        .data_out_num = I2S_DIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };
    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config);
}

void playBeep(float freqHz, int durationMs) {
    const int sampleRate = 22050;
    int totalSamples = (sampleRate * durationMs) / 1000;
    int16_t buffer[128];
    size_t bytesWritten;
    float phase = 0;
    float phaseInc = (2.0f * 3.14159265f * freqHz) / sampleRate;
    const int16_t volume = 5000;

    int samplesLeft = totalSamples;
    while (samplesLeft > 0) {
        int chunkSize = min(samplesLeft, 64);
        for (int i = 0; i < chunkSize; i++) {
            int16_t val = (int16_t)(sin(phase) * volume);
            buffer[i * 2] = val;
            buffer[i * 2 + 1] = val;
            phase += phaseInc;
            if (phase >= 2.0f * 3.14159265f) phase -= 2.0f * 3.14159265f;
        }
        i2s_write(I2S_NUM_0, buffer, chunkSize * 4, &bytesWritten, portMAX_DELAY);
        samplesLeft -= chunkSize;
    }
}

void playFanfare() {
    playBeep(523.25, 120); // C5
    playBeep(659.25, 120); // E5
    playBeep(783.99, 120); // G5
    playBeep(1046.50, 400); // C6
}

void setup() {
    Serial.begin(115200);
    delay(500);

    // Initialize Backlight & Display
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);
    tftSpi.begin(TFT_SCLK, -1, TFT_MOSI, TFT_CS);
    tftSpi.setFrequency(20000000);
    initILI9341();
    fillScreen(COLOR_NAVY);

    // Audio
    initI2S();

    // Initialize pins with Internal Pull-Up
    for (int i = 0; i < numScanPins; i++) {
        pinMode(scanPins[i], INPUT_PULLUP);
    }

    Serial.println("\n=======================================================");
    Serial.println("       RETRO-GO INTERACTIVE BUTTON CALIBRATION WIZARD    ");
    Serial.println("=======================================================\n");

    // Run through each button step-by-step
    for (int step = 0; step < totalButtons; step++) {
        Serial.printf("\n[STEP %2d of %d]  >>> PLEASE PRESS:  %-15s <<<\n", step + 1, totalButtons, buttonNames[step]);
        Serial.flush();

        // Wait until any monitored pin is pressed (reads LOW)
        int detectedPin = -1;
        while (detectedPin == -1) {
            for (int i = 0; i < numScanPins; i++) {
                if (digitalRead(scanPins[i]) == LOW) {
                    delay(20); // Debounce
                    if (digitalRead(scanPins[i]) == LOW) {
                        detectedPin = scanPins[i];
                        break;
                    }
                }
            }
            delay(10);
        }

        // Save recorded pin
        recordedPins[step] = detectedPin;
        Serial.printf("    [CAPTURED!]   %-15s is on GPIO %d\n", buttonNames[step], detectedPin);
        Serial.flush();

        // Positive feedback: Flash green + click sound
        fillScreen(COLOR_GREEN);
        playBeep(1000.0, 70);
        delay(150);
        fillScreen(COLOR_NAVY);

        // Wait until button is RELEASED (reads HIGH)
        while (digitalRead(detectedPin) == LOW) {
            delay(10);
        }
        delay(100); // Debounce release
    }

    // ==========================================
    // ALL 11 BUTTONS CALIBRATED!
    // ==========================================
    fillScreen(COLOR_GOLD);
    playFanfare();

    Serial.println("\n\n=======================================================");
    Serial.println("     CALIBRATION COMPLETE! YOUR FINAL PIN MAPPING:     ");
    Serial.println("=======================================================");
    Serial.println("// Put this directly in Retro-Go config.h:\n");
    Serial.printf("#define RG_GPIO_GAMEPAD_UP       %d\n", recordedPins[0]);
    Serial.printf("#define RG_GPIO_GAMEPAD_DOWN     %d\n", recordedPins[1]);
    Serial.printf("#define RG_GPIO_GAMEPAD_LEFT     %d\n", recordedPins[2]);
    Serial.printf("#define RG_GPIO_GAMEPAD_RIGHT    %d\n", recordedPins[3]);
    Serial.printf("#define RG_GPIO_GAMEPAD_A        %d\n", recordedPins[4]);
    Serial.printf("#define RG_GPIO_GAMEPAD_B        %d\n", recordedPins[5]);
    Serial.printf("#define RG_GPIO_GAMEPAD_X        %d\n", recordedPins[6]);
    Serial.printf("#define RG_GPIO_GAMEPAD_Y        %d\n", recordedPins[7]);
    Serial.printf("#define RG_GPIO_GAMEPAD_SELECT   %d\n", recordedPins[8]);
    Serial.printf("#define RG_GPIO_GAMEPAD_MENU     %d\n", recordedPins[9]);
    Serial.printf("#define RG_GPIO_GAMEPAD_START    %d\n", recordedPins[10]);
    Serial.println("=======================================================\n");
    Serial.flush();
}

void loop() {
    // Idle after calibration complete
    delay(1000);
}
