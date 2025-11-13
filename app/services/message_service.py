"""
Message service layer for multi-channel ingestion.
Handles email, SMS, and WhatsApp message processing.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from ..database.models import Message as MessageModel, ChannelType
from ..schemas.message import MessageIngest


class MessageService:
    """Service class for message ingestion and processing."""
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def ingest_message(self, message_data: MessageIngest) -> MessageModel:
        """
        Ingest a message from any supported channel.
        
        Args:
            message_data: Message ingestion data
            
        Returns:
            Created message object
            
        Example:
            >>> service = MessageService(db)
            >>> message = service.ingest_message(message_data)
        """
        db_message = MessageModel(
            channel=message_data.channel,
            sender=message_data.sender,
            recipient=message_data.recipient,
            subject=message_data.subject,
            body=message_data.body,
            raw_content=message_data.raw_content,
            session_id=message_data.session_id,
            received_at=message_data.received_at or datetime.utcnow(),
            processed=False
        )
        
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        
        return db_message
    
    def ingest_batch(self, messages: List[MessageIngest]) -> List[MessageModel]:
        """
        Ingest multiple messages in a batch.
        
        Args:
            messages: List of message data
            
        Returns:
            List of created message objects
        """
        db_messages = []
        
        for message_data in messages:
            db_message = MessageModel(
                channel=message_data.channel,
                sender=message_data.sender,
                recipient=message_data.recipient,
                subject=message_data.subject,
                body=message_data.body,
                raw_content=message_data.raw_content,
                session_id=message_data.session_id,
                received_at=message_data.received_at or datetime.utcnow(),
                processed=False
            )
            db_messages.append(db_message)
        
        self.db.add_all(db_messages)
        self.db.commit()
        
        for msg in db_messages:
            self.db.refresh(msg)
        
        return db_messages
    
    def mark_processed(self, message_id: int) -> MessageModel:
        """
        Mark a message as processed.
        
        Args:
            message_id: Message ID to mark
            
        Returns:
            Updated message object
        """
        message = self.db.query(MessageModel).filter(
            MessageModel.id == message_id
        ).first()
        
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        message.processed = True
        message.processed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_unprocessed_messages(
        self,
        channel: Optional[ChannelType] = None,
        limit: int = 100
    ) -> List[MessageModel]:
        """
        Get unprocessed messages with optional channel filter.
        
        Args:
            channel: Optional channel filter
            limit: Maximum number of messages to return
            
        Returns:
            List of unprocessed messages
        """
        query = self.db.query(MessageModel).filter(
            MessageModel.processed == False
        )
        
        if channel:
            query = query.filter(MessageModel.channel == channel)
        
        return query.order_by(MessageModel.received_at.asc()).limit(limit).all()
    
    def get_session_messages(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[MessageModel]:
        """
        Get all messages for a specific session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        return self.db.query(MessageModel).filter(
            MessageModel.session_id == session_id
        ).order_by(MessageModel.received_at.asc()).limit(limit).all()
    
    def get_user_messages(
        self,
        sender: str,
        channel: Optional[ChannelType] = None,
        limit: int = 100
    ) -> List[MessageModel]:
        """
        Get messages from a specific sender.
        
        Args:
            sender: Sender identifier
            channel: Optional channel filter
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        query = self.db.query(MessageModel).filter(
            MessageModel.sender == sender
        )
        
        if channel:
            query = query.filter(MessageModel.channel == channel)
        
        return query.order_by(MessageModel.received_at.desc()).limit(limit).all()
