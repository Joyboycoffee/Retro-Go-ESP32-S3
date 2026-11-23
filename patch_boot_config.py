# Patch config.h
with open('bruce/src/core/config.h', 'r', encoding='utf-8') as f:
    h = f.read()

target_h = "    int instantBoot = 0;"
replacement_h = "    int instantBoot = 0;\n    int bootAnim = 0; // 0 = Bruce 40FPS (Main), 1 = Cybernetic, 2 = Shark Genesis, 3 = Static Splash"
assert target_h in h, "target_h not found"
h = h.replace(target_h, replacement_h)

with open('bruce/src/core/config.h', 'w', encoding='utf-8') as f:
    f.write(h)
print("config.h patched")

# Patch config.cpp
with open('bruce/src/core/config.cpp', 'r', encoding='utf-8') as f:
    cpp = f.read()

target_cpp1 = '    setting["instantBoot"] = instantBoot;'
replacement_cpp1 = '    setting["instantBoot"] = instantBoot;\n    setting["bootAnim"] = bootAnim;'
assert target_cpp1 in cpp, "target_cpp1 not found"
cpp = cpp.replace(target_cpp1, replacement_cpp1)

target_cpp2 = '    if (!setting["instantBoot"].isNull()) {\n        instantBoot = setting["instantBoot"].as<int>();\n    }'
replacement_cpp2 = '''    if (!setting["instantBoot"].isNull()) {
        instantBoot = setting["instantBoot"].as<int>();
    }
    if (!setting["bootAnim"].isNull()) {
        bootAnim = setting["bootAnim"].as<int>();
    }'''
assert target_cpp2 in cpp, "target_cpp2 not found"
cpp = cpp.replace(target_cpp2, replacement_cpp2)

with open('bruce/src/core/config.cpp', 'w', encoding='utf-8') as f:
    f.write(cpp)
print("config.cpp patched")
