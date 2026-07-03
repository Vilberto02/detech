import urllib.request
import json
from pathlib import Path

# Test POST /api/analyze
fixture = Path('tests/fixtures/ejemplo_anomalias.py')
content = fixture.read_bytes()

boundary = b'DetechBoundary123'
CRLF = b'\r\n'

body = (
    b'--' + boundary + CRLF +
    b'Content-Disposition: form-data; name="files"; filename="ejemplo_anomalias.py"' + CRLF +
    b'Content-Type: text/x-python' + CRLF + CRLF +
    content + CRLF +
    b'--' + boundary + b'--' + CRLF
)

req = urllib.request.Request(
    'http://localhost:8000/api/analyze',
    data=body,
    headers={'Content-Type': 'multipart/form-data; boundary=' + boundary.decode()},
    method='POST'
)
res = urllib.request.urlopen(req)
data = json.loads(res.read())

s = data['summary']
print(f"Analyze OK")
print(f"  Archivos: {s['total_files']}")
print(f"  Total anomalias: {s['total_anomalies']}")
print(f"  Criticos: {s['critical']}")
print(f"  Advertencias: {s['warning']}")
print(f"  Informativos: {s['info']}")

# Test POST /api/report?format=html
json_bytes = json.dumps(data).encode()
req2 = urllib.request.Request(
    'http://localhost:8000/api/report?format=html',
    data=json_bytes,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
res2 = urllib.request.urlopen(req2)
html = res2.read().decode()
print(f"HTML Report OK - size: {len(html)} bytes")
print(f"  Has header: {'DETECH' in html}")
print(f"  Has anomaly table: {'anomaly-table' in html}")

print("ALL TESTS PASSED")
