# DeepSeek模型快速切换指南

> 版本: v2.0  
> 更新时间: 2026-09-09

---

## ✅ 无需修改代码即可切换到DeepSeek模型！

当前配置已将默认模型设置为 **DeepSeek**，你只需要设置API Key即可使用。

---

## 🚀 快速开始（3步）

### 步骤1：获取DeepSeek API Key

1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 登录/注册账号
3. 进入 **API Keys** 页面
4. 点击 **Create New API Key**
5. 复制生成的 Key（格式: `sk-xxxxxxxxxxxx`）

### 步骤2：设置API Key

```bash
# 临时设置（仅本次有效）
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"

# 或写入环境变量文件（持久化）
echo 'export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

### 步骤3：运行Agent

```bash
cd /Users/maple/Documents/agent-projects/oa-agent
python3 oa_agent_v2.py
```

---

## 📋 验证配置

运行以下命令验证DeepSeek模型是否启用：

```bash
python3 switch_to_deepseek.py
```

输出应显示：
```
✓ DeepSeek模型已配置完成！
```

---

## 🔄 切换回其他模型

### 切换回Mock模型（无需API Key）

```bash
# 修改config/model_config.yaml
default_model:
  provider: mock
  model_name: mock-v1

# 直接运行（无需设置API Key）
python3 oa_agent_v2.py
```

### 切换回OpenAI模型

```bash
# 设置OpenAI API Key
export OPENAI_API_KEY="sk-xxxxxxxx"

# 修改config/model_config.yaml
default_model:
  provider: openai
  model_name: gpt-4

python3 oa_agent_v2.py
```

### 切换回Anthropic模型

```bash
# 设置Anthropic API Key
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxx"

# 修改config/model_config.yaml
default_model:
  provider: anthropic
  model_name: claude-3-opus

python3 oa_agent_v2.py
```

---

## 📝 可用模型列表

| 模型 | 提供商 | 配置方式 | API Key环境变量 |
|-----|--------|---------|----------------|
| deepseek-chat | DeepSeek | `provider: deepseek` | `DEEPSEEK_API_KEY` |
| gpt-4 | OpenAI | `provider: openai` | `OPENAI_API_KEY` |
| claude-3-opus | Anthropic | `provider: anthropic` | `ANTHROPIC_API_KEY` |
| mock-v1 | Mock | `provider: mock` | 无需 |

---

## 💡 配置文件位置

- 主配置: `config/model_config.yaml`
- DeepSeek配置: `DEEPSEEK_CONFIG.md`
- 模型使用示例: `example_usage.py`
- 切换脚本: `switch_to_deepseek.py`

---

## ⚠️ 注意事项

1. **API Key安全**: 不要将API Key提交到Git仓库，使用环境变量或 `.env` 文件
2. **模型选择**: DeepSeek适合通用对话场景，OpenAI适合复杂任务
3. **成本控制**: 不同模型的计费标准不同，请根据需求选择

---

## 📚 相关文档

- [DeepSeek模型配置](./DEEPSEEK_CONFIG.md)
- [模型使用示例](./example_usage.py)
- [模型配置文件](./config/model_config.yaml)