"""
日志管理模块

使用loguru配置日志系统，支持终端和文件双输出。
"""

from pathlib import Path
from loguru import logger
from typing import Optional

from .config import Config


def setup_logger(config: Config) -> None:
    """
    配置loguru日志系统。

    Args:
        config: 配置对象
    """
    # 移除默认处理器
    logger.remove()

    # 添加终端处理器（彩色输出）
    logger.add(
        sink=lambda msg: print(msg, end=''),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>"
        ),
        level=config.logging.level,
        colorize=True
    )

    # 确保日志目录存在
    log_file = Path(config.logging.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 添加文件处理器（详细日志）
    logger.add(
        sink=config.logging.file,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        level=config.logging.level,
        rotation=config.logging.rotation,
        encoding="utf-8"
    )

    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {config.logging.level}")
    logger.info(f"日志文件: {config.logging.file}")


def log_activation_success(
    url: str,
    model: str,
    tokens: int,
    response_data: dict,
    next_run_time: str
) -> None:
    """
    记录激活成功日志。

    Args:
        url: API端点URL
        model: 模型名称
        tokens: Token数量
        response_data: 响应数据
        next_run_time: 下次运行时间
    """
    logger.success(
        f"✅ 激活成功 | "
        f"Token: {tokens} | "
        f"下次: {next_run_time}"
    )

    logger.info(
        f"  URL: {url}\n"
        f"  模型: {model}\n"
        f"  Token数: {tokens}\n"
        f"  响应: {response_data}\n"
        f"  下次请求时间: {next_run_time}"
    )


def log_activation_error(error: Exception, attempt: int = 1) -> None:
    """
    记录激活失败日志。

    Args:
        error: 异常对象
        attempt: 尝试次数
    """
    logger.error(
        f"❌ 激活失败 (第{attempt}次尝试) | "
        f"错误: {str(error)}"
    )


def log_retry(attempt: int, max_retries: int, wait_time: float) -> None:
    """
    记录重试日志。

    Args:
        attempt: 当前尝试次数
        max_retries: 最大重试次数
        wait_time: 等待时间（秒）
    """
    logger.warning(
        f"⏳ 正在重试 ({attempt}/{max_retries}) | "
        f"等待 {wait_time:.1f} 秒..."
    )


def log_shutdown() -> None:
    """记录程序退出日志"""
    logger.info("收到退出信号，正在优雅关闭...")
