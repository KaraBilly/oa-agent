from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


class LeaveBalanceStatus(Enum):
    """余额状态"""
    SUCCESS = "success"
    INSUFFICIENT = "insufficient"
    ERROR = "error"
    NOT_SUPPORTED = "not_supported"


@dataclass
class LeaveBalance:
    """请假余额"""
    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float
    last_updated: datetime


@dataclass
class BalanceCheckResult:
    """余额校验结果"""
    status: LeaveBalanceStatus
    balance: Optional[LeaveBalance] = None
    message: str = ""
    required_document: bool = False


class LeaveBalanceChecker:
    """请假余额校验器"""
    
    def __init__(self):
        self.mock_balances = {
            "annual_leave": {
                "total_days": 15.0,
                "used_days": 3.5,
                "remaining_days": 11.5,
                "last_updated": datetime.now()
            },
            "personal_leave": {
                "total_days": 0.0,
                "used_days": 0.0,
                "remaining_days": 0.0,
                "last_updated": datetime.now()
            },
            "sick_leave": {
                "total_days": 30.0,
                "used_days": 5.0,
                "remaining_days": 25.0,
                "last_updated": datetime.now()
            },
            "remuneration_leave": {
                "total_days": 10.0,
                "used_days": 2.0,
                "remaining_days": 8.0,
                "last_updated": datetime.now()
            }
        }
        self.leave_type_requirements = {
            "annual_leave": {"requires_document": False, "min_unit": 0.5},
            "personal_leave": {"requires_document": False, "min_unit": 0.5},
            "sick_leave": {"requires_document": True, "min_unit": 0.5},
            "remuneration_leave": {"requires_document": False, "min_unit": 0.5},
            "marriage_leave": {"requires_document": False, "min_unit": 1.0},
            "maternity_leave": {"requires_document": True, "min_unit": 1.0},
            "bereavement_leave": {"requires_document": False, "min_unit": 1.0}
        }
    
    def check_balance(self, leave_type: str, requested_days: float, 
                     user_id: str = "unknown") -> BalanceCheckResult:
        """
        检查请假余额
        
        Args:
            leave_type: 请假类型
            requested_days: 申请天数
            user_id: 用户ID
            
        Returns:
            BalanceCheckResult: 余额校验结果
        """
        if leave_type not in self.mock_balances:
            return BalanceCheckResult(
                status=LeaveBalanceStatus.NOT_SUPPORTED,
                message=f"不支持的请假类型: {leave_type}",
                required_document=False
            )
        
        balance_data = self.mock_balances[leave_type]
        remaining = balance_data["remaining_days"]
        
        if requested_days > remaining:
            return BalanceCheckResult(
                status=LeaveBalanceStatus.INSUFFICIENT,
                balance=LeaveBalance(
                    leave_type=leave_type,
                    total_days=balance_data["total_days"],
                    used_days=balance_data["used_days"],
                    remaining_days=remaining,
                    last_updated=balance_data["last_updated"]
                ),
                message=f"余额不足！剩余{remaining}天，申请{requested_days}天",
                required_document=self.leave_type_requirements.get(leave_type, {}).get("requires_document", False)
            )
        
        return BalanceCheckResult(
            status=LeaveBalanceStatus.SUCCESS,
            balance=LeaveBalance(
                leave_type=leave_type,
                total_days=balance_data["total_days"],
                used_days=balance_data["used_days"],
                remaining_days=remaining,
                last_updated=balance_data["last_updated"]
            ),
            message=f"余额充足：剩余{remaining}天",
            required_document=self.leave_type_requirements.get(leave_type, {}).get("requires_document", False)
        )
    
    def get_balance(self, leave_type: str, user_id: str = "unknown") -> Optional[LeaveBalance]:
        """
        获取请假余额
        
        Args:
            leave_type: 请假类型
            user_id: 用户ID
            
        Returns:
            LeaveBalance: 余额信息
        """
        if leave_type not in self.mock_balances:
            return None
        
        balance_data = self.mock_balances[leave_type]
        return LeaveBalance(
            leave_type=leave_type,
            total_days=balance_data["total_days"],
            used_days=balance_data["used_days"],
            remaining_days=balance_data["remaining_days"],
            last_updated=balance_data["last_updated"]
        )
    
    def get_all_balances(self, user_id: str = "unknown") -> Dict[str, LeaveBalance]:
        """获取所有请假余额"""
        balances = {}
        for leave_type, balance_data in self.mock_balances.items():
            balances[leave_type] = LeaveBalance(
                leave_type=leave_type,
                total_days=balance_data["total_days"],
                used_days=balance_data["used_days"],
                remaining_days=balance_data["remaining_days"],
                last_updated=balance_data["last_updated"]
            )
        return balances


if __name__ == "__main__":
    checker = LeaveBalanceChecker()
    
    print("=" * 60)
    print("请假余额校验器测试")
    print("=" * 60)
    
    test_cases = [
        ("annual_leave", 2.0, "user_001"),
        ("annual_leave", 20.0, "user_001"),
        ("sick_leave", 5.0, "user_001"),
        ("personal_leave", 1.0, "user_001"),
    ]
    
    for leave_type, days, user_id in test_cases:
        result = checker.check_balance(leave_type, days, user_id)
        print(f"\n【测试】{leave_type} 申请{days}天")
        print(f"  状态: {result.status.value}")
        print(f"  消息: {result.message}")
        print(f"  需要附件: {result.required_document}")
        if result.balance:
            print(f"  剩余天数: {result.balance.remaining_days}")
    
    print("\n" + "=" * 60)
    print("所有余额:")
    all_balances = checker.get_all_balances("user_001")
    for leave_type, balance in all_balances.items():
        print(f"  {balance.leave_type}: 剩余{balance.remaining_days}天")
    print("=" * 60)
