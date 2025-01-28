"""Command handling implementation for the GroupCode bot.

This module provides functionality for processing and executing bot commands,
with robust error handling and consistent message formatting.
"""

from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Tuple, Optional
from loguru import logger

from services.client import AgentMarketClient, AgentMarketAPIError
from utils.telegram_utils import send_message
from utils.errors import error_handler, ValidationError
from .messages import (
    HELP_MESSAGE,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    COMMAND_USAGE,
    COMMAND_MESSAGES,
    MessageCategory,
    Emoji
)

class CommandParseError(ValidationError):
    """Raised when command parsing fails."""
    pass

class RewardSubmissionError(ValidationError):
    """Raised when reward submission fails."""
    pass

def extract_command_parts(text: str) -> Tuple[str, str]:
    """Extract the command and arguments from message text.
    
    Args:
        text: Raw message text containing command
        
    Returns:
        Tuple of (command, arguments)
        
    Raises:
        CommandParseError: If command format is invalid
    """
    try:
        command_parts = text.strip().split(maxsplit=1)
        # Remove bot username if present (e.g., /command@bot_name)
        command = command_parts[0].split('@')[0].lower()
        args = command_parts[1] if len(command_parts) > 1 else ''
        return command, args
    except Exception as e:
        raise CommandParseError(f"Failed to parse command: {str(e)}")

def validate_reward_amount(amount_str: str) -> Decimal:
    """Validate and convert reward amount string to Decimal.
    
    Args:
        amount_str: String representation of reward amount
        
    Returns:
        Decimal: Validated reward amount
        
    Raises:
        ValidationError: If amount is invalid
    """
    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            raise ValidationError(
                f"Invalid reward amount: {amount_str}. Must be positive."
            )
        return amount
    except InvalidOperation:
        raise ValidationError(f"Invalid reward amount: {amount_str}")

def parse_reward_command(args: str) -> Tuple[str, Decimal]:
    """Parse and validate reward command arguments.
    
    Args:
        args: Command arguments string
        
    Returns:
        Tuple of (instance_id, validated_amount)
        
    Raises:
        ValidationError: If arguments are invalid
    """
    parts = args.split()
    if len(parts) != 2:
        raise ValidationError(COMMAND_MESSAGES["reward_parse_error"].template)
    
    instance_id, amount_str = parts
    amount = validate_reward_amount(amount_str)
    return instance_id, amount

async def submit_reward_to_market(
    instance_id: str,
    amount: Decimal
) -> None:
    """Submit reward to Agent Market API.
    
    Args:
        instance_id: Target instance ID
        amount: Reward amount
        
    Raises:
        RewardSubmissionError: If submission fails
    """
    try:
        async with AgentMarketClient() as client:
            await client.report_reward(instance_id, float(amount))
    except AgentMarketAPIError as e:
        raise RewardSubmissionError(f"Failed to submit reward: {str(e)}")

async def command_help(chat_id: int, args: str = '') -> None:
    """Handle /help command.
    
    Args:
        chat_id: Telegram chat ID
        args: Command arguments (unused)
    """
    send_message(chat_id, HELP_MESSAGE)

@error_handler(ValidationError)
@error_handler(RewardSubmissionError)
async def command_submit_reward(chat_id: int, args: str) -> None:
    """Handle /submit_reward command.
    
    Parses arguments, validates reward amount, and submits to Agent Market.
    
    Args:
        chat_id: Telegram chat ID
        args: Command arguments containing instance_id and amount
        
    Raises:
        ValidationError: If arguments are invalid
        RewardSubmissionError: If submission fails
    """
    instance_id, amount = parse_reward_command(args)
    await submit_reward_to_market(instance_id, amount)
    
    success_msg = SUCCESS_MESSAGES["reward_submitted"].format(
        float(amount),
        instance_id
    )
    send_message(chat_id, success_msg)

# Command router mapping
COMMAND_HANDLERS = {
    '/help': command_help,
    '/submit_reward': command_submit_reward
}

@error_handler(CommandParseError)
async def handle_command(message: Dict[str, Any]) -> None:
    """Route and handle bot commands.
    
    Main entry point for command processing. Extracts command and arguments
    from message and routes to appropriate handler.
    
    Args:
        message: Telegram message containing a command
        
    Raises:
        CommandParseError: If command parsing fails
    """
    chat_id = message['chat']['id']
    command, args = extract_command_parts(message['text'])
    
    handler = COMMAND_HANDLERS.get(command)
    if handler:
        await handler(chat_id, args)
    else:
        send_message(
            chat_id,
            ERROR_MESSAGES["invalid_command"].template.format(command=command)
        )
