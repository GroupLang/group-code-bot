"""Message handling implementation for the GroupCode bot."""

from typing import Dict, Any, Optional, Type
from datetime import datetime
import re
from loguru import logger

from .messages import (
    WELCOME_MESSAGE,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    PROVIDER_MESSAGES,
    GITHUB_MESSAGES,
    COMMAND_USAGE,
    MessageCategory,
    Emoji
)

from services.client import AgentMarketClient
from services.request_tracker import RequestTracker
from utils.telegram_utils import send_message
from utils.errors import (
    TelegramError, 
    ValidationError,
    error_handler,
    error_context
)
from .base_handler import BaseHandler
from .message_types import BaseMessage, TextMessage, NewChatMemberMessage
from .context import MessageContext
from .github import handle_github_issue_link
from .provider import parse_provider_mention, send_message_to_provider
from .initialization import set_bot_commands

BOT_MENTION_PATTERN = r'@group_code_bot\s+(.*)'

class MessageHandler(BaseHandler):
    """Handles processing of different message types."""

    @error_handler(TelegramError)
    def get_reaction_message(self, message_reaction: Dict[str, Any]) -> Dict[str, Any]:
        """Format a reaction update into a storable message format.
        
        Args:
            message_reaction: Raw reaction update from Telegram
            
        Returns:
            Dict containing formatted message data
        """
        emoji = message_reaction['new_reaction'][0]['emoji']
        message_id = message_reaction['message_id']
        chat_id = message_reaction['chat']['id']
        user = message_reaction['user']
        
        logger.info(f"Reaction received: {emoji} from user {user.get('username')} in chat {chat_id}")
        
        return {
        'message_id': message_id,
        'from': {
            'id': user['id'],
            'is_bot': user.get('is_bot', False),
            'first_name': user.get('first_name', ''),
            'username': user.get('username', '')
        },
        'chat': {
            'id': chat_id,
            'type': message_reaction['chat'].get('type', 'unknown')
        },
        'date': message_reaction['date'],
        'text': f"Reaction {emoji} to message {message_id}",
        'reaction': {
            'emoji': emoji,
            'message_id': message_id
        }
    }

    @error_handler(ValidationError)
    def parse_bot_mention(self, text: str) -> Optional[str]:
        """Extract command text from bot mention.
        
        Args:
            text: Message text to parse
            
        Returns:
            Extracted command text or None if no valid mention
        """
        match = re.search(BOT_MENTION_PATTERN, text)
        return match.group(1) if match else None

    @error_handler(TelegramError)
    async def handle_code_request(self, message: TextMessage, context: MessageContext) -> None:
        """Handle code request commands.
        
        Args:
            message: Telegram message containing code request
            context: Message context information
            
        Raises:
            ValidationError: If request text is invalid
            TelegramError: If request creation fails
        """
        with error_context(ValidationError, "Invalid code request"):
            chat_id = message.chat.id
            command_text = message.text.lower().split('@group_write_bot', 1)[1].strip()
            
            if not command_text:
                send_message(
                    chat_id,
                    ERROR_MESSAGES["missing_code_request"],
                    parse_mode="MarkdownV2"
                )
                return

            instance_data = {
                "background": command_text,
                "max_credit_per_instance": 0.03,
                "instance_timeout": 30,
                "gen_reward_timeout": 6000,
                "percentage_reward": 1,
            }
            
            try:
                async with AgentMarketClient() as client:
                    response = await client.create_instance(instance_data)
                instance_id = response['id']
                    
                tracker = RequestTracker()
                await tracker.add_request(instance_id, chat_id)
                
                send_message(
                    chat_id,
                    f"{Emoji.SUCCESS} {SUCCESS_MESSAGES['instance_created'].format(instance_id)}",
                    parse_mode="MarkdownV2"
                )
            except Exception as e:
                logger.error(f"Failed to create instance: {str(e)}")
                send_message(
                    chat_id,
                    f"{Emoji.ERROR} {ERROR_MESSAGES['instance_creation_failed'].format(str(e))}",
                    parse_mode="MarkdownV2"
                )

    @error_handler(TelegramError)
    async def handle_text_message(self, message: TextMessage, context: MessageContext) -> None:
        """Process text messages and route to appropriate handlers.
        
        Args:
            message: Telegram message to process
            context: Message context information
            
        Raises:
            ValidationError: If message format is invalid
            TelegramError: If message handling fails
        """
        from .command_handlers import handle_command
        
        with error_context(ValidationError, "Invalid message format"):
            chat_id = message.chat.id
            text = message.text.strip()

            if not text:
                send_message(
                    chat_id,
                    f"{Emoji.ERROR} {ERROR_MESSAGES['empty_message']}",
                    parse_mode="MarkdownV2"
                )
                return

            # Check for commands
            if text.startswith('/'):
                await handle_command(message)
                return

            # Check for provider mentions
            if text.startswith('@'):
                provider_mention = parse_provider_mention(text)
                if provider_mention:
                    provider_id, message_content, instance_id = provider_mention
                    await send_message_to_provider(
                        chat_id, 
                        provider_id, 
                        message_content, 
                        instance_id=instance_id
                    )
                    return
                else:
                    send_message(
                        chat_id,
                        f"{Emoji.ERROR} {ERROR_MESSAGES['invalid_provider_format']}",
                        parse_mode="MarkdownV2"
                    )
                    return

            # Check for GitHub issue links
            if 'github.com' in text.lower():
                await handle_github_issue_link(message)
                return

            # Check for bot mentions
            if '@group_write_bot' in text.lower():
                await self.handle_code_request(message, context)
                return

            # Unhandled message type
            logger.warning(f"Unhandled message type: {text[:50]}...")

    async def handle(self, message: BaseMessage, context: MessageContext) -> None:
        """Handle incoming messages based on their type.
        
        Args:
            message: Validated message object
            context: Message context information
            
        Raises:
            TelegramError: If message handling fails
            ValidationError: If message validation fails
        """
        with error_context(TelegramError, "Failed to handle message"):
            if isinstance(message, NewChatMemberMessage):
                await self._handle_new_chat_member(message, context)
            elif isinstance(message, TextMessage):
                await self.handle_text_message(message, context)
            else:
                logger.warning(f"Unsupported message type: {type(message)}")

    @error_handler(TelegramError)
    async def _handle_new_chat_member(self, message: NewChatMemberMessage, context: MessageContext) -> None:
        """Handle new chat member events.
        
        Args:
            message: New chat member message
            context: Message context information
            
        Raises:
            TelegramError: If welcome message fails to send
        """
        with error_context(TelegramError, "Failed to handle new chat member"):
            if 'new_chat_members' in message:
                from .initialization import set_bot_commands
                
                for member in message['new_chat_members']:
                    if member.get('username') == "group_code_bot":
                        chat_id = message.chat.id
                        set_bot_commands(chat_id)
                        send_message(
                            chat_id,
                            f"{Emoji.WAVE} {WELCOME_MESSAGE}",
                            parse_mode="MarkdownV2"
                        )
                        logger.info(f"Bot added to chat {chat_id}")
                return
            
            # Handle text messages
            if 'text' in message:
                await self.handle_text_message(message, context)
