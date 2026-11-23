with open('bruce/platformio.ini', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('\t; FFat', '\tFFat')
with open('bruce/platformio.ini', 'w', encoding='utf-8') as f:
    f.write(c)
print('Restored FFat in platformio.ini')
