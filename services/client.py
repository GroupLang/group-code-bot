from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Any, List
import os
import aiohttp
import asyncio
from loguru import logger
from utils.retry_utils import with_retry

class AgentMarketAPIError(Exception):
    """Raised when the Agent Market API returns an error response"""
    pass

class AgentMarketClient:
    def __init__(self, base_url: str = "https://api.agent.market/v1", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("AGENT_MARKET_API_KEY")
        if not self.api_key:
            raise AgentMarketAPIError("API key not provided")

    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        pass

    @with_retry(max_attempts=3, min_wait=1, max_wait=10)
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Agent Market API with retry capability"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with aiohttp.ClientSession(headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }) as session:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    timeout=aiohttp.ClientTimeout(total=30)  # Set timeout
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        if response.status >= 500:  # Server errors should trigger retry
                            logger.warning(f"Server error ({response.status}) for {method} {url}: {error_text}")
                            raise aiohttp.ClientError(f"Server error: {error_text}")
                        else:  # Client errors should not retry
                            raise AgentMarketAPIError(
                                f"API request failed ({response.status}): {error_text}"
                            )
                    return await response.json()
                    
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Request failed for {method} {url}: {str(e)}")
            raise  # Re-raise for retry
        
    async def add_repository(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a repository using the POST /repositories endpoint."""
        endpoint = "github/repositories"
        # Extract repo_url and default_reward from repo_data
        params = {
            "repo_url": repo_data.get("repo_url"),
            "default_reward": repo_data.get("default_reward", 0.03)  # Default value if not provided
        }
        response = await self._request("POST", endpoint, params=params)
        return response

    async def create_instance(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an instance using the POST / endpoint."""
        endpoint = "instances"
        response = await self._request("POST", endpoint, json=instance_data)
        return response

    async def get_repository_issues(self, repo_url: str) -> List[Dict[str, Any]]:
        """Retrieve issues from a repository using GET /repositories/issues."""
        endpoint = "github/repositories/issues"
        params = {"repo_url": repo_url}
        response = await self._request("GET", endpoint, params=params)
        return response

    async def get_instances(self, instance_status: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if instance_status is not None:
            params["instance_status"] = instance_status
        endpoint = "instances/"
        response = await self._request("GET", endpoint, params=params)
        return response
    
    async def get_instance_providers(self, instance_id: str) -> List[Dict[str, Any]]:
        endpoint = f"instances/{instance_id}/winning-providers"
        response = await self._request("GET", endpoint)
        return response

    async def get_instance(self, instance_id: str) -> Dict[str, Any]:
        endpoint = f"instances/{instance_id}"
        response = await self._request("GET", endpoint)
        return response

    async def report_reward(self, instance_id: str, gen_reward: float) -> Dict[str, Any]:
        endpoint = f"instances/{instance_id}/report-reward"
        payload = {"gen_reward": gen_reward}
        response = await self._request("PUT", endpoint, json=payload)
        return response

    async def get_conversation_messages(
        self,
        instance_id: str,
        provider_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        endpoint = f"chat/{instance_id}"
        params = {}
        if provider_id:
            params["provider_id"] = provider_id
        response = await self._request("GET", endpoint, params=params)
        return response

    async def send_message_in_conversation(
        self,
        instance_id: str,
        message: str,
        provider_id: Optional[str] = None
    ) -> Dict[str, Any]:
        endpoint = f"chat/send-message/{instance_id}"
        payload = {"message": message}
        if provider_id:
            payload["provider_id"] = provider_id
        response = await self._request("POST", endpoint, json=payload)
        return response
