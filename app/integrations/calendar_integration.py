"""
Google Calendar integration for scheduling.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CalendarProvider(str, Enum):
    """Supported calendar providers"""
    GOOGLE = "google"
    APPLE = "apple"
    OUTLOOK = "outlook"


class CalendarIntegration:
    """Google Calendar integration."""

    def __init__(self):
        self.credentials_file = getattr(settings, 'GOOGLE_CREDENTIALS_FILE', '')
        self.calendar_id = getattr(settings, 'GOOGLE_CALENDAR_ID', 'primary')
        self.service = None
        
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Calendar service."""
        try:
            import os.path
            if self.credentials_file and os.path.exists(self.credentials_file):
                from google.oauth2 import service_account
                from googleapiclient.discovery import build

                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                self.service = build('calendar', 'v3', credentials=credentials)
                logger.info("Google Calendar initialized")
            else:
                logger.warning("Google Calendar credentials not configured")

        except ImportError:
            logger.warning("Google Calendar packages not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Calendar: {str(e)}")

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a calendar event."""
        if not self.service:
            return {"success": False, "message": "Calendar not configured"}

        try:
            event = {
                'summary': title,
                'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},
                        {'method': 'email', 'minutes': 60},
                    ],
                },
            }

            if description:
                event['description'] = description
            if location:
                event['location'] = location

            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()

            logger.info(f"Calendar event created: {created_event.get('id')}")

            return {
                "success": True,
                "event_id": created_event.get('id'),
                "event_link": created_event.get('htmlLink'),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to create event: {str(e)}")
            return {"success": False, "message": f"Failed to create event: {str(e)}"}

    async def list_upcoming_events(
        self, days: int = 7, max_results: int = 10
    ) -> Dict[str, Any]:
        """List upcoming calendar events."""
        if not self.service:
            return {"success": False, "message": "Calendar not configured"}

        try:
            now = datetime.utcnow()
            end_date = now + timedelta(days=days)

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            parsed_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                parsed_events.append({
                    'id': event.get('id'),
                    'title': event.get('summary'),
                    'start': start,
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'description': event.get('description', ''),
                    'link': event.get('htmlLink'),
                })

            logger.info(f"Retrieved {len(parsed_events)} events")

            return {
                "success": True,
                "events": parsed_events,
                "count": len(parsed_events),
            }

        except Exception as e:
            logger.error(f"Failed to list events: {str(e)}")
            return {"success": False, "message": f"Failed to list events: {str(e)}"}
