import json
from app.services.mock_db import demo_trip
from app.agents.builder import build_canonical_trip

trip_dict = demo_trip.model_dump()
for stop in trip_dict["days"][0]["stops"]:
    stop.pop("latitude", None)
    stop.pop("longitude", None)

res = build_canonical_trip(trip_dict)

with open('demo_trip_output.json', 'w', encoding='utf-8') as f:
    json.dump(res['days'][0]['stops'], f, indent=2, ensure_ascii=False)
