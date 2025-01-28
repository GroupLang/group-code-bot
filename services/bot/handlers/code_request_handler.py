"""Handler for code requests."""

from typing import Dict, Any
from loguru import logger
from ..base_handler import BaseHandler
from ..context import MessageContext
from ..message_types import TextMessage
from services.client import AgentMarketClient
from services.request_tracker import RequestTracker
from utils.telegram_utils import send_message
from utils.errors import TelegramError, error_handler
from ..messages import ERROR_MESSAGES, SUCCESS_MESSAGES

class CodeRequestHandler(BaseHandler):
    """Handles processing of code request messages."""

    @error_handler(TelegramError)
    async def handle(self, message: TextMessage, context: MessageContext) -> None:
        """Handle code request commands.
        
        Args:
            message: Telegram message containing code request
            context: Message context information
        """
        chat_id = message.chat.id
        command_text = message.text.lower().split('@group_write_bot', 1)[1].strip()
        
        if not command_text:
            send_message(chat_id, ERROR_MESSAGES["missing_code_request"])
            return

        instance_data = {
            "background": command_text,
            "max_credit_per_instance": 0.03,
            "instance_timeout": 30,
            "gen_reward_timeout": 6000,
            "percentage_reward": 1,
        }
        
        async with AgentMarketClient() as client:
            response = await client.create_instance(instance_data)
        instance_id = response['id']
                
        tracker = RequestTracker()
        await tracker.add_request(instance_id, chat_id)
            
        send_message(chat_id, SUCCESS_MESSAGES["instance_created"].format(instance_id))
