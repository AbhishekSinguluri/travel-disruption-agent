import logging
from typing import List, Dict, Any, Optional
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

import sqlite3
import json

class GmailConnectionRepository:
    def __init__(self, db_path: str = "trips.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS gmail_connections (
                        user_id TEXT PRIMARY KEY,
                        creds_json TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init gmail_connections table: {e}")

    def save_credentials(self, user_id: str, creds_dict: dict):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO gmail_connections (user_id, creds_json) VALUES (?, ?)",
                    (user_id, json.dumps(creds_dict))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save gmail credentials: {e}")

    def get_credentials(self, user_id: str) -> Optional[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT creds_json FROM gmail_connections WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            logger.error(f"Failed to get gmail credentials: {e}")
        return None

    def delete_credentials(self, user_id: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM gmail_connections WHERE user_id = ?", (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to delete gmail credentials: {e}")

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
                "date": "Mon, 01 Oct 2026 10:00:00 +0000",
                "from": "Air India Reservations <reservations@airindia.in>"
            }
        ]

    def get_message(self, message_id: str) -> Dict[str, Any]:
        return {
            "id": message_id,
            "date": "Mon, 01 Oct 2026 10:00:00 +0000",
            "from": "Air India Reservations <reservations@airindia.in>",
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
            msg_detail = self.service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'Date', 'From']).execute()
            headers = msg_detail.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            from_val = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            parsed_msgs.append({
                "id": msg['id'],
                "threadId": msg['threadId'],
                "snippet": msg_detail.get('snippet', ''),
                "subject": subject,
                "date": date,
                "from": from_val
            })
        return parsed_msgs

    def get_message(self, message_id: str) -> Dict[str, Any]:
        msg = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        date_val = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        from_val = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        
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
            "body": body,
            "date": date_val,
            "from": from_val
        }

def get_gmail_provider(user_id: Optional[str] = None) -> GmailProvider:
    if os.getenv("GOOGLE_CLIENT_ID") and user_id:
        try:
            return RealGmailProvider(user_id)
        except ValueError:
            pass
    return MockGmailProvider()
