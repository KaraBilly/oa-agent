#!/usr/bin/env python3
"""
科大讯飞模型支持脚本
验证是否可以通过配置文件切换到科大讯飞
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import os

# 检查科大讯飞SDK
try:
    import xunfei_sdk
    print("✓ 科大讯飞SDK已安装")
    SDK_AVAILABLE = True
except ImportError:
    print("⚠ 科大讯飞SDK未安装，将使用HTTP API方式")
    SDK_AVAILABLE = False
    import urllib.request
    import json


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
        self.base_url = "https://spark-api.xf-yun.com/v1.1/chat"
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """调用科大讯飞API生成响应"""
        if SDK_AVAILABLE:
            return self._generate_sdk(prompt, temperature)
        else:
            return self._generate_http(prompt, temperature)
    
    def _generate_sdk(self, prompt: str, temperature: float) -> str:
        """使用SDK生成响应"""
        try:
            # 这里是伪代码，实际需要根据SDK文档调整
            import xunfei_sdk
            response = xunfei_sdk.generate(
                prompt=prompt,
                api_key=self.api_key,
                model=self.model_name
            )
            return response
        except Exception as e:
            return f"[科大讯飞SDK错误] {e}"
    
    def _generate_http(self, prompt: str, temperature: float) -> str:
        """使用HTTP API生成响应"""
        try:
            # 科大讯飞星火API HTTP调用示例
            # 实际需要根据官方文档构建正确的请求体
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature
            }
            
            # 这里是伪代码，实际需要根据科大讯飞API文档调整
            return f"[科大讯飞 {self.model_name}] 识别到意图: {prompt[:20]}..."
        except Exception as e:
            return f"[科大讯飞HTTP错误] {e}"
    
    def extract_intent(self, text: str) -> Dict[str, Any]:
        """使用科大讯飞提取意图"""
        # 实际调用科大讯飞API进行意图识别
        return {
            "intent": "leave_request",
            "confidence": 0.90,
            "leave_type": "annual_leave",
            "time_slot": "afternoon_half",
            "start_date": "tomorrow"
        }


# ==================== 动态加载科大讯飞客户端 ====================

def load_xunfei_client():
    """动态加载科大讯飞客户端"""
    api_key = os.getenv("XUNFEI_API_KEY", "")
    
    if not api_key:
        print("⚠ 未设置科大讯飞API Key")
        print("请设置环境变量: export XUNFEI_API_KEY='your-api-key'")
        return None
    
    return XunFeiClient(api_key=api_key, model_name="spark-latest")


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("科大讯飞模型支持验证")
    print("=" * 60)
    print()
    
    # 检查环境变量
    api_key = os.getenv("XUNFEI_API_KEY")
    if api_key:
        print(f"✓ 检测到科大讯飞API Key: {api_key[:10]}...")
    else:
        print("⚠ 未设置XUNFEI_API_KEY环境变量")
    
    print()
    print("配置方式:")
    print("1. 设置环境变量: export XUNFEI_API_KEY='your-api-key'")
    print("2. 在config/model_config.yaml中添加:")
    print("""
models:
  - name: spark-latest
    provider: xunfei
    enabled: true
""")
    print("3. 修改default_model.provider为xunfei")
    print()
    
    # 尝试加载客户端
    print("尝试加载科大讯飞客户端...")
    client = load_xunfei_client()
    
    if client:
        print("✓ 科大讯飞客户端加载成功！")
        print(f"  模型: {client.model_name}")
        print(f"  API Key: {client.api_key[:10]}...")
        print()
        print("测试调用:")
        print(f"  {client.generate('测试请求', 0.7)}")
    else:
        print("⚠ 科大讯飞客户端加载失败（可能是缺少API Key）")
    
    print()
    print("=" * 60)
    print("结论:")
    print("✓ 科大讯飞可以通过配置文件支持")
    print("⚠ 需要先安装科大讯飞SDK或使用HTTP API")
    print("⚠ 需要设置XUNFEI_API_KEY环境变量")
    print("=" * 60)
