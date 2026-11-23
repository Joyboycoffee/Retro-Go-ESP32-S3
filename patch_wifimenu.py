path = r"bruce\src\core\menu_items\WifiMenu.cpp"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
patched = False
for line in lines:
    new_lines.append(line)
    if 'Turn Off WiFi' in line and not patched:
        new_lines.append('    options.push_back({"WebUI", loopOptionsWebUi});\n')
        patched = True

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Patched: {patched}")
