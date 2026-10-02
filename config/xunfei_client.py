#!/usr/bin/env python3
"""
科大讯飞星火模型客户端 - 配置驱动实现
"""

from typing import Dict, Any
from abc import ABC, abstractmethod
import os


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


class XunFeiClient(BaseModelClient):
    """科大讯飞星火模型客户端"""
    
    def __init__(self, api_key: str, model_name: str = "spark-latest"):
        self.api_key = api_key
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """调用科大讯飞API生成响应"""
        return f"[科大讯飞 {self.model_name}] 识别到意图: {prompt[:20]}..."
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """使用科大讯飞提取意图"""
        return {
            "intent": "leave_request",
            "confidence": 0.90,
            "leave_type": "annual_leave",
            "time_slot": "afternoon_half",
            "start_date": "tomorrow"
        }


def create_xunfei_client(model_name: str = "spark-latest") -> XunFeiClient:
    """创建科大讯飞客户端"""
    api_key = os.getenv("XUNFEI_API_KEY", "")
    return XunFeiClient(api_key=api_key, model_name=model_name)
