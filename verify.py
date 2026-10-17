import json
import urllib.request
try:
    req = urllib.request.Request('http://localhost:8000/api/trips/demo')
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Trip ID: {data.get('id')}")
        print(f"Title: {data.get('name')}")
        days = data.get('days', [])
        print(f"Days count: {len(days)}")
        
        stops = []
        if len(days) > 0:
            stops = days[0].get('stops', [])
            print(f"Stop count: {len(stops)}")
            for stop in stops:
                print(f"  - Stop ID: {stop.get('id')}")
                print(f"    Title: {stop.get('title')}")
                print(f"    Location: {stop.get('location_name')}")
                print(f"    Lat/Lon: {stop.get('latitude')}, {stop.get('longitude')}")
                print(f"    Status: {stop.get('status')}")
                print(f"    Hours: {stop.get('opening_hours')}")
except Exception as e:
    print(f"Error: {e}")
