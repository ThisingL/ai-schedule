import asyncio
import json
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task
from app.schemas.task import TaskCreate
from app.services.ai_service import (
    ai_schedule_task, ai_chat, ai_daily_suggestion,
    prepare_chat_stream, prepare_daily_suggestion_stream,
)
from app.services.task_service import get_tasks, get_task, create_task

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatHistoryItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryItem] = []


class RescheduleRequest(BaseModel):
    hint: str = ""


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _parse_date(val) -> date | None:
    if isinstance(val, date):
        return val
    if isinstance(val, str) and val:
        try:
            return date.fromisoformat(val)
        except ValueError:
            pass
    return None


def _parse_time(val) -> time | None:
    if isinstance(val, time):
        return val
    if isinstance(val, str) and val:
        try:
            return time.fromisoformat(val)
        except ValueError:
            pass
    return None


def _convert_task_field(key: str, val):
    """将 AI 返回的字符串值转为 Task 模型需要的 Python 类型"""
    if key == "scheduled_date":
        return _parse_date(val) or date.today()
    if key in ("start_time", "end_time"):
        return _parse_time(val)
    return val


async def _execute_chat_action(result: dict, db: AsyncSession) -> tuple[str, list[int]]:
    """执行 AI 返回的操作，返回 (reply, related_ids)"""
    action = result.get("action", "none")
    reply = result.get("reply", "")
    related_ids: list[int] = []

    if action == "create":
        task_data = result.get("task", {})
        task = Task(
            title=task_data.get("title", "未命名任务"),
            scheduled_date=_convert_task_field("scheduled_date", task_data.get("scheduled_date")),
            start_time=_convert_task_field("start_time", task_data.get("start_time")),
            end_time=_convert_task_field("end_time", task_data.get("end_time")),
            priority=task_data.get("priority", "P2"),
            estimated_minutes=task_data.get("estimated_minutes"),
            category=task_data.get("category"),
            is_ai_generated=True,
            status=task_data.get("status", "todo"),
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        related_ids = [task.id]

    elif action == "update":
        task_id = result.get("task_id")
        updates = result.get("updates", {})
        if task_id and updates:
            task = await get_task(db, task_id)
            if task:
                for k, v in updates.items():
                    if hasattr(task, k):
                        setattr(task, k, _convert_task_field(k, v))
                await db.commit()
                related_ids = [task_id]

    elif action == "delete":
        task_id = result.get("task_id")
        if task_id:
            task = await get_task(db, task_id)
            if task:
                await db.delete(task)
                await db.commit()
                related_ids = [task_id]

    elif action == "reschedule":
        task_id = result.get("task_id")
        hint = result.get("hint", "")
        if task_id:
            task = await get_task(db, task_id)
            if task:
                schedule_result = await ai_schedule_task(db, task, hint)
                if "error" not in schedule_result:
                    for k in ["scheduled_date", "start_time", "end_time", "priority", "estimated_minutes"]:
                        if k in schedule_result:
                            setattr(task, k, _convert_task_field(k, schedule_result[k]))
                    task.ai_priority_reason = schedule_result.get("reason", "")
                    await db.commit()
                    reply += f"\n\n已重新安排: {schedule_result.get('reason', '')}"
                    related_ids = [task_id]

    return reply, related_ids


@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    tasks = await get_tasks(db)
    history = [{"role": h.role, "content": h.content} for h in req.history]
    result = await ai_chat(db, req.message, tasks, history)

    reply, related_ids = await _execute_chat_action(result, db)

    return {
        "id": int(datetime.now().timestamp() * 1000),
        "role": "assistant",
        "content": reply,
        "related_task_ids": related_ids or None,
        "created_at": datetime.now().isoformat(),
    }


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """流式聊天 SSE"""
    tasks = await get_tasks(db)
    history = [{"role": h.role, "content": h.content} for h in req.history]

    sync_gen = await prepare_chat_stream(db, req.message, tasks, history)

    async def event_generator():
        loop = asyncio.get_event_loop()
        parsed_result = None

        queue: asyncio.Queue = asyncio.Queue()

        def _consume():
            for item in sync_gen:
                queue.put_nowait(item)
            queue.put_nowait(None)

        await loop.run_in_executor(None, _consume)

        while True:
            item = await queue.get()
            if item is None:
                break
            msg_type, data = item
            if msg_type == "token":
                yield _sse_event({"type": "token", "content": data})
            elif msg_type == "result":
                parsed_result = data

        if parsed_result:
            reply, related_ids = await _execute_chat_action(parsed_result, db)

            yield _sse_event({
                "type": "done",
                "action": parsed_result.get("action", "none"),
                "reply": reply,
                "related_task_ids": related_ids or None,
            })

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/daily-suggestion/stream")
async def daily_suggestion_stream(db: AsyncSession = Depends(get_db)):
    """流式获取每日建议 SSE"""
    sync_gen = await prepare_daily_suggestion_stream(db)

    async def event_generator():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _consume():
            for token in sync_gen:
                queue.put_nowait(token)
            queue.put_nowait(None)

        await loop.run_in_executor(None, _consume)

        while True:
            token = await queue.get()
            if token is None:
                break
            yield _sse_event({"type": "token", "content": token})

        yield _sse_event({"type": "done"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/schedule")
async def schedule_task(data: dict, db: AsyncSession = Depends(get_db)):
    task_id = data.get("task_id")
    if not task_id:
        raise HTTPException(400, "task_id is required")

    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    result = await ai_schedule_task(db, task)
    if "error" in result:
        raise HTTPException(500, result["error"])

    for k in ["scheduled_date", "start_time", "end_time", "priority", "estimated_minutes"]:
        if k in result:
            setattr(task, k, _convert_task_field(k, result[k]))
    task.ai_priority_reason = result.get("reason", "")
    task.is_ai_generated = True
    await db.commit()

    return result


@router.post("/reschedule/{task_id}")
async def reschedule_task(task_id: int, req: RescheduleRequest = RescheduleRequest(), db: AsyncSession = Depends(get_db)):
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    result = await ai_schedule_task(db, task, req.hint)
    if "error" in result:
        raise HTTPException(500, result["error"])

    for k in ["scheduled_date", "start_time", "end_time", "priority", "estimated_minutes"]:
        if k in result:
            setattr(task, k, _convert_task_field(k, result[k]))
    task.ai_priority_reason = result.get("reason", "")
    task.is_ai_generated = True
    await db.commit()

    return result


@router.get("/daily-suggestion")
async def daily_suggestion(db: AsyncSession = Depends(get_db)):
    return await ai_daily_suggestion(db)
