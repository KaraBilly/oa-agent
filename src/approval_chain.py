from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


class ApprovalChainType(Enum):
    """审批链类型"""
    LEAVE_APPROVAL = "leave_approval"
    OVERTIME_APPROVAL = "overtime_approval"
    TRAVEL_APPROVAL = "travel_approval"


@dataclass
class ApprovalStep:
    """审批步骤"""
    step_number: int
    approver_id: str
    approver_name: str
    approver_role: str
    approval_type: str  # electronic, physical, verbal
    timeout_hours: int = 48


@dataclass
class ApprovalChain:
    """审批链"""
    chain_id: str
    chain_type: ApprovalChainType
    steps: List[ApprovalStep]
    description: str


@dataclass
class ApprovalChainResult:
    """审批链解析结果"""
    chain: Optional[ApprovalChain]
    current_step: int
    total_steps: int
    next_approver: Optional[ApprovalStep]
    message: str


class ApprovalChainResolver:
    """审批链解析器"""
    
    def __init__(self):
        self.mock_employees = {
            "user_001": {
                "name": "张三",
                "department": "研发部",
                "manager": "user_m1",
                "role": "工程师"
            },
            "user_002": {
                "name": "李四",
                "department": "产品部",
                "manager": "user_m2",
                "role": "产品经理"
            },
            "user_m1": {
                "name": "王经理",
                "department": "研发部",
                "manager": "user_dm1",
                "role": "研发经理"
            },
            "user_dm1": {
                "name": "赵总监",
                "department": "技术中心",
                "manager": None,
                "role": "技术总监"
            },
            "user_m2": {
                "name": "孙经理",
                "department": "产品部",
                "manager": "user_dm2",
                "role": "产品总监"
            }
        }
        
        self.mock_approval_chains = {
            "annual_leave_short": ApprovalChain(
                chain_id="chain_001",
                chain_type=ApprovalChainType.LEAVE_APPROVAL,
                steps=[
                    ApprovalStep(step_number=1, approver_id="user_m1", 
                                approver_name="王经理", approver_role="研发经理",
                                approval_type="electronic", timeout_hours=24),
                ],
                description="年假3天以内审批链"
            ),
            "annual_leave_long": ApprovalChain(
                chain_id="chain_002",
                chain_type=ApprovalChainType.LEAVE_APPROVAL,
                steps=[
                    ApprovalStep(step_number=1, approver_id="user_m1",
                                approver_name="王经理", approver_role="研发经理",
                                approval_type="electronic", timeout_hours=24),
                    ApprovalStep(step_number=2, approver_id="user_dm1",
                                approver_name="赵总监", approver_role="技术总监",
                                approval_type="electronic", timeout_hours=48),
                ],
                description="年假3天以上审批链"
            ),
            "sick_leave": ApprovalChain(
                chain_id="chain_003",
                chain_type=ApprovalChainType.LEAVE_APPROVAL,
                steps=[
                    ApprovalStep(step_number=1, approver_id="user_m1",
                                approver_name="王经理", approver_role="研发经理",
                                approval_type="electronic", timeout_hours=24),
                    ApprovalStep(step_number=2, approver_id="hr_001",
                                approver_name="HR小李", approver_role="HR",
                                approval_type="electronic", timeout_hours=48),
                ],
                description="病假审批链"
            ),
            "personal_leave": ApprovalChain(
                chain_id="chain_004",
                chain_type=ApprovalChainType.LEAVE_APPROVAL,
                steps=[
                    ApprovalStep(step_number=1, approver_id="user_m1",
                                approver_name="王经理", approver_role="研发经理",
                                approval_type="electronic", timeout_hours=24),
                ],
                description="事假审批链"
            )
        }
    
    def resolve(self, user_id: str, leave_type: str, 
               requested_days: float) -> ApprovalChainResult:
        """
        解析审批链
        
        Args:
            user_id: 用户ID
            leave_type: 请假类型
            requested_days: 申请天数
            
        Returns:
            ApprovalChainResult: 审批链解析结果
        """
        employee = self.mock_employees.get(user_id)
        if not employee:
            return ApprovalChainResult(
                chain=None,
                current_step=0,
                total_steps=0,
                next_approver=None,
                message=f"用户 {user_id} 不存在"
            )
        
        chain_key = self._determine_chain_key(leave_type, requested_days)
        chain = self.mock_approval_chains.get(chain_key)
        
        if not chain:
            return ApprovalChainResult(
                chain=None,
                current_step=0,
                total_steps=0,
                next_approver=None,
                message=f"未找到适用于 {leave_type} 的审批链"
            )
        
        current_step = 1
        next_approver = self._get_next_approver(chain, current_step)
        
        return ApprovalChainResult(
            chain=chain,
            current_step=current_step,
            total_steps=len(chain.steps),
            next_approver=next_approver,
            message=f"审批链已确定，共{len(chain.steps)}步，当前第{current_step}步"
        )
    
    def _determine_chain_key(self, leave_type: str, days: float) -> str:
        """根据请假类型和天数确定审批链键"""
        if leave_type == "annual_leave":
            if days <= 3:
                return "annual_leave_short"
            else:
                return "annual_leave_long"
        elif leave_type == "sick_leave":
            return "sick_leave"
        elif leave_type == "personal_leave":
            return "personal_leave"
        else:
            return f"{leave_type}_default"
    
    def _get_next_approver(self, chain: ApprovalChain, 
                          current_step: int) -> Optional[ApprovalStep]:
        """获取下一个审批人"""
        for step in chain.steps:
            if step.step_number == current_step:
                return step
        return None
    
    def get_next_approver(self, chain: ApprovalChain, current_step: int) -> Optional[ApprovalStep]:
        """获取指定步骤的审批人"""
        for step in chain.steps:
            if step.step_number == current_step:
                return step
        return None
    
    def get_all_approval_chains(self) -> Dict[str, ApprovalChain]:
        """获取所有审批链"""
        return self.mock_approval_chains


if __name__ == "__main__":
    resolver = ApprovalChainResolver()
    
    print("=" * 60)
    print("审批链解析器测试")
    print("=" * 60)
    
    test_cases = [
        ("user_001", "annual_leave", 2.0),
        ("user_001", "annual_leave", 5.0),
        ("user_001", "sick_leave", 3.0),
        ("user_002", "personal_leave", 1.0),
    ]
    
    for user_id, leave_type, days in test_cases:
        result = resolver.resolve(user_id, leave_type, days)
        print(f"\n【测试】{user_id} 申请 {leave_type} {days}天")
        print(f"  消息: {result.message}")
        print(f"  审批链: {result.chain.chain_id if result.chain else 'None'}")
        print(f"  步骤: {result.current_step}/{result.total_steps}")
        if result.next_approver:
            print(f"  下一步审批人: {result.next_approver.approver_name} ({result.next_approver.approver_role})")
        if result.chain:
            print(f"  审批链步骤:")
            for step in result.chain.steps:
                print(f"    {step.step_number}. {step.approver_name} - {step.approver_role} ({step.timeout_hours}h)")
    
    print("\n" + "=" * 60)
    print("所有审批链:")
    all_chains = resolver.get_all_approval_chains()
    for chain_id, chain in all_chains.items():
        print(f"  {chain_id}: {chain.description}")
    print("=" * 60)
