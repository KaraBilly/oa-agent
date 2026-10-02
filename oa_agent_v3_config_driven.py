#!/usr/bin/env python3
"""
OA Agent v3.0 - 完全配置驱动的LLM模型切换架构
类似OpenCLAW，通过配置文件管理所有LLM API密钥和模型
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import json
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime

# 导入配置驱动的LLM管理器
from config.llm_manager import llm_manager, get_llm_client, switch_llm_model, LLMClientManager


# ==================== 枚举定义 ====================

class CapabilityLevel(Enum):
    NOT_IMPLEMENTED = "not_implemented"
    BASIC = "basic"
    ENHANCED = "enhanced"
    ADVANCED = "advanced"
    EXPERT = "expert"


class IntentType(Enum):
    LEAVE_REQUEST = "leave_request"
    LEAVE_QUERY = "leave_query"
    LEAVE_WITHDRAW = "leave_withdraw"
    OTHER = "other"


class LeaveType(Enum):
    ANNUAL_LEAVE = "annual_leave"
    PERSONAL_LEAVE = "personal_leave"
    SICK_LEAVE = "sick_leave"
    REMUNERATION_LEAVE = "remuneration_leave"
    MARRIAGE_LEAVE = "marriage_leave"
    MATERNITY_LEAVE = "maternity_leave"
    BEREAVEMENT_LEAVE = "bereavement_leave"


class LeaveTimeSlot(Enum):
    FULL_DAY = "full_day"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    MORNING_HALF = "morning_half"
    AFTERNOON_HALF = "afternoon_half"
    SPECIFIC_HOURS = "specific_hours"


# ==================== 数据模型 ====================

class UserIntent(BaseModel):
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
    model_used: str = "default"


class IntentionMetrics(BaseModel):
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    avg_confidence: float = 0.0
    total_requests: int = 0
    correct_intents: int = 0
    extraction_recall: float = 0.0
    model_stats: Dict[str, int] = Field(default_factory=dict)


class AgentState(BaseModel):
    input_text: str = ""
    user_id: str = "unknown"
    intent: Optional[UserIntent] = None
    response: str = ""
    metrics: IntentionMetrics = Field(default_factory=IntentionMetrics)
    conversation_history: List[Dict[str, Any]] = []
    capabilities_registry: Dict[str, CapabilityLevel] = Field(default_factory=dict)
    error: Optional[str] = None


# ==================== Mock数据源 ====================

class MockDataSource:
    """Mock数据源 - 用于开发测试"""
    
    def __init__(self):
        self.employees = {
            "user_001": {
                "user_id": "user_001",
                "name": "张三",
                "department": "技术部",
                "position": "高级工程师",
                "annual_balance": 15.0
            },
            "user_002": {
                "user_id": "user_002",
                "name": "李四",
                "department": "技术部",
                "position": "技术经理",
                "annual_balance": 18.0
            }
        }
    
    def get_leave_balance(self, user_id: str) -> Dict[str, Any]:
        employee = self.employees.get(user_id)
        if not employee:
            return {"error": "员工不存在"}
        return {
            "user_id": user_id,
            "name": employee["name"],
            "annual_balance": employee["annual_balance"]
        }
    
    def get_employee_info(self, user_id: str) -> Dict[str, Any]:
        employee = self.employees.get(user_id)
        if not employee:
            return {"error": "员工不存在"}
        return {
            "user_id": employee["user_id"],
            "name": employee["name"],
            "department": employee["department"],
            "position": employee["position"]
        }


# ==================== 意图识别器 ====================

class EnhancedIntentionRecognizer:
    """增强版意图识别器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
        self.leave_keywords = {
            "我想请": IntentType.LEAVE_REQUEST,
            "我要请": IntentType.LEAVE_REQUEST,
            "请假": IntentType.LEAVE_REQUEST,
            "请年假": IntentType.LEAVE_REQUEST,
            "请事假": IntentType.LEAVE_REQUEST,
            "请病假": IntentType.LEAVE_REQUEST,
            "请调休": IntentType.LEAVE_REQUEST,
            "休假": IntentType.LEAVE_REQUEST,
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
        }
        
        self.capabilities = {
            "intent_recognition": CapabilityLevel.BASIC,
            "entity_extraction": CapabilityLevel.BASIC,
            "leave_type_classification": CapabilityLevel.ENHANCED,
            "time_extraction": CapabilityLevel.BASIC,
            "mock_data_support": CapabilityLevel.BASIC,
            "llm_config_driven": CapabilityLevel.BASIC,
        }
    
    def extract_intent(self, text: str, user_id: str = "unknown") -> UserIntent:
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
        
        # 7. 使用LLM（如果配置）
        model_used = llm_manager.config.get("default_model", {}).get("model_name", "default")
        
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
            required_fields=required_fields,
            model_used=model_used
        )
    
    def _recognize_main_intent(self, text: str) -> IntentType:
        """识别主意图"""
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


# ==================== 响应生成器 ====================

class EnhancedResponseGenerator:
    """增强版响应生成器"""
    
    def __init__(self, data_source=None):
        self.data_source = data_source or MockDataSource()
    
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


# ==================== OA Agent v3.0 ====================

class OAFlowAgentV3:
    """OA 流程 Agent v3.0 - 完全配置驱动"""
    
    def __init__(self):
        self.recognizer = EnhancedIntentionRecognizer()
        self.response_generator = EnhancedResponseGenerator()
        self.data_source = MockDataSource()
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
        model_name = llm_manager.config.get("default_model", {}).get("model_name", "default")
        intent = self.recognizer.extract_intent(state.input_text, user_id=state.user_id)
        if intent:
            intent.model_used = model_name
        return {
            "intent": intent,
            "capabilities_registry": self.recognizer.capabilities,
            "model_name": model_name
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
            
            model_stats = state.metrics.model_stats
            model_stats[intent.model_used] = model_stats.get(intent.model_used, 0) + 1
        
        return {}
    
    def process(self, input_text: str, user_id: str = "unknown") -> Dict[str, Any]:
        """处理输入"""
        config = {"configurable": {"thread_id": user_id}}
        inputs = {"input_text": input_text, "user_id": user_id}
        result = self.graph.invoke(inputs, config=config)
        
        intent_data = None
        if isinstance(result, dict):
            intent_obj = result.get("intent")
            if intent_obj:
                intent_data = intent_obj.model_dump() if hasattr(intent_obj, 'model_dump') else intent_obj.dict() if hasattr(intent_obj, 'dict') else intent_obj
        
        return {
            "intent": intent_data,
            "response": result.get("response", "") if isinstance(result, dict) else getattr(result, "response", ""),
            "capabilities": result.get("capabilities_registry", {}) if isinstance(result, dict) else {},
            "metrics": result.get("metrics", {}).model_dump() if hasattr(result.get("metrics", {}), 'model_dump') else {},
            "enabled_capabilities": [
                k for k, v in (result.get("capabilities_registry", {}) if isinstance(result, dict) else {}).items() 
                if v != CapabilityLevel.NOT_IMPLEMENTED
            ],
            "model_used": (intent_data.get("model_used") if intent_data else None) or result.get("model_name", "unknown")
        }


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("OA Agent v3.0 - 完全配置驱动的LLM模型切换架构")
    print("=" * 80)
    print()
    
    # 显示当前配置
    print("当前模型配置:")
    print(f"  默认模型: {llm_manager.config.get('default_model', {}).get('model_name', 'unknown')}")
    print(f"  可用模型: {llm_manager.get_all_available_models()}")
    print()
    
    # 初始化Agent
    agent = OAFlowAgentV3()
    
    test_cases = [
        "我想请明天下午半天年假",
        "我要请3天事假",
        "我今年用了几天年假",
        "我想撤回上周的请假申请",
        "请帮我查一下请假记录",
        "明天上午我要请假",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"【测试用例 {i}】")
        print(f"输入: {test_case}")
        
        result = agent.process(test_case, f"user_{i}")
        
        print(f"  识别意图: {result['intent']['intent'] if result['intent'] else 'None'}")
        print(f"  置信度: {result['intent']['confidence']:.2f}" if result['intent'] else "")
        print(f"  使用模型: {result['model_used']}")
        print(f"  响应: {result['response']}")
    
    print()
    print("=" * 80)
    print("能力状态:")
    for cap, level in agent.recognizer.capabilities.items():
        print(f"  - {cap}: {level.value}")
    print("=" * 80)
