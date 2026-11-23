import urllib.request
import urllib.parse
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_url = "http://192.168.1.35/login"
login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'bruce'}).encode('utf-8')

req = urllib.request.Request(login_url, data=login_data, method='POST')
try:
    with opener.open(req) as resp:
        print("Login response:", resp.status, resp.geturl())
        for c in cj:
            print(f"Cookie: {c.name}={c.value}")
except Exception as e:
    print("Login error:", e)

# Test edit/write of AllPlayer.js on SD
with open("AllPlayer_Fixed.js", "r", encoding="utf-8") as f:
    js_code = f.read()

edit_url = "http://192.168.1.35/edit"
edit_data = urllib.parse.urlencode({
    'name': '/BruceJS/Tools/AllPlayer.js',
    'content': js_code,
    'fs': 'SD'
}).encode('utf-8')

edit_req = urllib.request.Request(edit_url, data=edit_data, method='POST')
try:
    with opener.open(edit_req) as resp:
        print("Edit response:", resp.status, resp.read().decode('utf-8'))
except Exception as e:
    print("Edit error:", e)
