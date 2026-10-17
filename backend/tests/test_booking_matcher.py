import pytest
from app.services.booking_matcher import match_booking_to_trip

def test_no_matching_trip():
    # 4. No matching trip -> alert only, no recovery
    monitor = {"monitor_id": "m1", "provider": "Air India", "service_number": "AI 123", "travel_date": "2026-10-04"}
    trips = [
        {"id": "t1", "days": [{"stops": [{"title": "Lufthansa LH 456"}]}]}
    ]
    assert match_booking_to_trip(monitor, trips) is None

def test_one_matching_trip():
    # 1. One matching trip -> recovery invoked
    monitor = {"monitor_id": "m1", "provider": "Air India", "service_number": "AI 123", "travel_date": "2026-10-04"}
    trips = [
        {"id": "t1", "days": [{"stops": [{"title": "Flight Air India AI 123 to Delhi"}]}]}
    ]
    assert match_booking_to_trip(monitor, trips)["id"] == "t1"

def test_multiple_trips_correct_selected():
    # 2. Correct trip selected when multiple trips exist
    # 3. Wrong unrelated trip is not selected
    monitor = {"monitor_id": "m1", "provider": "Air India", "service_number": "AI 123", "travel_date": "2026-10-04"}
    trips = [
        {"id": "t1", "days": [{"stops": [{"title": "Flight Lufthansa LH 456"}]}]},
        {"id": "t2", "days": [{"stops": [{"title": "Flight Air India AI 123 to Delhi"}]}]},
        {"id": "t3", "days": [{"stops": [{"title": "Hotel Stay"}]}]}
    ]
    assert match_booking_to_trip(monitor, trips)["id"] == "t2"

def test_ambiguous_matching():
    # 5. Ambiguous matching -> no recovery
    monitor = {"monitor_id": "m1", "provider": "Air India", "service_number": "AI 123"}
    trips = [
        {"id": "t1", "days": [{"stops": [{"title": "Flight Air India AI 123 to Delhi"}]}]},
        {"id": "t2", "days": [{"stops": [{"title": "Flight Air India AI 123 Return"}]}]}
    ]
    assert match_booking_to_trip(monitor, trips) is None

def test_pnr_match():
    # 6. PNR match works
    monitor = {"monitor_id": "m1", "booking_reference": "XYZ123"}
    trips = [
        {"id": "t1", "days": [{"stops": [{"title": "Unrelated", "booking_reference": "ABC999"}]}]},
        {"id": "t2", "days": [{"stops": [{"title": "My Flight", "booking_reference": "xyz123"}]}]}
    ]
    assert match_booking_to_trip(monitor, trips)["id"] == "t2"

def test_flight_date_match():
    # 7. Flight/service number + date match works
    monitor = {"monitor_id": "m1", "service_number": "AI 123", "travel_date": "2026-10-04T10:30:00"}
    trips = [
        {"id": "t1", "days": [{"date": "2026-10-04", "stops": [{"title": "Air India AI 123"}]}]}
    ]
    assert match_booking_to_trip(monitor, trips)["id"] == "t1"

def test_explicit_trip_id():
    monitor = {"monitor_id": "m1", "trip_id": "t3"}
    trips = [
        {"id": "t1", "days": []},
        {"id": "t2", "days": []},
        {"id": "t3", "days": []}
    ]
    assert match_booking_to_trip(monitor, trips)["id"] == "t3"

def test_destination_fallback():
    monitor = {"monitor_id": "m1", "destination": "Tokyo"}
    trips = [
        {"id": "t1", "destination": "London", "days": []},
        {"id": "t2", "name": "Trip to Tokyo", "days": []}
    ]
    assert match_booking_to_trip(monitor, trips)["id"] == "t2"
