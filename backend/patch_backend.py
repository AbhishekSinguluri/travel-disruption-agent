import re

# 1. Update builder.py
with open("app/agents/builder.py", "r", encoding="utf-8") as f:
    builder = f.read()

# Add opening hours based on provider
builder = builder.replace(
    '"opening_hours": {"open": "09:30", "close": "17:30"} if place else None,',
    '"opening_hours": place.opening_hours if (place and hasattr(place, "opening_hours")) else ({"open": "09:30", "close": "17:30"} if place else None),'
)

with open("app/agents/builder.py", "w", encoding="utf-8") as f:
    f.write(builder)

# 2. Update providers.py mock data to include opening_hours
with open("app/services/providers.py", "r", encoding="utf-8") as f:
    providers = f.read()

if "opening_hours={" not in providers:
    providers = providers.replace(
        'rating=4.5, source="mock"',
        'rating=4.5, source="mock", opening_hours={"open": "09:00", "close": "17:30"}'
    ).replace(
        'rating=4.0, source="mock"',
        'rating=4.0, source="mock", opening_hours={"open": "10:00", "close": "18:00"}'
    )
    with open("app/services/providers.py", "w", encoding="utf-8") as f:
        f.write(providers)

# 3. Update places.py to add opening_hours to PlaceCandidate
with open("app/schemas/places.py", "r", encoding="utf-8") as f:
    places = f.read()

if "opening_hours" not in places:
    places = places.replace(
        "source: str = \"google\"",
        "source: str = \"google\"\n    opening_hours: Optional[Dict[str, str]] = None"
    ).replace(
        "from typing import Optional",
        "from typing import Optional, Dict"
    )
    with open("app/schemas/places.py", "w", encoding="utf-8") as f:
        f.write(places)

print("Patched backend")
