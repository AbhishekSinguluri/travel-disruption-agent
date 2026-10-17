import os
import pytest
from unittest import mock

import sys
import dotenv

# Mock it globally in sys.modules so even `from dotenv import load_dotenv` gets mocked
class MockDotenv:
    def load_dotenv(*args, **kwargs):
        pass
sys.modules['dotenv'] = MockDotenv()

keys_to_remove = [
    "GROQ_API_KEY",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_OAUTH_REDIRECT_URI",
    "GMAIL_SCOPES",
    "OPENWEATHER_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "GOOGLE_PLACES_API_KEY"
]

@pytest.fixture(autouse=True)
def clear_env_vars():
    # Store originals
    originals = {k: os.environ.get(k) for k in keys_to_remove}
    
    # Clear for test
    for key in keys_to_remove:
        os.environ[key] = ""
        
    yield
    
    # Restore
    for key in keys_to_remove:
        if originals[key] is not None:
            os.environ[key] = originals[key]
        else:
            os.environ.pop(key, None)
