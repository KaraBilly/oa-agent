#!/usr/bin/env python3
"""
测试运行器 - 运行所有测试
"""

import sys
import os
import subprocess


def run_test_file(filepath):
    """运行单个测试文件"""
    print(f"\n{'=' * 60}")
    print(f"运行测试文件: {filepath}")
    print('=' * 60)
    
    result = subprocess.run([sys.executable, filepath], 
                           cwd=os.path.dirname(filepath))
    return result.returncode == 0


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("OA Agent - 测试运行器")
    print("=" * 60)
    
    test_files = [
        "src/leave_balance.py",
        "src/conflict_checker.py", 
        "src/approval_chain.py",
    ]
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        filepath = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(filepath):
            try:
                if run_test_file(filepath):
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ 运行 {test_file} 出错: {e}")
                failed += 1
        else:
            print(f"⚠ 测试文件不存在: {test_file}")
    
    print("\n" + "=" * 60)
    print(f"测试结果汇总:")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
