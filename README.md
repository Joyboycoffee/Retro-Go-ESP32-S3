# ESP32-S3 Retro Handheld Console (Retro-Go)

A DIY retro gaming handheld built around the **ESP32-S3-PRO** (N16R8: 16MB QIO Flash, 8MB Octal PSRAM), featuring a 2.4" ILI9341 SPI display, MAX98357A I2S audio, onboard MicroSD storage, and an 11-button layout running **Retro-Go**.

Emulates **NES, SNES, Game Boy, Game Boy Color, Sega Master System, Game Gear, Sega Mega Drive / Genesis, PC Engine, MSX, and classic DOOM**.

---

## Hardware Specifications

| Component | Specification / Model |
| :--- | :--- |
| **MCU** | ESP32-S3 (Edgehax S3-PRO, N16R8: 16MB Flash, 8MB Octal PSRAM) |
| **Display** | 2.4" ILI9341 TFT SPI LCD (320x240) with LEDC PWM Backlight |
| **Audio** | MAX98357A I2S DAC Mono Amplifier + 8Ω 0.5W Speaker |
| **Storage** | Onboard MicroSD Slot (Dedicated SPI3 bus) |
| **Controls** | 11 Tactile Push Buttons (Active LOW, Internal Pull-Up) |
| **Power** | 18650 Li-ion Cell + TP4056 USB-C Charger + Mini 5V Boost Module + Slide Switch |

---

## Master Hardware Pinout

### 1. Gamepad Inputs (Active LOW, Internal Pull-Up)
| Button | GPIO | Logic |
| :--- | :--- | :--- |
| **D-Pad UP** | `GPIO 41` | Active LOW |
| **D-Pad DOWN** | `GPIO 42` | Active LOW |
| **D-Pad LEFT** | `GPIO 2` | Active LOW |
| **D-Pad RIGHT** | `GPIO 1` | Active LOW |
| **A** | `GPIO 47` | Active LOW |
| **B** | `GPIO 21` | Active LOW |
| **X** | `GPIO 45` | Active LOW |
| **Y** | `GPIO 48` | Active LOW |
| **SELECT** | `GPIO 40` | Active LOW |
| **MENU** | `GPIO 39` | Active LOW |
| **START** | `GPIO 38` | Active LOW |

### 2. Display (ILI9341 SPI - SPI2 Host)
| Signal | GPIO | Notes |
| :--- | :--- | :--- |
| **MOSI (SDI)** | `GPIO 18` | Hardware SPI2 |
| **CLK (SCK)** | `GPIO 17` | Hardware SPI2 |
| **CS** | `GPIO 46` | Chip Select |
| **DC** | `GPIO 8` | Data / Command |
| **RST** | `GPIO 3` | Reset |
| **BCKL (LED)**| `GPIO 16` | Hardware PWM Dimming |
| **MISO** | `NC (-1)` | Write-only |

### 3. Audio (MAX98357A I2S)
| Signal | GPIO | Notes |
| :--- | :--- | :--- |
| **BCK (BCLK)** | `GPIO 7` | Bit Clock |
| **WS (LRCLK)** | `GPIO 15` | Word Select (Left/Right Clock) |
| **DATA (DIN)** | `GPIO 6` | Serial Data |

### 4. MicroSD Card (Onboard Slot - SPI3 Host)
| Signal | GPIO | Notes |
| :--- | :--- | :--- |
| **CS** | `GPIO 10` | Chip Select |
| **MOSI** | `GPIO 11` | Dedicated SPI3 |
| **CLK** | `GPIO 12` | Dedicated SPI3 |
| **MISO** | `GPIO 13` | Dedicated SPI3 |

---

## MicroSD Card Setup

Format the MicroSD card as **FAT32**. Copy the `roms` folder from [`copy to SD card/`](copy%20to%20SD%20card/) directly to the root of your MicroSD card.

### Folder Mapping:
* `/roms/nes/` — NES (`.nes`, `.zip`)
* `/roms/snes/` — SNES (`.smc`, `.sfc`, `.zip`)
* `/roms/gb/` — Game Boy (`.gb`, `.zip`)
* `/roms/gbc/` — Game Boy Color (`.gbc`, `.zip`)
* `/roms/gba/` — Game Boy Advance (`.gba`, `.zip`)
* `/roms/md/` — Sega Genesis / Mega Drive (`.md`, `.gen`, `.bin`, `.zip`)
* `/roms/sms/` — Sega Master System (`.sms`, `.zip`)
* `/roms/gg/` — Sega Game Gear (`.gg`, `.zip`)
* `/roms/pce/` — PC Engine / TurboGrafx-16 (`.pce`, `.zip`)
* `/roms/doom/` — DOOM (`.wad` — shareware `doom1.wad` included)

---

## Flashing the Firmware

Download the built `retro-go_*.img` artifact from GitHub Actions and run:

```bash
esptool.py --chip esp32s3 --port COM10 --baud 921600 write_flash 0x0 retro-go_*.img
```

Or using `uv`:
```bash
uv tool run esptool --chip esp32s3 --port COM10 --baud 921600 write_flash 0x0 retro-go_*.img
```
