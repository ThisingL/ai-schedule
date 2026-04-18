from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ai_config import AiConfig

router = APIRouter(prefix="/ai-configs", tags=["ai-configs"])


class AiConfigCreate(BaseModel):
    name: str
    api_key: str
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "deepseek-ai/DeepSeek-V3"


class AiConfigUpdate(BaseModel):
    name: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


class AiConfigTestRequest(BaseModel):
    # 可以传 config_id 用已有配置测试，也可以传临时参数
    config_id: int | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


def mask_key(key: str) -> str:
    if len(key) > 12:
        return key[:8] + "****" + key[-4:]
    return "****"


def config_to_dict(c: AiConfig) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "api_key_display": mask_key(c.api_key),
        "base_url": c.base_url,
        "model": c.model,
        "is_active": c.is_active,
    }


@router.get("")
async def list_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AiConfig).order_by(AiConfig.id))
    configs = result.scalars().all()
    return [config_to_dict(c) for c in configs]


@router.post("")
async def create_config(data: AiConfigCreate, db: AsyncSession = Depends(get_db)):
    # 如果是第一条配置，自动激活
    count_result = await db.execute(select(AiConfig))
    is_first = len(count_result.scalars().all()) == 0

    config = AiConfig(
        name=data.name,
        api_key=data.api_key,
        base_url=data.base_url,
        model=data.model,
        is_active=is_first,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config_to_dict(config)


@router.put("/{config_id}")
async def update_config(config_id: int, data: AiConfigUpdate, db: AsyncSession = Depends(get_db)):
    config = await db.get(AiConfig, config_id)
    if not config:
        raise HTTPException(404, "配置不存在")

    if data.name is not None:
        config.name = data.name
    if data.api_key:  # 非空才更新
        config.api_key = data.api_key
    if data.base_url is not None:
        config.base_url = data.base_url
    if data.model is not None:
        config.model = data.model

    await db.commit()
    await db.refresh(config)
    return config_to_dict(config)


@router.delete("/{config_id}")
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    config = await db.get(AiConfig, config_id)
    if not config:
        raise HTTPException(404, "配置不存在")

    was_active = config.is_active
    await db.delete(config)
    await db.commit()

    # 如果删除的是激活配置，自动激活第一条
    if was_active:
        result = await db.execute(select(AiConfig).order_by(AiConfig.id).limit(1))
        first = result.scalar_one_or_none()
        if first:
            first.is_active = True
            await db.commit()

    return {"ok": True}


@router.post("/{config_id}/activate")
async def activate_config(config_id: int, db: AsyncSession = Depends(get_db)):
    config = await db.get(AiConfig, config_id)
    if not config:
        raise HTTPException(404, "配置不存在")

    # 先全部取消激活
    await db.execute(sql_update(AiConfig).values(is_active=False))
    config.is_active = True
    await db.commit()
    return {"ok": True}


@router.post("/test")
async def test_config(data: AiConfigTestRequest, db: AsyncSession = Depends(get_db)):
    api_key = data.api_key or ""
    base_url = data.base_url or "https://api.siliconflow.cn/v1"
    model = data.model or "deepseek-ai/DeepSeek-V3"

    # 如果指定了 config_id，从数据库读
    if data.config_id:
        config = await db.get(AiConfig, data.config_id)
        if not config:
            return {"ok": False, "message": "配置不存在"}
        api_key = api_key or config.api_key
        base_url = data.base_url or config.base_url
        model = data.model or config.model

    if not api_key:
        return {"ok": False, "message": "未提供 API Key"}

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "请回复OK"}],
            max_tokens=10,
        )
        content = resp.choices[0].message.content if resp.choices else ""
        return {"ok": True, "message": f"连接成功，模型响应: {content}"}
    except Exception as e:
        return {"ok": False, "message": f"连接失败: {str(e)}"}
