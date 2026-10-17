import pytest
import os
from unittest.mock import patch
from app.services.providers import get_places_provider, get_routes_provider, MockPlacesProvider, MockRoutesProvider, GooglePlacesProvider, GoogleRoutesProvider
from app.services.candidate_search import search_recovery_candidates

def test_provider_fallback_missing_key():
    with patch.dict(os.environ, clear=True):
        p_provider = get_places_provider()
        r_provider = get_routes_provider()
        assert isinstance(p_provider, MockPlacesProvider)
        assert isinstance(r_provider, MockRoutesProvider)

def test_provider_with_key():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "real-key"}):
        p_provider = get_places_provider()
        r_provider = get_routes_provider()
        assert isinstance(p_provider, GooglePlacesProvider)
        assert isinstance(r_provider, GoogleRoutesProvider)

@patch("app.services.providers.get_places_provider")
@patch("app.services.providers.get_routes_provider")
def test_candidate_search_flow(mock_routes, mock_places):
    mock_places.return_value = MockPlacesProvider()
    mock_routes.return_value = MockRoutesProvider()
    
    candidates = search_recovery_candidates(17.3, 78.4, {"categories": ["Museum"], "budget": "Low"})
    assert len(candidates) == 2
    assert candidates[0]["travel_minutes"] == 15
    assert candidates[0]["why_recommended"] is not None
