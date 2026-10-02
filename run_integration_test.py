#!/usr/bin/env python3
"""
集成测试运行器
"""

import sys
import os

# 确保模块路径正确
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# 重新导入
from oa_graph_agent import IntentionRecognizer, ResponseGenerator, IntentType
from leave_balance import LeaveBalanceChecker, LeaveBalanceStatus
from conflict_checker import ConflictChecker
from approval_chain import ApprovalChainResolver


class IntegratedOAFlowAgent:
    """集成的OA Agent - 包含所有新功能"""
    
    def __init__(self):
        self.recognizer = IntentionRecognizer()
        self.response_generator = ResponseGenerator()
        self.balance_checker = LeaveBalanceChecker()
        self.conflict_checker = ConflictChecker()
        self.chain_resolver = ApprovalChainResolver()
    
    def process_with_all_features(self, input_text: str, user_id: str = "unknown") -> dict:
        """处理用户输入 - 包含所有新功能"""
        intent_result = self.recognizer.extract_intent(input_text)
        
        result = {
            "input": input_text,
            "user_id": user_id,
            "intent": intent_result.model_dump() if hasattr(intent_result, 'model_dump') else intent_result.dict() if hasattr(intent_result, 'dict') else intent_result,
            "response": "",
            "balance_check": None,
            "conflict_check": None,
            "approval_chain": None,
            "all_checks_passed": True,
            "checks": []
        }
        
        if intent_result.intent == IntentType.LEAVE_REQUEST and intent_result.leave_type:
            leave_type = intent_result.leave_type.value
            duration_hours = intent_result.duration_hours or 8
            requested_days = duration_hours / 8 if duration_hours else 0.5
            
            balance_result = self.balance_checker.check_balance(leave_type, requested_days, user_id)
            
            result["balance_check"] = {
                "leave_type": leave_type,
                "requested_days": requested_days,
                "status": balance_result.status.value,
                "message": balance_result.message,
                "required_document": balance_result.required_document,
                "balance": {"remaining_days": balance_result.balance.remaining_days if balance_result.balance else None}
            }
            
            if balance_result.status == LeaveBalanceStatus.INSUFFICIENT:
                result["all_checks_passed"] = False
                result["checks"].append("余额校验未通过")
        
        if intent_result.intent == IntentType.LEAVE_REQUEST and intent_result.start_date:
            time_slot = intent_result.time_slot.value if intent_result.time_slot else None
            start_date = intent_result.start_date
            
            conflict_result = self.conflict_checker.check_all(user_id, start_date, time_slot, intent_result.leave_type.value if intent_result.leave_type else None)
            
            result["conflict_check"] = {
                "date": start_date,
                "time_slot": time_slot,
                "has_conflict": conflict_result.has_conflict,
                "message": conflict_result.message,
                "conflicts": [{"type": c.conflict_type.value, "description": c.description, "severity": c.severity} for c in conflict_result.conflicts]
            }
            
            if conflict_result.has_conflict:
                result["all_checks_passed"] = False
                result["checks"].append(f"发现{len(conflict_result.conflicts)}个冲突")
        
        if intent_result.intent == IntentType.LEAVE_REQUEST and intent_result.leave_type:
            leave_type = intent_result.leave_type.value
            duration_hours = intent_result.duration_hours or 8
            requested_days = duration_hours / 8 if duration_hours else 0.5
            
            chain_result = self.chain_resolver.resolve(user_id, leave_type, requested_days)
            
            result["approval_chain"] = {
                "leave_type": leave_type,
                "requested_days": requested_days,
                "chain_id": chain_result.chain.chain_id if chain_result.chain else None,
                "total_steps": chain_result.total_steps,
                "current_step": chain_result.current_step,
                "next_approver": {
                    "name": chain_result.next_approver.approver_name if chain_result.next_approver else None,
                    "role": chain_result.next_approver.approver_role if chain_result.next_approver else None,
                    "timeout_hours": chain_result.next_approver.timeout_hours if chain_result.next_approver else None
                } if chain_result.next_approver else None,
                "message": chain_result.message
            }
        
        if intent_result.clarification_needed:
            result["response"] = self.response_generator.generate_clarification_response(intent_result)
        elif intent_result.intent == IntentType.LEAVE_REQUEST:
            result["response"] = self.response_generator.generate_leave_request_response(intent_result)
        elif intent_result.intent == IntentType.LEAVE_QUERY:
            result["response"] = self.response_generator.generate_leave_query_response()
        elif intent_result.intent == IntentType.LEAVE_WITHDRAW:
            result["response"] = self.response_generator.generate_leave_withdraw_response()
        else:
            result["response"] = self.response_generator.generate_default_response()
        
        if not result["all_checks_passed"]:
            result["response"] += f"【校验提示: {'; '.join(result['checks'])}】"
        
        return result


if __name__ == "__main__":
    print("=" * 70)
    print("集成OA Agent测试")
    print("=" * 70)
    
    agent = IntegratedOAFlowAgent()
    
    test_cases = [
        "我想请明天下午半天年假",
        "我要请3天事假",
        "我想请后天上午年假",
        "请帮我查一下请假记录",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"测试用例 {i}: {test_case}")
        print('=' * 70)
        
        result = agent.process_with_all_features(test_case, f"user_{i}")
        
        print(f"\n意图识别:")
        print(f"  意图: {result['intent']['intent']}")
        print(f"  置信度: {result['intent']['confidence']:.2f}")
        print(f"  请假类型: {result['intent']['leave_type']}")
        print(f"  时间: {result['intent']['start_date']} {result['intent']['time_slot']}")
        
        if result.get('balance_check'):
            bc = result['balance_check']
            print(f"\n余额校验:")
            print(f"  状态: {bc['status']}")
            print(f"  消息: {bc['message']}")
            print(f"  剩余天数: {bc['balance']['remaining_days']}")
        
        if result.get('conflict_check'):
            cc = result['conflict_check']
            print(f"\n冲突校验:")
            print(f"  有冲突: {cc['has_conflict']}")
            print(f"  消息: {cc['message']}")
            if cc['conflicts']:
                for conflict in cc['conflicts']:
                    print(f"    - [{conflict['severity']}] {conflict['description']}")
        
        if result.get('approval_chain'):
            ac = result['approval_chain']
            print(f"\n审批链:")
            print(f"  审批链ID: {ac['chain_id']}")
            print(f"  步骤: {ac['current_step']}/{ac['total_steps']}")
            if ac['next_approver']:
                print(f"  下一步审批人: {ac['next_approver']['name']} ({ac['next_approver']['role']})")
        
        print(f"\n响应: {result['response']}")
        print(f"\n所有检查通过: {result['all_checks_passed']}")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)
