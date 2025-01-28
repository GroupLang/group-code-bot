import asyncio
import json
import os
from datetime import datetime
from services.request_tracker import RequestTracker
from services.client import AgentMarketClient
from utils.message_utils import process_instance_messages
from bot_handlers import handle_update
from loguru import logger

_RESOLVED_STATUS = 3

async def process_provider_messages(event=None, context=None):
    """Process new messages from providers for all active instances."""
    try:
        request_tracker = RequestTracker()
        async with AgentMarketClient() as client:
            active_instances = await client.get_instances(instance_status=_RESOLVED_STATUS)

            for instance in active_instances:
                instance_id = instance['id']
                last_processed_timestamp = request_tracker.get_last_processed_time(instance_id)
                
                new_timestamp = await process_instance_messages(
                    client,
                    request_tracker,
                    instance_id,
                    last_processed_timestamp
                )

                if new_timestamp:
                    logger.info(f"Updating last processed timestamp for instance {instance_id}")
                    request_tracker.update_last_processed_time(instance_id, new_timestamp)

    except Exception as e:
        logger.error(f"Error in process_provider_messages: {e}")

class ApplicationConfig:
    def __init__(self):
        self.telegram_token = os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']
        self.agent_market_api_key = os.environ['AGENT_MARKET_API_KEY']
        self.openai_api_key = os.environ['OPENAI_API_KEY']

def handler(event, context):
    # Check if this is an EventBridge scheduled event
    logger.info(f"Received event: {event}")
    if event.get('detail-type') == 'process_provider_messages':
        # Create a new event loop for the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(process_provider_messages(event, context))
        finally:
            loop.close()
    else:
        logger.info("Received regular API Gateway request")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(handle_update(json.loads(event['body'])))
        finally:
            loop.close()

