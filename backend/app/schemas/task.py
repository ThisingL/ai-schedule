from datetime import date, time, datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    parent_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str = "P2"
    status: str = "todo"
    category: Optional[str] = None
    scheduled_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    estimated_minutes: Optional[int] = None
    deadline: Optional[datetime] = None
    is_ai_generated: bool = False
    ai_priority_reason: Optional[str] = None
    sort_order: int = 0


class TaskUpdate(BaseModel):
    parent_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    scheduled_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    estimated_minutes: Optional[int] = None
    deadline: Optional[datetime] = None
    is_ai_generated: Optional[bool] = None
    ai_priority_reason: Optional[str] = None
    sort_order: Optional[int] = None


class TaskStatusUpdate(BaseModel):
    status: str


class _TaskBase(BaseModel):
    id: int
    parent_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    category: Optional[str] = None
    scheduled_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    estimated_minutes: Optional[int] = None
    deadline: Optional[datetime] = None
    is_ai_generated: bool
    ai_priority_reason: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubTaskResponse(_TaskBase):
    """子任务响应（不再嵌套 children，避免循环引用）"""
    pass


class TaskResponse(_TaskBase):
    """顶层任务响应（包含一层子任务列表）"""
    children: list[SubTaskResponse] = []
