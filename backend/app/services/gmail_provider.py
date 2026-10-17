import logging
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
        payload = msg.get('payload', {})
        body = ""
        import base64
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
            
        if not body:
            body = msg.get('snippet', '')
            
        return {
            "id": message_id,
            "body": body
        }

def get_gmail_provider(user_id: Optional[str] = None) -> GmailProvider:
    if os.getenv("GOOGLE_CLIENT_ID") and user_id:
        try:
            return RealGmailProvider(user_id)
        except ValueError:
            pass
    return MockGmailProvider()
