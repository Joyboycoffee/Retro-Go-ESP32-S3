with open('bruce/src/core/settings.cpp', 'r', encoding='utf-8') as f:
    text = f.read()

target = """        {" 1 %",
         [=]() { setBrightness((uint8_t)1); },
         bruceConfig.bright == 1,
         [](void *pointer, bool shouldRender) {
             setBrightness((uint8_t)1, false);
             return false;
         }}
    };
    addOptionToMainMenu(); // this one bugs the brightness selection
    loopOptions(options, MENU_TYPE_REGULAR, "", idx);
    setBrightness(bruceConfig.bright, false);
}"""

replacement = """        {" 1 %",
         [=]() { setBrightness((uint8_t)1); },
         bruceConfig.bright == 1,
         [](void *pointer, bool shouldRender) {
             setBrightness((uint8_t)1, false);
             return false;
         }},
        {"Back", [=]() { setBrightness(bruceConfig.bright); }}
    };
    loopOptions(options, MENU_TYPE_SUBMENU, "Brightness", idx);
    setBrightness(bruceConfig.bright, false);
}"""

# Normalize line endings for replacement
text_norm = text.replace('\r\n', '\n')
assert target in text_norm, "Target not found in settings.cpp"
text_norm = text_norm.replace(target, replacement, 1)

with open('bruce/src/core/settings.cpp', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_norm)

print("Updated settings.cpp successfully!")
