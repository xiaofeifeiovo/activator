"""
Activator - AI订阅套餐激活器工具

通过定期发送激活请求来延长AI订阅套餐的流量限制窗口。
"""

__version__ = "1.0.0"
__author__ = "Activator Team"
__description__ = "AI订阅套餐激活器工具"

from .cli import app, main
from .config import Config, ConfigLoader
from .scheduler import ActivatorScheduler

__all__ = [
    "app",
    "main",
    "Config",
    "ConfigLoader",
    "ActivatorScheduler"
]
