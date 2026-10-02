#!/usr/bin/env python3
"""
集成测试 - OA Agent 完整流程
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from oa_graph_agent import OAFlowAgent, UserIntent, IntentType, CapabilityLevel
from leave_balance import LeaveBalanceChecker
from conflict_checker import ConflictChecker
from approval_chain import ApprovalChainResolver


def test_full_leave_request_flow():
    """测试完整的请假请求流程"""
    print("\n【集成测试】完整请假请求流程")
    
    # 初始化所有模块
    agent = OAFlowAgent()
    balance_checker = LeaveBalanceChecker()
    conflict_checker = ConflictChecker()
    chain_resolver = ApprovalChainResolver()
    
    test_input = "我想请明天下午半天年假"
    user_id = "user_integration_001"
    
    # 1. 意图识别
    result = agent.process(test_input, user_id)
    intent = result.get("intent")
    
    assert intent is not None
    assert intent["intent"] == IntentType.LEAVE_REQUEST.value
    assert intent["leave_type"] == "annual_leave"
    print(f"  ✓ 意图识别: {intent['intent']}")
    
    # 2. 余额校验
    leave_type = intent.get("leave_type", "annual_leave")
    balance_result = balance_checker.check_balance(leave_type, 0.5, user_id)
    
    assert balance_result.status.value == "success"
    print(f"  ✓ 余额校验: {balance_result.message}")
    
    # 3. 冲突校验
    start_date = intent.get("start_date", "tomorrow")
    time_slot = intent.get("time_slot", "afternoon_half")
    conflict_result = conflict_checker.check_all(user_id, start_date, time_slot, leave_type)
    
    print(f"  ✓ 冲突校验: {conflict_result.message}")
    
    # 4. 审批链解析
    approval_result = chain_resolver.resolve(user_id, leave_type, 0.5)
    
    assert approval_result.chain is not None
    print(f"  ✓ 审批链: {approval_result.chain.chain_id}, {approval_result.total_steps}步")
    
    # 5. 响应生成
    response = result.get("response", "")
    assert "已识别" in response or "请问" in response
    print(f"  ✓ 响应生成: {response[:50]}...")
    
    print("  ✓ 完整流程测试通过")
    return True


def test_clarification_flow():
    """测试澄清流程"""
    print("\n【集成测试】澄清流程")
    
    agent = OAFlowAgent()
    
    # 测试缺失信息
    test_cases = [
        ("我要请3天事假", "missing_date_slot"),
        ("我想请病假", "missing_date_slot_type"),
        ("我想请明天年假", "missing_slot_type"),
    ]
    
    for test_input, desc in test_cases:
        result = agent.process(test_input, f"user_{desc}")
        intent = result.get("intent")
        
        assert intent is not None
        assert intent["clarification_needed"] == True
        print(f"  ✓ {desc}: 需要澄清, 缺失字段: {intent['required_fields']}")
    
    print("  ✓ 澄清流程测试通过")
    return True


def test_query_workflow():
    """测试查询流程"""
    print("\n【集成测试】查询流程")
    
    agent = OAFlowAgent()
    
    test_cases = [
        ("我今年用了几天年假", "leave_query"),
        ("请假记录", "leave_query"),
        ("用了多少假", "leave_query"),
    ]
    
    for test_input, expected_intent in test_cases:
        result = agent.process(test_input, f"user_query_{expected_intent}")
        intent = result.get("intent")
        
        assert intent is not None
        assert intent["intent"] == "leave_query"
        print(f"  ✓ {test_input}: {intent['intent']}")
    
    print("  ✓ 查询流程测试通过")
    return True


def test_capabilities_integration():
    """测试能力集成"""
    print("\n【集成测试】能力集成")
    
    agent = OAFlowAgent()
    
    # 测试启用的能力
    result = agent.process("我想请明天下午半天年假", "user_caps")
    enabled_caps = result.get("enabled_capabilities", [])
    
    assert len(enabled_caps) > 0
    assert "intent_recognition" in enabled_caps
    assert "entity_extraction" in enabled_caps
    assert "leave_type_classification" in enabled_caps
    assert "time_extraction" in enabled_caps
    print(f"  ✓ 启用能力: {enabled_caps}")
    
    print("  ✓ 能力集成测试通过")
    return True


def run_all_tests():
    """运行所有集成测试"""
    print("=" * 60)
    print("运行集成测试: OA Agent 完整流程")
    print("=" * 60)
    
    tests = [
        test_full_leave_request_flow,
        test_clarification_flow,
        test_query_workflow,
        test_capabilities_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"集成测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
