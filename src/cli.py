"""
CLI入口模块

使用Typer构建命令行界面。
"""

import asyncio
import sys
from typing import Optional

import typer

from .config import ConfigLoader
from .scheduler import ActivatorScheduler
from .logger import setup_logger, logger

# 创建Typer应用
app = typer.Typer(
    name="activator",
    help="Activator - AI订阅套餐激活器工具",
    add_completion=False
)


@app.command()
def run(
    interval: Optional[float] = typer.Option(
        None,
        "--interval", "-i",
        help="请求发送间隔（小时）"
    ),
    tokens: Optional[int] = typer.Option(
        None,
        "--tokens", "-t",
        help="单次请求token数"
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url", "-u",
        help="API端点URL"
    ),
    apikey: Optional[str] = typer.Option(
        None,
        "--apikey", "-k",
        help="API密钥"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model", "-m",
        help="模型名称"
    ),
    interface_type: Optional[str] = typer.Option(
        None,
        "--interface-type", "-I",
        help="接口类型 (openai/anthropic)"
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径 (YAML格式)"
    )
):
    """
    运行Activator调度器。

    可以通过命令行参数或配置文件提供配置。
    配置优先级：命令行参数 > 配置文件 > 默认值

    Examples:
        # 使用命令行参数
        activator run --interval 3 --tokens 1000 \\
            --url "https://api.openai.com/v1/chat/completions" \\
            --apikey "sk-xxx" --model "gpt-4"

        # 使用配置文件
        activator run --config config/config.yaml

        # 混合使用（配置文件 + 命令行覆盖）
        activator run --config config.yaml --interval 5
    """
    try:
        # 收集命令行参数
        cli_params = {
            "interval": interval,
            "tokens": tokens,
            "url": url,
            "apikey": apikey,
            "model": model,
            "interface_type": interface_type
        }

        # 加载配置
        loader = ConfigLoader()
        cfg = loader.load(config_path=config, cli_params=cli_params)

        # 设置日志
        setup_logger(cfg)

        # 创建并运行调度器
        scheduler = ActivatorScheduler(cfg)

        # 运行异步主循环
        asyncio.run(scheduler.run())

    except FileNotFoundError as e:
        logger.error(f"文件错误: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"配置错误: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("程序已中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        sys.exit(1)


@app.command()
def version():
    """显示版本信息"""
    typer.echo("Activator v1.0.0")


def main():
    """主入口函数"""
    app()


if __name__ == "__main__":
    main()
