#!/usr/bin/env python3
"""
单元测试 - 冲突校验器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from conflict_checker import ConflictChecker, ConflictCheckResult, ConflictType


def test_schedule_conflict():
    """测试日程冲突"""
    checker = ConflictChecker()
    result = checker.check_schedule_conflict("user_001", "tomorrow", "morning")
    
    assert result.has_conflict == True
    assert len(result.conflicts) > 0
    assert result.conflicts[0].conflict_type == ConflictType.SCHEDULE_CONFLICT
    print("✓ test_schedule_conflict passed")


def test_no_schedule_conflict():
    """测试无日程冲突"""
    checker = ConflictChecker()
    result = checker.check_schedule_conflict("user_001", "today", "morning")
    
    assert result.has_conflict == False
    assert result.message == "无日程冲突"
    print("✓ test_no_schedule_conflict passed")


def test_leave_overlap():
    """测试请假重叠"""
    checker = ConflictChecker()
    result = checker.check_leave_overlap("user_001", "today", "today")
    
    assert result.has_conflict == True
    assert len(result.conflicts) > 0
    assert result.conflicts[0].conflict_type == ConflictType.LEAVE_OVERLAP
    print("✓ test_leave_overlap passed")


def test_no_leave_overlap():
    """测试无请假重叠"""
    checker = ConflictChecker()
    result = checker.check_leave_overlap("user_001", "after_tomorrow", "after_tomorrow")
    
    # after_tomorrow 有 pending 的请假，应该冲突
    # 这里测试不重叠的情况
    result = checker.check_leave_overlap("user_001", "2026-10-20", "2026-10-22")
    assert result.has_conflict == False
    print("✓ test_no_leave_overlap passed")


def test_attendance_conflict():
    """测试考勤冲突"""
    checker = ConflictChecker()
    result = checker.check_attendance_conflict("user_001", "tomorrow", "morning")
    
    assert result.has_conflict == True
    print("✓ test_attendance_conflict passed")


def test_check_all():
    """测试综合检查"""
    checker = ConflictChecker()
    result = checker.check_all("user_001", "tomorrow", "morning", "annual_leave")
    
    # 至少有日程冲突
    assert result.has_conflict == True
    print("✓ test_check_all passed")


def test_no_conflict_for_new_user():
    """测试新用户无冲突"""
    checker = ConflictChecker()
    result = checker.check_schedule_conflict("new_user", "tomorrow", "morning")
    
    # 新用户没有日程，应该无冲突
    assert result.has_conflict == False
    print("✓ test_no_conflict_for_new_user passed")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行单元测试: 冲突校验器")
    print("=" * 60)
    
    tests = [
        test_schedule_conflict,
        test_no_schedule_conflict,
        test_leave_overlap,
        test_no_leave_overlap,
        test_attendance_conflict,
        test_check_all,
        test_no_conflict_for_new_user,
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
