import pytest
from unittest.mock import patch, MagicMock
from app.services.llm import classify_disruption_text, parse_user_preferences, determine_recovery_strategy
from app.schemas.llm import DisruptionClassification, UserRecoveryPreference, RecoveryStrategy

def test_missing_api_key_fallback():
    # When groq_client is None, it should gracefully fallback
    with patch("app.services.llm.groq_client", None):
        res = classify_disruption_text("Beach closed", "Trip context")
        assert res.type == "WEATHER_DISRUPTION"
        assert res.reason == "Fallback deterministic classification"
        
        pref = parse_user_preferences("peaceful and cheap")
        assert pref.budget == "Low"
        
        strat = determine_recovery_strategy("facts")
        assert strat.strategy == "ASK_USER"

@patch("app.services.llm.groq_client")
def test_groq_success(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"type": "WEATHER_DISRUPTION", "severity": "HIGH", "affected_stop_id": "stop-4", "reason": "Rain", "confidence": 0.9}'
    mock_client.chat.completions.create.return_value = mock_response
    
    res = classify_disruption_text("Rain", "Context")
    assert res.type == "WEATHER_DISRUPTION"
    assert res.reason == "Rain"

@patch("app.services.llm.groq_client")
def test_groq_failure_fallback(mock_client):
    mock_client.chat.completions.create.side_effect = Exception("API Down")
    
    res = classify_disruption_text("Rain", "Context")
    assert res.type == "WEATHER_DISRUPTION"
    assert res.reason == "Fallback deterministic classification"
