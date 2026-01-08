# Activator

AI订阅套餐激活器工具 - 通过定期发送激活请求来延长AI订阅套餐的流量限制窗口。

## 📖 项目背景

很多AI服务的订阅套餐都有流量限制，通常是每a小时限制b个请求次数。这里的a小时并非固定时间窗口，而是在用户发送第一个请求后激活的a小时内只能发送b个请求。

**Activator** 通过每隔a小时自动发送一个激活请求，使得用户在一次请求周期的末尾开始使用时，短时间内可用的请求次数理论上可以翻倍。

## ✨ 核心特性

- ⏰ **定时激活**: 按照设定的间隔自动发送激活请求
- 🔌 **多接口支持**: 支持 OpenAI-compatible 和 Anthropic 接口
- ⚙️ **灵活配置**: 支持命令行参数和 YAML 配置文件
- 📝 **双重日志**: 终端彩色输出 + 文件详细记录
- 🔄 **自动重试**: 智能的错误处理和重试机制
- 🛡️ **优雅退出**: Ctrl+C 安全退出，保证数据完整性

## 🚀 快速开始

### 安装

1. 克隆仓库
```bash
git clone https://github.com/your-username/activator.git
cd activator
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

### 配置

编辑 `config/config.yaml` 文件：

```yaml
activator:
  interval: 3.0              # 请求间隔（小时）
  tokens: 1000               # 单次请求token数

api:
  url: "https://api.openai.com/v1/chat/completions"
  apikey: "sk-your-api-key-here"
  model: "gpt-4"
  interface_type: "openai"   # openai 或 anthropic

logging:
  level: "INFO"
  file: "logs/activator.log"
  rotation: "10 MB"
```

### 运行

#### 方式1：使用配置文件（推荐）

```bash
python -m src.cli run --config config/config.yaml
```

#### 方式2：使用命令行参数

```bash
python -m src.cli run \
  --interval 3 \
  --tokens 1000 \
  --url "https://api.openai.com/v1/chat/completions" \
  --apikey "sk-your-api-key-here" \
  --model "gpt-4" \
  --interface-type "openai"
```

#### 方式3：混合使用（配置文件 + 命令行覆盖）

```bash
# 使用配置文件，但覆盖间隔时间为5小时
python -m src.cli run --config config/config.yaml --interval 5
```

## 📖 使用说明

### 命令行参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--interval` | `-i` | 请求发送间隔（小时） | `--interval 3` |
| `--tokens` | `-t` | 单次请求token数 | `--tokens 1000` |
| `--url` | `-u` | API端点URL | `--url "https://..."` |
| `--apikey` | `-k` | API密钥 | `--apikey "sk-xxx"` |
| `--model` | `-m` | 模型名称 | `--model "gpt-4"` |
| `--interface-type` | `-I` | 接口类型 | `--interface-type "openai"` |
| `--config` | `-c` | 配置文件路径 | `--config "config.yaml"` |

### 支持的接口类型

#### OpenAI-compatible

支持所有兼容 OpenAI API 格式的服务：

- OpenAI (官方)
- Azure OpenAI
- 各种兼容 OpenAI 的第三方服务

**端点示例**:
```
https://api.openai.com/v1/chat/completions
```

#### Anthropic

支持 Anthropic Claude API：

**端点示例**:
```
https://api.anthropic.com/v1/messages
```

## 📝 日志输出

### 终端输出（彩色）

```
2026-01-08 10:00:00 | INFO     | 日志系统初始化完成
2026-01-08 10:00:00 | INFO     | Activator 调度器启动
2026-01-08 10:00:01 | SUCCESS  | ✅ 激活成功 | Token: 1000 | 下次: 2026-01-08 13:00:01
```

### 文件输出（详细）

```
2026-01-08 10:00:01 | INFO     | 激活请求发送成功
  URL: https://api.openai.com/v1/chat/completions
  模型: gpt-4
  Token数: 1000
  响应: {'usage': {'total_tokens': 1001}}
  下次请求时间: 2026-01-08 13:00:01
```

## 🛠️ 项目结构

```
activator/
├── src/
│   ├── __init__.py       # 包初始化
│   ├── cli.py            # CLI入口
│   ├── config.py         # 配置管理
│   ├── api_client.py     # API客户端
│   ├── scheduler.py      # 定时调度器
│   ├── logger.py         # 日志管理
│   └── utils.py          # 工具函数
├── config/
│   └── config.yaml       # 配置文件模板
├── logs/                 # 日志目录
├── tests/                # 测试目录
├── requirements.txt      # 依赖清单
├── README.md            # 本文档
└── .gitignore
```

## 🔧 开发

### 技术栈

- **Python**: 3.8+
- **HTTP客户端**: httpx (异步)
- **CLI框架**: Typer
- **配置文件**: YAML
- **日志库**: loguru

### SOLID 原则应用

- **单一职责原则**: 每个模块负责单一功能
- **开闭原则**: 通过抽象基类支持新接口类型
- **依赖倒置原则**: 高层模块依赖抽象而非具体实现

### 运行测试

```bash
pytest tests/
```

## ❓ 常见问题

### Q: 如何停止程序？

A: 按 `Ctrl+C` 即可优雅退出。

### Q: 支持哪些接口类型？

A: 目前支持 OpenAI-compatible 和 Anthropic 接口。可以通过继承 `BaseAPIClient` 类来添加更多接口类型。

### Q: Token数量是如何计算的？

A: 目前使用简单的 `"the " * tokens` 方式生成内容。每个 `"the "` 大约对应1个token。后期可以集成 tiktoken 进行精确计算。

### Q: 如何调整日志级别？

A: 在配置文件中修改 `logging.level` 为 `DEBUG`、`INFO`、`WARNING`、`ERROR` 或 `CRITICAL`。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**注意**: 请遵守相关 AI 服务提供商的使用条款和服务协议。
