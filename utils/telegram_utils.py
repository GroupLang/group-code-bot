import requests
import os
import re
from typing import Dict, Any, Optional, Tuple

def escape_markdown(text: str) -> str:
    """
    Escape Markdown special characters in text for Telegram messages.
    Handles: _ * ` [ ] ( ) ~ > # + - = | { } . !
    """
    special_chars = r'[_*\[\]()~`>#+-=|{}.!]'
    return re.sub(special_chars, r'\\\g<0>', text)

def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None, 
                reply_to_message_id: Optional[int] = None, parse_mode: Optional[str] = 'MarkdownV2') -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']}/sendMessage"
    
    escaped_text = escape_markdown(text) if parse_mode == 'MarkdownV2' else text
    data = {
        'chat_id': chat_id,
        'text': escaped_text,
        'parse_mode': parse_mode
    }
    
    if reply_markup:
        data['reply_markup'] = reply_markup
    if reply_to_message_id:
        data['reply_to_message_id'] = reply_to_message_id

    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

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

    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()
