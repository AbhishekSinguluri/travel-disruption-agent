import json
from app.db.repositories import get_trip_repository

repo = get_trip_repository()
trips = repo.list_trips("demo-user")
for trip in trips:
    print("Trip:", trip["id"])
    for day in trip.get('days', []):
        for stop in day.get('stops', []):
            print(f"  {stop.get('title')}: {stop.get('latitude')}, {stop.get('longitude')}")
