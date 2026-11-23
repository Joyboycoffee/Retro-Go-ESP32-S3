with open("Morse_Code.js", "r", encoding="utf-8") as f:
    code = f.read()

old_keys = """        if (keyboard.getNextPress()) {
            if (moveCursor(0, 1)) {
                needsRedraw = true;
            }
        } else if (keyboard.getPrevPress()) {
            if (moveCursor(0, -1)) {
                needsRedraw = true;
            }
        } else if (keyboard.getSelPress()) {
            if (moveCursor(1, 0) || moveToTopInColumn()) {
                needsRedraw = true;
            }
        } else if (keyboard.getEscPress()) {
            return;
        }"""

new_keys = """        var up = (keyboard.getUpPress && keyboard.getUpPress());
        var down = (keyboard.getDownPress && keyboard.getDownPress());
        var next = keyboard.getNextPress();
        var prev = keyboard.getPrevPress();
        var sel = keyboard.getSelPress();
        var esc = keyboard.getEscPress();

        if (up) {
            if (moveCursor(-1, 0)) needsRedraw = true;
        } else if (down) {
            if (moveCursor(1, 0) || moveToTopInColumn()) needsRedraw = true;
        } else if (next) {
            if (moveCursor(0, 1)) needsRedraw = true;
        } else if (prev) {
            if (moveCursor(0, -1)) needsRedraw = true;
        } else if (sel) {
            if (moveCursor(1, 0) || moveToTopInColumn()) needsRedraw = true;
        } else if (esc) {
            return;
        }"""

code = code.replace(old_keys, new_keys)

with open("Morse_Code_Handheld.js", "w", encoding="utf-8") as f:
    f.write(code)

print("Morse_Code_Handheld.js created.")
