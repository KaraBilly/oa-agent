from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date


class ConflictType(Enum):
    """冲突类型"""
    NO_CONFLICT = "no_conflict"
    SCHEDULE_CONFLICT = "schedule_conflict"
    LEAVE_OVERLAP = "leave_overlap"
    ATTENDANCE_CONFLICT = "attendance_conflict"


@dataclass
class ScheduleItem:
    """日程项"""
    schedule_id: str
    date: str
    time_slot: str
    title: str
    organizer: str
    participants: List[str]


@dataclass
class LeaveRecord:
    """请假记录"""
    record_id: str
    user_id: str
    leave_type: str
    start_date: str
    end_date: str
    status: str  # pending, approved, rejected


@dataclass
class ConflictInfo:
    """冲突信息"""
    conflict_type: ConflictType
    conflict_with: str
    description: str
    severity: str  # warning, error


@dataclass
class ConflictCheckResult:
    """冲突校验结果"""
    has_conflict: bool
    conflicts: List[ConflictInfo]
    message: str


class ConflictChecker:
    """冲突校验器"""
    
    def __init__(self):
        self.mock_schedules = [
            ScheduleItem(
                schedule_id="sched_001",
                date="tomorrow",
                time_slot="morning",
                title="项目例会",
                organizer="张三",
                participants=["user_001", "user_002"]
            ),
            ScheduleItem(
                schedule_id="sched_002",
                date="tomorrow",
                time_slot="afternoon",
                title="客户会议",
                organizer="李四",
                participants=["user_001"]
            ),
            ScheduleItem(
                schedule_id="sched_003",
                date="after_tomorrow",
                time_slot="full_day",
                title="培训",
                organizer="王五",
                participants=["user_001", "user_003"]
            )
        ]
        
        self.mock_leave_records = [
            LeaveRecord(
                record_id="leave_001",
                user_id="user_001",
                leave_type="annual_leave",
                start_date="today",
                end_date="today",
                status="approved"
            ),
            LeaveRecord(
                record_id="leave_002",
                user_id="user_001",
                leave_type="personal_leave",
                start_date="after_tomorrow",
                end_date="after_tomorrow",
                status="pending"
            )
        ]
    
    def check_schedule_conflict(self, user_id: str, date: str, 
                               time_slot: Optional[str] = None) -> ConflictCheckResult:
        """
        检查日程冲突
        
        Args:
            user_id: 用户ID
            date: 日期
            time_slot: 时间槽
            
        Returns:
            ConflictCheckResult: 冲突校验结果
        """
        conflicts = []
        
        for schedule in self.mock_schedules:
            if schedule.date != date:
                continue
            
            if user_id not in schedule.participants:
                continue
            
            if time_slot:
                if schedule.time_slot == time_slot:
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.SCHEDULE_CONFLICT,
                        conflict_with=f"日程: {schedule.title}",
                        description=f"{date} {time_slot} 已有日程: {schedule.title}",
                        severity="warning"
                    ))
                elif schedule.time_slot == "full_day":
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.SCHEDULE_CONFLICT,
                        conflict_with=f"日程: {schedule.title}",
                        description=f"{date} 全天已有日程: {schedule.title}",
                        severity="warning"
                    ))
            else:
                conflicts.append(ConflictInfo(
                    conflict_type=ConflictType.SCHEDULE_CONFLICT,
                    conflict_with=f"日程: {schedule.title}",
                    description=f"{date} {schedule.time_slot} 有日程: {schedule.title}",
                    severity="warning"
                ))
        
        if conflicts:
            return ConflictCheckResult(
                has_conflict=True,
                conflicts=conflicts,
                message=f"发现{len(conflicts)}个日程冲突，请确认是否继续请假"
            )
        
        return ConflictCheckResult(
            has_conflict=False,
            conflicts=[],
            message="无日程冲突"
        )
    
    def check_leave_overlap(self, user_id: str, start_date: str, 
                           end_date: Optional[str] = None) -> ConflictCheckResult:
        """
        检查请假重叠
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            ConflictCheckResult: 冲突校验结果
        """
        conflicts = []
        end_date = end_date or start_date
        
        for record in self.mock_leave_records:
            if record.user_id != user_id:
                continue
            
            if record.status == "approved":
                if self._dates_overlap(start_date, end_date, 
                                      record.start_date, record.end_date):
                    conflicts.append(ConflictInfo(
                        conflict_type=ConflictType.LEAVE_OVERLAP,
                        conflict_with=f"请假记录: {record.leave_type} ({record.start_date} - {record.end_date})",
                        description=f"请假时间与已批准的请假重叠",
                        severity="error"
                    ))
        
        if conflicts:
            return ConflictCheckResult(
                has_conflict=True,
                conflicts=conflicts,
                message="存在请假时间重叠，请检查"
            )
        
        return ConflictCheckResult(
            has_conflict=False,
            conflicts=[],
            message="无请假时间重叠"
        )
    
    def _dates_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """判断两个日期范围是否重叠"""
        try:
            if start1 == "today":
                d1 = date.today()
            elif start1 == "tomorrow":
                d1 = date.today().replace(day=date.today().day + 1)
            else:
                d1 = datetime.strptime(start1, "%Y-%m-%d").date()
            
            if end1 == "today":
                d2 = date.today()
            elif end1 == "tomorrow":
                d2 = date.today().replace(day=date.today().day + 1)
            else:
                d2 = datetime.strptime(end1, "%Y-%m-%d").date()
            
            if start2 == "today":
                d3 = date.today()
            elif start2 == "tomorrow":
                d3 = date.today().replace(day=date.today().day + 1)
            else:
                d3 = datetime.strptime(start2, "%Y-%m-%d").date()
            
            if end2 == "today":
                d4 = date.today()
            elif end2 == "tomorrow":
                d4 = date.today().replace(day=date.today().day + 1)
            else:
                d4 = datetime.strptime(end2, "%Y-%m-%d").date()
            
            return not (d2 < d3 or d4 < d1)
        except:
            return start1 == start2
    
    def check_attendance_conflict(self, user_id: str, date: str,
                                  time_slot: Optional[str] = None) -> ConflictCheckResult:
        """
        检查考勤冲突
        
        Args:
            user_id: 用户ID
            date: 日期
            time_slot: 时间槽
            
        Returns:
            ConflictCheckResult: 冲突校验结果
        """
        conflicts = []
        
        # Mock考勤数据：如果请假上午，不能只打下午卡
        if time_slot in ["morning", "morning_half"]:
            conflicts.append(ConflictInfo(
                conflict_type=ConflictType.ATTENDANCE_CONFLICT,
                conflict_with="考勤系统",
                description="请假上午需确保上午打卡记录正确",
                severity="warning"
            ))
        
        if conflicts:
            return ConflictCheckResult(
                has_conflict=True,
                conflicts=conflicts,
                message="存在考勤相关提示，请确认"
            )
        
        return ConflictCheckResult(
            has_conflict=False,
            conflicts=[],
            message="无考勤冲突"
        )
    
    def check_all(self, user_id: str, date: str, time_slot: Optional[str] = None,
                  leave_type: Optional[str] = None) -> ConflictCheckResult:
        """
        综合检查所有冲突
        
        Args:
            user_id: 用户ID
            date: 日期
            time_slot: 时间槽
            leave_type: 请假类型
            
        Returns:
            ConflictCheckResult: 综合冲突校验结果
        """
        all_conflicts = []
        
        schedule_result = self.check_schedule_conflict(user_id, date, time_slot)
        all_conflicts.extend(schedule_result.conflicts)
        
        leave_result = self.check_leave_overlap(user_id, date)
        all_conflicts.extend(leave_result.conflicts)
        
        attendance_result = self.check_attendance_conflict(user_id, date, time_slot)
        all_conflicts.extend(attendance_result.conflicts)
        
        if all_conflicts:
            return ConflictCheckResult(
                has_conflict=True,
                conflicts=all_conflicts,
                message=f"发现{len(all_conflicts)}个潜在问题，请检查"
            )
        
        return ConflictCheckResult(
            has_conflict=False,
            conflicts=[],
            message="所有检查通过"
        )


if __name__ == "__main__":
    checker = ConflictChecker()
    
    print("=" * 60)
    print("冲突校验器测试")
    print("=" * 60)
    
    test_cases = [
        ("user_001", "tomorrow", "morning", None),
        ("user_001", "after_tomorrow", "full_day", "annual_leave"),
        ("user_001", "today", "morning", None),
    ]
    
    for user_id, date, time_slot, leave_type in test_cases:
        print(f"\n【测试】{user_id} {date} {time_slot} {leave_type or '无'}")
        result = checker.check_all(user_id, date, time_slot, leave_type)
        print(f"  有冲突: {result.has_conflict}")
        print(f"  消息: {result.message}")
        if result.conflicts:
            for conflict in result.conflicts:
                print(f"    - [{conflict.severity}] {conflict.description}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
