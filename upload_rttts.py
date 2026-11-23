import urllib.request
import urllib.parse
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_url = "http://192.168.1.35/login"
login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'bruce'}).encode('utf-8')
opener.open(urllib.request.Request(login_url, data=login_data, method='POST'))

melodies = {
    "/rttts/Super Mario.txt": "Super Mario:d=4,o=5,b=100:16e6,16e6,32p,8e6,16c6,8e6,8g6,8p,8g,8p,8c6,16p,8g,16p,8e,16p,8a,8b,16a#,8a,16g,16e6,16g6,8a6,16f6,8g6,8e6,16c6,16d6,8b",
    "/rttts/Tetris.txt": "Tetris:d=4,o=5,b=160:e6,8b,8c6,8d6,16e6,16d6,8c6,8b,a,8a,8c6,e6,8d6,8c6,b,8b,8c6,d6,e6,c6,a,2a",
    "/rttts/Star Wars.txt": "StarWars:d=4,o=5,b=45:32p,32f#,32f#,32f#,8b.,8f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32e6,8c#.6",
    "/rttts/Nokia.txt": "Nokia:d=4,o=5,b=225:8e6,8d6,f#,g#,8c#6,8b,d,e,8b,8a,c#,e,2a"
}

edit_url = "http://192.168.1.35/edit"
for path, content in melodies.items():
    data = urllib.parse.urlencode({
        'name': path,
        'content': content,
        'fs': 'SD'
    }).encode('utf-8')
    try:
        with opener.open(urllib.request.Request(edit_url, data=data, method='POST')) as resp:
            print(f"Uploaded {path}: {resp.status}")
    except Exception as e:
        print(f"Error {path}: {e}")
