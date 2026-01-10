# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**Activator** 是一个 AI 订阅套餐激活器工具，通过定期发送激活请求来延长 AI 订阅套餐的流量限制窗口。核心功能是按照用户设定的时间间隔自动向指定的 API 端点发送激活请求，从而在用户开始使用时获得双倍的请求配额。

## 核心命令

### 运行程序

```bash
# 方式1: 使用配置文件（推荐）
python -m src.cli run --config config/config.yaml

# 方式2: 使用命令行参数
python -m src.cli run --interval 3 --tokens 1000 \
  --url "https://api.openai.com/v1/chat/completions" \
  --apikey "sk-xxx" --model "gpt-4" --interface-type "openai"

# 方式3: 混合使用（配置文件 + 命令行覆盖）
python -m src.cli run --config config/config.yaml --interval 5
```

### 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_specific_file.py

# 带覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

## 架构设计

### 设计原则

项目严格遵循 **SOLID** 原则：

- **单一职责原则 (SRP)**: 每个模块负责单一功能
  - `cli.py`: 仅负责命令行接口
  - `config.py`: 仅负责配置加载和验证
  - `api_client.py`: 仅负责 API 通信
  - `scheduler.py`: 仅负责调度逻辑
  - `logger.py`: 仅负责日志处理

- **开闭原则 (OCP)**: 通过抽象基类 `BaseAPIClient` 支持扩展新接口类型，无需修改现有代码

- **依赖倒置原则 (DIP)**: 高层模块依赖抽象（`BaseAPIClient`）而非具体实现

### 核心模块

#### 1. 配置管理 (`config.py`)

**配置加载优先级**: 命令行参数 > 配置文件 > 默认值

关键特性：
- **URL 规范化**: 自动将 base URL 转换为完整 endpoint
  - OpenAI: 自动补全 `/chat/completions`
  - Anthropic: 自动补全 `/messages`
  - Azure: 保留查询参数（如 `?api-version=xxx`）

- **配置验证**: 在 `Config.validate()` 中统一验证所有配置项

**添加新配置项步骤**:
1. 在对应的 dataclass 中添加字段
2. 在 `Config.validate()` 中添加验证逻辑
3. 在 `ConfigLoader.load_from_yaml()` 和 `load_from_cli()` 中处理新字段

#### 2. API 客户端 (`api_client.py`)

**适配器模式**: 通过 `BaseAPIClient` 抽象基类统一接口

**支持的接口类型**:
- `OpenAIClient`: OpenAI-compatible 接口
- `AnthropicClient`: Anthropic Claude 接口

**添加新接口类型步骤**:
1. 继承 `BaseAPIClient`
2. 实现三个抽象方法：
   - `build_request(tokens)`: 构建请求体
   - `get_headers()`: 返回请求头
   - `parse_response(response)`: 解析响应
3. 在 `APIClientFactory.create()` 中注册新类型

**重试机制**:
- 最大重试次数: 3 次
- 退避策略: 指数退避（最大 60 秒）
- 可重试错误: 网络错误、超时、5xx 错误

#### 3. 调度器 (`scheduler.py`)

**核心组件**:
- `ActivatorScheduler`: 主调度器，管理定时任务
- `GracefulShutdown`: 优雅退出处理器，支持 Ctrl+C

**工作流程**:
1. 启动时立即发送首次激活请求
2. 进入主循环，每隔设定时间发送请求
3. 支持信号处理，优雅退出

#### 4. CLI 接口 (`cli.py`)

使用 **Typer** 框架构建命令行接口，支持:
- 短选项（如 `-i`, `-t`）
- 长选项（如 `--interval`, `--tokens`）
- 配置文件和命令行参数混合使用

## 重要实现细节

### URL 规范化逻辑

`URLNormalizer` 类负责处理 URL 的规范化：

1. **检测完整 endpoint**: 检查 URL 是否已包含 `/chat/completions` 或 `/messages`
2. **自动补全**: 如果是 base URL，根据 `interface_type` 自动补全 endpoint
3. **保留查询参数**: 支持 Azure 等需要查询参数的服务

**示例**:
```python
# 输入: "https://api.openai.com/v1" + interface_type="openai"
# 输出: "https://api.openai.com/v1/chat/completions"

# 输入: "https://resource.openai.azure.com/.../chat/completions?api-version=2023-05-15"
# 输出: 保持不变（已包含完整 endpoint）
```

### 异步上下文管理

所有 API 客户端都实现了异步上下文管理器：
```python
async with self.api_client as client:
    response = await client.send_activation(tokens)
```

这确保 HTTP 客户端的正确初始化和清理。

### 日志系统

使用 **loguru** 库，支持：
- 双重输出：终端彩色输出 + 文件详细记录
- 日志轮转：按大小自动轮转（默认 10 MB）
- 结构化日志：成功/错误/重试都有专门的日志格式

### Token 计算方式

当前使用简单策略：`"the " * tokens`
- 每个 `"the "` 大约对应 1 个 token
- 后期可集成 `tiktoken` 进行精确计算

## 常见开发任务

### 添加新的 API 接口支持

```python
# 在 api_client.py 中添加
class NewAPIClient(BaseAPIClient):
    def build_request(self, tokens: int) -> Dict[str, Any]:
        # 实现请求体构建
        pass

    def get_headers(self) -> Dict[str, str]:
        # 返回必要的请求头
        pass

    def parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        # 解析响应
        pass

# 在 APIClientFactory.create() 中注册
client_classes = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "newapi": NewAPIClient  # 添加这一行
}
```

### 修改重试策略

在 `scheduler.py:68` 初始化时调整参数：
```python
self.retry_strategy = RetryStrategy(
    max_retries=5,        # 修改最大重试次数
    backoff_factor=1.5    # 修改退避因子
)
```

### 添加新的配置验证

在 `config.py:Config.validate()` 中添加：
```python
def validate(self) -> None:
    # ... 现有验证 ...

    # 添加新验证
    if self.api.model not in ["gpt-4", "gpt-3.5-turbo"]:
        raise ValueError("不支持的模型")
```

## 环境信息

- **Python**: 3.8+ (当前环境: 3.11.5)
- **操作系统**: Windows 11
- **HTTP 客户端**: httpx (异步)
- **CLI 框架**: Typer
- **配置格式**: YAML
- **日志库**: loguru

## 关键文件路径

```
src/
├── cli.py              # CLI 入口，命令定义
├── config.py           # 配置管理，URL 规范化
├── api_client.py       # API 客户端，适配器模式
├── scheduler.py        # 调度器，主循环逻辑
├── logger.py           # 日志系统
└── utils.py            # 工具函数

config/
└── config.yaml         # 配置文件模板

tests/
└── __init__.py         # 测试包初始化
```

## 注意事项

1. **API 密钥安全**: 配置文件包含敏感信息，切勿提交到 Git
2. **URL 格式**: 支持 base URL 和完整 URL，程序会自动处理
3. **信号处理**: Windows 下支持 SIGINT (Ctrl+C) 和 SIGBREAK (Ctrl+Break)
4. **异步操作**: 所有 HTTP 请求都是异步的，必须使用 `async/await`
5. **优雅退出**: 使用 `GracefulShutdown` 确保资源正确释放

## 文档同步

修改以下内容时应同步更新文档：
- **新增配置项**: 更新 `README.md`、`config/config.yaml` 注释
- **API 变更**: 更新 `README.md` 的接口类型部分
- **命令行参数**: 更新 `README.md` 的参数表格
- **使用方式**: 更新 `QUICKSTART.md`
