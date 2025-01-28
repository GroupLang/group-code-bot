from typing import Optional, Dict
from botocore.exceptions import ClientError
import boto3
import asyncio
from datetime import datetime, timedelta
from loguru import logger

class RequestTracker:
    """Tracks active requests and their processing status"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = 'agent_requests'
        self.table = self.dynamodb.Table(self.table_name)
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Ensure the DynamoDB table exists, create if not"""
        try:
            self.dynamodb.meta.client.describe_table(TableName=self.table_name)
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            self._create_table()

    def _create_table(self) -> None:
        """Create the DynamoDB table"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'N'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'status-created_at-index',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)
            logger.info(f"Table {self.table_name} created successfully.")
        except ClientError as e:
            logger.error(f"Error creating table {self.table_name}: {e}")

    def update_last_processed_time(self, instance_id: str, timestamp: int) -> None:
        """Update the last processed time for an instance"""
        try:
            self.table.update_item(
                Key={'id': instance_id},
                UpdateExpression='SET last_processed_time = :time',
                ExpressionAttributeValues={':time': timestamp}
            )
        except Exception as e:
            logger.error(f"Error updating last processed time: {e}")
    
    def get_last_processed_time(self, instance_id: str) -> int:
        """Get the last processed timestamp for an instance."""
        try:
            response = self.table.get_item(
                Key={'id': str(instance_id)}  # Remove ProjectionExpression to get all attributes
            )
            
            item = response.get('Item', {})
            return int(item.get('last_processed_time', 0))
            
        except Exception as e:
            logger.error(f"Error getting last processed time for instance {instance_id}: {e}")
            return 0

    async def add_request(self, instance_id: str, chat_id: int, metadata: Optional[Dict] = None) -> None:
        """Add a new active request"""
        try:
            now = int(datetime.utcnow().timestamp())
            item = {
                'id': str(instance_id),  # Ensure id is string
                'chat_id': str(chat_id),
                'active': True,
                'created_at': now,
                'last_processed_time': now,
                'status': 'pending'
            }
            if metadata:
                item['metadata'] = metadata
                
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.table.put_item(Item=item)
            )
        except Exception as e:
            logger.error(f"Error adding request: {e}")
            raise

    def get_chat_id_by_instance_id(self, instance_id: str) -> Optional[int]:
        """Get chat_id associated with an instance_id."""
        try:
            response = self.table.get_item(
                Key={'id': str(instance_id)}  # Remove ProjectionExpression to get all attributes
            )
            
            item = response.get('Item', {})
            chat_id = item.get('chat_id')
            return int(chat_id) if chat_id is not None else None
            
        except Exception as e:
            logger.error(f"Error getting chat_id for instance {instance_id}: {e}")
            return None
