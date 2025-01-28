"""Handler for message reactions."""

from typing import Dict, Any
from loguru import logger
from ..base_handler import BaseHandler
from utils.errors import TelegramError, error_handler

class ReactionHandler(BaseHandler):
    """Handles processing of message reactions."""

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
