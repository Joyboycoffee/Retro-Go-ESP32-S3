p = 'bruce/src/core/desk_clock.cpp'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

old_s1 = 'snprintf(t, sizeof(t), "%02u:%02u.%02u", (elapsed / 60000) % 100, (elapsed / 1000) % 60, (elapsed % 1000) / 10);'
new_s1 = 'snprintf(t, sizeof(t), "%02u:%02u.%02u", (unsigned)((elapsed / 60000) % 100), (unsigned)((elapsed / 1000) % 60), (unsigned)((elapsed % 1000) / 10));'

c = c.replace(old_s1, new_s1)

old_s2 = 'snprintf(l, sizeof(l), "Lap %d   %02u:%02u.%02u", lapCount - i, (laps[i] / 60000) % 100,'
new_s2 = 'snprintf(l, sizeof(l), "Lap %d   %02u:%02u.%02u", lapCount - i, (unsigned)((laps[i] / 60000) % 100),'

c = c.replace(old_s2, new_s2)

old_s3 = '(laps[i] / 1000) % 60, (laps[i] % 1000) / 10);'
new_s3 = '(unsigned)((laps[i] / 1000) % 60), (unsigned)((laps[i] % 1000) / 10));'

c = c.replace(old_s3, new_s3)

with open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('desk_clock format strings fixed successfully')
