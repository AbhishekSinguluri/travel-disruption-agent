from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
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

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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
        raise HTTPException(status_code=500, detail="Google OAuth is not configured. Missing CLIENT_ID or CLIENT_SECRET.")
        
    state = secrets.token_urlsafe(32)
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=state,
        prompt='consent',
        login_hint=user.email
    )
    
    oauth_states[state] = {
        "user_id": user.id,
        "code_verifier": getattr(flow, "code_verifier", None)
    }
    
    return RedirectResponse(url=authorization_url)

@router.get("/callback")
async def gmail_callback(request: Request, state: str, code: str):
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")
        
    state_data = oauth_states.pop(state)
    user_id = state_data["user_id"]
    code_verifier = state_data["code_verifier"]
    
    flow = get_flow()
    if not flow:
        raise HTTPException(status_code=500, detail="OAuth not configured")
        
    if code_verifier:
        flow.code_verifier = code_verifier
        
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

@router.get("/status")
async def gmail_status(user: User = Depends(get_current_user)):
    repo = GmailConnectionRepository()
    creds = repo.get_credentials(user.id)
    if not creds:
        return {"connected": False, "email": None, "provider": "none"}
    
    try:
        provider = get_gmail_provider(user.id)
        profile = provider.connect()
        email = profile.get("email")
        if email:
            # Mask the email, e.g. a***************@gmail.com
            parts = email.split("@")
            if len(parts) == 2:
                masked = parts[0][0] + "*" * (len(parts[0]) - 1) + "@" + parts[1]
                return {"connected": True, "email": masked, "provider": "google"}
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        
    return {"connected": True, "email": "Unknown (Connected)", "provider": "google"}

@router.get("/search")
async def search_gmail(query: str = "", user: User = Depends(get_current_user)):
    provider = get_gmail_provider(user.id)
    return provider.search_messages(query)
