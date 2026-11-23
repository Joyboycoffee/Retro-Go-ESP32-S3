# Patch ConfigMenu.h
with open('bruce/src/core/menu_items/ConfigMenu.h', 'r', encoding='utf-8') as f:
    h = f.read()

target_h = "    void systemMenu(void);"
replacement_h = "    void systemMenu(void);\n    void setBootAnimation(void);"
assert target_h in h, "target_h not found in ConfigMenu.h"
h = h.replace(target_h, replacement_h)

with open('bruce/src/core/menu_items/ConfigMenu.h', 'w', encoding='utf-8') as f:
    f.write(h)
print("ConfigMenu.h patched")

# Patch ConfigMenu.cpp
with open('bruce/src/core/menu_items/ConfigMenu.cpp', 'r', encoding='utf-8') as f:
    cpp = f.read()

target_item = '''            {String("InstaBoot: ") + (bruceConfig.instantBoot ? "ON" : "OFF"),
             [this]() {
                 // Toggle InstaBoot setting
                 bruceConfig.instantBoot = !bruceConfig.instantBoot;
                 bruceConfig.saveFile();
             }                                                                                                           },'''

replacement_item = '''            {String("InstaBoot: ") + (bruceConfig.instantBoot ? "ON" : "OFF"),
             [this]() {
                 // Toggle InstaBoot setting
                 bruceConfig.instantBoot = !bruceConfig.instantBoot;
                 bruceConfig.saveFile();
             }                                                                                                           },
            {String("Boot Animation: ") + (bruceConfig.bootAnim == 0 ? "Bruce Main" : (bruceConfig.bootAnim == 1 ? "Cybernetic" : (bruceConfig.bootAnim == 2 ? "Shark Genesis" : "Static Splash"))),
             [this]() { setBootAnimation(); }                                                                            },'''

assert target_item in cpp, "target_item not found in ConfigMenu.cpp"
cpp = cpp.replace(target_item, replacement_item)

method_code = '''
void ConfigMenu::setBootAnimation() {
    while (true) {
        std::vector<Option> animOptions = {
            {String("Bruce 40FPS (Main) ") + (bruceConfig.bootAnim == 0 ? "[*]" : "[ ]"),
             [this]() { bruceConfig.bootAnim = 0; bruceConfig.saveFile(); }},
            {String("Cybernetic ") + (bruceConfig.bootAnim == 1 ? "[*]" : "[ ]"),
             [this]() { bruceConfig.bootAnim = 1; bruceConfig.saveFile(); }},
            {String("Shark Genesis ") + (bruceConfig.bootAnim == 2 ? "[*]" : "[ ]"),
             [this]() { bruceConfig.bootAnim = 2; bruceConfig.saveFile(); }},
            {String("Static Splash ") + (bruceConfig.bootAnim == 3 ? "[*]" : "[ ]"),
             [this]() { bruceConfig.bootAnim = 3; bruceConfig.saveFile(); }},
            {"Back", []() {}}
        };
        int selected = loopOptions(animOptions, MENU_TYPE_SUBMENU, "Boot Animation");
        if (selected == -1 || selected == (int)animOptions.size() - 1) return;
    }
}
'''

# Add method before end of file
cpp += method_code

with open('bruce/src/core/menu_items/ConfigMenu.cpp', 'w', encoding='utf-8') as f:
    f.write(cpp)
print("ConfigMenu.cpp patched")
