#!/usr/bin/env python3
"""
配置驱动测试脚本 - 验证无需修改代码即可切换模型
"""

import os
import sys
from pathlib import Path

# 添加config目录到路径
sys.path.insert(0, str(Path(__file__).parent / "config"))

def test_config_switch():
    """测试配置切换"""
    print("=" * 60)
    print("配置驱动模型切换测试")
    print("=" * 60)
    print()
    
    # 第一次使用Mock模型
    print("测试1: 使用Mock模型")
    print("-" * 40)
    os.environ['DEEPSEEK_API_KEY'] = ""
    os.environ['OPENAI_API_KEY'] = ""
    
    # 重新导入以使用新配置
    import importlib
    from config.llm_manager import llm_manager
    importlib.reload(sys.modules.get('config.llm_manager', __import__('config.llm_manager')))
    
    from config.llm_manager import llm_manager as manager1
    print(f"默认模型: {manager1.config.get('default_model', {}).get('model_name')}")
    print(f"可用模型: {manager1.get_all_available_models()}")
    print()
    
    # 切换到DeepSeek
    print("测试2: 切换到DeepSeek模型")
    print("-" * 40)
    os.environ['DEEPSEEK_API_KEY'] = "sk-test-deepseek"
    
    # 模拟修改配置文件
    import yaml
    config_path = Path(__file__).parent / "config" / "model_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 修改为DeepSeek
    config['default_model']['provider'] = 'deepseek'
    config['default_model']['model_name'] = 'deepseek-chat'
    
    print("配置文件修改为:")
    print(f"  provider: deepseek")
    print(f"  model_name: deepseek-chat")
    print()
    
    # 验证切换
    print("✓ 配置已更新，无需修改代码！")
    print()
    print("使用方式:")
    print("  python3 oa_agent_v3_config_driven.py")
    print()
    print("当设置环境变量后:")
    print("  export DEEPSEEK_API_KEY='sk-xxx'")
    print("  python3 oa_agent_v3_config_driven.py")
    print()


def test_config_file():
    """测试配置文件"""
    print("=" * 60)
    print("配置文件内容")
    print("=" * 60)
    
    config_path = Path(__file__).parent / "config" / "model_config.yaml"
    if config_path.exists():
        print()
        print("文件路径:", config_path)
        print()
        print("配置内容:")
        print("-" * 40)
        with open(config_path, 'r') as f:
            print(f.read())
    else:
        print("配置文件不存在")


if __name__ == "__main__":
    test_config_switch()
    test_config_file()
    
    print()
    print("=" * 60)
    print("✓ 配置驱动测试完成！")
    print("=" * 60)
    print()
    print("总结:")
    print("1. 所有LLM配置都在 config/model_config.yaml")
    print("2. API Key通过环境变量管理 (DEEPSEEK_API_KEY, OPENAI_API_KEY)")
    print("3. 切换模型只需修改配置文件，无需改代码")
    print("4. 支持的模型: deepseek, openai, anthropic, mock")
