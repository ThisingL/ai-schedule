from datetime import date
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


async def get_tasks(
    db: AsyncSession,
    scheduled_date: Optional[date] = None,
    status: Optional[str] = None,
    include_overdue: bool = False,
) -> list[Task]:
    """查询任务列表，只返回顶层任务（子任务嵌套在 children 中）"""
    query = select(Task).where(Task.parent_id.is_(None)).options(selectinload(Task.children))

    conditions = []
    if scheduled_date and include_overdue:
        # 看板模式：当天 + 过期未完成 + 未来
        conditions.append(
            (Task.scheduled_date <= scheduled_date) | (Task.scheduled_date > scheduled_date)
        )
    elif scheduled_date:
        conditions.append(Task.scheduled_date == scheduled_date)
    if status:
        conditions.append(Task.status == status)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(Task.sort_order, Task.created_at)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
    query = select(Task).where(Task.id == task_id).options(selectinload(Task.children))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_task(db: AsyncSession, data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    db.add(task)
    await db.commit()
    # 重新用 eager load 查询以包含 children
    return await get_task(db, task.id)


async def update_task(db: AsyncSession, task_id: int, data: TaskUpdate) -> Optional[Task]:
    from sqlalchemy import update as sql_update

    task = await get_task(db, task_id)
    if not task:
        return None
    old_parent_id = task.parent_id
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(task, key, value)
    await db.commit()

    # 联动父任务状态（当前父 + 旧父）
    parent_ids_to_check = set()
    if task.parent_id:
        parent_ids_to_check.add(task.parent_id)
    if old_parent_id and old_parent_id != task.parent_id:
        parent_ids_to_check.add(old_parent_id)

    for pid in parent_ids_to_check:
        parent = await get_task(db, pid)
        if parent and parent.children:
            all_done = all(c.status == "done" for c in parent.children)
            new_status = "done" if all_done else "todo"
            if parent.status != new_status:
                await db.execute(
                    sql_update(Task).where(Task.id == parent.id).values(status=new_status)
                )
                await db.commit()

    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    task = await get_task(db, task_id)
    if not task:
        return False
    await db.delete(task)
    await db.commit()
    return True


async def update_task_status(db: AsyncSession, task_id: int, status: str) -> Optional[Task]:
    from sqlalchemy import update as sql_update

    # 直接用 SQL 更新，避免 ORM 循环依赖
    result = await db.execute(
        sql_update(Task).where(Task.id == task_id).values(status=status)
    )
    if result.rowcount == 0:
        return None
    await db.commit()

    # 子任务状态变更 → 联动父任务状态
    task = await get_task(db, task_id)
    if task and task.parent_id:
        parent = await get_task(db, task.parent_id)
        if parent and parent.children:
            all_done = all(c.status == "done" for c in parent.children)
            if all_done and parent.status != "done":
                # 所有子任务完成 → 父任务自动完成
                await db.execute(
                    sql_update(Task).where(Task.id == parent.id).values(status="done")
                )
                await db.commit()
            elif not all_done and parent.status == "done":
                # 有子任务未完成 → 父任务恢复待办
                await db.execute(
                    sql_update(Task).where(Task.id == parent.id).values(status="todo")
                )
                await db.commit()

    return await get_task(db, task_id)
