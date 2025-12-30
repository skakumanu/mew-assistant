"""
Message service for handling incoming messages from multiple channels.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.database.models import Message
from app.integrations import AIIntegration
from app.schemas.message import MessageBatchIngest, MessageIngest
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MessageService:
    """Service for processing incoming messages."""

    def __init__(self, db: Session):
        self.db = db
        self.ai_integration = AIIntegration()

    def ingest_message(self, message_data: MessageIngest) -> Message:
        """
        Ingest a new message and store in database.

        Args:
            message_data: MessageIngest schema with message details

        Returns:
            Message: Created message record
        """
        message = Message(
            channel=message_data.channel.value,
            sender=message_data.sender,
            recipient=message_data.recipient,
            subject=message_data.subject,
            body=message_data.body,
            raw_content=message_data.raw_content,
            session_id=message_data.session_id,
            received_at=message_data.received_at or datetime.utcnow(),
            processed=False,
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        logger.info(f"Ingested message {message.id} from {message_data.sender} via {message_data.channel}")
        return message

    def ingest_batch(self, batch_data: MessageBatchIngest) -> List[Message]:
        """
        Ingest multiple messages in batch.

        Args:
            batch_data: MessageBatchIngest with list of messages

        Returns:
            List[Message]: Created message records
        """
        messages = []
        # Accept either a MessageBatchIngest object or a raw list passed by router
        items = getattr(batch_data, "messages", None) or batch_data
        for msg_data in items:
            # msg_data may be a dict-like (from test client) or a MessageIngest model
            try:
                message = self.ingest_message(msg_data)
            except Exception:
                # If ingest_message expects a MessageIngest, attempt construction
                from app.schemas.message import MessageIngest as MI

                message = self.ingest_message(MI.model_validate(msg_data))
            messages.append(message)

        return messages

    async def process_incoming_message(
        self,
        source: str,
        from_contact: str,
        message_body: str,
        message_id: str,
        profile_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process an incoming message from any channel.

        Args:
            source: Message source (sms, whatsapp, email)
            from_contact: Contact identifier (phone/email)
            message_body: Message content
            message_id: Message identifier
            profile_name: Optional sender name

        Returns:
            Dict with reply and processing info
        """
        try:
            logger.info(f"Processing {source} message from {from_contact}")

            # Analyze message intent
            analysis = await self.ai_integration.analyze_message(
                message=message_body,
                context=f"Source: {source}, From: {profile_name or from_contact}",
            )

            intent = "unknown"
            if analysis.get("success") and analysis.get("analysis"):
                intent = analysis["analysis"].get("intent", "unknown")

            # Route based on intent
            if intent == "schedule":
                reply = await self._handle_schedule_request(message_body)
            elif intent == "reminder":
                reply = await self._handle_reminder_request(message_body)
            elif intent == "question":
                reply = await self._handle_question(message_body)
            elif intent == "report":
                reply = await self._handle_report_request(message_body)
            else:
                reply = await self._handle_general_message(message_body)

            return {
                "success": True,
                "reply": reply,
                "intent": intent,
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "success": False,
                "reply": "Sorry, I encountered an error processing your message. Please try again.",
                "error": str(e),
            }

    async def _handle_schedule_request(self, message: str) -> str:
        """Handle scheduling requests."""
        return "I'll help you schedule that. Please provide the date, time, and activity details."

    async def _handle_reminder_request(self, message: str) -> str:
        """Handle reminder requests."""
        return "I'll set up a reminder for you. When would you like to be reminded?"

    async def _handle_question(self, message: str) -> str:
        """Handle questions using AI."""
        response = await self.ai_integration.generate_response(message)
        if response.get("success"):
            return response.get("text", "I'm here to help!")
        return "I'm here to help! Could you please rephrase your question?"

    async def _handle_report_request(self, message: str) -> str:
        """Handle report/summary requests."""
        return "I'll generate a report for you. What time period would you like covered?"

    async def _handle_general_message(self, message: str) -> str:
        """Handle general messages."""
        response = await self.ai_integration.generate_response(message=message, conversation_history=[])
        if response.get("success"):
            return response.get("text", "Thanks for your message!")
        return "Thanks for your message! How can I assist you today?"

    def get_unprocessed_messages(self, channel_filter=None, limit: int = 100):
        """Return unprocessed messages, optionally filtered by channel."""
        query = self.db.query(Message).filter(Message.processed.is_(False))
        if channel_filter is not None:
            # channel_filter may be an Enum or string; compare by value/name
            try:
                query = query.filter(Message.channel == channel_filter)
            except Exception:
                query = query.filter(Message.channel == str(channel_filter))
        messages = query.order_by(Message.received_at).limit(limit).all()
        return messages

    def get_session_messages(self, session_id: int, limit: int = 100):
        """Return messages for a given session id."""
        sid = str(session_id)
        messages = (
            self.db.query(Message).filter(Message.session_id == sid).order_by(Message.received_at).limit(limit).all()
        )
        return messages

    def get_user_messages(self, sender: str, channel_filter=None, limit: int = 100):
        """Return messages from a specific sender, optionally filtered by channel."""
        query = self.db.query(Message).filter(Message.sender == sender)
        if channel_filter is not None:
            try:
                query = query.filter(Message.channel == channel_filter)
            except Exception:
                query = query.filter(Message.channel == str(channel_filter))
        return query.order_by(Message.received_at).limit(limit).all()

    def mark_processed(self, message_id: int):
        """Mark a message as processed and return the updated record."""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message is None:
            raise ValueError(f"Message with id {message_id} not found")
        message.processed = True
        from datetime import datetime

        message.processed_at = datetime.utcnow()
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
