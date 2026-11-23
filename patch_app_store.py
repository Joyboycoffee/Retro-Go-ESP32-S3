import re

with open("App_Store.js", "r", encoding="utf-8") as f:
    code = f.read()

# Replace function h(e,t,r,s){...} with function h(e,t,r,s){return true;}
patched = re.sub(r'function h\(e,t,r,s\)\{[^}]*\}', 'function h(e,t,r,s){return true;}', code)

with open("App_Store_Patched.js", "w", encoding="utf-8") as f:
    f.write(patched)

print("Patched App Store written. Modified:", len(code) != len(patched))
