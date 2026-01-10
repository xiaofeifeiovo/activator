"""
定时调度器模块

负责管理定时任务，处理信号和优雅退出。
"""

import asyncio
import signal
from datetime import datetime
from typing import Optional

from .config import Config
from .api_client import APIClientFactory, RetryStrategy
from .logger import (
    logger,
    log_activation_success,
    log_activation_error,
    log_retry,
    log_shutdown
)
from .utils import calculate_next_run_time, format_timestamp


class GracefulShutdown:
    """优雅退出处理器"""

    def __init__(self):
        """初始化优雅退出处理器"""
        self.shutdown = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        try:
            # Windows和Unix信号处理
            signal.signal(signal.SIGINT, self._signal_handler)
            if hasattr(signal, 'SIGBREAK'):
                # Windows特有的Ctrl+Break信号
                signal.signal(signal.SIGBREAK, self._signal_handler)
        except ValueError:
            # 在某些环境中可能无法设置信号处理器
            logger.warning("无法设置信号处理器")

    def _signal_handler(self, signum, frame):
        """
        信号处理函数。

        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        log_shutdown()
        self.shutdown = True


class ActivatorScheduler:
    """激活器调度器"""

    def __init__(self, config: Config):
        """
        初始化调度器。

        Args:
            config: 配置对象
        """
        self.config = config
        self.api_client = APIClientFactory.create(config)
        self.retry_strategy = RetryStrategy(max_retries=3)
        self.shutdown_handler = GracefulShutdown()

    async def send_activation(self) -> bool:
        """
        发送激活请求。

        Returns:
            是否成功
        """
        tokens = self.config.activator.tokens

        try:
            async with self.api_client as client:
                response = await self.retry_strategy.execute_with_retry(
                    client,
                    tokens
                )

                # 记录成功日志
                next_time = calculate_next_run_time(self.config.activator.interval)
                log_activation_success(
                    url=self.config.api.get_normalized_url(),
                    model=self.config.api.model,
                    tokens=tokens,
                    response_data=response,
                    next_run_time=format_timestamp(next_time)
                )

                return True

        except Exception as e:
            log_activation_error(e)
            return False

    async def run(self):
        """
        运行调度器主循环。

        每隔指定时间发送一次激活请求，直到收到退出信号。
        """
        interval_seconds = self.config.activator.interval * 3600

        logger.info("=" * 60)
        logger.info("Activator 调度器启动")
        logger.info(f"接口类型: {self.config.api.interface_type}")
        logger.info(f"API端点: {self.config.api.get_normalized_url()}")
        logger.info(f"模型: {self.config.api.model}")
        logger.info(f"请求间隔: {self.config.activator.interval} 小时")
        logger.info(f"Token数量: {self.config.activator.tokens}")
        logger.info("=" * 60)

        # 立即发送第一次请求
        logger.info("发送首次激活请求...")
        await self.send_activation()

        # 主循环
        while not self.shutdown_handler.shutdown:
            try:
                # 计算下次运行时间
                next_time = calculate_next_run_time(self.config.activator.interval)
                logger.info(f"下次运行时间: {format_timestamp(next_time)}")

                # 等待指定间隔（可被中断）
                await asyncio.wait_for(
                    self._wait_for_shutdown(interval_seconds),
                    timeout=interval_seconds
                )

            except asyncio.CancelledError:
                # 任务被取消（收到退出信号）
                break
            except asyncio.TimeoutError:
                # 正常超时，继续发送请求
                pass
            except Exception as e:
                logger.error(f"调度器错误: {str(e)}")
                # 等待一段时间后继续
                await asyncio.sleep(60)
                continue

            # 发送激活请求
            await self.send_activation()

        logger.info("调度器已停止")

    async def _wait_for_shutdown(self, timeout: float):
        """
        等待退出信号或超时。

        Args:
            timeout: 超时时间（秒）

        Raises:
            asyncio.CancelledError: 收到退出信号
        """
        while timeout > 0 and not self.shutdown_handler.shutdown:
            wait_time = min(1.0, timeout)
            await asyncio.sleep(wait_time)
            timeout -= wait_time

        if self.shutdown_handler.shutdown:
            raise asyncio.CancelledError()
