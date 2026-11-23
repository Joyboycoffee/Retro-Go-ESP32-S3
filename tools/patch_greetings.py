p = 'copy to SD card/BruceJS/Tools/Lock Device.js'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

greetings_list = [
    # Personal & Heroic
    "Welcome back, Gourav!",
    "Welcome back, JoiBoi!",
    "System Unlocked. Hello Gourav!",
    "Ready to hack, JoiBoi!",
    "Greetings, Gourav! Have fun!",
    "Session Active: Welcome JoiBoi!",
    "Access Authorized for Gourav.",
    "Console Armed & Ready, JoiBoi!",
    "Welcome back, Captain Gourav!",
    "Great to see you again, JoiBoi!",
    "Welcome aboard, Gourav!",
    "Cyberdeck Activated. Hey JoiBoi!",
    "Good day, Gourav! Systems Nominal.",
    "Security Cleared. Go for it, JoiBoi!",
    "Welcome back, Legendary Gourav!",
    "Console Online. Welcome JoiBoi!",
    # Retro Gamer Vibes
    "Player 1 Ready! Welcome Gourav!",
    "High Score Champion: JoiBoi!",
    "Level Loaded. Go get 'em, Gourav!",
    "Continue? 9... 8... Welcome JoiBoi!",
    "All Bosses Beware! Gourav is back!",
    "Insert Coin to Win! Welcome JoiBoi!",
    "1-UP Extra Life granted to Gourav!",
    "Retro Gaming Master: JoiBoi!",
    "Press Start to Conquer, Gourav!",
    "8-Bit Nostalgia loaded for JoiBoi!",
    "Power-Up Collected! Hey Gourav!",
    "Cheat Code Activated: JoiBoi Mode!",
    # Cyberpunk & Hacker Themes
    "Neural Link Established, Gourav.",
    "Bypassing Firewalls... Welcome JoiBoi!",
    "Root Shell Granted to Gourav.",
    "Decrypting Payload for JoiBoi...",
    "Zero-Day Exploits Ready, Gourav!",
    "Cyber Grid Synchronized, JoiBoi.",
    "Matrix Entry Confirmed. Hello Gourav!",
    "Terminal Hijack Complete, JoiBoi!",
    "Sub-GHz Transceiver Hot, Gourav!",
    "Packet Sniffer Armed for JoiBoi.",
    "Bruce Predatory Instincts: Gourav!",
    "Master of the Airwaves: JoiBoi!",
    "Kernel Bootstrapped for Gourav.",
    "RF Spectrum Clear. Hey JoiBoi!",
    "Hardware Hacking Suite: Gourav Edition!",
    "Firmware Dominance achieved, JoiBoi!",
    # Casual & Cheerful
    "Hope you have an epic day, Gourav!",
    "Another brilliant mission awaits, JoiBoi!",
    "Nice to have you at the controls, Gourav!",
    "Ready to test some cool stuff, JoiBoi?",
    "Everything is running fast and smooth, Gourav!",
    "Let's see what we can build today, JoiBoi!",
    "Maximum Performance unlocked, Gourav!",
    "Battery charged and ready, JoiBoi!",
    "Dual-Boot Beast awakened by Gourav!",
    "Always one step ahead, JoiBoi!",
    "The handheld legend: Gourav!",
    "ESP32-S3 Beast Mode: JoiBoi Online!",
    "Infinite Possibilities await, Gourav!",
    "Your pocket cyberdeck is ready, JoiBoi!",
    "Welcome home, Architect Gourav!",
    "Let the games begin, JoiBoi!"
]

import json
greetings_js = 'var GREETINGS = ' + json.dumps(greetings_list, indent=4) + ';\n'

old_greetings_start = 'var GREETINGS = ['
old_greetings_end = 'var greetingIndex = Math.floor(Math.random() * GREETINGS.length);'
idx1 = c.find(old_greetings_start)
idx2 = c.find(old_greetings_end)

if idx1 != -1 and idx2 != -1:
    idx2 += len(old_greetings_end)
    c = c[:idx1] + greetings_js + 'function getRandomGreeting() {\n    return GREETINGS[Math.floor(Math.random() * GREETINGS.length)];\n}\n' + c[idx2:]
    print('Replaced GREETINGS with 60+ entries')
else:
    print('ERROR: could not find GREETINGS block')

# Replace var welcomeMsg = GREETINGS[greetingIndex];
old_msg = 'var welcomeMsg = GREETINGS[greetingIndex];'
new_msg = 'var welcomeMsg = getRandomGreeting();'
if old_msg in c:
    c = c.replace(old_msg, new_msg)
    print('Updated welcomeMsg call')

with open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)

print('Lock Device.js greetings updated successfully!')
