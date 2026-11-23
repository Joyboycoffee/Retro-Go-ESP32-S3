with open("Musicstreaming.js", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update controls hint
code = code.replace("turn = move   press = ok   back = cancel", "D-Pad = Move   A = OK   B = Back")
code = code.replace("turn = seek back / forward, press = play, back = menu", "Left/Right = Seek, A = Play/Pause, B = Menu")

# 2. Add D-pad Up and Down support to navigation in choose()
old_nav = "if (keyboard.getNextPress()) { sel = (sel + 1) % labels.length; dirty = true; }\n    else if (keyboard.getPrevPress()) { sel = (sel + labels.length - 1) % labels.length; dirty = true; }"
new_nav = "var navNext = keyboard.getNextPress() || (keyboard.getDownPress && keyboard.getDownPress());\n    var navPrev = keyboard.getPrevPress() || (keyboard.getUpPress && keyboard.getUpPress());\n    if (navNext) { sel = (sel + 1) % labels.length; dirty = true; }\n    else if (navPrev) { sel = (sel + labels.length - 1) % labels.length; dirty = true; }"
code = code.replace(old_nav, new_nav)

with open("Musicstreaming_Handheld.js", "w", encoding="utf-8") as f:
    f.write(code)

print("Musicstreaming_Handheld.js created.")
