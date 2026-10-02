# OA Agent 模型配置说明

> 版本：v2.0  
> 更新时间：2026-09-09

---

## 当前使用的模型

目前 OA Agent v2.0 使用的是 **Mock模型** (`mock-v1`)，这是一个用于开发测试的模拟模型。

### 查看当前模型

运行以下命令查看当前模型：

```bash
python3 oa_agent_v2.py
```

输出中会显示：
```
使用的模型: default
数据源: mock
```

---

## 如何配置模型

### 方式1：修改配置文件（推荐）

编辑 `config/model_config.yaml`：

```yaml
default_model:
  provider: mock  # 可选: mock, openai, anthropic, local
  model_name: mock-v1
  temperature: 0.7
  max_tokens: 1000

models:
  - name: mock-v1
    provider: mock
    enabled: true
    
  - name: gpt-4
    provider: openai
    enabled: false  # 设置为true启用
    # api_key: ${OPENAI_API_KEY}  # 从环境变量读取

intent_model_mapping:
  leave_request: mock-v1  # 请假意图使用Mock模型
  leave_query: mock-v1    # 查询意图使用Mock模型
```

### 方式2：使用环境变量

```bash
# 设置API Key
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# 运行Agent
python3 oa_agent_v2.py
```

### 方式3：代码中直接配置

```python
from oa_agent_v2 import (
    OAFlowAgentV2, 
    OpenAIClient, 
    AnthropicClient, 
    ModelRouter,
    ModelProvider
)
import os

# 配置OpenAI模型
api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
openai_client = OpenAIClient(api_key=api_key, model_name="gpt-4")

# 创建自定义ModelRouter
router = ModelRouter()
router.clients[ModelProvider.OPENAI] = openai_client

# 初始化Agent
agent = OAFlowAgentV2(model_router=router)

# 处理请求
result = agent.process("我想请明天下午半天年假", "user_001")
print(result)
```

---

## 支持的模型提供商

| 提供商 | 模型名称 | 配置方式 | 状态 |
|-------|---------|---------|------|
| Mock | mock-v1 | 默认启用 | ✅ 开发测试 |
| OpenAI | gpt-4, gpt-3.5-turbo | 环境变量 `OPENAI_API_KEY` | ⏳ 待配置 |
| Anthropic | claude-3-opus | 环境变量 `ANTHROPIC_API_KEY` | ⏳ 待配置 |
| Local | 本地模型 | 自定义客户端 | ⏳ 待实现 |

---

## 模型选择策略

### 默认策略

```python
模型 = {
    "leave_request": "mock-v1",
    "leave_query": "mock-v1",
    "leave_withdraw": "mock-v1",
    "other": "mock-v1"
}
```

### 自定义策略

你可以根据意图类型选择不同模型：

```python
# 举例：复杂的意图使用GPT-4
intent_model_mapping = {
    "leave_request": "gpt-4",      # 请假申请用强模型
    "leave_query": "mock-v1",      # 查询用轻量模型
    "leave_withdraw": "mock-v1",   # 撤回用轻量模型
}
```

---

## API Key 配置

### OpenAI

```bash
# 临时设置
export OPENAI_API_KEY="sk-..."

# 或写入环境变量文件
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Anthropic

```bash
# 临时设置
export ANTHROPIC_API_KEY="sk-ant-..."

# 或写入环境变量文件
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

---

## 快速切换模型

### 临时切换（代码中）

```python
from oa_agent_v2 import OAFlowAgentV2, OpenAIClient, ModelRouter

# 创建OpenAI客户端
router = ModelRouter()
router.clients[ModelProvider.OPENAI] = OpenAIClient("your-api-key")

# 使用OpenAI模型
agent = OAFlowAgentV2(model_router=router)
result = agent.process("我想请明天下午半天年假", "user_001")
```

### 切换数据源

```python
from oa_agent_v2 import OAFlowAgentV2, MockDataSource, DatabaseDataSource

# 使用Mock数据源（默认）
agent = OAFlowAgentV2(data_source=MockDataSource())

# 或使用数据库数据源
# agent = OAFlowAgentV2(data_source=DatabaseDataSource(db_type="sqlite"))
```

---

## 模型使用统计

Agent 会自动统计每个模型的使用次数：

```python
result = agent.process("我想请明天下午半天年假", "user_001")

# 查看模型统计
print(result['metrics']['model_stats'])
# 输出: {'default': 1}
```

---

## 故障排查

### 问题1：无法调用OpenAI模型

**错误**: `ModuleNotFoundError: No module named 'openai'`

**解决方案**:
```bash
pip3 install openai --break-system-packages
```

### 问题2：API Key 无效

**错误**: `AuthenticationError: Incorrect API key provided`

**解决方案**: 检查环境变量或代码中的API Key是否正确。

### 问题3：模型未启用

**解决方案**: 在 `config/model_config.yaml` 中将 `enabled: false` 改为 `enabled: true`。

---

## 下一步

1. 配置真实模型API Key（OpenAI/Anthropic）
2. 测试模型性能和准确率
3. 根据需求调整模型选择策略
4. 实现更复杂的模型路由逻辑（如根据复杂度自动选择模型）
