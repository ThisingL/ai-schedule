import json
from datetime import date, time, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task


async def get_day_tasks(db: AsyncSession, target_date: date) -> list[Task]:
    """获取指定天的所有任务"""
    query = (
        select(Task)
        .where(Task.scheduled_date == target_date)
        .options(selectinload(Task.children))
        .order_by(Task.start_time, Task.sort_order)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_week_tasks(db: AsyncSession, week_start: date) -> list[Task]:
    """获取指定周的所有任务（周一到周日）"""
    week_end = week_start + timedelta(days=6)
    query = (
        select(Task)
        .where(and_(Task.scheduled_date >= week_start, Task.scheduled_date <= week_end))
        .options(selectinload(Task.children))
        .order_by(Task.scheduled_date, Task.start_time)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_free_slots(
    db: AsyncSession,
    target_date: date,
    work_hours: dict = None,
    exclude_task_id: int = None,
) -> list[dict]:
    """获取指定日期的空闲时间段"""
    if work_hours is None:
        work_hours = {"start": "09:00", "end": "18:00"}

    wh_start = time(*map(int, work_hours["start"].split(":")))
    wh_end = time(*map(int, work_hours["end"].split(":")))

    tasks = await get_day_tasks(db, target_date)
    # 排除正在被重新安排的任务本身
    if exclude_task_id:
        tasks = [t for t in tasks if t.id != exclude_task_id]
    # 只看有时间段的进行中/待办任务
    busy = []
    for t in tasks:
        if t.start_time and t.end_time and t.status != "done":
            busy.append((t.start_time, t.end_time))
    # 合并子任务
    for t in tasks:
        if t.children:
            for c in t.children:
                if c.start_time and c.end_time and c.status != "done" and c.id != exclude_task_id:
                    busy.append((c.start_time, c.end_time))

    busy.sort(key=lambda x: x[0])

    # 计算空闲
    free = []
    current = wh_start
    for start, end in busy:
        if start > current:
            free.append({"start": current.strftime("%H:%M"), "end": start.strftime("%H:%M")})
        if end > current:
            current = end
    if current < wh_end:
        free.append({"start": current.strftime("%H:%M"), "end": wh_end.strftime("%H:%M")})

    return free
