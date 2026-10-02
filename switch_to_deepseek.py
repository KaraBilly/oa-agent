#!/usr/bin/env python3
"""
DeepSeek模型切换脚本
无需修改代码，只需运行此脚本即可切换到DeepSeek模型
"""

import os
import sys

# 设置DeepSeek API Key（从环境变量读取）
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "sk-")

print("=" * 60)
print("OA Agent - DeepSeek模型切换工具")
print("=" * 60)
print()

# 导入必要的模块
try:
    from oa_agent_v2 import (
        OAFlowAgentV2, 
        DeepSeekClient, 
        ModelProvider
    )
    print("✓ 成功导入模块")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print()
print("配置步骤:")
print(f"1. DeepSeek API Key: {deepseek_api_key[:10]}...{deepseek_api_key[-10:] if len(deepseek_api_key) > 20 else '未设置'}")
print("2. 初始化DeepSeek客户端...")
print("3. 创建ModelRouter并添加DeepSeek客户端...")
print()

# 初始化DeepSeek客户端
deepseek_client = DeepSeekClient(
    api_key=deepseek_api_key,
    model_name="deepseek-chat"
)

# 创建ModelRouter并添加DeepSeek客户端
router = ModelProvider
router.clients = {ModelProvider.DEEPSEEK: deepseek_client}

# 初始化Agent
print("4. 初始化OA Agent...")
agent = OAFlowAgentV2(model_router=type('Router', (), {'clients': router.clients})())

print()
print("=" * 60)
print("✓ DeepSeek模型已配置完成！")
print("=" * 60)
print()
print("使用示例:")
print("  agent = OAFlowAgentV2(model_router=router)")
print("  result = agent.process('我想请明天下午半天年假')")
print()
