import urllib.request

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open('copy to SD card/BruceJS/Tools/Lock Device.json', 'rb') as f:
    file_bytes = f.read()

body = bytearray()
body.extend(f'--{boundary}\r\n'.encode())
body.extend(b'Content-Disposition: form-data; name="file"; filename="Lock Device.json"\r\n')
body.extend(b'Content-Type: application/json\r\n\r\n')
body.extend(file_bytes)
body.extend(f'\r\n--{boundary}--\r\n'.encode())

req = urllib.request.Request(
    'https://file.io/?expires=1d',
    data=bytes(body),
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'User-Agent': 'Mozilla/5.0'
    }
)
try:
    resp = urllib.request.urlopen(req)
    print('file.io response:', resp.read().decode())
except Exception as e:
    print('file.io error:', e)
