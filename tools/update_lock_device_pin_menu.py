import os

files_to_patch = [
    r'C:\Users\Gourav\Documents\GitHub\Retro Go\copy to SD card\BruceJS\Tools\Lock Device.js',
    r'C:\Users\Gourav\Documents\GitHub\Retro Go\tools\Lock Device.js'
]

old_block = '''  if (entered === config.password) {
    unlocked = true;

    // Success Screen
    display.fill(BLACK);
    display.drawRoundRect(6, 6, displayWidth - 12, displayHeight - 12, 6, GREEN);
    display.setTextAlign("center", "middle");
    display.setTextSize(2);
    display.setTextColor(GREEN, BLACK);
    display.drawText("ACCESS GRANTED", displayWidth / 2, displayHeight / 2 - 16);

    display.setTextSize(1);
    display.setTextColor(WHITE, BLACK);
    var welcomeMsg = getRandomGreeting();
    display.drawText(welcomeMsg, displayWidth / 2, displayHeight / 2 + 14);

    display.setTextColor(CYAN, BLACK);
    display.drawText("Authenticating BruceOS Session...", displayWidth / 2, displayHeight / 2 + 34);

    // Display welcome screen for 3 full seconds as requested
    delay(3000);
    break;
  }'''

new_block = '''  if (entered === config.password) {
    unlocked = true;

    // Success Screen
    display.fill(BLACK);
    display.drawRoundRect(6, 6, displayWidth - 12, displayHeight - 12, 6, GREEN);
    display.setTextAlign("center", "middle");
    display.setTextSize(2);
    display.setTextColor(GREEN, BLACK);
    display.drawText("ACCESS GRANTED", displayWidth / 2, 45);

    display.setTextSize(1);
    display.setTextColor(WHITE, BLACK);
    var welcomeMsg = getRandomGreeting();
    display.drawText(welcomeMsg, displayWidth / 2, 75);

    display.setTextColor(GOLD, BLACK);
    display.drawText("Press [SELECT] to Change PIN", displayWidth / 2, 130);
    display.setTextColor(CYAN, BLACK);
    display.drawText("Or wait 3s to Enter Bruce...", displayWidth / 2, 155);

    var changeRequested = false;
    for (var t = 0; t < 60; t++) {
      if (selectIsDown()) {
        changeRequested = true;
        break;
      }
      delay(50);
    }

    if (changeRequested) {
      waitSelectReleased();
      drainKeys();
      display.fill(BLACK);
      display.setTextColor(CYAN, BLACK);
      display.setTextSize(2);
      display.drawText("SET NEW PIN", displayWidth / 2, 50);
      display.setTextSize(1);
      display.setTextColor(WHITE, BLACK);
      display.drawText("Enter 4-6 digits on keypad:", displayWidth / 2, 85);
      var newPin = keyboard.numKeyboard(10, "New PIN:", true);
      if (newPin && newPin.length >= 4) {
        config.password = newPin;
        saveConfig();
        display.fill(BLACK);
        display.setTextColor(GREEN, BLACK);
        display.setTextSize(2);
        display.drawText("PIN UPDATED!", displayWidth / 2, displayHeight / 2 - 10);
        display.setTextSize(1);
        display.setTextColor(WHITE, BLACK);
        display.drawText("New PIN saved successfully.", displayWidth / 2, displayHeight / 2 + 15);
        delay(2000);
      } else {
        display.fill(BLACK);
        display.setTextColor(RED, BLACK);
        display.setTextSize(1);
        display.drawText("PIN change cancelled.", displayWidth / 2, displayHeight / 2);
        delay(1200);
      }
    }
    break;
  }'''

for p in files_to_patch:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            txt = f.read()
        # Normalize line endings
        txt_norm = txt.replace('\r\n', '\n')
        old_norm = old_block.replace('\r\n', '\n')
        if old_norm in txt_norm:
            txt_norm = txt_norm.replace(old_norm, new_block.replace('\r\n', '\n'))
            with open(p, 'w', encoding='utf-8', newline='\r\n') as f:
                f.write(txt_norm)
            print("Successfully updated", p)
        else:
            print("Could not find exact block in", p)
