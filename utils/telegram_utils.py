import requests
import os
import re
from typing import Dict, Any, Optional, Tuple

def escape_markdown(text: str) -> str:
    """
    Escape Telegram MarkdownV2 special characters in text outside of code blocks.
    Special characters that need to be escaped: _ * [ ] ( ) ~ ` > # + - = | { } . !
    This function escapes all required reserved characters (including '#' so that headers render correctly)
    but leaves markdown formatting markers like asterisks (*) and underscores (_) unchanged.
    Additionally, text within triple-backtick code blocks (e.g. ```markdown ... ```) is not escaped.
    """
    parts = re.split(r'(```[\s\S]*?```)', text)
    
    pattern = r'(?<!\\)([#\[\]()~`>+\=|{}.!-])'
    
    for i, part in enumerate(parts):
        if part.startswith("```"):
            if len(part) > 3 and part[3] == "\n":
                parts[i] = "```markdown" + part[3:]
        else:
            parts[i] = re.sub(pattern, r'\\\1', part)
    return "".join(parts)

def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None, 
                reply_to_message_id: Optional[int] = None, parse_mode: Optional[str] = None) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']}/sendMessage"
    
    escaped_text = escape_markdown(text) if parse_mode == 'MarkdownV2' else text
    data = {
        'chat_id': chat_id,
        'text': escaped_text,
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
        # Get the full error details from the response
        error_details = f"HTTP Error: {e}\n"
        if hasattr(e, 'response') and e.response is not None:
            error_details += f"Status Code: {e.response.status_code}\n"
            error_details += f"Response Content: {e.response.text}\n"
            error_details += f"Request Data: {data}\n"
        print(f"Telegram API Error: {error_details}")
        # Re-raise the exception to maintain the original behavior
        raise

def edit_message(chat_id: int, message_id: int, text: str, 
                reply_markup: Optional[Dict] = None) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']}/editMessageText"
    
    escaped_text = escape_markdown(text)
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': escaped_text,
        'parse_mode': 'MarkdownV2'
    }
    
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
        # Re-raise the exception to maintain the original behavior
        raise
