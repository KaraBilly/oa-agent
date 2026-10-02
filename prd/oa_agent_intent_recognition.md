# PRD - OA Agent 请假流程意图识别系统

> 产品需求文档  
> 版本：v2.0  
> 日期：2026-09-09  
> 作者：AI Assistant

---

## 1. 产品概述

### 1.1 产品目标

构建一个基于 LangGraph 的 OA Agent，专注于**请假流程的自然语言理解**，实现从用户自然语言输入到结构化请假申请的自动转换，最终交付可跑通「自然语言发起 → 审批 → 回写」闭环的 MVP。

### 1.2 MVP 范围

本 PRD 聚焦于 **Phase 0 的核心能力 - 意图识别**，具体包括：
- 自然语言解析请假意图
- 实体抽取（时间、类型）
- 能力分级与指标量化
- 澄清机制
- LangGraph 状态图实现

### 1.3 新增特性 (v2.0)

本版本新增以下关键特性：
- **外部数据源支持**：支持连接Mock数据或真实数据库
- **多模型支持**：类似Hermes Agent的模型路由策略
- **模型选择策略**：根据意图类型和复杂度自动选择模型
- **Mock数据服务**：无需外部依赖即可快速开发测试

### 1.3 用户价值

| 用户痛点 | 本产品解决方案 |
|---------|---------------|
| 发起请假流程繁琐，需填写多个表单字段 | 自然语言输入，Agent 自动识别并结构化 |
| 请假类型、规则复杂，员工易出错 | Agent 智能识别请假类型并校验规则 |
| 多轮沟通确认信息，耗时长 | Agent 自动澄清缺失信息，提高效率 |
| 无法量化 Agent 能力成熟度 | 能力分级 + 多维度指标监控 |

---

## 2. 功能需求

### 2.1 意图识别模块

#### 2.1.1 核心能力
| 能力名称 | 描述 | 优先级 |
|---------|------|--------|
| 意图分类 | 识别用户输入属于哪一类 HR 流程 | P0 |
| 实体抽取 | 提取时间、类型、时长等关键信息 | P0 |
| 置信度计算 | 评估识别结果的可靠性 | P1 |
| 澄清判断 | 判断是否需要向用户追问 | P0 |

#### 2.1.2 意图类型定义
```python
class IntentType(Enum):
    LEAVE_REQUEST = "leave_request"    # 请假申请
    LEAVE_QUERY = "leave_query"        # 请假查询
    LEAVE_WITHDRAW = "leave_withdraw"  # 请假撤回
    OTHER = "other"                    # 其他
```

#### 2.1.3 实体定义

**请假类型**
| 类型 | 英文名 | 是否需要附件 | 最小单位 |
|-----|--------|------------|---------|
| 年假 | annual_leave | 否 | 0.5天 |
| 事假 | personal_leave | 否 | 0.5天 |
| 病假 | sick_leave | 是（病假条） | 0.5天 |
| 调休 | remuneration_leave | 否 | 0.5天 |
| 婚假 | marriage_leave | 否 | 1天 |
| 产假 | maternity_leave | 是（证明） | 1天 |
| 丧假 | bereavement_leave | 否 | 1天 |

**时间槽**
| 槽位 | 英文名 | 示例 |
|-----|--------|------|
| 全天 | full_day | 明天、后天 |
| 上午 | morning | 明天上午 |
| 下午 | afternoon | 明天下午 |
| 上午半天 | morning_half | 明天上午半天 |
| 下午半天 | afternoon_half | 明天下午半天 |

#### 2.1.4 识别规则

| 规则类型 | 描述 | 示例 |
|---------|------|------|
| 关键词匹配 | 精确匹配预定义关键词 | "我想请明天下午半天年假" |
| 模糊匹配 | 语义相近的表达 | "休假"、"请长假" |
| 上下文判断 | 结合前后文判断 | "撤回请假申请" → LEAVE_WITHDRAW |

### 2.2 能力分级模块

#### 2.2.1 能力分级标准

| 等级 | 标准 | 评估指标 |
|-----|------|---------|
| NOT_IMPLEMENTED | 未实现 | 功能缺失 |
| BASIC | 基础功能可用 | 置信度 > 0.5，准确率 > 70% |
| ENHANCED | 功能完整 | 置信度 > 0.7，准确率 > 85% |
| ADVANCED | 智能优化 | 置信度 > 0.85，准确率 > 95% |
| EXPERT | 专家级 | 置信度 > 0.95，准确率 > 99% |

#### 2.2.2 能力清单

| 能力ID | 能力名称 | 当前等级 | 下一等级目标 |
|-------|---------|---------|-------------|
| intent_recognition | 意图识别 | BASIC | ENHANCED |
| entity_extraction | 实体抽取 | BASIC | ENHANCED |
| leave_type_classification | 请假类型分类 | ENHANCED | ADVANCED |
| time_extraction | 时间信息抽取 | BASIC | ENHANCED |
| clarification | 多轮澄清 | NOT_IMPLEMENTED | BASIC |
| conflict_check | 冲突校验 | NOT_IMPLEMENTED | BASIC |
| balance_check | 余额校验 | NOT_IMPLEMENTED | BASIC |
| approval_chain | 审批链解析 | NOT_IMPLEMENTED | NOT_IMPLEMENTED |

### 2.3 指标模块

#### 2.3.1 核心指标定义

| 指标 | 公式 | 说明 |
|-----|------|------|
| accuracy | correct_intents / total_requests | 总体准确率 |
| precision | correct_intents / predicted_intents | 精确率 |
| recall | correct_intents / actual_intents | 召回率 |
| f1_score | 2 * precision * recall / (precision + recall) | 综合评分 |
| avg_confidence | sum(confidence) / total_requests | 平均置信度 |
| extraction_recall | matching_entities / actual_entities | 实体抽取召回率 |

#### 2.3.2 质量目标

| 指标 | Phase 0 目标 | Phase 1 目标 | Phase 2 目标 |
|-----|------------|------------|------------|
| 准确率 | > 80% | > 90% | > 95% |
| 置信度 | > 0.7 | > 0.8 | > 0.9 |
| 实体召回率 | > 75% | > 85% | > 90% |

### 2.4 澄清机制模块

#### 2.4.1 澄清触发条件

当以下任一条件满足时，触发澄清：
- 未识别出请假类型
- 未识别出日期信息
- 未识别出时间槽（上午/下午/全天）

#### 2.4.2 澄清问题模板

| 缺失字段 | 澄清问题 |
|---------|---------|
| leave_type | "请问您想请什么类型的假？(年假 / 事假 / 病假 / 调休)" |
| start_date | "请问您想请哪天的假？" |
| time_slot | "请问是全天还是半天？上午还是下午？" |

#### 2.4.3 澄清策略

- 单次澄清最多追问 2 个问题
- 连续 3 次澄清失败后转人工
- 澄清记录存入对话历史

### 2.5 响应生成模块

#### 2.5.1 响应类型

| 意图类型 | 响应模板 |
|---------|---------|
| LEAVE_REQUEST + 完整信息 | "已识别您的请假申请：{type}，时间：{date}，{slot}。" |
| LEAVE_REQUEST + 需澄清 | 澄清问题（见 2.4.2） |
| LEAVE_QUERY | "正在查询您的请假记录..." |
| LEAVE_WITHDRAW | "正在处理请假撤回..." |
| OTHER | "我理解您想处理一些 HR 相关事务，可以告诉我具体需要什么帮助吗？" |

#### 2.5.2 响应格式

```json
{
  "text": "响应文本",
  "intent": {...},
  "entities": {...},
  "actions": ["clarify", "query", "submit"]
}
```

---

## 3. 非功能需求

### 3.1 性能需求

| 指标 | 要求 |
|-----|------|
| 响应时间 | < 500ms |
| 并发支持 | > 100 QPS |
| 意图识别准确率 | > 80% (Phase 0) |

### 3.2 可靠性需求

- 识别失败率 < 5%
- 澄清成功率 > 70%
- 系统可用性 > 99%

### 3.3 可扩展性需求

- 能力分级机制支持动态升级
- 新增请假类型无需修改核心代码
- 新增意图类型可通过配置添加

### 3.4 安全需求

- 用户输入敏感信息脱敏
- 操作审计日志记录
- 会话数据加密存储

---

## 4. 系统架构

### 4.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        OA Agent                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ LangGraph    │  │ Intention    │  │ Response     │       │
│  │ Workflow     │→ │ Recognizer   │→ │ Generator    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ Capability   │  │ Metrics      │                          │
│  │ Registry     │  │ Module       │                          │
│  └──────────────┘  └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 LangGraph 状态图

```
start → recognize_intent → generate_response → update_metrics → end
     └─────────────────────↑                                ↓
     └───────────────────────────────────────────────────────┘
```

### 4.3 数据流

```
用户输入 → 意图识别 → 实体抽取 → 澄清判断 → 状态更新 → 响应生成 → 输出结果
```

---

## 5. 数据定义

### 5.1 核心数据结构

```python
class UserIntent(BaseModel):
    intent: IntentType              # 意图类型
    confidence: float               # 置信度
    leave_type: Optional[LeaveType] # 请假类型
    time_slot: Optional[LeaveTimeSlot] # 时间槽
    start_date: Optional[str]       # 开始日期
    end_date: Optional[str]         # 结束日期
    duration_hours: Optional[float] # 时长（小时）
    entities_extracted: List[str]   # 抽取的实体
    clarification_needed: bool      # 是否需要澄清
    required_fields: List[str]      # 缺失字段
```

```python
class IntentionMetrics(BaseModel):
    accuracy: float                 # 准确率
    precision: float                # 精确率
    recall: float                   # 召回率
    f1_score: float                 # F1分数
    avg_confidence: float           # 平均置信度
    total_requests: int             # 总请求数
    correct_intents: int            # 正确意图数
    extraction_recall: float        # 实体抽取召回率
```

### 5.2 配置文件

```yaml
# config/intent_keywords.yaml
leave_keywords:
  "我想请": "leave_request"
  "我要请": "leave_request"
  "请假": "leave_request"
  # ...

leave_type_keywords:
  "年假": "annual_leave"
  "事假": "personal_leave"
  # ...
```

---

## 6. 验收标准

### 6.1 功能验收

| 功能 | 验收标准 |
|-----|---------|
| 意图识别 | 6 个测试用例准确率 > 80% |
| 实体抽取 | 关键实体抽取召回率 > 75% |
| 澄清机制 | 缺失信息时能正确触发澄清 |
| 能力分级 | 8 项能力均有明确等级 |
| 指标计算 | 所有指标可计算且合理 |

### 6.2 质量验收

| 指标 | 要求 |
|-----|------|
| 代码覆盖率 | > 70% |
| 单元测试通过率 | 100% |
| 意图识别准确率 | > 80% |
| 平均响应时间 | < 500ms |

---

## 7. 迭代路线

### Phase 0 (当前): 请假流程基础能力
- ✅ 意图识别
- ✅ 实体抽取
- ✅ 能力分级
- ✅ 指标量化
- ⏳ 澄清机制
- ⏳ 状态追踪

### Phase 1: 增强能力
- 附件 OCR 处理
- 员工主数据查询
- 请假余额校验
- 冲突校验

### Phase 2: 企业集成
- 企业微信机器人对接
- 审批链解析
- 消息回执
- 审计日志

### Phase 3: 扩展到其他 HR 流程
- 调休、加班流程
- 出差、报销流程
- 入职、转正、离职流程

---

## 8. 附录

### 8.1 参考文档

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [PRD 模板参考](https://www.productplan.com/learn/prd-template/)

### 8.2 术语表

| 术语 | 说明 |
|-----|------|
| 意图 | 用户输入想要达成的目标 |
| 实体 | 意图中提取的关键信息 |
| 能力分级 | 对 Agent 能力成熟度的分级评估 |
| 澄清 | 当信息不完整时向用户追问 |

### 8.3 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|-----|------|------|---------|
| v1.0 | 2026-09-09 | AI | 初始版本 |
| v2.0 | 2026-09-09 | AI | 新增多模型支持和外部数据源 |
