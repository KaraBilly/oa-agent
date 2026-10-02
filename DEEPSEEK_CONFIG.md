# DeepSeek模型配置说明

> 版本: v2.0  
> 更新时间: 2026-09-09

---

## 当前配置

根据 `config/model_config.yaml`，当前默认模型已切换为 **DeepSeek**：

```yaml
default_model:
  provider: deepseek
  model_name: deepseek-chat
  temperature: 0.7
  max_tokens: 1000
```

---

## 如何配置DeepSeek模型

### 方式1：通过环境变量（推荐）

```bash
# 设置DeepSeek API Key
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# 运行Agent
python3 oa_agent_v2.py
```

### 方式2：直接在代码中配置

```python
from oa_agent_v2 import OAFlowAgentV2, DeepSeekClient, ModelRouter
import os

# 配置DeepSeek客户端
api_key = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
deepseek_client = DeepSeekClient(api_key=api_key, model_name="deepseek-chat")

# 创建自定义ModelRouter
router = ModelRouter()
router.clients[ModelProvider.DEEPSEEK] = deepseek_client

# 初始化Agent
agent = OAFlowAgentV2(model_router=router)

# 处理请求
result = agent.process("我想请明天下午半天年假", "user_001")
print(result)
```

### 方式3：修改配置文件

编辑 `config/model_config.yaml`：

```yaml
default_model:
  provider: deepseek
  model_name: deepseek-chat
  temperature: 0.7
  max_tokens: 1000

models:
  - name: deepseek-chat
    provider: deepseek
    enabled: true
```

---

## DeepSeek API Key 获取

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 登录或注册账号
3. 进入 API Key 管理页面
4. 创建新的 API Key
5. 复制 Key 并设置为环境变量

---

## 测试DeepSeek模型

```bash
# 设置API Key
export DEEPSEEK_API_KEY="sk-xxxxxxxx"

# 运行测试
python3 example_usage.py
```

---

## 切换回其他模型

### 切换回Mock模型

```bash
# 修改config/model_config.yaml
default_model:
  provider: mock
  model_name: mock-v1
```

### 切换回OpenAI模型

```bash
# 设置环境变量
export OPENAI_API_KEY="sk-xxxxxxxx"

# 修改config/model_config.yaml
default_model:
  provider: openai
  model_name: gpt-4
```

---

## 支持的DeepSeek模型

| 模型名称 | 描述 | 适用场景 |
|---------|------|---------|
| deepseek-chat | DeepSeek Chat模型 | 通用对话、意图识别（推荐） |
| deepseek-coder | DeepSeek Coder模型 | 代码生成、技术任务 |

---

## 注意事项

1. DeepSeek API Key 需要从 [DeepSeek Platform](https://platform.deepseek.com/) 获取
2. API Key 请妥善保管，不要提交到版本控制系统
3. 可以设置环境变量 `DEEPSEEK_API_KEY` 来安全存储API Key
4. 当前配置已将默认模型设置为 DeepSeek，直接设置API Key即可使用