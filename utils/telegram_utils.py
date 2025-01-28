import requests
import os
from typing import Dict, Any, Optional

def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None, 
                reply_to_message_id: Optional[int] = None, parse_mode: Optional[str] = 'Markdown') -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']}/sendMessage"
    
    data = {
        'chat_id': chat_id,
        'text': text,
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
    
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
    if reply_markup:
        data['reply_markup'] = reply_markup

    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()
