import requests
import json

print("Running Controlled Test: Test A & Test B...")

req_data = {
    "operator": "IndiGo",
    "service_number": "6E 652",
    "origin": "Hyderabad",
    "destination": "Goa",
    "travel_date": "2026-10-01",
    "monitoring_window": "LAST_1_WEEK"
}

try:
    res = requests.post("http://localhost:8000/api/monitor/test-start", json=req_data)
    print("Test-Start Response:")
    print(json.dumps(res.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

