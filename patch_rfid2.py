import re

rfid2_path = r"bruce/src/modules/rfid/RFID2.cpp"
with open(rfid2_path, "r", encoding="utf-8") as f:
    code = f.read().replace("\r\n", "\n")

# 1. Update PICC_IsNewCardPresent
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

    mfrc522.PCD_SetAntennaGain(MFRC522::PCD_RxGain::RxGain_max);
    mfrc522.PCD_AntennaOn();

    byte result = mfrc522.PICC_RequestA(bufferATQA, &bufferSize);
    if (result != MFRC522::StatusCode::STATUS_OK && result != MFRC522::StatusCode::STATUS_COLLISION) {
        delay(5);
        bufferSize = sizeof(bufferATQA);
        result = mfrc522.PICC_WakeupA(bufferATQA, &bufferSize);
    }
    bool bl_result =
        (result == MFRC522::StatusCode::STATUS_OK || result == MFRC522::StatusCode::STATUS_COLLISION);
    if (bl_result) {
        printableUID.atqa = "";
        for (byte i = 0; i < bufferSize; i++) {
            printableUID.atqa += bufferATQA[i] < 0x10 ? " 0" : " ";
            printableUID.atqa += String(bufferATQA[i], HEX);
        }
        printableUID.atqa.trim();
        printableUID.atqa.toUpperCase();
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

# 2. Update read()
old_read = """int RFID2::read(int cardBaudRate) {
    pageReadStatus = FAILURE;

#if defined(SDCARD_CS) && SDCARD_CS != -1
    digitalWrite(SDCARD_CS, HIGH);
#endif
#if defined(NRF24_CE_PIN) && NRF24_CE_PIN != -1
    digitalWrite(NRF24_CE_PIN, HIGH);
#endif

    mfrc522.PCD_SetAntennaGain(MFRC522::PCD_RxGain::RxGain_max);
    mfrc522.PCD_AntennaOn();

    bool hasCard = PICC_IsNewCardPresent();
    if (!hasCard) {
        byte bufferATQA[2];
        byte bufferSize = sizeof(bufferATQA);
        byte res = mfrc522.PICC_WakeupA(bufferATQA, &bufferSize);
        if (res == MFRC522::StatusCode::STATUS_OK || res == MFRC522::StatusCode::STATUS_COLLISION) {
            hasCard = true;
        }
    }
    if (!hasCard) return TAG_NOT_PRESENT;

    if (!mfrc522.PICC_ReadCardSerial()) return TAG_NOT_PRESENT;

    byte piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    if (piccType == MFRC522::PICC_Type::PICC_TYPE_ISO_14443_4) {
        pageReadStatus = NOT_IMPLEMENTED;
        pageReadSuccess = false;
        format_data();
        set_uid();
        mfrc522.PICC_HaltA();
        return SUCCESS;
    } else {
        displayInfo("Reading data blocks...");
        pageReadStatus = read_data_blocks();
        pageReadSuccess = pageReadStatus == SUCCESS;
    }
    format_data();
    set_uid();
    return SUCCESS;
}"""

new_read = """int RFID2::read(int cardBaudRate) {
    pageReadStatus = FAILURE;

#if defined(SDCARD_CS) && SDCARD_CS != -1
    digitalWrite(SDCARD_CS, HIGH);
#endif
#if defined(NRF24_CE_PIN) && NRF24_CE_PIN != -1
    digitalWrite(NRF24_CE_PIN, HIGH);
#endif

    mfrc522.PCD_AntennaOn();

    bool hasCard = PICC_IsNewCardPresent();
    if (!hasCard) return TAG_NOT_PRESENT;

    if (!mfrc522.PICC_ReadCardSerial()) return TAG_NOT_PRESENT;

    byte piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    if (piccType == MFRC522::PICC_Type::PICC_TYPE_ISO_14443_4) {
        pageReadStatus = NOT_IMPLEMENTED;
        pageReadSuccess = false;
        format_data();
        set_uid();
        mfrc522.PICC_HaltA();
        return SUCCESS;
    } else {
        displayInfo("Reading data blocks...");
        pageReadStatus = read_data_blocks();
        pageReadSuccess = pageReadStatus == SUCCESS;
    }
    format_data();
    set_uid();
    return SUCCESS;
}"""

# 3. Update format_data()
old_format = """void RFID2::format_data() {
    byte bcc = 0;

    printableUID.picc_type = get_tag_type();

    printableUID.sak = mfrc522.uid.sak < 0x10 ? "0" : "";
    printableUID.sak += String(mfrc522.uid.sak, HEX);
    printableUID.sak.toUpperCase();

    // UID
    printableUID.uid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
        printableUID.uid += mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ";
        printableUID.uid += String(mfrc522.uid.uidByte[i], HEX);
        bcc = bcc ^ mfrc522.uid.uidByte[i];
    }
    printableUID.uid.trim();
    printableUID.uid.toUpperCase();

    // BCC
    printableUID.bcc = bcc < 0x10 ? "0" : "";
    printableUID.bcc += String(bcc, HEX);
    printableUID.bcc.toUpperCase();

    // ATQA
    String atqaPart1 = printableUID.atqa.substring(0, 2);
    String atqaPart2 = printableUID.atqa.substring(3, 5);
    printableUID.atqa = atqaPart2 + " " + atqaPart1;
}"""

new_format = """void RFID2::format_data() {
    byte bcc = 0;

    printableUID.picc_type = get_tag_type();

    printableUID.sak = mfrc522.uid.sak < 0x10 ? "0" : "";
    printableUID.sak += String(mfrc522.uid.sak, HEX);
    printableUID.sak.toUpperCase();

    // UID
    printableUID.uid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
        printableUID.uid += mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ";
        printableUID.uid += String(mfrc522.uid.uidByte[i], HEX);
        bcc = bcc ^ mfrc522.uid.uidByte[i];
    }
    printableUID.uid.trim();
    printableUID.uid.toUpperCase();

    // BCC
    printableUID.bcc = bcc < 0x10 ? "0" : "";
    printableUID.bcc += String(bcc, HEX);
    printableUID.bcc.toUpperCase();
}"""

# 4. Update read_data_blocks()
old_read_data_blocks = """int RFID2::read_data_blocks() {
    dataPages = 0;
    totalPages = 0;
    int readStatus = FAILURE;
    byte piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    strAllPages = "";

    switch (piccType) {
        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_MINI:
        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_1K:
        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_4K:
            readStatus = read_mifare_classic_data_blocks(piccType);
            break;

        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_UL:
            readStatus = read_mifare_ultralight_data_blocks();
            dataPages = (readStatus == SUCCESS && dataPages > 0) ? dataPages - 1 : dataPages;
            if (totalPages == 0) totalPages = dataPages;
            break;

        default: break;
    }

    mfrc522.PICC_HaltA();
    return readStatus;
}"""

new_read_data_blocks = """int RFID2::read_data_blocks() {
    dataPages = 0;
    totalPages = 0;
    int readStatus = FAILURE;
    byte piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    strAllPages = "";

    switch (piccType) {
        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_MINI:
        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_1K:
        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_4K:
            readStatus = read_mifare_classic_data_blocks(piccType);
            break;

        case MFRC522::PICC_Type::PICC_TYPE_MIFARE_UL:
            readStatus = read_mifare_ultralight_data_blocks();
            if (totalPages == 0) totalPages = dataPages;
            break;

        default: break;
    }

    mfrc522.PICC_HaltA();
    return readStatus;
}"""

# 5. Update read_mifare_classic_data_blocks()
old_read_classic = """    if (no_of_sectors) {
        for (int8_t i = 0; i < no_of_sectors; i++) {
            sectorReadStatus = read_mifare_classic_data_sector(i);
            if (sectorReadStatus != SUCCESS) break;
        }
    }
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    return sectorReadStatus;
}"""

new_read_classic = """    if (no_of_sectors) {
        for (int8_t i = 0; i < no_of_sectors; i++) {
            vTaskDelay(pdMS_TO_TICKS(1)); // Feed watchdog and yield
            sectorReadStatus = read_mifare_classic_data_sector(i);
            if (sectorReadStatus != SUCCESS) break;
        }
    }
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    return (dataPages > 0) ? SUCCESS : sectorReadStatus;
}"""

# 6. Update authenticate_mifare_classic()
old_auth = """int RFID2::authenticate_mifare_classic(byte block) {
    bruceConfig.ensureMifareKeysLoaded();
    byte statusA = 0;
    byte statusB = 0;

    MFRC522::MIFARE_Key keyA;
    MFRC522::MIFARE_Key keyB;

    for (auto key : keys) {
        memcpy(keyA.keyByte, key, 6);

        statusA = mfrc522.PCD_Authenticate(
            MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_A, block, &keyA, &mfrc522.uid
        );
        if (statusA == MFRC522::StatusCode::STATUS_OK) break;

        if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
    }

    if (statusA != MFRC522::StatusCode::STATUS_OK) {
        for (const auto &mifKey : bruceConfig.mifareKeys) {
            for (size_t i = 0; i < mifKey.length(); i += 2) {
                keyA.keyByte[i / 2] = strtoul(mifKey.substring(i, i + 2).c_str(), NULL, 16);
            }

            statusA = mfrc522.PCD_Authenticate(
                MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_A, block, &keyA, &mfrc522.uid
            );
            if (statusA == MFRC522::StatusCode::STATUS_OK) break;

            if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
        }
    }

    for (auto key : keys) {
        memcpy(keyB.keyByte, key, 6);

        statusB = mfrc522.PCD_Authenticate(
            MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_B, block, &keyB, &mfrc522.uid
        );
        if (statusB == MFRC522::StatusCode::STATUS_OK) break;

        if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
    }

    if (statusB != MFRC522::StatusCode::STATUS_OK) {
        for (const auto &mifKey : bruceConfig.mifareKeys) {
            for (size_t i = 0; i < mifKey.length(); i += 2) {
                keyB.keyByte[i / 2] = strtoul(mifKey.substring(i, i + 2).c_str(), NULL, 16);
            }

            statusB = mfrc522.PCD_Authenticate(
                MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_A, block, &keyB, &mfrc522.uid
            );
            if (statusB == MFRC522::StatusCode::STATUS_OK) break;

            if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
        }
    }

    return (statusA == MFRC522::StatusCode::STATUS_OK && statusB == MFRC522::StatusCode::STATUS_OK)
               ? SUCCESS
               : TAG_AUTH_ERROR;
}"""

new_auth = """int RFID2::authenticate_mifare_classic(byte block) {
    byte statusA = 0;
    byte statusB = 0;

    MFRC522::MIFARE_Key keyA;
    MFRC522::MIFARE_Key keyB;

    // 1. Try Key A against standard keys
    for (auto key : keys) {
        vTaskDelay(pdMS_TO_TICKS(1));
        memcpy(keyA.keyByte, key, 6);

        statusA = mfrc522.PCD_Authenticate(
            MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_A, block, &keyA, &mfrc522.uid
        );
        if (statusA == MFRC522::StatusCode::STATUS_OK) return SUCCESS;

        if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
    }

    // 2. Try Key A against custom loaded keys
    for (const auto &mifKey : bruceConfig.mifareKeys) {
        if (mifKey.length() != 12) continue;
        vTaskDelay(pdMS_TO_TICKS(1));
        for (size_t i = 0; i < 12; i += 2) {
            keyA.keyByte[i / 2] = strtoul(mifKey.substring(i, i + 2).c_str(), NULL, 16);
        }

        statusA = mfrc522.PCD_Authenticate(
            MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_A, block, &keyA, &mfrc522.uid
        );
        if (statusA == MFRC522::StatusCode::STATUS_OK) return SUCCESS;

        if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
    }

    // 3. Fallback to Key B against standard keys
    for (auto key : keys) {
        vTaskDelay(pdMS_TO_TICKS(1));
        memcpy(keyB.keyByte, key, 6);

        statusB = mfrc522.PCD_Authenticate(
            MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_B, block, &keyB, &mfrc522.uid
        );
        if (statusB == MFRC522::StatusCode::STATUS_OK) return SUCCESS;

        if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
    }

    // 4. Fallback to Key B against custom loaded keys
    for (const auto &mifKey : bruceConfig.mifareKeys) {
        if (mifKey.length() != 12) continue;
        vTaskDelay(pdMS_TO_TICKS(1));
        for (size_t i = 0; i < 12; i += 2) {
            keyB.keyByte[i / 2] = strtoul(mifKey.substring(i, i + 2).c_str(), NULL, 16);
        }

        statusB = mfrc522.PCD_Authenticate(
            MFRC522::PICC_Command::PICC_CMD_MF_AUTH_KEY_B, block, &keyB, &mfrc522.uid
        );
        if (statusB == MFRC522::StatusCode::STATUS_OK) return SUCCESS;

        if (!PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) { return TAG_NOT_PRESENT; }
    }

    return TAG_AUTH_ERROR;
}"""

# 7. Update read_mifare_ultralight_data_blocks()
old_ul = """int RFID2::read_mifare_ultralight_data_blocks() {
    byte status;
    byte byteCount;
    byte buffer[18];
    byte i;
    byte cc;
    String strPage = "";

    for (byte page = 0; page <= 252; page += 4) {
        byteCount = sizeof(buffer);
        status = mfrc522.MIFARE_Read(page, buffer, &byteCount);
        if (status != MFRC522::StatusCode::STATUS_OK) {
            return status == MFRC522::StatusCode::STATUS_MIFARE_NACK ? SUCCESS : FAILURE;
        }
        for (byte offset = 0; offset < 4; offset++) {
            strPage = "";
            if (page + offset == 3) {
                cc = buffer[4 * offset + 2];
                switch (cc) {
                    // NTAG213
                    case 0x12: totalPages = 45; break;
                    // NTAG215
                    case 0x3E: totalPages = 135; break;
                    // NTAG216
                    case 0x6D: totalPages = 231; break;
                    default: break;
                }
            }
            for (byte index = 0; index < 4; index++) {
                i = 4 * offset + index;
                strPage += buffer[i] < 0x10 ? F(" 0") : F(" ");
                strPage += String(buffer[i], HEX);
            }
            strPage.trim();
            strPage.toUpperCase();

            strAllPages += "Page " + String(dataPages) + ": " + strPage + "\n";
            dataPages++;
        }
    }

    return SUCCESS;
}"""

new_ul = """int RFID2::read_mifare_ultralight_data_blocks() {
    byte status;
    byte byteCount;
    byte buffer[18];
    byte i;
    byte cc;
    String strPage = "";

    totalPages = 16; // Minimum default until CC read

    for (byte page = 0; page <= 252; page += 4) {
        vTaskDelay(pdMS_TO_TICKS(1)); // Watchdog feed
        if (totalPages > 0 && dataPages >= totalPages) break;

        byteCount = sizeof(buffer);
        status = mfrc522.MIFARE_Read(page, buffer, &byteCount);
        if (status != MFRC522::StatusCode::STATUS_OK) {
            // Reached end of readable pages on this tag
            break;
        }
        for (byte offset = 0; offset < 4; offset++) {
            if (totalPages > 0 && dataPages >= totalPages) break;

            strPage = "";
            if (page + offset == 3) {
                cc = buffer[4 * offset + 2];
                switch (cc) {
                    // NTAG213 (144 bytes user + system = 45 pages)
                    case 0x12: totalPages = 45; break;
                    // NTAG215 (504 bytes user + system = 135 pages)
                    case 0x3E: totalPages = 135; break;
                    // NTAG216 (888 bytes user + system = 231 pages)
                    case 0x6D: totalPages = 231; break;
                    default: break;
                }
            }
            for (byte index = 0; index < 4; index++) {
                i = 4 * offset + index;
                strPage += buffer[i] < 0x10 ? F(" 0") : F(" ");
                strPage += String(buffer[i], HEX);
            }
            strPage.trim();
            strPage.toUpperCase();

            strAllPages += "Page " + String(dataPages) + ": " + strPage + "\n";
            dataPages++;
        }
    }

    return (dataPages > 0) ? SUCCESS : FAILURE;
}"""

for name, old, new in [
    ("PICC_IsNewCardPresent", old_is_new_card, new_is_new_card),
    ("read", old_read, new_read),
    ("format_data", old_format, new_format),
    ("read_data_blocks", old_read_data_blocks, new_read_data_blocks),
    ("read_mifare_classic_data_blocks", old_read_classic, new_read_classic),
    ("authenticate_mifare_classic", old_auth, new_auth),
    ("read_mifare_ultralight_data_blocks", old_ul, new_ul)
]:
    if old in code:
        code = code.replace(old, new)
        print(f"Patched {name}")
    else:
        print(f"FAILED to match {name}")

with open(rfid2_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(code)
print("Finished patching RFID2.cpp")
