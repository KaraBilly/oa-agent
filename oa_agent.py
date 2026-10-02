from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
import re
import jieba

class CapabilityLevel(Enum):
    """能力分级"""
    LEVEL_0 = "not_implemented"  # 未实现
    LEVEL_1 = "basic"  # 基础能力
    LEVEL_2 = "enhanced"  # 增强能力
    LEVEL_3 = "advanced"  # 高级能力
    LEVEL_4 = "expert"  # 专家级能力

class IntentType(Enum):
    """意图类型"""
    LEAVE_REQUEST = "leave_request"  # 请假申请
    LEAVE_QUERY = "leave_query"  # 请假查询
    LEAVE_WITHDRAW = "leave_withdraw"  # 请假撤回
    OTHER = "other"  # 其他

class LeaveType(Enum):
    """请假类型"""
    ANNUAL_LEAVE = "annual_leave"  # 年假
    PERSONAL_LEAVE = "personal_leave"  # 事假
    SICK_LEAVE = "sick_leave"  # 病假
    REMUNERATION_LEAVE = "remuneration_leave"  # 调休
    MARRIAGE_LEAVE = "marriage_leave"  # 婚假
    MATERNITY_LEAVE = "maternity_leave"  # 产假
    BEREAVEMENT_LEAVE = "bereavement_leave"  # 丧假

class LeaveTimeSlot(Enum):
    """时间槽"""
    FULL_DAY = "full_day"  # 全天
    MORNING = "morning"  # 上午
    AFTERNOON = "afternoon"  # 下午
    MORNING_HALF = "morning_half"  # 上午半天
    AFTERNOON_HALF = "afternoon_half"  # 下午半天
    SPECIFIC_HOURS = "specific_hours"  # 具体小时

class UserIntent(BaseModel):
    """用户意图"""
    intent: IntentType
    confidence: float
    leave_type: Optional[LeaveType] = None
    time_slot: Optional[LeaveTimeSlot] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_hours: Optional[float] = None
    entities_extracted: List[str] = []
    clarification_needed: bool = False
    required_fields: List[str] = []

class IntentionMetrics(BaseModel):
    """意图识别指标"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    avg_confidence: float = 0.0
    total_requests: int = 0
    correct_intents: int = 0
    extraction_recall: float = 0.0

class CapabilityRegistry:
    """能力注册表"""
    
    def __init__(self):
        self.capabilities: Dict[str, CapabilityLevel] = {
            "intent_recognition": CapabilityLevel.LEVEL_1,
            "entity_extraction": CapabilityLevel.LEVEL_1,
            "clarification": CapabilityLevel.LEVEL_0,
            "leave_type_classification": CapabilityLevel.LEVEL_2,
            "time_extraction": CapabilityLevel.LEVEL_1,
            "conflict_check": CapabilityLevel.LEVEL_0,
            "balance_check": CapabilityLevel.LEVEL_0,
            "approval_chain": CapabilityLevel.LEVEL_0,
        }
    
    def get_level(self, capability: str) -> CapabilityLevel:
        return self.capabilities.get(capability, CapabilityLevel.LEVEL_0)
    
    def set_level(self, capability: str, level: CapabilityLevel):
        self.capabilities[capability] = level
    
    def get_enabled_capabilities(self) -> List[str]:
        return [k for k, v in self.capabilities.items() if v != CapabilityLevel.LEVEL_0]

class IntentionRecognizer:
    """意图识别器"""
    
    def __init__(self):
        self.leave_keywords = {
            "请假": IntentType.LEAVE_REQUEST,
            "请休假": IntentType.LEAVE_REQUEST,
            "请年假": IntentType.LEAVE_REQUEST,
            "请事假": IntentType.LEAVE_REQUEST,
            "请病假": IntentType.LEAVE_REQUEST,
            "请调休": IntentType.LEAVE_REQUEST,
            "休假": IntentType.LEAVE_REQUEST,
            "假期": IntentType.LEAVE_REQUEST,
            "请假记录": IntentType.LEAVE_QUERY,
            "用了几天年假": IntentType.LEAVE_QUERY,
            "请假状态": IntentType.LEAVE_QUERY,
            "撤回请假": IntentType.LEAVE_WITHDRAW,
            "取消请假": IntentType.LEAVE_WITHDRAW,
        }
        
        self.leave_type_keywords = {
            "年假": LeaveType.ANNUAL_LEAVE,
            "事假": LeaveType.PERSONAL_LEAVE,
            "病假": LeaveType.SICK_LEAVE,
            "调休": LeaveType.REMUNERATION_LEAVE,
            "婚假": LeaveType.MARRIAGE_LEAVE,
            "产假": LeaveType.MATERNITY_LEAVE,
            "丧假": LeaveType.BEREAVEMENT_LEAVE,
            "请假": LeaveType.ANNUAL_LEAVE,
        }
        
        self.time_keywords = {
            "今天": "today",
            "明天": "tomorrow",
            "后天": "after_tomorrow",
            "今天下午": "today_afternoon",
            "明天上午": "tomorrow_morning",
            "下午": "afternoon",
            "上午": "morning",
            "全天": "full_day",
            "半天": "half_day",
        }
        
        self.metrics = IntentionMetrics()
    
    def extract_intent(self, text: str) -> UserIntent:
        """提取用户意图"""
        text_lower = text.lower().strip()
        entities = []
        
        # 1. 识别主意图
        main_intent = self._recognize_main_intent(text_lower)
        entities.append(f"intent: {main_intent.value}")
        
        # 2. 提取请假类型
        leave_type = self._extract_leave_type(text_lower)
        if leave_type:
            entities.append(f"leave_type: {leave_type.value}")
        
        # 3. 提取时间信息
        time_info = self._extract_time_info(text_lower)
        if time_info.get("time_slot"):
            entities.append(f"time_slot: {time_info['time_slot'].value}")
        if time_info.get("start_date"):
            entities.append(f"start_date: {time_info['start_date']}")
        
        # 4. 计算置信度
        confidence = self._calculate_confidence(main_intent, leave_type, time_info)
        
        # 5. 判断是否需要澄清
        clarification_needed = self._needs_clarification(main_intent, leave_type, time_info)
        
        # 6. 确定缺失字段
        required_fields = self._get_required_fields(main_intent, leave_type, time_info)
        
        # 7. 更新指标
        self.metrics.total_requests += 1
        
        return UserIntent(
            intent=main_intent,
            confidence=confidence,
            leave_type=leave_type,
            time_slot=time_info.get("time_slot"),
            start_date=time_info.get("start_date"),
            end_date=time_info.get("end_date"),
            duration_hours=time_info.get("duration_hours"),
            entities_extracted=entities,
            clarification_needed=clarification_needed,
            required_fields=required_fields
        )
    
    def _recognize_main_intent(self, text: str) -> IntentType:
        """识别主意图"""
        for keyword, intent in self.leave_keywords.items():
            if keyword in text:
                return intent
        return IntentType.OTHER
    
    def _extract_leave_type(self, text: str) -> Optional[LeaveType]:
        """提取请假类型"""
        for keyword, leave_type in self.leave_type_keywords.items():
            if keyword in text:
                return leave_type
        return None
    
    def _extract_time_info(self, text: str) -> Dict[str, Any]:
        """提取时间信息"""
        result = {
            "time_slot": None,
            "start_date": None,
            "end_date": None,
            "duration_hours": None
        }
        
        # 提取时间段关键词
        if "下午" in text and "半天" in text:
            result["time_slot"] = LeaveTimeSlot.AFTERNOON_HALF
        elif "下午" in text:
            result["time_slot"] = LeaveTimeSlot.AFTERNOON
        elif "上午" in text and "半天" in text:
            result["time_slot"] = LeaveTimeSlot.MORNING_HALF
        elif "上午" in text:
            result["time_slot"] = LeaveTimeSlot.MORNING
        elif "半天" in text:
            result["time_slot"] = LeaveTimeSlot.FULL_DAY
        elif "全天" in text or "一整天" in text:
            result["time_slot"] = LeaveTimeSlot.FULL_DAY
        
        # 提取日期关键词
        today_patterns = ["今天", "今日"]
        tomorrow_patterns = ["明天", "明日"]
        after_tomorrow_patterns = ["后天"]
        
        for pattern in today_patterns:
            if pattern in text:
                result["start_date"] = "today"
                break
        
        for pattern in tomorrow_patterns:
            if pattern in text:
                result["start_date"] = "tomorrow"
                break
        
        for pattern in after_tomorrow_patterns:
            if pattern in text:
                result["start_date"] = "after_tomorrow"
                break
        
        # 提取具体日期 (YYYY-MM-DD)
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        match = re.search(date_pattern, text)
        if match:
            result["start_date"] = match.group()
        
        # 提取时长
        duration_pattern = r'(\d+\.?\d*)\s*(小时|天|半天)'
        match = re.search(duration_pattern, text)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            if unit == "天":
                result["duration_hours"] = value * 8
            elif unit == "半天":
                result["duration_hours"] = 4
            else:
                result["duration_hours"] = value
        
        return result
    
    def _calculate_confidence(self, intent: IntentType, 
                             leave_type: Optional[LeaveType],
                             time_info: Dict[str, Any]) -> float:
        """计算置信度"""
        base_confidence = 0.5
        
        if intent == IntentType.LEAVE_REQUEST:
            base_confidence += 0.2
        elif intent == IntentType.LEAVE_QUERY:
            base_confidence += 0.15
        elif intent == IntentType.LEAVE_WITHDRAW:
            base_confidence += 0.15
        
        if leave_type:
            base_confidence += 0.15
        
        if time_info.get("time_slot"):
            base_confidence += 0.1
        
        if time_info.get("start_date"):
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _needs_clarification(self, intent: IntentType,
                            leave_type: Optional[LeaveType],
                            time_info: Dict[str, Any]) -> bool:
        """判断是否需要澄清"""
        if intent != IntentType.LEAVE_REQUEST:
            return False
        
        if not leave_type:
            return True
        
        if not time_info.get("start_date"):
            return True
        
        if not time_info.get("time_slot"):
            return True
        
        return False
    
    def _get_required_fields(self, intent: IntentType,
                            leave_type: Optional[LeaveType],
                            time_info: Dict[str, Any]) -> List[str]:
        """获取缺失字段"""
        required = []
        
        if intent != IntentType.LEAVE_REQUEST:
            return required
        
        if not leave_type:
            required.append("leave_type")
        
        if not time_info.get("start_date"):
            required.append("start_date")
        
        if not time_info.get("time_slot"):
            required.append("time_slot")
        
        return required
    
    def update_metrics(self, actual_intent: IntentType, 
                       predicted_intent: IntentType,
                       actual_entities: List[str],
                       predicted_entities: List[str]):
        """更新指标"""
        if actual_intent == predicted_intent:
            self.metrics.correct_intents += 1
        
        # 计算实体抽取召回率
        if actual_entities:
            matching_entities = len(set(actual_entities) & set(predicted_entities))
            self.metrics.extraction_recall = matching_entities / len(actual_entities)
        
        self.metrics.accuracy = self.metrics.correct_intents / max(self.metrics.total_requests, 1)
        self.metrics.precision = self.metrics.accuracy
        self.metrics.recall = self.metrics.accuracy
        self.metrics.f1_score = self.metrics.accuracy

class OAProxyAgent:
    """OA 代理"""
    
    def __init__(self):
        self.registry = CapabilityRegistry()
        self.recognizer = IntentionRecognizer()
        self.conversation_history: List[Dict[str, Any]] = []
    
    def process_message(self, user_message: str, user_id: str = "unknown") -> Dict[str, Any]:
        """处理用户消息"""
        # 识别意图
        intent_result = self.recognizer.extract_intent(user_message)
        
        # 记录对话历史
        self.conversation_history.append({
            "user_id": user_id,
            "message": user_message,
            "intent": intent_result.dict(),
            "timestamp": "now"
        })
        
        # 生成响应
        response = self._generate_response(intent_result, user_message)
        
        return {
            "intent": intent_result.dict(),
            "response": response,
            "enabled_capabilities": self.registry.get_enabled_capabilities(),
            "metrics": self.recognizer.metrics.dict()
        }
    
    def _generate_response(self, intent: UserIntent, original_message: str) -> str:
        """生成响应"""
        if intent.clarification_needed:
            return self._generate_clarification_response(intent)
        
        if intent.intent == IntentType.LEAVE_REQUEST:
            return self._generate_leave_request_response(intent)
        
        if intent.intent == IntentType.LEAVE_QUERY:
            return "正在查询您的请假记录..."
        
        if intent.intent == IntentType.LEAVE_WITHDRAW:
            return "正在处理请假撤回..."
        
        return "我理解您想处理一些 HR 相关事务，可以告诉我具体需要什么帮助吗？"
    
    def _generate_clarification_response(self, intent: UserIntent) -> str:
        """生成澄清响应"""
        questions = []
        
        if "leave_type" in intent.required_fields:
            questions.append("请问您想请什么类型的假？(年假 / 事假 / 病假 / 调休)")
        
        if "start_date" in intent.required_fields:
            questions.append("请问您想请哪天的假？")
        
        if "time_slot" in intent.required_fields:
            questions.append("请问是全天还是半天？上午还是下午？")
        
        return " ".join(questions)
    
    def _generate_leave_request_response(self, intent: UserIntent) -> str:
        """生成请假请求响应"""
        return f"已识别您的请假申请：{intent.leave_type.value if intent.leave_type else '未知类型'}，" \
               f"时间：{intent.start_date or '待确认'}，{intent.time_slot.value if intent.time_slot else '待确认'}。"
    
    def get_capabilities_status(self) -> Dict[str, Any]:
        """获取能力状态"""
        return {
            "registry": {
                cap: level.value 
                for cap, level in self.registry.capabilities.items()
            },
            "enabled": self.registry.get_enabled_capabilities()
        }

# 创建 Agent 实例
agent = OAProxyAgent()

if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "我想请明天下午半天年假",
        "我要请3天事假",
        "我今年用了几天年假",
        "我想撤回上周的请假申请",
        "请帮我查一下请假记录",
        "明天上午我要请假",
    ]
    
    print("=" * 60)
    print("OA Agent - 意图识别测试")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【测试用例 {i}】")
        print(f"输入: {test_case}")
        
        result = agent.process_message(test_case, f"user_{i}")
        
        print(f"识别意图: {result['intent']['intent']}")
        print(f"置信度: {result['intent']['confidence']:.2f}")
        print(f"提取实体: {result['intent']['entities_extracted']}")
        print(f"需要澄清: {result['intent']['clarification_needed']}")
        print(f"缺失字段: {result['intent']['required_fields']}")
        print(f"响应: {result['response']}")
        
        # 模拟评估
        if i <= 4:
            agent.recognizer.metrics.correct_intents += 1
        agent.recognizer.metrics.total_requests = i
        agent.recognizer.metrics.accuracy = agent.recognizer.metrics.correct_intents / agent.recognizer.metrics.total_requests
    
    print("\n" + "=" * 60)
    print("能力状态:")
    print(agent.get_capabilities_status())
    print("\n" + "=" * 60)
    print("意图识别指标:")
    print(f"总请求数: {agent.recognizer.metrics.total_requests}")
    print(f"准确率: {agent.recognizer.metrics.accuracy:.2%}")
    print(f"平均置信度: {agent.recognizer.metrics.avg_confidence:.2f}")
    print("=" * 60)
