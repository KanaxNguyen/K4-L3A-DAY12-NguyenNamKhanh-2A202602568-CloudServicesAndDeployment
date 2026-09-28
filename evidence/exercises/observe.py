import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
compose = ['docker', 'compose', '-p', 'day12-exercises', '-f', str(root / 'evidence/exercises/compose.yaml')]
records = []
for index in [1, 2, 3, 1]:
    code = '''import json, urllib.request
request = urllib.request.Request(
    "http://127.0.0.1:8000/ask",
    data=json.dumps({"question": "Redis lưu hội thoại như thế nào?"}).encode(),
    headers={"Content-Type": "application/json", "X-API-Key": "exercise-local-key", "X-User-Id": "exercises-scale"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=20) as response:
    print(response.read().decode())
'''
    result = subprocess.run(compose + ['exec', '-T', '--index', str(index), 'agent', 'python', '-'], input=code, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    body = json.loads(result.stdout)
    record = {'instance': index, 'history_length': body['history_length'], 'cost_usd': body['cost_usd']}
    records.append(record)
    print(json.dumps(record), flush=True)

logs = subprocess.run(compose + ['logs', '--no-color', 'agent'], capture_output=True, text=True, check=True).stdout
ask_logs = [line[line.index('{'):] for line in logs.splitlines() if '"event": "ask_completed"' in line]
print('Log JSON thật: ' + ask_logs[0], flush=True)
(root / 'evidence/exercises/observations.json').write_text(json.dumps({'requests': records, 'ask_logs': ask_logs}, ensure_ascii=False, indent=2))
