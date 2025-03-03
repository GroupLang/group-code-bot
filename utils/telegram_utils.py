import requests
import os
import re
from typing import Dict, Any, Optional, Tuple

def escape_markdown(text: str) -> str:
    """
    Escape Telegram MarkdownV2 special characters in text outside of code blocks.
    Special characters that need to be escaped: _ * [ ] ( ) ~ ` > # + - = | { } . !
    This function escapes all required reserved characters for MarkdownV2 format.
    Additionally, text within triple-backtick code blocks (e.g. ```markdown ... ```) is not escaped.
    """
    # Return plain text if input is None or empty
    if not text:
        return ""
        
    # Split by code blocks to preserve them
    parts = re.split(r'(```[\s\S]*?```)', text)
    
    # These are all the special characters that need escaping in MarkdownV2
    # Note: We're explicitly including * and _ which are formatting characters
    pattern = r'(?<!\\)([\[\]()~`>#+=|{}.!_*-])'
    
    for i, part in enumerate(parts):
        if part.startswith("```"):
            # Leave code blocks alone
            if len(part) > 3 and part[3] == "\n":
                parts[i] = "```markdown" + part[3:]
        else:
            # Escape special characters
            parts[i] = re.sub(pattern, r'\\\1', part)
    return "".join(parts)

def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None, 
                reply_to_message_id: Optional[int] = None, parse_mode: Optional[str] = None,
                disable_notification: bool = False) -> Dict[str, Any]:
    """
    Send a message to a Telegram chat.
    
    Args:
        chat_id: The chat ID to send the message to
        text: The text of the message
        reply_markup: Optional reply markup for the message
        reply_to_message_id: Optional message ID to reply to
        parse_mode: The parse mode (None, 'MarkdownV2', 'HTML')
        disable_notification: Whether to send the message silently
    
    Returns:
        The response from the Telegram API
    """
    url = f"https://api.telegram.org/bot{os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']}/sendMessage"
    
    # Handle empty messages
    if not text:
        text = "⚠️ Empty message"
    
    # Escape markdown if needed
    escaped_text = escape_markdown(text) if parse_mode == 'MarkdownV2' else text
    
    # Build request data
    data = {
        'chat_id': chat_id,
        'text': escaped_text,
        'disable_notification': disable_notification
    }
    
    if parse_mode:
        data['parse_mode'] = parse_mode
    
    if reply_markup:
        data['reply_markup'] = reply_markup
    
    if reply_to_message_id:
        data['reply_to_message_id'] = reply_to_message_id

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Log error details
        error_details = f"HTTP Error: {e}\n"
        if hasattr(e, 'response') and e.response is not None:
            error_details += f"Status Code: {e.response.status_code}\n"
            error_details += f"Response Content: {e.response.text}\n"
            error_details += f"Request Data: {data}\n"
        print(f"Telegram API Error: {error_details}")
        
        # Return error info instead of raising exception
        # This allows callers to handle errors gracefully
        return {'ok': False, 'error': str(e)}

def edit_message(chat_id: int, message_id: int, text: str, 
                reply_markup: Optional[Dict] = None, 
                parse_mode: Optional[str] = 'MarkdownV2') -> Dict[str, Any]:
    """
    Edit a previously sent message.
    
    Args:
        chat_id: The chat ID where the message is
        message_id: The ID of the message to edit
        text: The new text for the message
        reply_markup: Optional reply markup for the message
        parse_mode: The parse mode, defaults to MarkdownV2 but can be None for plain text
    
    Returns:
        The response from the Telegram API
    """
    url = f"https://api.telegram.org/bot{os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']}/editMessageText"
    
    # Only escape if a parse mode is specified
    escaped_text = escape_markdown(text) if parse_mode == 'MarkdownV2' else text
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': escaped_text,
    }
    
    # Only add parse_mode if specified
    if parse_mode:
        data['parse_mode'] = parse_mode
    
    if reply_markup:
        data['reply_markup'] = reply_markup

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Get the full error details from the response
        error_details = f"HTTP Error: {e}\n"
        if hasattr(e, 'response') and e.response is not None:
            error_details += f"Status Code: {e.response.status_code}\n"
            error_details += f"Response Content: {e.response.text}\n"
            error_details += f"Request Data: {data}\n"
        print(f"Telegram API Error: {error_details}")
        
        # Instead of re-raising the exception, return a dummy response
        # This allows the bot to continue functioning even if a message edit fails
        return {'ok': False, 'error': str(e)}
