#!/usr/bin/env python3
"""
综合测试脚本 - 验证所有新功能
"""

import sys
import os

# 设置路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from oa_graph_agent import IntentionRecognizer, ResponseGenerator, IntentType
from leave_balance import LeaveBalanceChecker, LeaveBalanceStatus
from conflict_checker import ConflictChecker, ConflictType
from approval_chain import ApprovalChainResolver, ApprovalChainType


def test_all_features():
    """测试所有新功能"""
    print("=" * 70)
    print("综合功能测试 - OA Agent 新增模块")
    print("=" * 70)
    
    # 初始化所有模块
    recognizer = IntentionRecognizer()
    response_gen = ResponseGenerator()
    balance_checker = LeaveBalanceChecker()
    conflict_checker = ConflictChecker()
    chain_resolver = ApprovalChainResolver()
    
    test_cases = [
        {
            "input": "我想请明天下午半天年假",
            "user_id": "user_001",
            "expected_intent": IntentType.LEAVE_REQUEST,
            "expected_leave_type": "annual_leave",
            "desc": "完整信息的请假申请"
        },
        {
            "input": "我要请3天事假",
            "user_id": "user_002",
            "expected_intent": IntentType.LEAVE_REQUEST,
            "expected_leave_type": "personal_leave",
            "desc": "缺失日期和时段的请假申请"
        },
        {
            "input": "我今年用了几天年假",
            "user_id": "user_003",
            "expected_intent": IntentType.LEAVE_QUERY,
            "desc": "查询类型的请求"
        },
        {
            "input": "请帮我查一下请假记录",
            "user_id": "user_004",
            "expected_intent": IntentType.LEAVE_QUERY,
            "desc": "另一个查询请求"
        }
    ]
    
    all_passed = True
    total_tests = 0
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"测试用例 {i}: {test_case['desc']}")
        print('=' * 70)
        print(f"输入: {test_case['input']}")
        print(f"用户ID: {test_case['user_id']}")
        
        # 1. 意图识别测试
        intent = recognizer.extract_intent(test_case['input'])
        total_tests += 1
        
        if intent.intent == test_case['expected_intent']:
            print(f"✓ 意图识别: {intent.intent.value}")
            passed_tests += 1
        else:
            print(f"✗ 意图识别失败: 期望 {test_case['expected_intent'].value}, 实际 {intent.intent.value}")
            all_passed = False
        
        # 2. 余额校验测试
        if intent.intent == IntentType.LEAVE_REQUEST and intent.leave_type:
            leave_type = intent.leave_type.value
            duration_hours = intent.duration_hours or 8
            requested_days = duration_hours / 8 if duration_hours else 0.5
            
            balance_result = balance_checker.check_balance(leave_type, requested_days, test_case['user_id'])
            total_tests += 1
            
            if balance_result.status == LeaveBalanceStatus.SUCCESS or balance_result.status == LeaveBalanceStatus.INSUFFICIENT:
                print(f"✓ 余额校验: {balance_result.message}")
                passed_tests += 1
            else:
                print(f"✗ 余额校验失败: {balance_result.status.value}")
                all_passed = False
            
            # 3. 冲突校验测试
            if intent.start_date:
                time_slot = intent.time_slot.value if intent.time_slot else None
                conflict_result = conflict_checker.check_all(
                    test_case['user_id'], intent.start_date, time_slot, leave_type
                )
                total_tests += 1
                print(f"✓ 冲突校验: {conflict_result.message} (有冲突: {conflict_result.has_conflict})")
                passed_tests += 1
            
            # 4. 审批链解析测试
            chain_result = chain_resolver.resolve(test_case['user_id'], leave_type, requested_days)
            total_tests += 1
            
            if chain_result.chain:
                print(f"✓ 审批链解析: {chain_result.chain.chain_id} ({chain_result.total_steps}步)")
                passed_tests += 1
            else:
                print(f"✗ 审批链解析失败: 未找到审批链")
                all_passed = False
        
        # 5. 响应生成测试
        if intent.clarification_needed:
            response = response_gen.generate_clarification_response(intent)
        elif intent.intent == IntentType.LEAVE_REQUEST:
            response = response_gen.generate_leave_request_response(intent)
        elif intent.intent == IntentType.LEAVE_QUERY:
            response = response_gen.generate_leave_query_response()
        elif intent.intent == IntentType.LEAVE_WITHDRAW:
            response = response_gen.generate_leave_withdraw_response()
        else:
            response = response_gen.generate_default_response()
        
        total_tests += 1
        print(f"✓ 响应生成: {response[:50]}...")
        passed_tests += 1
        
        print(f"  实体抽取: {len(intent.entities_extracted)}个实体")
        print(f"  置信度: {intent.confidence:.2f}")
    
    print(f"\n{'=' * 70}")
    print("测试结果汇总")
    print('=' * 70)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests / total_tests * 100:.1f}%")
    
    if all_passed:
        print("\n✅ 所有测试通过!")
    else:
        print("\n⚠️ 部分测试失败，请检查上述详情")
    
    print("=" * 70)
    
    return all_passed


def test_edge_cases():
    """测试边界情况"""
    print(f"\n{'=' * 70}")
    print("边界情况测试")
    print('=' * 70)
    
    balance_checker = LeaveBalanceChecker()
    conflict_checker = ConflictChecker()
    
    edge_cases = [
        ("annual_leave", 20.0, "余额不足测试"),
        ("sick_leave", 1.0, "病假需要附件测试"),
        ("unknown_type", 1.0, "未知请假类型测试"),
        ("user_unknown", "tomorrow", "无日程用户测试"),
    ]
    
    total = 0
    passed = 0
    
    for test in edge_cases:
        total += 1
        if len(test) == 3:
            leave_type, days, desc = test
            result = balance_checker.check_balance(leave_type, days, "user_edge")
            print(f"\n{desc}: {result.status.value} - {result.message}")
            if result.status in [LeaveBalanceStatus.SUCCESS, LeaveBalanceStatus.INSUFFICIENT, LeaveBalanceStatus.NOT_SUPPORTED]:
                passed += 1
                print("✓ 通过")
            else:
                print("✗ 失败")
        else:
            user_id, date, desc = test
            result = conflict_checker.check_schedule_conflict(user_id, date, "morning")
            print(f"\n{desc}: {result.has_conflict}")
            print("✓ 通过")
            passed += 1
    
    print(f"\n边界测试: {passed}/{total} 通过")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success1 = test_all_features()
    success2 = test_edge_cases()
    
    if success1 and success2:
        print("\n🎉 所有测试完成并通过!")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
