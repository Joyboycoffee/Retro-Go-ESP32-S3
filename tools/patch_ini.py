with open('bruce/platformio.ini', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('bruce/platformio.ini', 'w', encoding='utf-8') as f:
    for line in lines:
        if line.strip() == 'FFat':
            f.write('\t; FFat\n')
        else:
            f.write(line)
print('Updated platformio.ini')
