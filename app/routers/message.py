"""
Message ingestion router.
Handles /mew/ingest for multi-channel message ingestion.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.message import (
    ChannelType,
    MessageBatchIngest,
    MessageIngest,
    MessageResponse,
)
from ..services.message_service import MessageService
from ..utils.logger import get_logger
from ..utils.privacy import privacy_guardrails

router = APIRouter(prefix="/mew", tags=["messages"])
logger = get_logger(__name__)


@router.post(
    "/ingest", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def ingest_message(message_data: MessageIngest, db: Session = Depends(get_db)):
    """
    Ingest a message from any supported channel (email, SMS, WhatsApp).

    **Privacy Protection**: All messages are automatically scanned for PII.
    Detected PII is logged but not blocked to preserve user experience.

    **Supported Channels**:
    - email: Email messages with subject and body
    - sms: Text messages from phone numbers
    - whatsapp: WhatsApp messages
    - web: Web form submissions

    **Example Request (Email)**:
    ```json
    {
        "channel": "email",
        "sender": "parent@example.com",
        "recipient": "mew@assistant.com",
        "subject": "Need tutoring help",
        "body": "My child needs help with math homework.",
        "session_id": null
    }
    ```

    **Example Request (SMS)**:
    ```json
    {
        "channel": "sms",
        "sender": "+1234567890",
        "body": "Can we schedule a session for tomorrow?",
        "session_id": 42
    }
    ```
    """
    service = MessageService(db)

    try:
        # Privacy scan for informational purposes
        message_dict = message_data.model_dump()
        privacy_scan = privacy_guardrails.scan_and_protect(
            message_dict, anonymize=False
        )

        if privacy_scan["pii_detected"]:
            logger.info(
                f"PII detected in message from {message_data.sender}: {privacy_scan['findings']}"
            )

        message = service.ingest_message(message_data)
        return MessageResponse.model_validate(message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/ingest/batch",
    response_model=List[MessageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def ingest_batch(batch_data: MessageBatchIngest, db: Session = Depends(get_db)):
    """
    Ingest multiple messages in a single request.

    **Batch Size**: Maximum 100 messages per request.

    **Example Request**:
    ```json
    {
        "messages": [
            {
                "channel": "email",
                "sender": "parent1@example.com",
                "body": "Need scheduling help"
            },
            {
                "channel": "sms",
                "sender": "+1234567890",
                "body": "Thank you!"
            }
        ]
    }
    ```
    """
    service = MessageService(db)

    try:
        messages = service.ingest_batch(batch_data.messages)
        return [MessageResponse.model_validate(msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/message/{message_id}/processed", response_model=MessageResponse)
async def mark_message_processed(message_id: int, db: Session = Depends(get_db)):
    """
    Mark a message as processed.

    **Use Case**: After successfully handling a message, mark it as processed
    to avoid duplicate processing.
    """
    service = MessageService(db)

    try:
        message = service.mark_processed(message_id)
        return MessageResponse.model_validate(message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/messages/unprocessed", response_model=List[MessageResponse])
async def get_unprocessed_messages(
    channel: Optional[str] = None, limit: int = 100, db: Session = Depends(get_db)
):
    """
    Get unprocessed messages for background processing.

    **Query Parameters**:
    - channel: Filter by channel (optional)
    - limit: Maximum results (default: 100)
    """
    service = MessageService(db)

    # Convert channel string to enum if provided
    channel_filter = None
    if channel:
        try:
            channel_filter = ChannelType[channel.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")

    messages = service.get_unprocessed_messages(channel_filter, limit)
    return [MessageResponse.model_validate(msg) for msg in messages]


@router.get("/messages/session/{session_id}", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: int, limit: int = 100, db: Session = Depends(get_db)
):
    """
    Get all messages for a specific session.

    **Use Case**: View conversation history for a session across all channels.
    """
    service = MessageService(db)
    messages = service.get_session_messages(session_id, limit)
    return [MessageResponse.model_validate(msg) for msg in messages]


@router.get("/messages/user/{sender}", response_model=List[MessageResponse])
async def get_user_messages(
    sender: str,
    channel: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all messages from a specific sender.

    **Query Parameters**:
    - sender: Email address, phone number, or user identifier
    - channel: Filter by channel (optional)
    - limit: Maximum results (default: 100)
    """
    service = MessageService(db)

    channel_filter = None
    if channel:
        try:
            channel_filter = ChannelType[channel.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")

    messages = service.get_user_messages(sender, channel_filter, limit)
    return [MessageResponse.model_validate(msg) for msg in messages]
