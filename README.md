# OA Agent - 基于 LangGraph 的意图识别系统

## 项目概述

本项目基于 LangGraph 构建了一个 OA（办公自动化）Agent，专注于请假流程的**意图识别**能力。

## 核心功能

### 1. 意图识别（Intent Recognition）
- 识别用户自然语言中的请假意图
- 支持多类型意图：请假申请、请假查询、请假撤回、其他

### 2. 实体抽取（Entity Extraction）
- 请假类型：年假、事假、病假、调休、婚假、产假、丧假
- 时间信息：日期、时段（上午/下午/全天/半天）
- 时长信息：支持小时、天、半天单位

### 3. 能力分级（Capability Levels）
```
能力等级枚举：
- NOT_IMPLEMENTED = "not_implemented"  # 未实现
- BASIC = "basic"                       # 基础能力
- ENHANCED = "enhanced"                 # 增强能力
- ADVANCED = "advanced"                 # 高级能力
- EXPERT = "expert"                     # 专家级能力
```

当前已实现能力：
- ✅ `intent_recognition`: basic - 意图识别
- ✅ `entity_extraction`: basic - 实体抽取
- ✅ `leave_type_classification`: enhanced - 请假类型分类
- ✅ `time_extraction`: basic - 时间信息抽取

### 4. 意图指标（Metrics）
```python
{
    "accuracy": 0.0,           # 准确率
    "precision": 0.0,          # 精确率
    "recall": 0.0,             # 召回率
    "f1_score": 0.0,           # F1分数
    "avg_confidence": 0.0,     # 平均置信度
    "total_requests": 0,       # 总请求数
    "correct_intents": 0,      # 正确意图数
    "extraction_recall": 0.0   # 实体抽取召回率
}
```

### 5. 澄清机制（Clarification）
当意图识别不完整时，Agent 会自动请求用户补充信息：
- 请假类型缺失 → 询问"想请什么类型的假？"
- 日期缺失 → 询问"想请哪天的假？"
- 时段缺失 → 询问"全天还是半天？上午还是下午？"

## 技术架构

### LangGraph 状态图
```
recognize_intent → generate_response → update_metrics → END
```

### 状态定义（AgentState）
```python
- input_text: str           # 用户输入
- user_id: str              # 用户ID
- intent: UserIntent        # 识别的意图
- response: str             # Agent响应
- metrics: IntentionMetrics # 指标
- conversation_history: list # 对话历史
- capabilities_registry: dict # 能力注册表
```

## 使用方法

### 基本使用
```python
from oa_graph_agent import OAFlowAgent

agent = OAFlowAgent()

result = agent.process("我想请明天下午半天年假", "user_001")

print(result)
```

### 查看能力状态
```python
capabilities = agent.get_capabilities_status()
print(capabilities)
```

### 运行测试
```bash
python3 oa_graph_agent.py
```

## 测试用例示例

| 输入 | 识别意图 | 置信度 | 说明 |
|------|---------|--------|------|
| 我想请明天下午半天年假 | LEAVE_REQUEST | 0.95 | 完整信息，无需澄清 |
| 我要请3天事假 | LEAVE_REQUEST | 0.85 | 缺日期和时段，需澄清 |
| 我今年用了几天年假 | LEAVE_QUERY | 0.80 | 查询意图，直接响应 |
| 我想撤回上周的请假申请 | LEAVE_REQUEST | 0.70 | 撤回意图，需更多信息 |
| 明天上午我要请假 | LEAVE_REQUEST | 0.90 | 缺请假类型，需澄清 |

## 能力扩展路线

### Phase 0 (当前): 请假流程基础能力
- ✅ 意图识别
- ✅ 实体抽取
- ⏳ 冲突校验
- ⏳ 余额校验

### Phase 1: 增强能力
- 附件OCR处理
- 撤销/取消功能
- 催办提醒
- Web入口

### Phase 2: 扩展到其他HR流程
- 调休、加班
- 出差、报销
- 入职、转正、离职

## 输出示例

```
======================================================================
OA Agent - 基于 LangGraph 的意图识别系统
======================================================================

【测试用例 1】
输入: 我想请明天下午半天年假
识别意图: IntentType.LEAVE_REQUEST
置信度: 0.95
提取实体: ['intent: leave_request', 'leave_type: annual_leave', 'time_slot: afternoon_half', 'start_date: tomorrow']
需要澄清: False
缺失字段: []
响应: 已识别您的请假申请：annual_leave，时间：tomorrow，afternoon_half。
启用能力: ['intent_recognition', 'entity_extraction', 'leave_type_classification', 'time_extraction']
```

## 安装依赖

```bash
pip install langgraph pydantic
```

## 未来改进方向

1. **意图准确率优化**
   - 引入更强大的NLP模型
   - 添加训练数据集
   - 实现A/B测试

2. **能力分级量化**
   - 为每个能力定义更详细的评估指标
   - 实现自动能力升级机制

3. **多轮对话管理**
   - 改进状态追踪
   - 支持更复杂的对话上下文

4. **企业微信集成**
   - 对接企业微信机器人API
   - 实现消息回执

5. **HR系统对接**
   - 员工主数据查询
   - 请假余额校验
   - 审批链解析

## 文件结构

```
oa-agent/
├── oa_graph_agent.py      # 主要实现文件
├── oa_agent.py            # 简化版实现
└── README.md              # 本文件
```

## 许可证

MIT License
