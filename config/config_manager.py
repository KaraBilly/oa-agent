#!/usr/bin/env python3
"""
配置管理模块
用于加载和管理模型配置
"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/model_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "default_model": {
                "provider": "mock",
                "model_name": "mock-v1",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "models": [
                {
                    "name": "mock-v1",
                    "provider": "mock",
                    "description": "Mock模型，用于开发测试",
                    "enabled": True
                }
            ],
            "intent_model_mapping": {
                "leave_request": "mock-v1",
                "leave_query": "mock-v1",
                "leave_withdraw": "mock-v1",
                "other": "mock-v1"
            }
        }
    
    def get_default_model(self) -> Dict[str, Any]:
        """获取默认模型配置"""
        return self.config.get("default_model", {})
    
    def get_enabled_models(self) -> list:
        """获取已启用的模型列表"""
        return [m for m in self.config.get("models", []) if m.get("enabled", False)]
    
    def get_model_by_name(self, model_name: str) -> Dict[str, Any]:
        """根据名称获取模型配置"""
        for model in self.config.get("models", []):
            if model.get("name") == model_name:
                return model
        return {}
    
    def get_model_for_intent(self, intent_type: str) -> str:
        """根据意图类型获取模型名称"""
        mapping = self.config.get("intent_model_mapping", {})
        return mapping.get(intent_type, self.config.get("default_model", {}).get("model_name", "mock-v1"))
    
    def get_api_key(self, provider: str) -> str:
        """获取API密钥（优先从环境变量读取）"""
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }
        env_var = env_var_map.get(provider, f"{provider.upper()}_API_KEY")
        return os.getenv(env_var, "")


# 使用示例
if __name__ == "__main__":
    config = ConfigManager()
    
    print("=== OA Agent 配置信息 ===")
    print(f"默认模型: {config.get_default_model()}")
    print(f"已启用模型:")
    for model in config.get_enabled_models():
        print(f"  - {model['name']} ({model['provider']})")
    
    print(f"\n意图->模型映射:")
    for intent, model in config.config.get("intent_model_mapping", {}).items():
        print(f"  {intent} -> {model}")
