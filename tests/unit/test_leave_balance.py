#!/usr/bin/env python3
"""
单元测试 - 请假余额校验器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from leave_balance import LeaveBalanceChecker, LeaveBalance, BalanceCheckResult, LeaveBalanceStatus


def test_check_balance_insufficient():
    """测试余额不足情况"""
    checker = LeaveBalanceChecker()
    result = checker.check_balance("annual_leave", 20.0, "user_001")
    
    assert result.status == LeaveBalanceStatus.INSUFFICIENT
    assert "余额不足" in result.message
    assert result.required_document == False
    assert result.balance is not None
    assert result.balance.remaining_days == 11.5
    print("✓ test_check_balance_insufficient passed")


def test_check_balance_sufficient():
    """测试余额充足情况"""
    checker = LeaveBalanceChecker()
    result = checker.check_balance("annual_leave", 2.0, "user_001")
    
    assert result.status == LeaveBalanceStatus.SUCCESS
    assert "余额充足" in result.message
    assert result.balance is not None
    assert result.balance.remaining_days == 11.5
    print("✓ test_check_balance_sufficient passed")


def test_check_balance_sick_leave_requires_document():
    """测试病假需要附件"""
    checker = LeaveBalanceChecker()
    result = checker.check_balance("sick_leave", 5.0, "user_001")
    
    assert result.status == LeaveBalanceStatus.SUCCESS
    assert result.required_document == True
    print("✓ test_check_balance_sick_leave_requires_document passed")


def test_get_balance():
    """测试获取余额"""
    checker = LeaveBalanceChecker()
    balance = checker.get_balance("annual_leave", "user_001")
    
    assert balance is not None
    assert balance.leave_type == "annual_leave"
    assert balance.total_days == 15.0
    assert balance.used_days == 3.5
    assert balance.remaining_days == 11.5
    print("✓ test_get_balance passed")


def test_get_all_balances():
    """测试获取所有余额"""
    checker = LeaveBalanceChecker()
    balances = checker.get_all_balances("user_001")
    
    assert len(balances) > 0
    assert "annual_leave" in balances
    assert balances["annual_leave"].remaining_days == 11.5
    print("✓ test_get_all_balances passed")


def test_unsupported_leave_type():
    """测试不支持的请假类型"""
    checker = LeaveBalanceChecker()
    result = checker.check_balance("unknown_leave", 1.0, "user_001")
    
    assert result.status == LeaveBalanceStatus.NOT_SUPPORTED
    print("✓ test_unsupported_leave_type passed")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行单元测试: 请假余额校验器")
    print("=" * 60)
    
    tests = [
        test_check_balance_insufficient,
        test_check_balance_sufficient,
        test_check_balance_sick_leave_requires_document,
        test_get_balance,
        test_get_all_balances,
        test_unsupported_leave_type,
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
