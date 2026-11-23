import re

# 1. Patch MFRC522v2.cpp
mfrc522_path = r"bruce/.pio/libdeps/retro-handheld-s3/RFID_MFRC522v2/src/MFRC522v2.cpp"
with open(mfrc522_path, "r", encoding="utf-8") as f:
    mfrc = f.read()

# Restore PCD_Reset() unconditionally in PCD_Init()
target_prev = """  byte preV = _driver->PCD_ReadRegister(PCD_Register::VersionReg);
  if (preV == 0x00 || preV == 0xFF) { PCD_Reset(); }"""
replacement_prev = """  PCD_Reset();"""

if target_prev in mfrc:
    mfrc = mfrc.replace(target_prev, replacement_prev)
    print("[MFRC522v2] Restored PCD_Reset() in PCD_Init()")
else:
    print("[MFRC522v2] target_prev NOT found")

# Remove yield() in PCD_CommunicateWithPICC
target_yield = """    if (n & 0x01) { return StatusCode::STATUS_TIMEOUT; }
    yield();
  } while"""
replacement_yield = """    if (n & 0x01) { return StatusCode::STATUS_TIMEOUT; }
  } while"""

if target_yield in mfrc:
    mfrc = mfrc.replace(target_yield, replacement_yield)
    print("[MFRC522v2] Removed yield() in fast IRQ loop")
else:
    print("[MFRC522v2] target_yield NOT found")

with open(mfrc522_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(mfrc)

# 2. Patch RFID2.cpp
rfid2_path = r"bruce/src/modules/rfid/RFID2.cpp"
with open(rfid2_path, "r", encoding="utf-8") as f:
    rfid2 = f.read()

# Replace begin() gain setting with RxGain_43dB
rfid2 = rfid2.replace(
    "mfrc522.PCD_SetAntennaGain(MFRC522::PCD_RxGain::RxGain_max);",
    "mfrc522.PCD_SetAntennaGain(MFRC522::PCD_RxGain::RxGain_43dB);"
)
print("[RFID2] Set begin() antenna gain to RxGain_43dB")

# Replace PICC_IsNewCardPresent with stable carrier polling
old_is_new_card = """bool RFID2::PICC_IsNewCardPresent() {
#if defined(SDCARD_CS) && SDCARD_CS != -1
    digitalWrite(SDCARD_CS, HIGH);
#endif
#if defined(NRF24_CE_PIN) && NRF24_CE_PIN != -1
    digitalWrite(NRF24_CE_PIN, HIGH);
#endif

    byte bufferATQA[2];
    byte bufferSize = sizeof(bufferATQA);

    if (_driver) {
        _driver->PCD_WriteRegister(MFRC522::PCD_Register::TxModeReg, 0x00);
        _driver->PCD_WriteRegister(MFRC522::PCD_Register::RxModeReg, 0x00);
        _driver->PCD_WriteRegister(MFRC522::PCD_Register::ModWidthReg, 0x26);
    }

    mfrc522.PCD_AntennaOn();

    // Stage 1: Standard 38 dB gain (prevents receiver saturation when touching antenna!)
    mfrc522.PCD_SetAntennaGain(MFRC522::PCD_RxGain::RxGain_38dB);
    bufferSize = sizeof(bufferATQA);
    byte result = mfrc522.PICC_RequestA(bufferATQA, &bufferSize);
    if (result != MFRC522::StatusCode::STATUS_OK && result != MFRC522::StatusCode::STATUS_COLLISION) {
        bufferSize = sizeof(bufferATQA);
        result = mfrc522.PICC_WakeupA(bufferATQA, &bufferSize);
    }

    // Stage 2: 43 dB gain (medium sensitivity for fobs/keychains)
    if (result != MFRC522::StatusCode::STATUS_OK && result != MFRC522::StatusCode::STATUS_COLLISION) {
        mfrc522.PCD_SetAntennaGain(MFRC522::PCD_RxGain::RxGain_43dB);
        bufferSize = sizeof(bufferATQA);
        result = mfrc522.PICC_RequestA(bufferATQA, &bufferSize);
        if (result != MFRC522::StatusCode::STATUS_OK && result != MFRC522::StatusCode::STATUS_COLLISION) {
            bufferSize = sizeof(bufferATQA);
            result = mfrc522.PICC_WakeupA(bufferATQA, &bufferSize);
        }
    }

    // Stage 3: Max 48 dB gain (for small coils / NTAG stickers / distant tags)
    if (result != MFRC522::StatusCode::STATUS_OK && result != MFRC522::StatusCode::STATUS_COLLISION) {
        mfrc522.PCD_SetAntennaGain(MFRC522::PCD_RxGain::RxGain_max);
        bufferSize = sizeof(bufferATQA);
        result = mfrc522.PICC_RequestA(bufferATQA, &bufferSize);
        if (result != MFRC522::StatusCode::STATUS_OK && result != MFRC522::StatusCode::STATUS_COLLISION) {
            bufferSize = sizeof(bufferATQA);
            result = mfrc522.PICC_WakeupA(bufferATQA, &bufferSize);
        }
    }

    bool bl_result =
        (result == MFRC522::StatusCode::STATUS_OK || result == MFRC522::StatusCode::STATUS_COLLISION);
    if (bl_result) {
        if (bufferSize >= 2) {
            char atqaBuf[8];
            snprintf(atqaBuf, sizeof(atqaBuf), "%02X %02X", bufferATQA[1], bufferATQA[0]);
            printableUID.atqa = String(atqaBuf);
        } else if (bufferSize == 1) {
            char atqaBuf[4];
            snprintf(atqaBuf, sizeof(atqaBuf), "%02X", bufferATQA[0]);
            printableUID.atqa = String(atqaBuf);
        }
    }
    return bl_result;
}"""

new_is_new_card = """bool RFID2::PICC_IsNewCardPresent() {
#if defined(SDCARD_CS) && SDCARD_CS != -1
    digitalWrite(SDCARD_CS, HIGH);
#endif
#if defined(NRF24_CE_PIN) && NRF24_CE_PIN != -1
    digitalWrite(NRF24_CE_PIN, HIGH);
#endif

    byte bufferATQA[2];
    byte bufferSize = sizeof(bufferATQA);

    if (_driver) {
        _driver->PCD_WriteRegister(MFRC522::PCD_Register::TxModeReg, 0x00);
        _driver->PCD_WriteRegister(MFRC522::PCD_Register::RxModeReg, 0x00);
        _driver->PCD_WriteRegister(MFRC522::PCD_Register::ModWidthReg, 0x26);
    }

    // Ensure RF field is energized (only write register if antenna was turned off)
    byte tx = _driver ? _driver->PCD_ReadRegister(MFRC522::PCD_Register::TxControlReg) : 0;
    if ((tx & 0x03) != 0x03) {
        mfrc522.PCD_AntennaOn();
    }

    // Step 1: Standard REQA (wakes up any tag in IDLE state)
    byte result = mfrc522.PICC_RequestA(bufferATQA, &bufferSize);

    // Step 2: Fallback WUPA (wakes up tags in HALT state, e.g. NTAG stickers or re-read cards)
    if (result != MFRC522::StatusCode::STATUS_OK && result != MFRC522::StatusCode::STATUS_COLLISION) {
        bufferSize = sizeof(bufferATQA);
        result = mfrc522.PICC_WakeupA(bufferATQA, &bufferSize);
    }

    bool bl_result =
        (result == MFRC522::StatusCode::STATUS_OK || result == MFRC522::StatusCode::STATUS_COLLISION);
    if (bl_result) {
        if (bufferSize >= 2) {
            char atqaBuf[8];
            snprintf(atqaBuf, sizeof(atqaBuf), "%02X %02X", bufferATQA[1], bufferATQA[0]);
            printableUID.atqa = String(atqaBuf);
        } else if (bufferSize == 1) {
            char atqaBuf[4];
            snprintf(atqaBuf, sizeof(atqaBuf), "%02X", bufferATQA[0]);
            printableUID.atqa = String(atqaBuf);
        }
    }
    return bl_result;
}"""

if old_is_new_card in rfid2:
    rfid2 = rfid2.replace(old_is_new_card, new_is_new_card)
    print("[RFID2] Replaced PICC_IsNewCardPresent with stable carrier polling")
else:
    print("[RFID2] old_is_new_card NOT matched directly, trying normalized...")
    # Normalize line endings
    norm_rfid2 = rfid2.replace("\r\n", "\n")
    norm_old = old_is_new_card.replace("\r\n", "\n")
    if norm_old in norm_rfid2:
        norm_rfid2 = norm_rfid2.replace(norm_old, new_is_new_card.replace("\r\n", "\n"))
        rfid2 = norm_rfid2
        print("[RFID2] Replaced PICC_IsNewCardPresent with stable carrier polling (normalized)")
    else:
        print("[RFID2] FAILED to match old_is_new_card")

with open(rfid2_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(rfid2)

# 3. Patch tag_o_matic.cpp
tag_path = r"bruce/src/modules/rfid/tag_o_matic.cpp"
with open(tag_path, "r", encoding="utf-8") as f:
    tag = f.read()

old_felica_check = """        if (bruceConfigPins.rfidModule != M5_RFID2_MODULE) { // Read felica if module is PN532
            readStatus = _rfid->read(1);"""

new_felica_check = """        if (bruceConfigPins.rfidModule == PN532_I2C_MODULE || 
            bruceConfigPins.rfidModule == PN532_SPI_MODULE) { // Read felica ONLY if module is PN532
            readStatus = _rfid->read(1);"""

if old_felica_check in tag:
    tag = tag.replace(old_felica_check, new_felica_check)
    print("[tag_o_matic] Restricted FeliCa read to PN532 modules only")
else:
    norm_tag = tag.replace("\r\n", "\n")
    norm_old_f = old_felica_check.replace("\r\n", "\n")
    if norm_old_f in norm_tag:
        norm_tag = norm_tag.replace(norm_old_f, new_felica_check.replace("\r\n", "\n"))
        tag = norm_tag
        print("[tag_o_matic] Restricted FeliCa read to PN532 modules only (normalized)")
    else:
        print("[tag_o_matic] FAILED to match old_felica_check")

with open(tag_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(tag)

print("All patches applied!")
