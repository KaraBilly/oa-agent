# OA Agent v3.0 - 完全配置驱动使用指南

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

## 🚀 快速开始

### 步骤1: 设置DeepSeek API Key

```bash
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### 步骤2: 修改配置文件（如果需要）

编辑 `config/model_config.yaml`:

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
```

### 步骤3: 运行Agent

```bash
cd /Users/maple/Documents/agent-projects/oa-agent
python3 oa_agent_v3_config_driven.py
```

---

## 📊 输出示例

```
✓ 已加载模型: deepseek-chat (deepseek)
================================================================================
OA Agent v3.0 - 完全配置驱动的LLM模型切换架构
================================================================================

当前模型配置:
  默认模型: deepseek-chat
  可用模型: [{'name': 'deepseek-chat', 'provider': 'deepseek'}]

【测试用例 1】
输入: 我想请明天下午半天年假
  识别意图: IntentType.LEAVE_REQUEST
  置信度: 0.95
  使用模型: deepseek-chat    ← 从配置文件读取
  响应: 已识别您的请假申请：annual_leave，时间：tomorrow，afternoon_half。
```

---

## 🔄 如何切换模型

### 方式1: 修改配置文件（推荐）

**切换到OpenAI**:
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

**输出显示**:
```
  使用模型: gpt-4
```

### 方式2: 切换到Anthropic

**修改配置文件**:
```yaml
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

## 📋 配置文件详解

### `config/model_config.yaml`

```yaml
# 默认模型设置
default_model:
  provider: deepseek         # 模型提供商: deepseek, openai, anthropic, mock
  model_name: deepseek-chat  # 模型名称
  temperature: 0.7           # 温度参数
  max_tokens: 1000           # 最大token数

# 可用模型列表
models:
  - name: deepseek-chat      # 模型名称
    provider: deepseek       # 提供商
    enabled: true            # 是否启用
    
  - name: gpt-4
    provider: openai
    enabled: false
    
  - name: claude-3-opus
    provider: anthropic
    enabled: false

# 意图->模型映射（可选）
intent_model_mapping:
  leave_request: deepseek-chat
  leave_query: deepseek-chat
  leave_withdraw: deepseek-chat
  other: deepseek-chat

# 模型优先级
model_priority:
  - deepseek-chat
  - mock-v1
  - gpt-4
  - claude-3-opus
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

# 持久化
echo 'export DEEPSEEK_API_KEY="sk-xxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

### 临时使用

```bash
DEEPSEEK_API_KEY="sk-xxxxxxxx" python3 oa_agent_v3_config_driven.py
```

---

## 📁 支持的模型

| 提供商 | 模型名称 | 配置provider | 环境变量 | 状态 |
|-------|---------|-------------|---------|------|
| DeepSeek | deepseek-chat | `deepseek` | `DEEPSEEK_API_KEY` | ✅ 默认 |
| DeepSeek | deepseek-coder | `deepseek` | `DEEPSEEK_API_KEY` | ⏳ 可用 |
| OpenAI | gpt-4 | `openai` | `OPENAI_API_KEY` | ⏳ 可用 |
| OpenAI | gpt-3.5-turbo | `openai` | `OPENAI_API_KEY` | ⏳ 可用 |
| Anthropic | claude-3-opus | `anthropic` | `ANTHROPIC_API_KEY` | ⏳ 可用 |
| Mock | mock-v1 | `mock` | 无需 | ⏳ 测试用 |

---

## 🧪 测试配置

运行测试脚本验证配置:

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

## 📁 文件结构

```
oa-agent/
├── config/
│   ├── model_config.yaml       # 配置文件（所有LLM配置）
│   └── llm_manager.py          # LLM客户端管理器
├── oa_agent_v3_config_driven.py # 主程序（配置驱动）
├── test_config_driven.py       # 配置测试脚本
├── CONFIG_DRIVEN_GUIDE.md      # 配置驱动指南
└── README.md
```

---

## 🎓 与版本对比

| 特性 | v2.0 | v3.0 (配置驱动) |
|-----|------|----------------|
| 修改代码切换模型 | 需要 | ❌ 不需要 |
| 修改配置文件切换模型 | 部分支持 | ✅ 完全支持 |
| API Key管理 | 代码硬编码 | 环境变量 |
| 新增模型 | 需要改代码 | 只改配置 |
| 团队协作 | 代码冲突 | 配置文件隔离 |

---

## ✅ 验证配置

运行以下命令验证:

```bash
# 1. 检查配置文件
cat config/model_config.yaml

# 2. 运行测试脚本
python3 test_config_driven.py

# 3. 运行主程序
python3 oa_agent_v3_config_driven.py
```

---

## 🎯 使用场景

### 场景1: 开发测试
```yaml
default_model:
  provider: mock
  model_name: mock-v1
```
无需API Key，快速测试。

### 场景2: 生产环境
```yaml
default_model:
  provider: deepseek
  model_name: deepseek-chat
```
设置DEEPSEEK_API_KEY后即可使用。

### 场景3: 多模型测试
```yaml
# 意图->模型映射
intent_model_mapping:
  leave_request: gpt-4      # 请假用强模型
  leave_query: mock-v1      # 查询用轻量模型
```

---

## 📚 相关文档

- [配置驱动指南](./CONFIG_DRIVEN_GUIDE.md)
- [模型配置文件](./config/model_config.yaml)
- [LLM管理器](./config/llm_manager.py)
- [主程序](./oa_agent_v3_config_driven.py)
- [测试脚本](./test_config_driven.py)