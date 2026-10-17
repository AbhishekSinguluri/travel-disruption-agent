from app.db.repositories import get_trip_repository, InMemoryTripRepository
import os
from unittest.mock import patch

def test_repo_fallback():
    with patch.dict(os.environ, clear=True):
        repo = get_trip_repository()
        assert isinstance(repo, InMemoryTripRepository)

def test_trip_events():
    repo = InMemoryTripRepository()
    repo.log_event("trip-1", "TEST_EVENT", {"data": 123})
    events = repo.get_events("trip-1")
    assert len(events) > 0
    assert events[-1]["event_type"] == "TEST_EVENT"
