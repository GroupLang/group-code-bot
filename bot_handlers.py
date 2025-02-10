import os
import re
import time
from typing import Dict, Any, Optional
import requests
from loguru import logger

from services.bot.messages import (
    WELCOME_MESSAGE,
    HELP_MESSAGE,
    INVALID_REWARD_FORMAT,
    REWARD_SUCCESS
)

from services.client import AgentMarketClient
from services.request_tracker import RequestTracker
from services.bot.provider import send_message_to_provider, parse_provider_mention
from utils.telegram_utils import send_message

BOT_MENTION_PATTERN = r'@group_code_bot\s+(.*)'
GITHUB_ISSUE_PATTERN = r'(?:https?://)?github\.com/([^/]+)/([^/]+)/issues/(\d+)'


async def handle_update(update: Dict[str, Any]) -> None:
    """Handle incoming updates from Telegram.
    
    Args:
        update: Update object from Telegram
    """
    try:
        if 'message' in update:
            await handle_message(update['message'])
            
    except Exception as e:
        logger.error(f"Error handling update: {e}")

async def handle_code_request(message: Dict[str, Any]) -> None:
    """Handle code request commands"""
    chat_id = message['chat']['id']
    command_text = message['text'].lower().split('@group_write_bot', 1)[1].strip()
    
    if not command_text:
        send_message(
            chat_id,
            "❌ Please provide a code request description after the command.",
        )
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
        
    send_message(
        chat_id,
        f"✅ Instance created!\n\n"
        f"🔍 Instance ID: `{instance_id}`\n"
    )

async def handle_github_issue_link(message: Dict[str, Any]) -> None:
    """Handle GitHub issue link detection using authorized endpoints."""
    chat_id = message['chat']['id']
    match = re.search(GITHUB_ISSUE_PATTERN, message['text'])
    if not match:
        return
        
    owner, repo, issue_num = match.groups()
    repo_url = f"https://github.com/{owner}/{repo}"
    issue_number = int(issue_num)
    
    async with AgentMarketClient() as client:
        try:
            # Include 'issue_url' in repo_data instead of 'issue_number'
            issue_url = f"{repo_url}/issues/{issue_number}"
            repo_data = {
                "repo_url": issue_url,
                "default_reward": 0.03,
            }
            try:
                try:
                    issues = await client.get_repository_issues(repo_url=issue_url)
                    return
                except Exception as e:
                    repo_url = repo_url.replace(owner, 'agentmarketproxy') 
                    issue_url = f"{repo_url}/issues/{issue_number}"
                    issues = await client.get_repository_issues(repo_url=issue_url)
                    return
            except Exception as e:
                pass
            try:
                await client.add_repository(repo_data)
            except Exception as e:
                logger.error(f"Error adding repository: {e}")
                return 

            time.sleep(61)

            try:
                issues = await client.get_repository_issues(repo_url=issue_url)
            except Exception as e:
                repo_url = repo_url.replace(owner, 'agentmarketproxy') 
                issue_url = f"{repo_url}/issues/{issue_number}"
                issues = await client.get_repository_issues(repo_url=issue_url)
            issue = next((issue for issue in issues if issue['issue_number'] == issue_number), None)

            if not issue or not issue.get('instance_id'):
                send_message(
                    chat_id,
                    f"❌ Instance for issue #{issue_number} not found.",
                )
                return

            instance_id = issue['instance_id']
            
            # Store the instance
            tracker = RequestTracker()
            await tracker.add_request(instance_id, chat_id)

            # Format and send issue details
            message_text = (
                f"✅ Created instance `{instance_id}` from GitHub issue #{issue_number}\n\n"
                f"*Title:* {issue['title']}\n"
            )
            
            if issue.get('body'):
                # Escape special Markdown characters in the body
                body = issue['body'].replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
                message_text += f"\n*Description:*\n{body}\n"
                
            if issue.get('reward_amount'):
                message_text += f"\n*Reward Amount:* ${issue['reward_amount']:.2f}"
                
            send_message(
                chat_id,
                message_text
            )
        except Exception as e:
            logger.error(f"Error handling GitHub issue: {e}")
            send_message(
                chat_id,
                f"❌ Failed to process GitHub issue {e}. Please try again later.",
            )

async def handle_new_chat_members(message: Dict[str, Any]) -> None:
    """Handle new members joining the chat"""
    chat_id = message['chat']['id']
    for member in message['new_chat_members']:
        if member.get('username') == "group_code_bot":
            set_bot_commands(chat_id)
            send_message(chat_id, WELCOME_MESSAGE)

async def handle_provider_reply(message: Dict[str, Any], replied_msg: Dict[str, Any]) -> bool:
    """Handle replies to provider messages"""
    chat_id = message['chat']['id']
    text = message['text']
    
    if 'text' not in replied_msg or 'message from' not in replied_msg['text'].lower():
        return False
        
    try:
        provider_id = replied_msg['text'].split('(')[1].split(')')[0]
        instance_info = replied_msg['text'].split('for instance: ')[1]
        instance_id = re.search(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', instance_info).group(0)

        await send_message_to_provider(chat_id, provider_id, text, instance_id=instance_id)
        return True
    except (IndexError, ValueError):
        logger.error("Failed to parse provider or instance ID from message")
        return False

async def handle_provider_mention(message: Dict[str, Any]) -> bool:
    """Handle direct provider mentions"""
    chat_id = message['chat']['id']
    text = message['text']
    
    if not text.startswith('@'):
        return False
        
    provider_info = parse_provider_mention(text)
    if not provider_info:
        return False
        
    provider_id, message_content, instance_id = provider_info
    await send_message_to_provider(chat_id, provider_id, message_content, instance_id=instance_id)
    return True

async def handle_message(message: Dict[str, Any]) -> None:
    """Main message handler that routes to specific handlers"""
    if 'new_chat_members' in message:
        await handle_new_chat_members(message)
        return
    
    if 'text' not in message:
        return
        
    text = message['text']
    
    # Handle commands first
    if text.startswith('/'):
        # Extract the command by removing the @ portion if present
        command = text.split('@')[0]  # This will convert "/help@group_code_bot" to "help"
        await handle_command(message, command)
        return
    
    # Handle replies to provider messages
    if 'reply_to_message' in message:
        if await handle_provider_reply(message, message['reply_to_message']):
            return
            
    # Handle provider mentions
    if await handle_provider_mention(message):
        return

    # Handle non-command messages
    if 'github.com' in text.lower():
        await handle_github_issue_link(message)
        return
    elif '@group_write_bot' in text.lower():
        await handle_code_request(message)
        return
    

def parse_bot_mention(text: str) -> Optional[str]:
    """Extract command text from bot mention"""
    match = re.search(BOT_MENTION_PATTERN, text)
    return match.group(1) if match else None


async def handle_command(message: Dict[str, Any], command: str) -> bool:
    """Handle bot commands"""
    chat_id = message['chat']['id']
    
    if command.startswith('/help'):
        send_message(chat_id, HELP_MESSAGE)
        return True
        
    if command.startswith('/submit_reward'):
        await handle_submit_reward(message)
        return True
        
    return False

async def handle_submit_reward(message: Dict[str, Any]) -> None:
    """Handle the submit_reward command"""
    chat_id = message['chat']['id']
    parts = message['text'].split()
    
    if len(parts) != 3:
        send_message(chat_id, INVALID_REWARD_FORMAT)
        return
        
    instance_id = parts[1]
    try:
        amount = float(parts[2].replace(',', '.'))
        async with AgentMarketClient() as client:
            await client.report_reward(instance_id, amount)
        send_message(chat_id, REWARD_SUCCESS.format(amount=amount, instance_id=instance_id))
    except ValueError:
        send_message(chat_id, "❌ Amount must be a valid number")
    except Exception as e:
        logger.error(f"Error submitting reward: {e}")
        send_message(chat_id, f"❌ Failed to submit reward: {str(e)}")

async def initialize_bot() -> None:
    """Initialize bot settings and configurations"""
    logger.info("Initializing bot...")
    
    # Set up default commands for the bot
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

def set_bot_commands(chat_id: int) -> None:
    """Set up the bot's commands for a group chat with proper scope and language support."""
    
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
    
    # Set commands with proper scope for the specific group chat
    commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
    # Commands by chat_id
    commands_payload = {
        "commands": commands,
        "chat_id": chat_id
    }
    
    try:
        commands_response = requests.post(commands_url, json=commands_payload)
        commands_response.raise_for_status()  # Raise exception for non-200 status codes
        print(f"Successfully set commands for chat {chat_id}")
    except Exception as e:
        print(f"Error setting commands: {str(e)}")
