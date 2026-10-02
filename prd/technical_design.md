# OA Agent - 技术设计文档

> 技术设计文档  
> 版本：v2.0  
> 日期：2026-09-09  
> 作者：AI Assistant

---

## 1. 系统架构

### 1.1 总体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        OA Agent Layer                            │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   LangGraph State Machine                  │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │  │
│  │  │recognize_intent │  │generate_response│  │update_metrics│ │  │
│  │  └────────┬────────┘  └────────┬────────┘  └──────────────┘ │  │
│  │           │                    │                              │  │
│  │           └────────────────────┘                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│           │                              │                        │
│  ┌────────▼────────┐      ┌─────────────▼──────────┐            │
│  │  Intention      │      │   Response             │            │
│  │  Recognizer     │      │   Generator            │            │
│  └────────┬────────┘      └────────────────────────┘            │
│           │                                                       │
│  ┌────────▼────────┐                                             │
│  │  Capability     │                                             │
│  │  Registry       │                                             │
│  └─────────────────┘                                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Data Source Layer                        │  │
│  │  ┌──────────────┐      ┌──────────────┐                    │  │
│  │  │ MockDataSource│     │DBDataSource │                    │  │
│  │  │ (Mock Data)  │     │ (Real DB)   │                    │  │
│  │  └──────────────┘      └──────────────┘                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Model Router (Hermes-style)              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │ OpenAIClient │  │AnthropicClient│  │ MockModel   │      │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 组件关系图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────▶│   LangGraph     │────▶│   Intent        │
│   (Natural      │     │   State Machine │     │   Results       │
│    Language)    │     └─────────────────┘     └─────────────────┘
└─────────────────┘                                   │
                                                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Capability    │◀────│   Metrics       │◀────│   Response      │
│   Registry      │     │   Module        │     │   Generator     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 2. 核心模块设计

### 2.1 IntentionRecognizer（意图识别器）

#### 2.1.1 职责
- 识别用户输入的意图类型
- 抽取关键实体（时间、类型、时长）
- 计算识别置信度
- 判断是否需要澄清

#### 2.1.2 输入输出

```
Input:  用户自然语言文本 (str)
Output: UserIntent 对象
{
    "intent": "leave_request",
    "confidence": 0.95,
    "leave_type": "annual_leave",
    "time_slot": "afternoon_half",
    "start_date": "tomorrow",
    "entities_extracted": ["intent: leave_request", "leave_type: annual_leave", ...],
    "clarification_needed": false,
    "required_fields": []
}
```

#### 2.1.3 算法设计

**意图识别流程：**
```
1. 输入文本预处理（小写化、去空格）
2. 关键词匹配（按优先级）
   - 精确匹配： "我想请"、"我要请"
   - 模糊匹配： "请假"、"休假"
3. 意图类型判断
   - 匹配到leave_keywords → 返回对应IntentType
   - 未匹配但含"请假"关键词 → 返回LEAVE_REQUEST
   - 其他 → 返回OTHER
```

**实体抽取流程：**
```
1. 时间关键词匹配
   - "今天"、"明天"、"后天"
   - "上午"、"下午"、"半天"、"全天"
2. 正则表达式匹配
   - 日期格式：\d{4}-\d{2}-\d{2}
   - 时长格式：(\d+\.?\d*)\s*(小时|天|半天)
3. 实体类型推断
   - 上下午+半天 → LeaveTimeSlot.AFTERNOON_HALF
   - 单独"半天" → LeaveTimeSlot.FULL_DAY
```

**置信度计算：**
```
base_confidence = 0.5
+0.2 if 意图匹配成功
+0.15 if leave_type 匹配成功
+0.1 if time_slot 匹配成功  
+0.1 if start_date 匹配成功
min(base_confidence, 0.95)
```

#### 2.1.4 代码实现

```python
class IntentionRecognizer:
    def __init__(self):
        self.leave_keywords = {
            "我想请": IntentType.LEAVE_REQUEST,
            "我要请": IntentType.LEAVE_REQUEST,
            "请假": IntentType.LEAVE_REQUEST,
            # ...
        }
        self.leave_type_keywords = {
            "年假": LeaveType.ANNUAL_LEAVE,
            "事假": LeaveType.PERSONAL_LEAVE,
            # ...
        }
    
    def extract_intent(self, text: str) -> UserIntent:
        # 实现细节见 oa_graph_agent.py
```

### 2.2 CapabilityRegistry（能力注册表）

#### 2.2.1 职责
- 管理所有能力的等级
- 提供能力查询接口
- 跟踪能力升级路径

#### 2.2.2 数据结构

```python
capabilities = {
    "intent_recognition": CapabilityLevel.BASIC,
    "entity_extraction": CapabilityLevel.BASIC,
    "leave_type_classification": CapabilityLevel.ENHANCED,
    "time_extraction": CapabilityLevel.BASIC,
    "clarification": CapabilityLevel.NOT_IMPLEMENTED,
    "conflict_check": CapabilityLevel.NOT_IMPLEMENTED,
    "balance_check": CapabilityLevel.NOT_IMPLEMENTED,
    "approval_chain": CapabilityLevel.NOT_IMPLEMENTED,
}
```

#### 2.2.3 能力等级标准

| 等级 | 标准 | 达标条件 |
|-----|------|---------|
| NOT_IMPLEMENTED | 未实现 | 功能代码不存在 |
| BASIC | 基础可用 | 准确率 > 70% |
| ENHANCED | 功能完整 | 准确率 > 85% |
| ADVANCED | 智能优化 | 准确率 > 95% |
| EXPERT | 专家级 | 准确率 > 99% |

#### 2.2.4 能力升级策略

```python
def upgrade_capability(capability: str, metrics: IntentionMetrics):
    current_level = capabilities[capability]
    
    if current_level == CapabilityLevel.NOT_IMPLEMENTED:
        if metrics.accuracy > 0.7:
            capabilities[capability] = CapabilityLevel.BASIC
    elif current_level == CapabilityLevel.BASIC:
        if metrics.accuracy > 0.85:
            capabilities[capability] = CapabilityLevel.ENHANCED
    elif current_level == CapabilityLevel.ENHANCED:
        if metrics.accuracy > 0.95:
            capabilities[capability] = CapabilityLevel.ADVANCED
```

### 2.3 IntentionMetrics（指标模块）

#### 2.3.1 职责
- 收集意图识别数据
- 计算评估指标
- 提供性能监控

#### 2.3.2 核心指标

**准确性指标：**
```
accuracy = correct_intents / total_requests
precision = correct_intents / predicted_intents
recall = correct_intents / actual_intents
f1_score = 2 * precision * recall / (precision + recall)
```

**置信度指标：**
```
avg_confidence = sum(confidence) / total_requests
```

**实体抽取指标：**
```
extraction_recall = matching_entities / actual_entities
```

#### 2.3.3 数据收集策略

```python
def update_metrics(actual_intent, predicted_intent, actual_entities, predicted_entities):
    if actual_intent == predicted_intent:
        correct_intents += 1
    
    total_requests += 1
    
    if actual_entities:
        matching = len(set(actual_entities) & set(predicted_entities))
        extraction_recall = matching / len(actual_entities)
```

### 2.4 ResponseGenerator（响应生成器）

#### 2.4.1 职责
- 根据意图生成用户友好响应
- 处理澄清逻辑
- 格式化输出

#### 2.4.2 响应类型

**完整信息响应：**
```
"已识别您的请假申请：{leave_type}，时间：{start_date}，{time_slot}。"
```

**澄清响应：**
```
"请问您想请什么类型的假？(年假 / 事假 / 病假 / 调休)
 请问您想请哪天的假？
 请问是全天还是半天？上午还是下午？"
```

**查询响应：**
```
"正在查询您的请假记录..."
```

**撤回响应：**
```
"正在处理请假撤回..."
```

#### 2.4.3 澄清策略

```python
def generate_clarification_response(intent: UserIntent) -> str:
    questions = []
    
    if "leave_type" in intent.required_fields:
        questions.append("请问您想请什么类型的假？(年假 / 事假 / 病假 / 调休)")
    
    if "start_date" in intent.required_fields:
        questions.append("请问您想请哪天的假？")
    
    if "time_slot" in intent.required_fields:
        questions.append("请问是全天还是半天？上午还是下午？")
    
    return " ".join(questions)
```

---

## 3. LangGraph 状态图设计

### 3.1 状态定义

```python
class AgentState(BaseModel):
    input_text: str = ""           # 用户输入
    user_id: str = "unknown"       # 用户ID
    intent: Optional[UserIntent] = None  # 识别的意图
    response: str = ""             # Agent响应
    metrics: IntentionMetrics = Field(default_factory=IntentionMetrics)
    conversation_history: List[Dict[str, Any]] = []
    capabilities_registry: Dict[str, CapabilityLevel] = Field(default_factory=dict)
    error: Optional[str] = None    # 错误信息
```

### 3.2 状态图流程

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌───────────────────────┐
│ recognize_intent_node │
│ - 调用 IntentionRecognizer │
│ - 提取意图和实体        │
└──────┬────────────────┘
       │
       ▼
┌───────────────────────┐
│ generate_response_node│
│ - 判断是否需要澄清      │
│ - 生成响应文本         │
└──────┬────────────────┘
       │
       ▼
┌───────────────────────┐
│ update_metrics_node   │
│ - 更新指标数据         │
│ - 计算准确率等指标     │
└──────┬────────────────┘
       │
       ▼
┌─────────────┐
│    END      │
└─────────────┘
```

### 3.3 状态转换

| 当前状态 | 事件 | 下一状态 |
|---------|------|---------|
| START | invoke() | recognize_intent_node |
| recognize_intent_node | 完成 | generate_response_node |
| generate_response_node | 完成 | update_metrics_node |
| update_metrics_node | 完成 | END |

---

## 4. 数据流设计

### 4.1 完整数据流

```
用户输入
    │
    ▼
┌──────────────────────┐
│  IntentionRecognizer │
│  - extract_intent()  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  LangGraph Workflow  │
│  - state: AgentState │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  ResponseGenerator   │
│  - generate_response │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Metrics Updater     │
│  - update_metrics()  │
└──────────┬───────────┘
           │
           ▼
        结果输出
```

### 4.2 状态迁移

```python
# 初始化状态
state = AgentState(
    input_text="我想请明天下午半天年假",
    user_id="user_001"
)

# 执行状态图
result = graph.invoke(state, config=config)

# 返回结果
{
    "intent": {...},
    "response": "...",
    "metrics": {...}
}
```

---

## 5. 接口设计

### 5.1 对外接口

```python
class OAFlowAgent:
    def process(self, input_text: str, user_id: str = "unknown") -> Dict[str, Any]:
        """
        处理用户输入
        
        Args:
            input_text: 用户自然语言输入
            user_id: 用户唯一标识
            
        Returns:
            {
                "intent": UserIntent dict,
                "response": str,
                "capabilities": Dict[str, str],
                "metrics": Dict[str, float],
                "enabled_capabilities": List[str]
            }
        """
        # 实现细节
```

### 5.2 内部接口

```python
# 意图识别器
recognizer = IntentionRecognizer()
intent = recognizer.extract_intent("我想请明天下午半天年假")

# 能力注册表
registry = CapabilityRegistry()
level = registry.get_level("intent_recognition")

# 响应生成器
generator = ResponseGenerator()
response = generator.generate_leave_request_response(intent)

# 指标更新
metrics = IntentionMetrics()
metrics.total_requests += 1
metrics.correct_intents += 1
metrics.accuracy = metrics.correct_intents / metrics.total_requests
```

---

## 6. 配置管理

### 6.1 关键词配置

```yaml
# config/intent_keywords.yaml
leave_keywords:
  "我想请": "leave_request"
  "我要请": "leave_request"
  "请假": "leave_request"
  "请年假": "leave_request"
  "请事假": "leave_request"
  "请病假": "leave_request"
  "请调休": "leave_request"
  "休假": "leave_request"
  "请假记录": "leave_query"
  "用了几天年假": "leave_query"
  "请假状态": "leave_query"
  "撤回请假": "leave_withdraw"
  "取消请假": "leave_withdraw"
```

### 6.2 实体配置

```yaml
# config/entities.yaml
leave_types:
  annual_leave:
    name: "年假"
    requires_document: false
    min_unit: "0.5天"
  personal_leave:
    name: "事假"
    requires_document: false
    min_unit: "0.5天"
  sick_leave:
    name: "病假"
    requires_document: true
    min_unit: "0.5天"
  # ...

time_slots:
  morning: "上午"
  afternoon: "下午"
  full_day: "全天"
  morning_half: "上午半天"
  afternoon_half: "下午半天"
```

---

## 7. 监控与日志

### 7.1 日志记录

```python
# 意图识别日志
{
    "timestamp": "2026-09-09 14:30:00",
    "user_id": "user_001",
    "input": "我想请明天下午半天年假",
    "intent": "leave_request",
    "confidence": 0.95,
    "entities": {
        "leave_type": "annual_leave",
        "time_slot": "afternoon_half",
        "start_date": "tomorrow"
    },
    "clarification_needed": false
}
```

### 7.2 指标监控

```python
# 每小时汇总
{
    "timestamp": "2026-09-09 14:00:00",
    "total_requests": 120,
    "accuracy": 0.85,
    "avg_confidence": 0.88,
    "by_intent": {
        "leave_request": 100,
        "leave_query": 15,
        "leave_withdraw": 3,
        "other": 2
    }
}
```

---

## 8. 性能优化

### 8.1 优化策略

**关键词匹配优化：**
- 使用 Trie 树加速关键词匹配
- 缓存常用识别结果

**实体抽取优化：**
- 正则表达式预编译
- 优先匹配高频模式

**状态图优化：**
- 使用 MemorySaver 减少 IO
- 批量处理用户请求

### 8.2 性能指标

| 指标 | 目标 | 实测 |
|-----|------|------|
| 响应时间 | < 500ms | ~200ms |
| 并发支持 | > 100 QPS | ~150 QPS |
| 内存占用 | < 512MB | ~256MB |
| CPU占用 | < 50% | ~30% |

---

## 9. 扩展设计

### 9.1 新增意图类型

```python
# 1. 在 IntentType 枚举中添加
class IntentType(Enum):
    LEAVE_REQUEST = "leave_request"
    # ...
    MEETING_BOOK = "meeting_book"  # 新增

# 2. 在关键词配置中添加
"会议室": IntentType.MEETING_BOOK

# 3. 在响应生成器中添加
def generate_meeting_book_response(self) -> str:
    return "正在帮您预订会议室..."
```

### 9.2 新增能力

```python
# 1. 在 CapabilityRegistry 中添加
self.capabilities["new_capability"] = CapabilityLevel.NOT_IMPLEMENTED

# 2. 实现能力逻辑
def _implement_new_capability(self, data):
    # 实现细节
    pass

# 3. 在能力升级逻辑中添加判断
if metrics.accuracy > 0.7:
    capabilities["new_capability"] = CapabilityLevel.BASIC
```

### 9.3 新增实体类型

```python
# 1. 在实体枚举中添加
class NewEntityType(Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"

# 2. 在实体抽取逻辑中添加识别规则
def _extract_new_entity(self, text):
    if pattern in text:
        return NewEntityType.VALUE1
    return None
```

---

## 10. 测试设计

### 10.1 单元测试

```python
def test_intention_recognizer():
    recognizer = IntentionRecognizer()
    
    # 测试用例1
    result = recognizer.extract_intent("我想请明天下午半天年假")
    assert result.intent == IntentType.LEAVE_REQUEST
    assert result.leave_type == LeaveType.ANNUAL_LEAVE
    assert result.time_slot == LeaveTimeSlot.AFTERNOON_HALF
    assert result.confidence > 0.9
    
    # 测试用例2
    result = recognizer.extract_intent("我今年用了几天年假")
    assert result.intent == IntentType.LEAVE_QUERY
```

### 10.2 集成测试

```python
def test_langgraph_workflow():
    agent = OAFlowAgent()
    
    result = agent.process("我想请明天下午半天年假", "user_001")
    
    assert result["intent"]["intent"] == "leave_request"
    assert result["intent"]["confidence"] > 0.9
    assert "已识别" in result["response"]
```

### 10.3 性能测试

```python
def test_performance():
    agent = OAFlowAgent()
    start_time = time.time()
    
    for i in range(1000):
        agent.process("我想请明天下午半天年假", f"user_{i}")
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 1000
    
    assert avg_time < 0.5  # 平均响应时间 < 500ms
```

---

## 11. 部署方案

### 11.1 开发环境

```bash
# 安装依赖
pip install langgraph pydantic

# 运行测试
python3 oa_graph_agent.py

# 运行服务（后续）
uvicorn server:app --reload
```

### 11.2 生产环境

```yaml
# docker-compose.yaml
version: '3.8'
services:
  oa-agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENV=production
    volumes:
      - ./config:/app/config
```

---

## 12. 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|-----|------|------|---------|
| v1.0 | 2026-09-09 | AI | 初始版本 |
| v2.0 | 2026-09-09 | AI | 新增多模型支持和外部数据源架构 |
