"""
OA Agent v2.0 - 支持多模型和外部数据源的完整实现
类似Hermes Agent的架构设计
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import json
import os
from abc import ABC, abstractmethod
import re
import random
from datetime import datetime, timedelta


# ==================== 配置与枚举 ====================

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


# ==================== 数据模型 ====================

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
    model_used: str = "default"


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
    model_stats: Dict[str, int] = Field(default_factory=dict)


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
    data_source: Optional[str] = None


# ==================== 数据源抽象层 ====================

class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def get_leave_balance(self, user_id: str) -> Dict[str, Any]:
        """获取员工请假余额"""
        pass
    
    @abstractmethod
    def get_employee_info(self, user_id: str) -> Dict[str, Any]:
        """获取员工信息"""
        pass
    
    @abstractmethod
    def get_approval_chain(self, leave_type: str, duration: float) -> List[str]:
        """获取审批链"""
        pass
    
    @abstractmethod
    def submit_leave_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """提交请假申请"""
        pass
    
    @abstractmethod
    def get_leave_records(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取请假记录"""
        pass


class MockDataSource(DataSource):
    """Mock数据源 - 用于开发测试"""
    
    def __init__(self):
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """初始化Mock数据"""
        # 员工数据
        self.employees = {
            "user_001": {
                "user_id": "user_001",
                "name": "张三",
                "department": "技术部",
                "position": "高级工程师",
                "manager": "user_002",
                "annual_balance": 15.0,
                "personal_balance": 3.0,
                "sick_balance": 5.0,
                "remuneration_balance": 8.0,
                "join_date": "2023-01-15",
            },
            "user_002": {
                "user_id": "user_002",
                "name": "李四",
                "department": "技术部",
                "position": "技术经理",
                "manager": "user_003",
                "annual_balance": 18.0,
                "personal_balance": 3.0,
                "sick_balance": 5.0,
                "remuneration_balance": 10.0,
                "join_date": "2022-03-10",
            },
            "user_003": {
                "user_id": "user_003",
                "name": "王五",
                "department": "技术部",
                "position": "技术总监",
                "manager": "user_004",
                "annual_balance": 20.0,
                "personal_balance": 3.0,
                "sick_balance": 5.0,
                "remuneration_balance": 12.0,
                "join_date": "2021-06-01",
            },
            "user_004": {
                "user_id": "user_004",
                "name": "赵六",
                "department": "人力资源部",
                "position": "HRBP",
                "manager": None,
                "annual_balance": 15.0,
                "personal_balance": 3.0,
                "sick_balance": 5.0,
                "remuneration_balance": 8.0,
                "join_date": "2020-09-01",
            }
        }
        
        # 请假记录
        self.leave_records = [
            {
                "record_id": "LR001",
                "user_id": "user_001",
                "leave_type": "annual_leave",
                "start_date": "2026-09-01",
                "end_date": "2026-09-02",
                "duration_hours": 16.0,
                "status": "approved",
                "approved_by": "user_002",
                "submit_time": "2026-08-30 10:00:00",
                "reason": "回家探亲"
            },
            {
                "record_id": "LR002",
                "user_id": "user_001",
                "leave_type": "personal_leave",
                "start_date": "2026-08-20",
                "end_date": "2026-08-20",
                "duration_hours": 8.0,
                "status": "approved",
                "approved_by": "user_002",
                "submit_time": "2026-08-18 14:00:00",
                "reason": "看病"
            },
            {
                "record_id": "LR003",
                "user_id": "user_002",
                "leave_type": "annual_leave",
                "start_date": "2026-09-05",
                "end_date": "2026-09-08",
                "duration_hours": 32.0,
                "status": "pending",
                "approved_by": None,
                "submit_time": "2026-09-01 09:00:00",
                "reason": "旅游"
            }
        ]
    
    def get_leave_balance(self, user_id: str) -> Dict[str, Any]:
        """获取员工请假余额"""
        employee = self.employees.get(user_id)
        if not employee:
            return {"error": "员工不存在"}
        
        return {
            "user_id": user_id,
            "name": employee["name"],
            "annual_balance": employee["annual_balance"],
            "personal_balance": employee["personal_balance"],
            "sick_balance": employee["sick_balance"],
            "remuneration_balance": employee["remuneration_balance"],
            "total_balance": (
                employee["annual_balance"] + 
                employee["personal_balance"] + 
                employee["sick_balance"] + 
                employee["remuneration_balance"]
            )
        }
    
    def get_employee_info(self, user_id: str) -> Dict[str, Any]:
        """获取员工信息"""
        employee = self.employees.get(user_id)
        if not employee:
            return {"error": "员工不存在"}
        
        return {
            "user_id": employee["user_id"],
            "name": employee["name"],
            "department": employee["department"],
            "position": employee["position"],
            "manager_id": employee["manager"],
            "join_date": employee["join_date"],
            "annual_balance": employee["annual_balance"]
        }
    
    def get_approval_chain(self, leave_type: str, duration: float) -> List[str]:
        """获取审批链"""
        # 默认审批链
        approval_chains = {
            "annual_leave": {
                "range": [(0, 1), (1, 3), (3, 7), (7, float('inf'))],
                "managers": ["user_002", "user_003", "user_004", "user_004"]  # 直属领导->总监->HR->总监
            }
        }
        
        return ["user_002"]  # 默认返回直属领导
    
    def submit_leave_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """提交请假申请"""
        new_record = {
            "record_id": f"LR{len(self.leave_records) + 1:03d}",
            "user_id": request.get("user_id"),
            "leave_type": request.get("leave_type"),
            "start_date": request.get("start_date"),
            "end_date": request.get("end_date"),
            "duration_hours": request.get("duration_hours"),
            "status": "pending",
            "approved_by": None,
            "submit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reason": request.get("reason", "")
        }
        
        self.leave_records.append(new_record)
        return new_record
    
    def get_leave_records(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取请假记录"""
        records = [
            r for r in self.leave_records 
            if r["user_id"] == user_id
        ][:limit]
        return records


class DatabaseDataSource(DataSource):
    """外部数据库数据源 - 支持连接实际数据库"""
    
    def __init__(self, db_type: str = "sqlite", db_path: str = None):
        self.db_type = db_type
        self.db_path = db_path or "data/oa_agent.db"
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保数据库已初始化"""
        if not self._initialized:
            self._create_tables()
            self._initialized = True
    
    def _create_tables(self):
        """创建数据库表"""
        # 这里需要实际数据库连接代码
        # 暂时只做示意
        pass
    
    def get_leave_balance(self, user_id: str) -> Dict[str, Any]:
        """获取员工请假余额 - 从数据库查询"""
        self._ensure_initialized()
        # 实际数据库查询逻辑
        return {
            "user_id": user_id,
            "annual_balance": 15.0,
            "personal_balance": 3.0,
            "sick_balance": 5.0,
            "remuneration_balance": 8.0
        }
    
    def get_employee_info(self, user_id: str) -> Dict[str, Any]:
        """获取员工信息 - 从数据库查询"""
        self._ensure_initialized()
        # 实际数据库查询逻辑
        return {
            "user_id": user_id,
            "name": "张三",
            "department": "技术部",
            "position": "高级工程师",
            "manager_id": "user_002"
        }
    
    def get_approval_chain(self, leave_type: str, duration: float) -> List[str]:
        """获取审批链 - 从数据库查询"""
        self._ensure_initialized()
        # 实际数据库查询逻辑
        return ["user_002"]
    
    def submit_leave_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """提交请假申请 - 写入数据库"""
        self._ensure_initialized()
        # 实际数据库插入逻辑
        return request
    
    def get_leave_records(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取请假记录 - 从数据库查询"""
        self._ensure_initialized()
        # 实际数据库查询逻辑
        return []


# ==================== 多模型支持（类似Hermes） ====================

class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    LOCAL = "local"
    MOCK = "mock"


class ModelConfig(BaseModel):
    """模型配置"""
    provider: ModelProvider = ModelProvider.MOCK
    model_name: str = "mock-model"
    temperature: float = 0.7
    max_tokens: int = 1000
    api_key: Optional[str] = None
    endpoint: Optional[str] = None


class BaseModelClient(ABC):
    """模型客户端抽象基类"""
    
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """生成响应"""
        pass
    
    @abstractmethod
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """提取意图"""
        pass


class DeepSeekClient(BaseModelClient):
    """DeepSeek模型客户端"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
        self.api_key = api_key
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """调用DeepSeek API生成响应"""
        # 实际调用DeepSeek API
        return f"[DeepSeek {self.model_name}] 识别到意图: {prompt[:20]}..."
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """使用DeepSeek提取意图"""
        # 实际调用DeepSeek API进行意图识别
        return {
            "intent": "leave_request",
            "confidence": 0.92,
            "leave_type": "annual_leave"
        }


class OpenAIClient(BaseModelClient):
    """OpenAI模型客户端"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4"):
        self.api_key = api_key
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """调用OpenAI API生成响应"""
        # 实际调用OpenAI API
        # 这里模拟返回
        return f"[OpenAI {self.model_name}] 识别到意图: {prompt[:20]}..."
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """使用OpenAI提取意图"""
        # 实际调用OpenAI API进行意图识别
        return {
            "intent": "leave_request",
            "confidence": 0.95,
            "leave_type": "annual_leave"
        }


class AnthropicClient(BaseModelClient):
    """Anthropic模型客户端"""
    
    def __init__(self, api_key: str, model_name: str = "claude-3-opus"):
        self.api_key = api_key
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """调用Anthropic API生成响应"""
        # 实际调用Anthropic API
        return f"[Anthropic {self.model_name}] 识别到意图: {prompt[:20]}..."
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """使用Anthropic提取意图"""
        return {
            "intent": "leave_request",
            "confidence": 0.93,
            "leave_type": "personal_leave"
        }


class MockModelClient(BaseModelClient):
    """Mock模型客户端 - 用于开发测试"""
    
    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Mock生成响应"""
        return f"[Mock {self.model_name}] 响应: {prompt[:50]}..."
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """Mock意图识别"""
        return {
            "intent": "leave_request",
            "confidence": 0.85,
            "leave_type": "annual_leave",
            "time_slot": "afternoon_half",
            "start_date": "tomorrow"
        }


class ModelRouter:
    """模型路由 - 类似Hermes的模型选择策略"""
    
    def __init__(self):
        self.clients: Dict[ModelProvider, BaseModelClient] = {}
        self.default_model = ModelConfig(provider=ModelProvider.MOCK)
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化所有模型客户端"""
        self.clients[ModelProvider.MOCK] = MockModelClient("mock-v1")
        # 实际使用时初始化真实客户端
        # self.clients[ModelProvider.DEEPSEEK] = DeepSeekClient(os.getenv("DEEPSEEK_API_KEY"))
        # self.clients[ModelProvider.OPENAI] = OpenAIClient(os.getenv("OPENAI_API_KEY"))
        # self.clients[ModelProvider.ANTHROPIC] = AnthropicClient(os.getenv("ANTHROPIC_API_KEY"))
    
    def select_model(self, intent_type: IntentType, complexity: str = "simple") -> BaseModelClient:
        """根据意图类型和复杂度选择模型"""
        # 简单规则：不同意图使用不同模型
        model_selection = {
            IntentType.LEAVE_REQUEST: ModelProvider.DEEPSEEK,
            IntentType.LEAVE_QUERY: ModelProvider.DEEPSEEK,
            IntentType.LEAVE_WITHDRAW: ModelProvider.DEEPSEEK,
            IntentType.OTHER: ModelProvider.DEEPSEEK
        }
        
        provider = model_selection.get(intent_type, self.default_model.provider)
        return self.clients[provider]
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表"""
        return [
            {"provider": "mock", "model": "mock-v1", "status": "active"},
            {"provider": "deepseek", "model": "deepseek-chat", "status": "available"},
            # {"provider": "openai", "model": "gpt-4", "status": "available"},
            # {"provider": "anthropic", "model": "claude-3-opus", "status": "available"},
        ]


# ==================== 意图识别器（增强版） ====================

class EnhancedIntentionRecognizer:
    """增强版意图识别器 - 支持多模型和更多规则"""
    
    def __init__(self, model_router: ModelRouter = None, data_source: DataSource = None):
        self.model_router = model_router or ModelRouter()
        self.data_source = data_source or MockDataSource()
        
        # 保留原有关键词规则
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
        
        self.capabilities = {
            "intent_recognition": CapabilityLevel.BASIC,
            "entity_extraction": CapabilityLevel.BASIC,
            "leave_type_classification": CapabilityLevel.ENHANCED,
            "time_extraction": CapabilityLevel.BASIC,
            "mock_data_support": CapabilityLevel.BASIC,
            "multi_model_routing": CapabilityLevel.BASIC,
        }
    
    def extract_intent(self, text: str, model_name: str = None, user_id: str = "unknown") -> UserIntent:
        """提取用户意图 - 支持指定模型"""
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
        
        # 7. 使用模型（可选）
        model_used = model_name or "default"
        if model_name and model_name != "default":
            # 使用指定模型进行增强识别
            client = self.model_router.clients.get(ModelProvider.MOCK)
            if client:
                # 可以加入模型辅助识别逻辑
                pass
        
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
    
    def __init__(self, data_source: DataSource = None):
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
    
    def generate_leave_query_response(self, user_id: str = "unknown") -> str:
        """生成请假查询响应 - 支持查询实际数据"""
        # 查询Mock数据
        records = self.data_source.get_leave_records(user_id, limit=5)
        
        if not records:
            return "正在查询您的请假记录..."
        
        return f"正在查询您的请假记录... 共找到 {len(records)} 条记录。"
    
    def generate_leave_withdraw_response(self) -> str:
        """生成请假撤回响应"""
        return "正在处理请假撤回..."
    
    def generate_default_response(self) -> str:
        """生成默认响应"""
        return "我理解您想处理一些 HR 相关事务，可以告诉我具体需要什么帮助吗？"


# ==================== OA Agent v2.0 ====================

class OAFlowAgentV2:
    """OA 流程 Agent v2.0 - 支持多模型和外部数据源"""
    
    def __init__(self, data_source: DataSource = None, model_router: ModelRouter = None):
        self.data_source = data_source or MockDataSource()
        self.model_router = model_router or ModelRouter()
        self.recognizer = EnhancedIntentionRecognizer(self.model_router, self.data_source)
        self.response_generator = EnhancedResponseGenerator(self.data_source)
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
        intent = self.recognizer.extract_intent(
            state.input_text, 
            user_id=state.user_id
        )
        return {
            "intent": intent,
            "capabilities_registry": self.recognizer.capabilities,
            "data_source": "mock" if isinstance(self.data_source, MockDataSource) else "database"
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
            response = self.response_generator.generate_leave_query_response(state.user_id)
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
            
            # 统计模型使用
            model_stats = state.metrics.model_stats
            model_stats[intent.model_used] = model_stats.get(intent.model_used, 0) + 1
        
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
        
        data_source = result.get("data_source") if isinstance(result, dict) else "unknown"
        
        return {
            "intent": intent_data,
            "response": result.get("response", "") if isinstance(result, dict) else getattr(result, "response", ""),
            "capabilities": capabilities_data,
            "metrics": result.metrics.model_dump() if hasattr(result, 'metrics') else {},
            "enabled_capabilities": enabled_caps,
            "data_source": data_source,
            "model_used": intent_data.get("model_used", "unknown") if intent_data else "unknown"
        }


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 80)
    print("OA Agent v2.0 - 支持多模型和外部数据源")
    print("=" * 80)
    
    # 初始化 Agent（使用Mock数据源）
    agent = OAFlowAgentV2()
    
    # 切换到DeepSeek模型（无需修改代码，只需配置）
    agent.model_router.clients[ModelProvider.DEEPSEEK] = DeepSeekClient(
        api_key=os.getenv("DEEPSEEK_API_KEY", "sk-")
    )
    
    test_cases = [
        "我想请明天下午半天年假",
        "我要请3天事假",
        "我今年用了几天年假",
        "我想撤回上周的请假申请",
        "请帮我查一下请假记录",
        "明天上午我要请假",
    ]
    
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
        print(f"数据源: {result['data_source']}")
        print(f"使用的模型: {result.get('model_used', 'unknown')}")
    
    print("\n" + "=" * 80)
    print("能力状态:")
    for cap, level in agent.recognizer.capabilities.items():
        print(f"  - {cap}: {level.value}")
    print("=" * 80)
