"""Trigger evaluation via FastAPI API and poll for completion."""
import urllib.request
import json
import time

# Start evaluation
payload = json.dumps({"judge": None, "test_file": None}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:8000/evaluate',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(f"Status: {resp.status}")
    print(f"Job: {json.dumps(result, indent=2)}")
    job_id = result.get('job_id')

print(f"\nJob ID: {job_id}")
print("Polling for completion...")

start = time.time()
while True:
    time.sleep(10)
    elapsed = time.time() - start
    
    poll_req = urllib.request.Request(
        f'http://127.0.0.1:8000/evaluate/{job_id}',
        method='GET'
    )
    with urllib.request.urlopen(poll_req, timeout=10) as resp:
        status_data = json.loads(resp.read())
    
    print(f"[{elapsed:.0f}s] Status: {status_data.get('status')} | Progress: {status_data.get('progress')}% | {status_data.get('message', '')}")
    
    if status_data.get('status') in ('completed', 'failed'):
        print("\nFINAL:")
        print(json.dumps(status_data, indent=2, default=str))
        
        if status_data.get('status') == 'completed' and status_data.get('report_path'):
            results_req = urllib.request.Request(
                f'http://127.0.0.1:8000/evaluate/{job_id}/results',
                method='GET'
            )
            with urllib.request.urlopen(results_req, timeout=10) as resp:
                results = json.loads(resp.read())
            print("\n=== RESULTS ===")
            print(json.dumps(results.get('summary'), indent=2))
        break
    
    if elapsed > 600:
        print("TIMEOUT: 10 minute limit exceeded")
        break
