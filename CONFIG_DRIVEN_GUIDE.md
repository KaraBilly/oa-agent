# OA Agent - 完全配置驱动架构 (OpenCLAW风格)

> 版本: v3.0  
> 更新时间: 2026-09-09

---

## 🎯 核心特性

### 类似OpenCLAW的配置驱动架构

- ✅ **无需修改代码** - 所有LLM配置通过YAML文件管理
- ✅ **环境变量存储API Key** - 安全且灵活
- ✅ **运行时切换模型** - 动态加载不同LLM客户端
- ✅ **配置文件即代码** - 一份配置文件控制所有模型

---

## 📋 配置文件结构

### `config/model_config.yaml`

```yaml
# 默认模型设置
default_model:
  provider: deepseek
  model_name: deepseek-chat
  temperature: 0.7
  max_tokens: 1000

# 可用模型列表
models:
  - name: deepseek-chat
    provider: deepseek
    enabled: true
    
  - name: gpt-4
    provider: openai
    enabled: false
    
  - name: claude-3-opus
    provider: anthropic
    enabled: false

# 意图->模型映射
intent_model_mapping:
  leave_request: deepseek-chat
  leave_query: deepseek-chat

# 模型优先级
model_priority:
  - deepseek-chat
  - mock-v1
```

---

## 🚀 如何使用

### 方式1: 使用DeepSeek模型

**步骤1**: 设置API Key
```bash
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

**步骤2**: 修改配置文件
```yaml
# config/model_config.yaml
default_model:
  provider: deepseek
  model_name: deepseek-chat
```

**步骤3**: 运行
```bash
python3 oa_agent_v3_config_driven.py
```

### 方式2: 切换到OpenAI模型

**只需修改配置文件**:
```yaml
# config/model_config.yaml
default_model:
  provider: openai
  model_name: gpt-4
```

**设置API Key**:
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

**运行**:
```bash
python3 oa_agent_v3_config_driven.py
```

### 方式3: 切换到Anthropic模型

**只需修改配置文件**:
```yaml
# config/model_config.yaml
default_model:
  provider: anthropic
  model_name: claude-3-opus
```

**设置API Key**:
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxx"
```

**运行**:
```bash
python3 oa_agent_v3_config_driven.py
```

---

## 🔑 API Key管理

### 环境变量方式（推荐）

```bash
# DeepSeek
export DEEPSEEK_API_KEY="sk-xxxxxxxx"

# OpenAI
export OPENAI_API_KEY="sk-xxxxxxxx"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxx"

# 写入.zshrc实现持久化
echo 'export DEEPSEEK_API_KEY="sk-xxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

### 临时使用

```bash
DEEPSEEK_API_KEY="sk-xxxxxxxx" python3 oa_agent_v3_config_driven.py
```

---

## 📊 支持的模型

| 提供商 | 模型名称 | 配置provider | 环境变量 | 状态 |
|-------|---------|-------------|---------|------|
| DeepSeek | deepseek-chat | `deepseek` | `DEEPSEEK_API_KEY` | ✅ 默认 |
| DeepSeek | deepseek-coder | `deepseek` | `DEEPSEEK_API_KEY` | ⏳ 可用 |
| OpenAI | gpt-4 | `openai` | `OPENAI_API_KEY` | ⏳ 可用 |
| OpenAI | gpt-3.5-turbo | `openai` | `OPENAI_API_KEY` | ⏳ 可用 |
| Anthropic | claude-3-opus | `anthropic` | `ANTHROPIC_API_KEY` | ⏳ 可用 |
| Mock | mock-v1 | `mock` | 无需 | ⏳ 测试用 |

---

## 🔧 添加新模型

### 1. 在配置文件中添加

```yaml
models:
  - name: new-model
    provider: new-provider
    enabled: true
```

### 2. 添加客户端类

在 `oa_agent_v3_config_driven.py` 中添加:

```python
class NewProviderClient(BaseModelClient):
    """新提供商客户端"""
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        # 实现意图识别
        pass
```

### 3. 在llm_manager.py中添加导入

```python
elif provider == "new-provider":
    from oa_agent_v3_config_driven import NewProviderClient
    api_key = os.getenv("NEW_PROVIDER_API_KEY", "")
    return NewProviderClient(api_key=api_key, model_name=model_name)
```

---

## 📁 文件结构

```
oa-agent/
├── config/
│   ├── model_config.yaml       # 配置文件（所有LLM配置在这里）
│   ├── llm_manager.py          # LLM客户端管理器
│   └── config_manager.py       # 配置管理器
├── oa_agent_v3_config_driven.py # 主程序（完全配置驱动）
├── test_config_driven.py       # 配置测试脚本
└── CONFIG_DRIVEN_GUIDE.md      # 本指南
```

---

## ✅ 验证配置

运行测试脚本:

```bash
python3 test_config_driven.py
```

输出应显示:
```
✓ 已加载模型: deepseek-chat (deepseek)
默认模型: deepseek-chat
可用模型: [{'name': 'deepseek-chat', 'provider': 'deepseek'}]
```

---

## 🎓 配置驱动的优势

| 特性 | 传统方式 | 配置驱动 |
|-----|---------|---------|
| 添加新模型 | 修改代码 + 重新编译 | 只修改配置文件 |
| 切换API Key | 修改代码 | 设置环境变量 |
| 多环境配置 | 多个代码分支 | 多个配置文件 |
| 团队协作 | 代码冲突风险 | 配置文件隔离 |
| 版本控制 | 代码历史混乱 | 配置文件清晰 |

---

## 🚨 注意事项

1. **API Key安全**: 不要将API Key提交到Git仓库
2. **环境变量**: 推荐使用 `.env` 文件 + `.gitignore`
3. **配置验证**: 修改配置后运行 `test_config_driven.py` 验证
4. **模型选择**: 根据任务复杂度选择合适的模型

---

## 📚 相关文档

- [配置文件示例](./config/model_config.yaml)
- [LLM管理器](./config/llm_manager.py)
- [主程序](./oa_agent_v3_config_driven.py)
- [测试脚本](./test_config_driven.py)