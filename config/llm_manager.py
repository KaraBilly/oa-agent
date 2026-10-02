"""
LLM客户端管理器 - 类似OpenCLAW的配置驱动架构
通过配置文件动态加载和管理不同LLM模型
"""

import importlib
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
import os


class LLMClientManager:
    """
    LLM客户端管理器
    通过配置文件动态加载和管理不同LLM模型，无需修改代码
    """
    
    def __init__(self, config_path: str = "config/model_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.clients: Dict[str, Any] = {}
        self._initialize_clients()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
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
    
    def _initialize_clients(self):
        """初始化所有客户端"""
        models = self.config.get("models", [])
        
        for model in models:
            if model.get("enabled", False):
                provider = model.get("provider", "mock")
                model_name = model.get("name", "default")
                
                # 根据provider动态导入客户端类
                client = self._create_client(provider, model_name)
                if client:
                    self.clients[model_name] = client
                    print(f"✓ 已加载模型: {model_name} ({provider})")
    
    def _create_client(self, provider: str, model_name: str) -> Optional[Any]:
        """动态创建客户端"""
        try:
            # 尝试从oa_agent_v2模块导入对应客户端
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            
            # 动态导入客户端类
            if provider == "deepseek":
                from oa_agent_v2 import DeepSeekClient
                api_key = os.getenv("DEEPSEEK_API_KEY", "")
                return DeepSeekClient(api_key=api_key, model_name=model_name)
            
            elif provider == "openai":
                from oa_agent_v2 import OpenAIClient
                api_key = os.getenv("OPENAI_API_KEY", "")
                return OpenAIClient(api_key=api_key, model_name=model_name)
            
            elif provider == "anthropic":
                from oa_agent_v2 import AnthropicClient
                api_key = os.getenv("ANTHROPIC_API_KEY", "")
                return AnthropicClient(api_key=api_key, model_name=model_name)
            
            elif provider == "mock":
                from oa_agent_v2 import MockModelClient
                return MockModelClient(model_name=model_name)
            
            else:
                print(f"未知的provider: {provider}")
                return None
                
        except ImportError as e:
            print(f"导入{provider}客户端失败: {e}")
            return None
    
    def get_client(self, model_name: str = None) -> Optional[Any]:
        """获取指定模型的客户端"""
        if not model_name:
            model_name = self.config.get("default_model", {}).get("model_name", "mock-v1")
        return self.clients.get(model_name)
    
    def get_model_for_intent(self, intent_type: str) -> str:
        """根据意图获取模型名称"""
        mapping = self.config.get("intent_model_mapping", {})
        return mapping.get(intent_type, self.config.get("default_model", {}).get("model_name", "mock-v1"))
    
    def get_all_available_models(self) -> List[Dict[str, Any]]:
        """获取所有可用模型列表"""
        return [
            {
                "name": name,
                "provider": self._get_provider_for_model(name)
            }
            for name in self.clients.keys()
        ]
    
    def _get_provider_for_model(self, model_name: str) -> str:
        """获取模型的provider"""
        models = self.config.get("models", [])
        for model in models:
            if model.get("name") == model_name:
                return model.get("provider", "unknown")
        return "unknown"
    
    def switch_model(self, new_model_name: str) -> bool:
        """切换模型（运行时）"""
        if new_model_name in self.clients:
            # 更新默认模型配置
            self.config["default_model"]["model_name"] = new_model_name
            return True
        return False


# 全局实例
llm_manager = LLMClientManager()


def get_llm_client(model_name: str = None):
    """获取LLM客户端（全局便捷函数）"""
    return llm_manager.get_client(model_name)


def switch_llm_model(model_name: str) -> bool:
    """切换LLM模型（全局便捷函数）"""
    return llm_manager.switch_model(model_name)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("LLM客户端管理器测试")
    print("=" * 60)
    print()
    
    print("可用模型:")
    for model in llm_manager.get_all_available_models():
        print(f"  - {model['name']} ({model['provider']})")
    
    print()
    print("默认模型:", llm_manager.config.get("default_model", {}).get("model_name"))
    print("意图->模型映射:", llm_manager.config.get("intent_model_mapping"))
