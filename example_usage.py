#!/usr/bin/env python3
"""
使用示例：如何配置和使用不同模型
"""

from oa_agent_v2 import (
    OAFlowAgentV2, 
    MockDataSource, 
    ModelRouter, 
    ModelProvider,
    ModelConfig,
    DeepSeekClient
)


def example_mock_model():
    """使用Mock模型（默认）"""
    print("=" * 60)
    print("示例1: 使用Mock模型（开发测试）")
    print("=" * 60)
    
    agent = OAFlowAgentV2()
    result = agent.process("我想请明天下午半天年假", "user_001")
    
    print(f"使用的模型: {result.get('model_used', 'unknown')}")
    print(f"数据源: {result['data_source']}")
    print(f"响应: {result['response']}")
    print()


def example_with_deepseek():
    """使用DeepSeek模型（需要配置API Key）"""
    print("=" * 60)
    print("示例2: 使用DeepSeek模型（需要API Key）")
    print("=" * 60)
    
    print("配置步骤:")
    print("1. 在config/model_config.yaml中设置default_model.provider为deepseek")
    print("2. 设置环境变量: export DEEPSEEK_API_KEY='your-api-key'")
    print("3. 或直接修改代码:")
    print()
    print("# 示例代码:")
    print("""
from oa_agent_v2 import OAFlowAgentV2, DeepSeekClient, ModelRouter
import os

# 配置DeepSeek客户端
api_key = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
deepseek_client = DeepSeekClient(api_key=api_key, model_name="deepseek-chat")

# 创建自定义ModelRouter
router = ModelRouter()
router.clients[ModelProvider.DEEPSEEK] = deepseek_client

# 初始化Agent
agent = OAFlowAgentV2(model_router=router)

# 处理请求
result = agent.process("我想请明天下午半天年假", "user_001")
print(result)
    """)
    print()


if __name__ == "__main__":
    print("\n")
    print("=" * 60)
    print("OA Agent v2.0 - 模型使用示例")
    print("=" * 60)
    print()
    
    example_mock_model()
    example_with_deepseek()
    
    print("=" * 60)
    print("运行完成！")
    print("=" * 60)
