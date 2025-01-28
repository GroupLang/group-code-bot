"""Message processing and routing logic."""

from typing import Dict, Type, Optional
from loguru import logger

from .base_handler import BaseHandler
from .message_types import BaseMessage, CommandMessage, GitHubIssue
from .context import MessageContext
from utils.errors import ValidationError, TelegramError, handle_error
from utils.errors import error_context

class MessageProcessor:
    """Routes and processes messages to appropriate handlers."""
    
    def __init__(self):
        self.handlers: Dict[Type[BaseMessage], BaseHandler] = {}

    def register_handler(self, message_type: Type[BaseMessage], handler: BaseHandler) -> None:
        """Register a handler for a message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler instance
        """
        self.handlers[message_type] = handler

    def get_message_type(self, message: Dict) -> Optional[Type[BaseMessage]]:
        """Determine message type from raw message.
        
        Args:
            message: Raw message dictionary
            
        Returns:
            Message type class or None if unknown
        """
        if 'text' in message:
            text = message['text']
            if text.startswith('/'):
                return CommandMessage
            elif '@group_write_bot' in text.lower():
                return CodeRequest
            elif 'github.com' in text.lower():
                return GitHubIssue
            elif text.startswith('@'):
                return ProviderMessage
        return BaseMessage

    async def process_message(self, message: Dict) -> None:
        """Process and route a message to appropriate handler.
        
        Args:
            message: Raw message dictionary
            
        Raises:
            ValidationError: If message validation fails
            TelegramError: If handler processing fails
        """
        with error_context(ValidationError, "Message processing failed"):
            # Determine message type
            message_type = self.get_message_type(message)
            if not message_type:
                logger.warning(f"Unknown message type: {message}")
                return

            # Get appropriate handler
            handler = self.handlers.get(message_type)
            if not handler:
                logger.warning(f"No handler for message type: {message_type}")
                return

            # Validate message
            validated_message = handler.validate_message(message)
            
            # Create context
            context = handler.create_context(validated_message)
            
            # Handle message
            try:
                await handler.handle(validated_message, context)
            except Exception as e:
                handle_error(TelegramError, f"Handler failed: {str(e)}")
