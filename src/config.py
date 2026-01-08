"""
配置管理模块

负责加载和验证配置，支持从YAML文件和命令行参数加载配置。
配置优先级：命令行参数 > 配置文件 > 默认值
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse
import yaml
import logging


class URLNormalizer:
    """URL规范化工具类"""

    # 已知的完整endpoint路径
    KNOWN_ENDPOINTS = [
        "/chat/completions",  # OpenAI
        "/messages",          # Anthropic
    ]

    @staticmethod
    def has_full_endpoint(url: str) -> bool:
        """
        检测URL是否已包含完整的endpoint路径

        Args:
            url: 待检测的URL

        Returns:
            True表示已包含完整endpoint, False表示是base URL
        """
        url_lower = url.lower()
        for endpoint in URLNormalizer.KNOWN_ENDPOINTS:
            if url_lower.endswith(endpoint):
                return True
        return False

    @staticmethod
    def normalize_url(url: str, interface_type: str) -> str:
        """
        规范化URL,确保包含完整的endpoint路径

        Args:
            url: 原始URL (可能是base URL或完整URL)
            interface_type: 接口类型 (openai/anthropic)

        Returns:
            规范化后的完整URL
        """
        # 如果URL已包含完整endpoint,直接返回
        if URLNormalizer.has_full_endpoint(url):
            return url

        # 根据接口类型确定endpoint
        endpoint_map = {
            "openai": "/chat/completions",
            "anthropic": "/messages"
        }
        endpoint = endpoint_map.get(interface_type.lower(), "/chat/completions")

        # 处理包含查询参数的URL (如Azure)
        parsed = urlparse(url)

        # 规范化路径部分
        path = parsed.path.rstrip("/")

        # 如果路径不包含endpoint，则拼接
        if not any(path.endswith(ep) for ep in URLNormalizer.KNOWN_ENDPOINTS):
            path = f"{path}{endpoint}"

        # 重建URL，保留查询参数
        normalized_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.params,
            parsed.query,  # 保留查询参数
            parsed.fragment
        ))

        return normalized_url

    @staticmethod
    def validate_url_format(url: str) -> None:
        """
        验证URL格式是否有效

        Args:
            url: 待验证的URL

        Raises:
            ValueError: URL格式无效
        """
        if not url:
            raise ValueError("URL不能为空")

        # 基本的URL格式验证
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError(
                f"URL格式无效: 必须以 http:// 或 https:// 开头\n"
                f"当前值: {url}"
            )

        # 检查URL中是否包含域名
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError(
                f"URL格式无效: 缺少域名\n"
                f"当前值: {url}"
            )


@dataclass
class ActivatorConfig:
    """激活器配置"""
    interval: float = 3.0  # 请求间隔（小时）
    tokens: int = 1000     # 单次请求token数


@dataclass
class APIConfig:
    """API配置"""
    url: str = ""
    apikey: str = ""
    model: str = ""
    interface_type: str = "openai"  # openai 或 anthropic

    def get_normalized_url(self) -> str:
        """
        获取规范化后的URL（包含完整endpoint路径）

        Returns:
            规范化后的完整URL
        """
        return URLNormalizer.normalize_url(self.url, self.interface_type)


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/activator.log"
    rotation: str = "10 MB"


@dataclass
class Config:
    """主配置类，包含所有配置项"""
    activator: ActivatorConfig = field(default_factory=ActivatorConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def validate(self) -> None:
        """验证配置是否有效"""
        if self.activator.interval <= 0:
            raise ValueError("interval必须大于0")

        if self.activator.tokens <= 0:
            raise ValueError("tokens必须大于0")

        if not self.api.url:
            raise ValueError("url不能为空")

        # 验证URL格式
        try:
            URLNormalizer.validate_url_format(self.api.url)
        except ValueError as e:
            raise ValueError(f"URL验证失败: {str(e)}")

        # 检查URL是否被规范化，记录提示
        normalized = URLNormalizer.normalize_url(self.api.url, self.api.interface_type)
        if normalized != self.api.url:
            logger.warning(
                f"URL已自动规范化:\n"
                f"  原始URL: {self.api.url}\n"
                f"  规范化后: {normalized}"
            )

        if not self.api.apikey:
            raise ValueError("apikey不能为空")

        if not self.api.model:
            raise ValueError("model不能为空")

        if self.api.interface_type not in ["openai", "anthropic"]:
            raise ValueError("interface_type必须是 'openai' 或 'anthropic'")

        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是以下之一: {', '.join(valid_levels)}")


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_from_yaml(config_path: Optional[str] = None) -> Config:
        """
        从YAML文件加载配置。

        Args:
            config_path: 配置文件路径

        Returns:
            Config对象
        """
        config = Config()

        if not config_path:
            return config

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)

        if not yaml_data:
            return config

        # 合并配置
        if 'activator' in yaml_data:
            config.activator = ActivatorConfig(**yaml_data['activator'])

        if 'api' in yaml_data:
            config.api = APIConfig(**yaml_data['api'])

        if 'logging' in yaml_data:
            config.logging = LoggingConfig(**yaml_data['logging'])

        return config

    @staticmethod
    def load_from_cli(cli_params: dict) -> Config:
        """
        从命令行参数加载配置。

        Args:
            cli_params: 命令行参数字典

        Returns:
            Config对象
        """
        config = Config()

        # 更新activator配置
        if 'interval' in cli_params and cli_params['interval'] is not None:
            config.activator.interval = cli_params['interval']

        if 'tokens' in cli_params and cli_params['tokens'] is not None:
            config.activator.tokens = cli_params['tokens']

        # 更新API配置
        if 'url' in cli_params and cli_params['url'] is not None:
            config.api.url = cli_params['url']

        if 'apikey' in cli_params and cli_params['apikey'] is not None:
            config.api.apikey = cli_params['apikey']

        if 'model' in cli_params and cli_params['model'] is not None:
            config.api.model = cli_params['model']

        if 'interface_type' in cli_params and cli_params['interface_type'] is not None:
            config.api.interface_type = cli_params['interface_type']

        return config

    @staticmethod
    def load(config_path: Optional[str] = None, cli_params: Optional[dict] = None) -> Config:
        """
        加载配置（YAML文件 + 命令行参数）。

        优先级：命令行参数 > 配置文件 > 默认值

        Args:
            config_path: YAML配置文件路径
            cli_params: 命令行参数字典

        Returns:
            Config对象
        """
        # 先加载YAML配置
        config = ConfigLoader.load_from_yaml(config_path)

        # 再用命令行参数覆盖
        if cli_params:
            cli_config = ConfigLoader.load_from_cli(cli_params)

            # 合并配置
            if cli_config.activator.interval != 3.0:  # 不是默认值
                config.activator.interval = cli_config.activator.interval
            if cli_config.activator.tokens != 1000:  # 不是默认值
                config.activator.tokens = cli_config.activator.tokens

            if cli_config.api.url:
                config.api.url = cli_config.api.url
            if cli_config.api.apikey:
                config.api.apikey = cli_config.api.apikey
            if cli_config.api.model:
                config.api.model = cli_config.api.model
            if cli_config.api.interface_type != "openai":  # 不是默认值
                config.api.interface_type = cli_config.api.interface_type

        # 验证配置
        config.validate()

        return config
