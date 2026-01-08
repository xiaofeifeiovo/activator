"""
工具函数模块

提供项目中使用的通用工具函数。
"""

from datetime import datetime, timedelta


def generate_activation_content(tokens: int) -> str:
    """
    生成指定token数的激活内容。

    使用"the "重复填充来生成指定数量的token。
    注意：这是一个近似值，实际token数可能因分词器而异。

    Args:
        tokens: 需要生成的token数量

    Returns:
        包含重复"the "的字符串

    Examples:
        >>> generate_activation_content(3)
        'the the the '
    """
    return "the " * tokens


def calculate_next_run_time(interval_hours: float) -> datetime:
    """
    计算下次运行时间。

    Args:
        interval_hours: 间隔时间（小时）

    Returns:
        下次运行的datetime对象
    """
    return datetime.now() + timedelta(hours=interval_hours)


def format_timestamp(dt: datetime) -> str:
    """
    格式化datetime对象为字符串。

    Args:
        dt: datetime对象

    Returns:
        格式化的时间字符串 (YYYY-MM-DD HH:MM:SS)
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")
