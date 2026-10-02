#!/usr/bin/env python3
"""
单元测试 - 审批链解析器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from approval_chain import ApprovalChainResolver, ApprovalChainResult, ApprovalChainType


def test_resolve_annual_leave_short():
    """测试年假短审批链（3天以内）"""
    resolver = ApprovalChainResolver()
    result = resolver.resolve("user_001", "annual_leave", 2.0)
    
    assert result.chain is not None
    assert result.chain.chain_type == ApprovalChainType.LEAVE_APPROVAL
    assert result.current_step == 1
    assert result.total_steps == 1
    assert result.next_approver is not None
    assert result.next_approver.approver_name == "王经理"
    print("✓ test_resolve_annual_leave_short passed")


def test_resolve_annual_leave_long():
    """测试年假长审批链（3天以上）"""
    resolver = ApprovalChainResolver()
    result = resolver.resolve("user_001", "annual_leave", 5.0)
    
    assert result.chain is not None
    assert result.total_steps == 2
    assert result.next_approver is not None
    assert result.next_approver.approver_name == "王经理"
    print("✓ test_resolve_annual_leave_long passed")


def test_resolve_sick_leave():
    """测试病假审批链"""
    resolver = ApprovalChainResolver()
    result = resolver.resolve("user_001", "sick_leave", 3.0)
    
    assert result.chain is not None
    assert result.total_steps == 2
    approvers = [step.approver_name for step in result.chain.steps]
    assert "王经理" in approvers
    assert "HR小李" in approvers
    print("✓ test_resolve_sick_leave passed")


def test_resolve_personal_leave():
    """测试事假审批链"""
    resolver = ApprovalChainResolver()
    result = resolver.resolve("user_001", "personal_leave", 1.0)
    
    assert result.chain is not None
    assert result.total_steps == 1
    assert result.next_approver.approver_name == "王经理"
    print("✓ test_resolve_personal_leave passed")


def test_resolve_for_unknown_user():
    """测试未知用户"""
    resolver = ApprovalChainResolver()
    result = resolver.resolve("unknown_user", "annual_leave", 1.0)
    
    assert result.chain is None
    assert "不存在" in result.message
    print("✓ test_resolve_for_unknown_user passed")


def test_get_all_approval_chains():
    """测试获取所有审批链"""
    resolver = ApprovalChainResolver()
    chains = resolver.get_all_approval_chains()
    
    assert len(chains) > 0
    assert "annual_leave_short" in chains
    assert "annual_leave_long" in chains
    print("✓ test_get_all_approval_chains passed")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行单元测试: 审批链解析器")
    print("=" * 60)
    
    tests = [
        test_resolve_annual_leave_short,
        test_resolve_annual_leave_long,
        test_resolve_sick_leave,
        test_resolve_personal_leave,
        test_resolve_for_unknown_user,
        test_get_all_approval_chains,
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
            failed += 1
    
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
