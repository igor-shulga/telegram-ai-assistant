"""
Google Services integration: Drive (knowledge base), Calendar, Gmail.
Uses OAuth2 refresh token — no browser interaction needed after setup.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def get_credentials() -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return creds


# ─── GOOGLE CALENDAR ──────────────────────────────────────────────────────────

def get_calendar_events(days_ahead: int = 1) -> str:
    """Get calendar events for the next N days."""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return "No events found."

        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", ""))
            title = e.get("summary", "No title")
            # Format time nicely
            if "T" in start:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                time_str = dt.strftime("%d.%m %H:%M")
            else:
                time_str = start
            lines.append(f"- {time_str}: {title}")

        return "\n".join(lines)
    except HttpError as e:
        logger.error("Calendar error: %s", e)
        return f"Calendar error: {e}"


def create_calendar_event(title: str, start_iso: str, duration_minutes: int = 60) -> str:
    """Create a calendar event."""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        start = datetime.fromisoformat(start_iso)
        end = start + timedelta(minutes=duration_minutes)

        event = {
            "summary": title,
            "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Kyiv"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Kyiv"},
        }

        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"Event created: {created.get('htmlLink', 'done')}"
    except HttpError as e:
        logger.error("Calendar create error: %s", e)
        return f"Error: {e}"


# ─── GMAIL ────────────────────────────────────────────────────────────────────

def get_recent_emails(query: str = "", max_results: int = 5) -> str:
    """Get recent emails, optionally filtered by query."""
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)

        q = query if query else "is:unread"
        result = service.users().messages().list(
            userId="me", q=q, maxResults=max_results
        ).execute()

        messages = result.get("messages", [])
        if not messages:
            return "No emails found."

        lines = []
        for msg in messages:
            m = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "No subject")
            sender = headers.get("From", "Unknown")
            date = headers.get("Date", "")[:16]
            snippet = m.get("snippet", "")[:100]

            lines.append(f"- [{date}] {sender[:30]}: {subject}\n  {snippet}")

        return "\n\n".join(lines)
    except HttpError as e:
        logger.error("Gmail error: %s", e)
        return f"Gmail error: {e}"


# ─── GOOGLE DRIVE ─────────────────────────────────────────────────────────────

def list_drive_files(folder_name: str = "my-brain") -> list[dict]:
    """List MD files in a Drive folder."""
    try:
        creds = get_credentials()
        service = build("drive", "v3", credentials=creds)

        # Find the folder
        folders = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)"
        ).execute()

        if not folders.get("files"):
            logger.warning("Drive folder '%s' not found", folder_name)
            return []

        folder_id = folders["files"][0]["id"]

        # List MD files in the folder
        files = service.files().list(
            q=f"'{folder_id}' in parents and name contains '.md' and trashed=false",
            fields="files(id, name, description)"
        ).execute()

        return files.get("files", [])
    except HttpError as e:
        logger.error("Drive list error: %s", e)
        return []


def read_drive_file(file_id: str) -> str:
    """Read content of a Drive file."""
    try:
        creds = get_credentials()
        service = build("drive", "v3", credentials=creds)
        content = service.files().get_media(fileId=file_id).execute()
        return content.decode("utf-8") if isinstance(content, bytes) else content
    except HttpError as e:
        logger.error("Drive read error: %s", e)
        return ""
