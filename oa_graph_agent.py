from enum import Enum
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import re

class CapabilityLevel(Enum):
    """能力分级"""
    NOT_IMPLEMENTED = "not_implemented"
    BASIC = "basic"
    ENHANCED = "enhanced"
    ADVANCED = "advanced"
    EXPERT = "expert"

class IntentType(Enum):
    """意图类型"""
    LEAVE_REQUEST = "leave_request"
    LEAVE_QUERY = "leave_query"
    LEAVE_WITHDRAW = "leave_withdraw"
    OTHER = "other"

class LeaveType(Enum):
    """请假类型"""
    ANNUAL_LEAVE = "annual_leave"
    PERSONAL_LEAVE = "personal_leave"
    SICK_LEAVE = "sick_leave"
    REMUNERATION_LEAVE = "remuneration_leave"
    MARRIAGE_LEAVE = "marriage_leave"
    MATERNITY_LEAVE = "maternity_leave"
    BEREAVEMENT_LEAVE = "bereavement_leave"

class LeaveTimeSlot(Enum):
    """时间槽"""
    FULL_DAY = "full_day"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    MORNING_HALF = "morning_half"
    AFTERNOON_HALF = "afternoon_half"
    SPECIFIC_HOURS = "specific_hours"

class UserIntent(BaseModel):
    """用户意图"""
    intent: IntentType
    confidence: float = 0.0
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

class AgentState(BaseModel):
    """Agent状态"""
    input_text: str = ""
    user_id: str = "unknown"
    intent: Optional[UserIntent] = None
    response: str = ""
    metrics: IntentionMetrics = Field(default_factory=IntentionMetrics)
    conversation_history: List[Dict[str, Any]] = []
    capabilities_registry: Dict[str, CapabilityLevel] = Field(default_factory=dict)
    error: Optional[str] = None

class IntentionRecognizer:
    """意图识别器"""
    
    def __init__(self):
        self.leave_keywords = {
            "我想请": IntentType.LEAVE_REQUEST,
            "我要请": IntentType.LEAVE_REQUEST,
            "我想休假": IntentType.LEAVE_REQUEST,
            "我要休假": IntentType.LEAVE_REQUEST,
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
            "查询请假": IntentType.LEAVE_QUERY,
            "撤回请假": IntentType.LEAVE_WITHDRAW,
            "取消请假": IntentType.LEAVE_WITHDRAW,
            "撤回": IntentType.LEAVE_WITHDRAW,
            "取消": IntentType.LEAVE_WITHDRAW,
        }
        
        self.leave_type_keywords = {
            "年假": LeaveType.ANNUAL_LEAVE,
            "事假": LeaveType.PERSONAL_LEAVE,
            "病假": LeaveType.SICK_LEAVE,
            "调休": LeaveType.REMUNERATION_LEAVE,
            "婚假": LeaveType.MARRIAGE_LEAVE,
            "产假": LeaveType.MATERNITY_LEAVE,
            "丧假": LeaveType.BEREAVEMENT_LEAVE,
        }
        
        self._initialize_capabilities()
    
    def _initialize_capabilities(self):
        """初始化能力注册"""
        self.capabilities = {
            "intent_recognition": CapabilityLevel.BASIC,
            "entity_extraction": CapabilityLevel.BASIC,
            "clarification": CapabilityLevel.NOT_IMPLEMENTED,
            "leave_type_classification": CapabilityLevel.ENHANCED,
            "time_extraction": CapabilityLevel.BASIC,
            "conflict_check": CapabilityLevel.NOT_IMPLEMENTED,
            "balance_check": CapabilityLevel.NOT_IMPLEMENTED,
            "approval_chain": CapabilityLevel.NOT_IMPLEMENTED,
        }
    
    def extract_intent(self, text: str) -> UserIntent:
        """提取用户意图"""
        text_lower = text.lower().strip()
        entities = []
        
        main_intent = self._recognize_main_intent(text_lower)
        entities.append(f"intent: {main_intent.value}")
        
        leave_type = self._extract_leave_type(text_lower)
        if leave_type:
            entities.append(f"leave_type: {leave_type.value}")
        
        time_info = self._extract_time_info(text_lower)
        if time_info.get("time_slot"):
            entities.append(f"time_slot: {time_info['time_slot'].value}")
        if time_info.get("start_date"):
            entities.append(f"start_date: {time_info['start_date']}")
        
        confidence = self._calculate_confidence(main_intent, leave_type, time_info)
        clarification_needed = self._needs_clarification(main_intent, leave_type, time_info)
        required_fields = self._get_required_fields(main_intent, leave_type, time_info)
        
        self.capabilities["intent_recognition"] = CapabilityLevel.BASIC
        self.capabilities["entity_extraction"] = CapabilityLevel.BASIC
        
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
        """识别主意图 - 按优先级匹配"""
        for keyword, intent in self.leave_keywords.items():
            if keyword in text:
                return intent
        
        if "请假" in text or "休假" in text or "假" in text:
            return IntentType.LEAVE_REQUEST
        
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
        
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        match = re.search(date_pattern, text)
        if match:
            result["start_date"] = match.group()
        
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

class ResponseGenerator:
    """响应生成器"""
    
    def generate_clarification_response(self, intent: UserIntent) -> str:
        """生成澄清响应"""
        questions = []
        
        if "leave_type" in intent.required_fields:
            questions.append("请问您想请什么类型的假？(年假 / 事假 / 病假 / 调休)")
        
        if "start_date" in intent.required_fields:
            questions.append("请问您想请哪天的假？")
        
        if "time_slot" in intent.required_fields:
            questions.append("请问是全天还是半天？上午还是下午？")
        
        return " ".join(questions)
    
    def generate_leave_request_response(self, intent: UserIntent) -> str:
        """生成请假请求响应"""
        leave_type_str = intent.leave_type.value if intent.leave_type else "未知类型"
        start_date_str = intent.start_date or "待确认"
        time_slot_str = intent.time_slot.value if intent.time_slot else "待确认"
        
        return f"已识别您的请假申请：{leave_type_str}，时间：{start_date_str}，{time_slot_str}。"
    
    def generate_leave_query_response(self) -> str:
        """生成请假查询响应"""
        return "正在查询您的请假记录..."
    
    def generate_leave_withdraw_response(self) -> str:
        """生成请假撤回响应"""
        return "正在处理请假撤回..."
    
    def generate_default_response(self) -> str:
        """生成默认响应"""
        return "我理解您想处理一些 HR 相关事务，可以告诉我具体需要什么帮助吗？"

class OAFlowAgent:
    """OA 流程 Agent - 基于 LangGraph"""
    
    def __init__(self):
        self.recognizer = IntentionRecognizer()
        self.response_generator = ResponseGenerator()
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("recognize_intent", self._recognize_intent_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("update_metrics", self._update_metrics_node)
        
        workflow.set_entry_point("recognize_intent")
        workflow.add_edge("recognize_intent", "generate_response")
        workflow.add_edge("generate_response", "update_metrics")
        workflow.add_edge("update_metrics", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _recognize_intent_node(self, state: AgentState) -> Dict[str, Any]:
        """意图识别节点"""
        intent = self.recognizer.extract_intent(state.input_text)
        return {
            "intent": intent,
            "capabilities_registry": self.recognizer.capabilities,
            "input_text": state.input_text,
            "user_id": state.user_id
        }
    
    def _generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """响应生成节点"""
        intent = state.intent
        if not intent:
            return {"response": "无法识别您的意图，请重试。"}
        
        if intent.clarification_needed:
            response = self.response_generator.generate_clarification_response(intent)
        elif intent.intent == IntentType.LEAVE_REQUEST:
            response = self.response_generator.generate_leave_request_response(intent)
        elif intent.intent == IntentType.LEAVE_QUERY:
            response = self.response_generator.generate_leave_query_response()
        elif intent.intent == IntentType.LEAVE_WITHDRAW:
            response = self.response_generator.generate_leave_withdraw_response()
        else:
            response = self.response_generator.generate_default_response()
        
        return {"response": response}
    
    def _update_metrics_node(self, state: AgentState) -> Dict[str, Any]:
        """更新指标节点"""
        intent = state.intent
        if intent:
            state.metrics.total_requests += 1
            
            if intent.intent != IntentType.OTHER:
                state.metrics.correct_intents += 1
            
            state.metrics.accuracy = (
                state.metrics.correct_intents / max(state.metrics.total_requests, 1)
            )
            
            state.metrics.avg_confidence = (
                state.metrics.avg_confidence * (state.metrics.total_requests - 1) 
                + intent.confidence
            ) / state.metrics.total_requests
            
            state.metrics.precision = state.metrics.accuracy
            state.metrics.recall = state.metrics.accuracy
            state.metrics.f1_score = state.metrics.accuracy
        
        return {}
    
    def process(self, input_text: str, user_id: str = "unknown") -> Dict[str, Any]:
        """处理输入"""
        config = {"configurable": {"thread_id": user_id}}
        inputs = {
            "input_text": input_text,
            "user_id": user_id
        }
        
        result = self.graph.invoke(inputs, config=config)
        
        intent_data = None
        if isinstance(result, dict):
            intent_obj = result.get("intent")
            if intent_obj:
                intent_data = intent_obj.model_dump() if hasattr(intent_obj, 'model_dump') else (intent_obj.dict() if hasattr(intent_obj, 'dict') else intent_obj)
        elif hasattr(result, 'intent'):
            intent_obj = result.intent
            intent_data = intent_obj.model_dump() if intent_obj and hasattr(intent_obj, 'model_dump') else (intent_obj.dict() if intent_obj and hasattr(intent_obj, 'dict') else None)
        
        capabilities_data = {}
        if isinstance(result, dict):
            capabilities_data = result.get("capabilities_registry", {})
        elif hasattr(result, 'capabilities_registry'):
            capabilities_data = result.capabilities_registry
        
        enabled_caps = [
            k for k, v in capabilities_data.items() 
            if v != CapabilityLevel.NOT_IMPLEMENTED
        ] if capabilities_data else []
        
        return {
            "intent": intent_data,
            "response": result.get("response", "") if isinstance(result, dict) else getattr(result, "response", ""),
            "capabilities": capabilities_data,
            "metrics": result.metrics.dict() if hasattr(result, 'metrics') else {},
            "enabled_capabilities": enabled_caps
        }

if __name__ == "__main__":
    agent = OAFlowAgent()
    
    test_cases = [
        "我想请明天下午半天年假",
        "我要请3天事假",
        "我今年用了几天年假",
        "我想撤回上周的请假申请",
        "请帮我查一下请假记录",
        "明天上午我要请假",
    ]
    
    print("=" * 70)
    print("OA Agent - 基于 LangGraph 的意图识别系统")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n【测试用例 {i}】")
        print(f"输入: {test_case}")
        
        result = agent.process(test_case, f"user_{i}")
        
        print(f"识别意图: {result['intent']['intent'] if result['intent'] else 'None'}")
        print(f"置信度: {result['intent']['confidence']:.2f}" if result['intent'] else "")
        print(f"提取实体: {result['intent']['entities_extracted'] if result['intent'] else 'None'}")
        print(f"需要澄清: {result['intent']['clarification_needed'] if result['intent'] else False}")
        print(f"缺失字段: {result['intent']['required_fields'] if result['intent'] else 'None'}")
        print(f"响应: {result['response']}")
        print(f"启用能力: {result['enabled_capabilities']}")
    
    print("\n" + "=" * 70)
    print("最终指标:")
    print(f"总请求数: {agent.recognizer.capabilities}")
    print(f"能力分级:")
    for cap, level in agent.recognizer.capabilities.items():
        print(f"  - {cap}: {level.value}")
    print("=" * 70)
