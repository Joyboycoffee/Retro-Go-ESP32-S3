import urllib.request
import mimetypes

def upload_uguu(filepath):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    with open(filepath, 'rb') as f:
        file_bytes = f.read()
    
    body = bytearray()
    body.extend(f'--{boundary}\r\n'.encode())
    body.extend(b'Content-Disposition: form-data; name="files[]"; filename="Lock Device.json"\r\n')
    body.extend(b'Content-Type: application/json\r\n\r\n')
    body.extend(file_bytes)
    body.extend(f'\r\n--{boundary}--\r\n'.encode())
    
    req = urllib.request.Request(
        'https://uguu.se/upload',
        data=bytes(body),
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
    )
    try:
        resp = urllib.request.urlopen(req)
        print('uguu response:', resp.read().decode())
    except Exception as e:
        print('uguu error:', e)

upload_uguu('copy to SD card/BruceJS/Tools/Lock Device.json')
