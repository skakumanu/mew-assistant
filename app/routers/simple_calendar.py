"""
Simple Google Calendar integration
Uses stored OAuth tokens to fetch calendar events
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import logging

from ..database.connection import get_db
from ..database.models import FederatedIdentity
from ..utils.auth import get_current_user
from ..utils.config import settings
from ..utils.log_sanitizer import sanitize_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simple-calendar", tags=["Simple Calendar"])


@router.get("/events")
async def get_calendar_events(
    max_results: int = 10,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming Google Calendar events for the current user.
    
    Simple endpoint that:
    1. Gets user's stored Google OAuth token
    2. Calls Google Calendar API
    3. Returns events
    """
    
    # Find user's Google OAuth tokens
    fed_identity = db.query(FederatedIdentity).filter(
        FederatedIdentity.user_id == current_user.id,
        FederatedIdentity.provider == 'google'
    ).first()
    
    if not fed_identity:
        raise HTTPException(
            status_code=400,
            detail="Google account not connected. Please sign in with Google first."
        )
    
    if not fed_identity.access_token:
        raise HTTPException(
            status_code=400,
            detail="No Google access token found. Please sign in again."
        )
    
    # Function to refresh Google token if needed
    async def refresh_google_token():
        if not fed_identity.refresh_token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'client_id': settings.GOOGLE_CLIENT_ID,
                        'client_secret': settings.GOOGLE_CLIENT_SECRET,
                        'refresh_token': fed_identity.refresh_token,
                        'grant_type': 'refresh_token'
                    }
                )
                
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    fed_identity.access_token = token_data['access_token']
                    db.commit()
                    logger.info(f"Refreshed Google token for user {sanitize_user_id(current_user.id)}")
                    return True
                else:
                    logger.error(f"Token refresh failed: {token_response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False
    
    # Call Google Calendar API
    try:
        from datetime import datetime, timezone
        
        # Get current time in RFC3339 format (required for timeMin with orderBy)
        time_min = datetime.now(timezone.utc).isoformat()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                params={
                    'maxResults': max_results,
                    'orderBy': 'startTime',
                    'singleEvents': True,
                    'timeMin': time_min  # Required when using orderBy=startTime
                },
                headers={'Authorization': f'Bearer {fed_identity.access_token}'}
            )
            
            # If token expired, try to refresh and retry once
            if response.status_code == 401:
                logger.info(f"Google token expired for user {sanitize_user_id(current_user.id)}, attempting refresh...")
                if await refresh_google_token():
                    # Retry with new token
                    response = await client.get(
                        'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                        params={
                            'maxResults': max_results,
                            'orderBy': 'startTime',
                            'singleEvents': True,
                            'timeMin': time_min  # Use same timeMin
                        },
                        headers={'Authorization': f'Bearer {fed_identity.access_token}'}
                    )
                else:
                    raise HTTPException(
                        status_code=401,
                        detail="Google token expired and refresh failed. Please sign in again."
                    )
            
            if response.status_code != 200:
                logger.error(f"Google Calendar API error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get calendar events: {response.text}"
                )
            
            events_data = response.json()
            
            # Simplify the response
            simplified_events = []
            for event in events_data.get('items', []):
                simplified_events.append({
                    'id': event.get('id'),
                    'summary': event.get('summary', 'No title'),
                    'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                    'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'link': event.get('htmlLink')
                })
            
            return {
                'success': True,
                'count': len(simplified_events),
                'events': simplified_events
            }
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling Google Calendar: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error connecting to Google Calendar: {str(e)}"
        )
