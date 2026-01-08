# 快速开始示例

## 示例1：使用OpenAI API

### 1. 创建配置文件 `openai_config.yaml`

```yaml
activator:
  interval: 3.0              # 每3小时发送一次
  tokens: 1000               # 每次请求1000个token

api:
  url: "https://api.openai.com/v1/chat/completions"
  apikey: "sk-your-openai-api-key"
  model: "gpt-4"
  interface_type: "openai"

logging:
  level: "INFO"
  file: "logs/openai_activator.log"
  rotation: "10 MB"
```

### 2. 运行

```bash
python -m src.cli run --config openai_config.yaml
```

## 示例2：使用Anthropic Claude API

### 1. 创建配置文件 `claude_config.yaml`

```yaml
activator:
  interval: 4.0              # 每4小时发送一次
  tokens: 1000

api:
  url: "https://api.anthropic.com/v1/messages"
  apikey: "sk-ant-your-anthropic-api-key"
  model: "claude-3-opus-20240229"
  interface_type: "anthropic"

logging:
  level: "INFO"
  file: "logs/claude_activator.log"
```

### 2. 运行

```bash
python -m src.cli run --config claude_config.yaml
```

## 示例3：使用命令行参数

```bash
# 完整命令行参数方式
python -m src.cli run \
  --interval 2 \
  --tokens 500 \
  --url "https://api.openai.com/v1/chat/completions" \
  --apikey "sk-xxx" \
  --model "gpt-3.5-turbo" \
  --interface-type "openai"
```

## 示例4：混合使用配置文件和命令行参数

```bash
# 使用配置文件，但覆盖间隔时间为5小时
python -m src.cli run --config openai_config.yaml --interval 5
```

## 示例5：使用Azure OpenAI

### 1. 创建配置文件 `azure_config.yaml`

```yaml
activator:
  interval: 3.0
  tokens: 1000

api:
  url: "https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-05-15"
  apikey: "your-azure-api-key"
  model: "gpt-4"  # deployment名称
  interface_type: "openai"

logging:
  level: "INFO"
  file: "logs/azure_activator.log"
```

### 2. 运行

```bash
python -m src.cli run --config azure_config.yaml
```

## 示例6：调试模式

```bash
# 使用配置文件，但设置日志级别为DEBUG
python -m src.cli run --config openai_config.yaml
# 然后编辑配置文件中的 logging.level 为 "DEBUG"
```

## 运行输出示例

```
2026-01-08 10:00:00 | INFO     | 日志系统初始化完成
2026-01-08 10:00:00 | INFO     | Activator 调度器启动
2026-01-08 10:00:00 | INFO     | 接口类型: openai
2026-01-08 10:00:00 | INFO     | API端点: https://api.openai.com/v1/chat/completions
2026-01-08 10:00:00 | INFO     | 模型: gpt-4
2026-01-08 10:00:00 | INFO     | 请求间隔: 3.0 小时
2026-01-08 10:00:00 | INFO     | Token数量: 1000
2026-01-08 10:00:00 | INFO     | ============================================================
2026-01-08 10:00:00 | INFO     | 发送首次激活请求...
2026-01-08 10:00:01 | SUCCESS  | ✅ 激活成功 | Token: 1000 | 下次: 2026-01-08 13:00:01
2026-01-08 10:00:01 | INFO     | 下次运行时间: 2026-01-08 13:00:01
```

## 停止程序

按 `Ctrl+C` 即可优雅退出：

```
^C2026-01-08 10:05:00 | INFO     | 收到退出信号，正在优雅关闭...
2026-01-08 10:05:00 | INFO     | 调度器已停止
```

## 注意事项

1. **API密钥安全**：不要将包含真实API密钥的配置文件提交到Git
2. **日志文件**：日志文件会保存在 `logs/` 目录下
3. **间隔时间**：建议根据您的订阅套餐限制设置合理的间隔时间
4. **网络连接**：确保您的网络可以访问相应的API端点

## 故障排查

### 问题1：连接超时

**原因**：网络问题或API端点不可达

**解决**：
- 检查网络连接
- 验证API端点URL是否正确
- 检查防火墙设置

### 问题2：认证失败

**原因**：API密钥无效或过期

**解决**：
- 验证API密钥是否正确
- 检查API密钥是否已过期
- 确认API密钥有相应的权限

### 问题3：配置文件错误

**原因**：YAML格式错误或配置项错误

**解决**：
- 使用YAML验证器检查配置文件格式
- 参考 `config/config.yaml` 模板
- 查看错误日志获取详细信息

## 高级用法

### 1. 使用环境变量

虽然当前版本不支持直接从环境变量读取，但您可以通过命令行参数使用：

```bash
# Linux/Mac
python -m src.cli run --config config.yaml --apikey $OPENAI_API_KEY

# Windows
python -m src.cli run --config config.yaml --apikey %OPENAI_API_KEY%
```

### 2. 定时任务

您可以使用系统的定时任务工具来启动activator：

**Windows 任务计划程序**：
- 创建基本任务
- 触发器：启动时
- 操作：启动程序
- 程序：`python`
- 参数：`-m src.cli run --config config.yaml`

**Linux Cron**：
```bash
@reboot python /path/to/activator -m src.cli run --config config.yaml
```

### 3. 多实例运行

您可以为不同的API运行多个activator实例：

```bash
# 终端1：OpenAI
python -m src.cli run --config openai_config.yaml

# 终端2：Anthropic
python -m src.cli run --config claude_config.yaml
```

每个实例使用不同的配置文件和日志文件。
