import re

with open("bruce/src/modules/rfid/RFID2.cpp", "r", encoding="utf-8") as f:
    c = f.read()

pattern = r"bool RFID2::PICC_IsNewCardPresent\(\) \{[\s\S]*?return bl_result;\s*\}"

replacement = """bool RFID2::PICC_IsNewCardPresent() {
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

new_c, count = re.subn(pattern, replacement, c)
print("Replaced count:", count)
with open("bruce/src/modules/rfid/RFID2.cpp", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(new_c)
