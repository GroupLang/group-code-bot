from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
from services.client import AgentMarketClient
from services.request_tracker import RequestTracker
from utils.telegram_utils import send_message

async def fetch_new_messages(
    client: AgentMarketClient,
    instance_id: str,
    provider_id: str,
    last_processed_timestamp: int
) -> List[Dict[str, Any]]:
    """Fetch and filter new messages for a provider."""
    try:
        provider_messages = await client.get_conversation_messages(
            instance_id,
            provider_id=provider_id
        )
        return [
            msg for msg in provider_messages
            if int(datetime.fromisoformat(msg.get('timestamp')).timestamp()) > last_processed_timestamp
        ]
    except Exception as e:
        logger.error(f"Error fetching messages for provider {provider_id}: {e}")
        return []

def format_provider_message(
    content: str,
    sender: str,
    provider: str,
    instance_id: str,
    timestamp: str
) -> str:
    """Format a provider message for sending."""
    timestamp_dt = datetime.fromisoformat(timestamp)
    formatted_timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    return (f"📩 Message from {sender}:\n"
            f"({provider})\n"
            f"for instance: {instance_id}\n"
            f"⏰ {formatted_timestamp}\n\n{content}")

async def process_instance_messages(
    client: AgentMarketClient,
    request_tracker: RequestTracker,
    instance_id: str,
    last_processed_timestamp: int
) -> Optional[int]:
    """Process all messages for a single instance."""
    try:
        chat_id = request_tracker.get_chat_id_by_instance_id(instance_id)
        if not chat_id:
            return None

        winning_providers = await client.get_instance_providers(instance_id)
        latest_timestamp = last_processed_timestamp

        for provider in winning_providers:
            new_messages = await fetch_new_messages(
                client, instance_id, provider, last_processed_timestamp
            )

            for message in new_messages:
                if message.get('sender') == 'provider':
                    formatted_msg = format_provider_message(
                        content=message.get('message'),
                        sender=message.get('sender'),
                        provider=provider,
                        instance_id=instance_id,
                        timestamp=message.get('timestamp')
                    )
                    send_message(chat_id=chat_id, text=formatted_msg)

                msg_timestamp = int(datetime.fromisoformat(message.get('timestamp')).timestamp())
                latest_timestamp = max(latest_timestamp, msg_timestamp)

        return int(datetime.utcnow().timestamp()) if latest_timestamp > last_processed_timestamp else None

    except Exception as e:
        logger.error(f"Error processing instance {instance_id}: {e}")
        return None
