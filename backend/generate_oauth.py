import os

def update_env_example():
    path = ".env.example"
    content = ""
    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read()
            
    additions = """
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/gmail/callback
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly
"""
    if "GOOGLE_CLIENT_ID" not in content:
        with open(path, "a") as f:
            f.write(additions)

def update_gmail_api():
    path = "app/api/gmail.py"
    code = """from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from app.services.gmail_provider import get_gmail_provider, GmailConnectionRepository
from app.api.auth import get_current_user, User
import os
import secrets
import logging
from google_auth_oauthlib.flow import Flow

router = APIRouter()
logger = logging.getLogger(__name__)

CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS_FILE") # Or build from env
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")
SCOPES = os.getenv("GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.readonly").split(",")

# In-memory state store for OAuth (use Redis/DB in prod)
oauth_states = {}

def get_flow():
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    return Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

@router.get("/connect")
async def connect_gmail(user: User = Depends(get_current_user)):
    flow = get_flow()
    if not flow:
        # Fallback to mock behavior
        provider = get_gmail_provider()
        return provider.connect()
        
    state = secrets.token_urlsafe(32)
    oauth_states[state] = user.id
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
        prompt='consent',
        login_hint=user.email
    )
    return RedirectResponse(url=authorization_url)

@router.get("/callback")
async def gmail_callback(request: Request, state: str, code: str):
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")
        
    user_id = oauth_states.pop(state)
    flow = get_flow()
    if not flow:
        raise HTTPException(status_code=500, detail="OAuth not configured")
        
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    repo = GmailConnectionRepository()
    repo.save_credentials(user_id, {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    })
    
    # Redirect back to frontend
    return RedirectResponse(url="http://localhost:5173/?view=TRIPS")

@router.post("/disconnect")
async def disconnect_gmail(user: User = Depends(get_current_user)):
    repo = GmailConnectionRepository()
    repo.delete_credentials(user.id)
    return {"status": "disconnected"}

@router.get("/search")
async def search_gmail(query: str = "", user: User = Depends(get_current_user)):
    provider = get_gmail_provider(user.id)
    return provider.search_messages(query)
"""
    with open(path, "w") as f:
        f.write(code)

def update_gmail_provider():
    path = "app/services/gmail_provider.py"
    code = """import logging
from typing import List, Dict, Any, Optional
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Temporary in-memory repo, replace with DB implementation in repositories.py
class GmailConnectionRepository:
    _store = {}
    def save_credentials(self, user_id: str, creds_dict: dict):
        self._store[user_id] = creds_dict
    def get_credentials(self, user_id: str) -> Optional[dict]:
        return self._store.get(user_id)
    def delete_credentials(self, user_id: str):
        if user_id in self._store:
            del self._store[user_id]

class GmailProvider:
    def connect(self): ...
    def search_messages(self, query: str, days: int = 5) -> List[Dict[str, Any]]: ...
    def get_message(self, message_id: str) -> Dict[str, Any]: ...

class MockGmailProvider(GmailProvider):
    def connect(self):
        logger.info("[MOCK] Connected to Gmail")
        return {"status": "connected", "email": "demo@example.com"}
        
    def search_messages(self, query: str, days: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"[MOCK] Searching Gmail for '{query}' in last {days} days")
        return [
            {
                "id": "msg-mock-1",
                "threadId": "thread-mock-1",
                "snippet": "Your Air India AI 123 flight booking from Hyderabad to Delhi is confirmed.",
                "subject": "Booking Confirmation: Air India AI 123",
                "date": "2026-10-01T10:00:00Z"
            }
        ]

    def get_message(self, message_id: str) -> Dict[str, Any]:
        return {
            "id": message_id,
            "body": "Your Air India AI 123 flight originally scheduled for 09:20 has been delayed. The new departure time is 11:10."
        }

class RealGmailProvider(GmailProvider):
    def __init__(self, user_id: str):
        self.user_id = user_id
        repo = GmailConnectionRepository()
        creds_data = repo.get_credentials(user_id)
        if not creds_data:
            raise ValueError("No credentials found for user")
        
        self.creds = Credentials(**creds_data)
        self.service = build('gmail', 'v1', credentials=self.creds)
        
    def connect(self):
        profile = self.service.users().getProfile(userId='me').execute()
        return {"status": "connected", "email": profile.get("emailAddress")}
        
    def search_messages(self, query: str, days: int = 5) -> List[Dict[str, Any]]:
        q = f"{query} newer_than:{days}d"
        results = self.service.users().messages().list(userId='me', q=q).execute()
        messages = results.get('messages', [])
        
        parsed_msgs = []
        for msg in messages[:10]: # Limit to 10 for safety
            msg_detail = self.service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
            headers = msg_detail.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            parsed_msgs.append({
                "id": msg['id'],
                "threadId": msg['threadId'],
                "snippet": msg_detail.get('snippet', ''),
                "subject": subject,
                "date": date
            })
        return parsed_msgs

    def get_message(self, message_id: str) -> Dict[str, Any]:
        msg = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
        return {
            "id": message_id,
            "body": msg.get('snippet', '') # simplified for this demo
        }

def get_gmail_provider(user_id: Optional[str] = None) -> GmailProvider:
    if os.getenv("GOOGLE_CLIENT_ID") and user_id:
        try:
            return RealGmailProvider(user_id)
        except ValueError:
            pass
    return MockGmailProvider()
"""
    with open(path, "w") as f:
        f.write(code)

if __name__ == "__main__":
    update_env_example()
    update_gmail_api()
    update_gmail_provider()
    print("Code written.")
