import urllib.request
import urllib.parse
import json

content = '{"password":"1234","baseTimeout":10000,"maxTimeout":120000}\n'

# 1. dpaste.org
try:
    data = urllib.parse.urlencode({'content': content, 'syntax': 'json', 'expiry_days': 14}).encode()
    req = urllib.request.Request('https://dpaste.org/api/', data=data, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req)
    url = resp.read().decode().strip().strip('"')
    print('dpaste raw:', url + '/raw')
except Exception as e:
    print('dpaste error:', e)

# 2. paste.c-net.org
try:
    req = urllib.request.Request('https://paste.c-net.org/', data=content.encode(), headers={'User-Agent': 'curl/7.68.0'})
    resp = urllib.request.urlopen(req)
    print('c-net url:', resp.read().decode().strip())
except Exception as e:
    print('c-net error:', e)
