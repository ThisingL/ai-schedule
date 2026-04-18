import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import Setting
from app.schemas.task import TaskResponse
from app.services.calendar_service import get_week_tasks, get_day_tasks, get_free_slots

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/week")
async def week_view(
    date: str = Query(default=None, description="YYYY-MM-DD, 默认本周"),
    db: AsyncSession = Depends(get_db),
):
    if date:
        from datetime import date as date_type
        d = date_type.fromisoformat(date)
    else:
        from datetime import date as date_type
        d = date_type.today()

    # 计算周一
    day = d.weekday()
    monday = d - timedelta(days=day)

    tasks = await get_week_tasks(db, monday)
    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/day")
async def day_view(
    date: str = Query(default=None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    if date:
        from datetime import date as date_type
        d = date_type.fromisoformat(date)
    else:
        from datetime import date as date_type
        d = date_type.today()

    tasks = await get_day_tasks(db, d)
    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/free-slots")
async def free_slots(
    date: str = Query(default=None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    if date:
        from datetime import date as date_type
        d = date_type.fromisoformat(date)
    else:
        from datetime import date as date_type
        d = date_type.today()

    # 读取用户工作时间配置
    result = await db.execute(select(Setting).where(Setting.key == "work_hours"))
    setting = result.scalar_one_or_none()
    work_hours = json.loads(setting.value) if setting else {"start": "09:00", "end": "18:00"}

    return await get_free_slots(db, d, work_hours)
