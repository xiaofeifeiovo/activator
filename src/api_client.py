"""
API客户端模块

支持多种AI接口类型的HTTP客户端。
使用适配器模式支持不同的API接口。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import httpx

from .config import Config
from .utils import generate_activation_content


class BaseAPIClient(ABC):
    """API客户端抽象基类"""

    def __init__(self, config: Config):
        """
        初始化API客户端。

        Args:
            config: 配置对象
        """
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.client:
            await self.client.aclose()

    @abstractmethod
    def build_request(self, tokens: int) -> Dict[str, Any]:
        """
        构建请求体。

        Args:
            tokens: Token数量

        Returns:
            请求体字典
        """
        pass

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """
        获取请求头。

        Returns:
            请求头字典
        """
        pass

    @abstractmethod
    def parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        解析响应。

        Args:
            response: HTTP响应对象

        Returns:
            解析后的数据字典
        """
        pass

    async def send_activation(self, tokens: int) -> Dict[str, Any]:
        """
        发送激活请求。

        Args:
            tokens: Token数量

        Returns:
            响应数据

        Raises:
            httpx.HTTPStatusError: HTTP状态错误
            httpx.RequestError: 请求错误
        """
        if not self.client:
            raise RuntimeError("客户端未初始化，请使用 async with 语句")

        request_data = self.build_request(tokens)
        headers = self.get_headers()

        # 使用规范化后的URL
        target_url = self.config.api.get_normalized_url()

        response = await self.client.post(
            target_url,
            json=request_data,
            headers=headers
        )

        response.raise_for_status()

        return self.parse_response(response)


class OpenAIClient(BaseAPIClient):
    """OpenAI兼容接口客户端"""

    def build_request(self, tokens: int) -> Dict[str, Any]:
        """构建OpenAI格式请求"""
        content = generate_activation_content(tokens)
        return {
            "model": self.config.api.model,
            "messages": [
                {
                    "role": "user",
                    "content": content.strip()
                }
            ]
        }

    def get_headers(self) -> Dict[str, str]:
        """获取OpenAI请求头"""
        return {
            "Authorization": f"Bearer {self.config.api.apikey}",
            "Content-Type": "application/json"
        }

    def parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """解析OpenAI响应"""
        data = response.json()
        return {
            "usage": data.get("usage", {}),
            "model": data.get("model", ""),
            "full_response": data
        }


class AnthropicClient(BaseAPIClient):
    """Anthropic接口客户端"""

    def build_request(self, tokens: int) -> Dict[str, Any]:
        """构建Anthropic格式请求"""
        content = generate_activation_content(tokens)
        return {
            "model": self.config.api.model,
            "messages": [
                {
                    "role": "user",
                    "content": content.strip()
                }
            ],
            "max_tokens": 1  # Anthropic需要此参数
        }

    def get_headers(self) -> Dict[str, str]:
        """获取Anthropic请求头"""
        return {
            "x-api-key": self.config.api.apikey,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

    def parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """解析Anthropic响应"""
        data = response.json()
        return {
            "usage": data.get("usage", {}),
            "model": data.get("model", ""),
            "full_response": data
        }


class APIClientFactory:
    """API客户端工厂"""

    @staticmethod
    def create(config: Config) -> BaseAPIClient:
        """
        根据配置创建API客户端。

        Args:
            config: 配置对象

        Returns:
            API客户端实例

        Raises:
            ValueError: 不支持的接口类型
        """
        client_classes = {
            "openai": OpenAIClient,
            "anthropic": AnthropicClient
        }

        interface_type = config.api.interface_type.lower()
        client_class = client_classes.get(interface_type)

        if not client_class:
            raise ValueError(
                f"不支持的接口类型: {interface_type}。"
                f"支持的类型: {', '.join(client_classes.keys())}"
            )

        return client_class(config)


class RetryStrategy:
    """重试策略"""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        """
        初始化重试策略。

        Args:
            max_retries: 最大重试次数
            backoff_factor: 退避因子
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def should_retry(self, error: Exception) -> bool:
        """
        判断是否应该重试。

        Args:
            error: 异常对象

        Returns:
            是否应该重试
        """
        # 网络错误和5xx错误可以重试
        if isinstance(error, httpx.ConnectError):
            return True
        if isinstance(error, httpx.TimeoutException):
            return True
        if isinstance(error, httpx.HTTPStatusError):
            return 500 <= error.response.status_code < 600

        return False

    def calculate_wait_time(self, attempt: int) -> float:
        """
        计算等待时间。

        Args:
            attempt: 尝试次数

        Returns:
            等待时间（秒）
        """
        return min(self.backoff_factor ** attempt, 60.0)

    async def execute_with_retry(
        self,
        client: BaseAPIClient,
        tokens: int
    ) -> Dict[str, Any]:
        """
        执行带重试的请求。

        Args:
            client: API客户端
            tokens: Token数量

        Returns:
            响应数据

        Raises:
            Exception: 重试失败后抛出最后一次异常
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await client.send_activation(tokens)
            except Exception as e:
                last_error = e

                if attempt < self.max_retries - 1 and self.should_retry(e):
                    wait_time = self.calculate_wait_time(attempt)
                    await asyncio.sleep(wait_time)
                else:
                    break

        raise last_error
