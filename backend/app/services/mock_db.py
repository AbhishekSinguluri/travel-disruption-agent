from app.schemas.trip import Trip, TripDay, ItineraryStop

demo_trip = Trip(
    id="trip-1",
    destination="Hyderabad",
    start_date="2026-10-01",
    end_date="2026-10-01",
    days=[
        TripDay(
            id="day-1",
            date="2026-10-01",
            stops=[
                ItineraryStop(id="stop-1", title="Hotel", category="Lodging", location_name="Taj Falaknuma Palace", latitude=17.3309283, longitude=78.4672623, date="2026-10-01", start_time="09:00", end_time="09:30", duration_minutes=30, status="COMPLETED", place_id="249443907", address="Taj Falaknuma Palace, Falaknuma Road", source="nominatim"),
                ItineraryStop(id="stop-2", title="Charminar", category="Attraction", location_name="Charminar", latitude=17.3616024, longitude=78.4746421, date="2026-10-01", start_time="10:00", end_time="11:30", duration_minutes=90, status="COMPLETED", place_id="249063568", address="Charminar, Charminar Circle", source="nominatim"),
                ItineraryStop(id="stop-3", title="Lunch", category="Food", location_name="Shadab Hotel", latitude=17.3687527, longitude=78.4755405, date="2026-10-01", start_time="12:00", end_time="13:30", duration_minutes=90, status="COMPLETED", place_id="249336962", address="Hotel Shadab, High Court Road", source="nominatim"),
                ItineraryStop(id="stop-4", title="Salar Jung Museum", category="Attraction", location_name="Salar Jung Museum", latitude=17.371392, longitude=78.4801498, date="2026-10-01", start_time="14:00", end_time="16:00", duration_minutes=120, status="PLANNED", place_id="248893658", address="Salar Jung Museum, Darul Shifa Road", source="nominatim"),
                ItineraryStop(id="stop-5", title="Shopping", category="Shopping", location_name="Laad Bazaar", latitude=17.3625085, longitude=78.4729754, date="2026-10-01", start_time="17:00", end_time="19:00", duration_minutes=120, status="PLANNED", place_id="247489479", address="Laad Bazaar, Khilwat", source="nominatim"),
                ItineraryStop(id="stop-6", title="Dinner", category="Food", location_name="Jewel of Nizam", latitude=17.3916, longitude=78.3188, date="2026-10-01", start_time="20:00", end_time="21:30", duration_minutes=90, status="PLANNED", place_id="ChIJ_Y9K5q2TyzsRV7rJkR-Q0eM", address="The Minar, Golkonda Resort", source="google_mock")
            ]
        )
    ]
)

MOCK_DB = {
    "trips": {
        "trip-1": demo_trip.model_dump()
    },
    "disruptions": {},
    "state": {}
}

def get_trip(trip_id: str):
    return MOCK_DB["trips"].get(trip_id)

def update_trip(trip_id: str, data: dict):
    MOCK_DB["trips"][trip_id] = data
    return data
