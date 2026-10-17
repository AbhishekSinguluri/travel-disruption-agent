import os
import logging
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
from pydantic import BaseModel

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class User(BaseModel):
    id: str
    email: str
    is_demo: bool = False

from typing import Any
def get_supabase_client() -> Any | None:
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if SUPABASE_AVAILABLE and sb_url and sb_key and sb_url != "your_supabase_url_here":
        try:
            return create_client(sb_url, sb_key)
        except ImportError:
            pass
    return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    client = get_supabase_client()
    
    if not client:
        # Demo mode bypass
        logger.info("[AUTH] Using Demo Mode user bypass")
        return User(id="demo-user", email="demo@example.com", is_demo=True)
        
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
        
    try:
        # Validate JWT using the client
        res = client.auth.get_user(credentials.credentials)
        if not res or not res.user:
            raise HTTPException(status_code=401, detail="Invalid authorization token")
        return User(id=res.user.id, email=res.user.email)
    except Exception as e:
        logger.error(f"[AUTH ERROR] {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
