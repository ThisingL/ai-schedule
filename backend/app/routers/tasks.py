from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = await task_service.create_task(db, data)
    return task


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    date: Optional[date] = None,
    status: Optional[str] = None,
    include_overdue: bool = False,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.get_tasks(db, date, status, include_overdue)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await task_service.update_task(db, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    success = await task_service.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int, data: TaskStatusUpdate, db: AsyncSession = Depends(get_db)
):
    task = await task_service.update_task_status(db, task_id, data.status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
