"""Base handler class for bot message processing."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .context import MessageContext
from .message_types import BaseMessage
from utils.errors import ValidationError, TelegramError

class BaseHandler(ABC):
    """Abstract base class for message handlers."""

    @abstractmethod
    async def handle(self, message: BaseMessage, context: MessageContext) -> None:
        """Handle a message with context.
        
        Args:
            message: Validated message object
            context: Message processing context
            
        Raises:
            ValidationError: If message validation fails
            TelegramError: If Telegram API interaction fails
        """
        pass

    def validate_message(self, message: Dict[str, Any]) -> BaseMessage:
        """Validate raw message data into typed message object.
        
        Args:
            message: Raw message dictionary
            
        Returns:
            BaseMessage: Validated message object
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            return BaseMessage.parse_obj(message)
        except Exception as e:
            raise ValidationError(f"Message validation failed: {str(e)}")

    def create_context(self, message: BaseMessage) -> MessageContext:
        """Create message context from validated message.
        
        Args:
            message: Validated message object
            
        Returns:
            MessageContext: New context object
        """
        return MessageContext(
            chat_id=message.chat.id,
            user_id=message.from_user.id if message.from_user else None,
            message_id=message.message_id
        )
