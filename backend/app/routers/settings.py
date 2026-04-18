import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import Setting

router = APIRouter(prefix="/settings", tags=["settings"])

# 默认配置（AI 相关已移到 ai_configs 表）
DEFAULTS = {
    "work_hours": json.dumps({"start": "09:00", "end": "18:00"}),
    "categories": json.dumps(["工作", "学习", "生活", "健康"]),
}


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting))
    rows = {s.key: s.value for s in result.scalars().all()}
    merged = {**DEFAULTS, **rows}
    return merged


@router.put("")
async def update_settings(data: dict, db: AsyncSession = Depends(get_db)):
    for key, value in data.items():
        existing = await db.get(Setting, key)
        if existing:
            existing.value = value
        else:
            db.add(Setting(key=key, value=value))
    await db.commit()
    return {"ok": True}
