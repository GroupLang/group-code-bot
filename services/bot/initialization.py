import os
import requests
from typing import List, Dict
from loguru import logger

def set_bot_commands(chat_id: int) -> None:
    """Set up the bot's commands for a group chat.
    
    Args:
        chat_id: Telegram chat ID to set commands for
    """
    commands = [
        {
            "command": "help",
            "description": "Show help message"
        },
        {
            "command": "submit_reward",
            "description": "Submit reward for an instance"
        }
    ]
    
    token = os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']
    commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
    
    try:
        response = requests.post(commands_url, json={
            "commands": commands,
            "chat_id": chat_id
        })
        response.raise_for_status()
        logger.info(f"Successfully set commands for chat {chat_id}")
    except Exception as e:
        logger.error(f"Error setting commands: {str(e)}")

async def initialize_bot() -> None:
    """Initialize bot settings and configurations."""
    logger.info("Initializing bot...")
    
    token = os.environ.get('GROUPWRITE_TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Bot token not found in environment variables")
        return
        
    # Set global bot commands
    commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
    commands = [
        {
            "command": "help",
            "description": "Show help message"
        },
        {
            "command": "submit_reward", 
            "description": "Submit reward for an instance"
        }
    ]
    
    try:
        response = requests.post(commands_url, json={"commands": commands})
        response.raise_for_status()
        logger.info("Successfully set global bot commands")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")
