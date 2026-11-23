with open('bruce/src/modules/rfid/RFID2.cpp', 'r', encoding='utf-8') as f:
    text = f.read().replace('\r\n', '\n')

old_func = """int RFID2::read_mifare_ultralight_data_blocks() {
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

            strAllPages += "Page " + String(dataPages) + ": " + strPage + "\\n";
            dataPages++;
        }
    }

    return SUCCESS;
}"""

new_func = """int RFID2::read_mifare_ultralight_data_blocks() {
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

            strAllPages += "Page " + String(dataPages) + ": " + strPage + "\\n";
            dataPages++;
        }
    }

    return (dataPages > 0) ? SUCCESS : FAILURE;
}"""

if old_func in text:
    text = text.replace(old_func, new_func)
    with open('bruce/src/modules/rfid/RFID2.cpp', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text)
    print('read_mifare_ultralight_data_blocks patched successfully!')
else:
    print('read_mifare_ultralight_data_blocks: old_func pattern not found')
