import asyncio
import json
from datetime import date, datetime, timedelta
from typing import Optional

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import AiConfig
from app.models.setting import Setting
from app.models.task import Task
from app.services.calendar_service import get_free_slots, get_day_tasks
from app.utils.holidays import is_holiday, is_workday


async def get_active_ai_config(db: AsyncSession) -> Optional[AiConfig]:
    """获取当前激活的 AI 配置"""
    result = await db.execute(select(AiConfig).where(AiConfig.is_active == True))
    return result.scalar_one_or_none()


async def get_general_settings(db: AsyncSession) -> dict:
    """获取通用设置（工作时间等）"""
    result = await db.execute(select(Setting))
    return {s.key: s.value for s in result.scalars().all()}


def get_client(config: AiConfig) -> OpenAI:
    return OpenAI(api_key=config.api_key, base_url=config.base_url)


async def build_schedule_context(db: AsyncSession, target_date: date, task: Optional[Task] = None) -> str:
    """组装调度上下文信息"""
    settings = await get_general_settings(db)
    work_hours = json.loads(settings.get("work_hours", '{"start":"09:00","end":"18:00"}'))

    day_tasks = await get_day_tasks(db, target_date)
    # 排除正在被重新安排的任务本身，避免自身时间段被误判为冲突
    if task and task.id:
        day_tasks = [t for t in day_tasks if t.id != task.id]
    free_slots = await get_free_slots(db, target_date, work_hours, exclude_task_id=task.id if task else None)

    # 未来3天负载
    future_load = []
    for i in range(1, 4):
        d = target_date + timedelta(days=i)
        dt = await get_day_tasks(db, d)
        future_load.append(f"  {d}: {len(dt)} 个任务")

    holiday_info = "节假日" if is_holiday(target_date) else ("工作日" if is_workday(target_date) else "周末")

    ctx = f"""当前日期: {target_date} ({holiday_info})
工作时间段: {work_hours['start']} - {work_hours['end']}

目标日期已有任务:
"""
    for t in day_tasks:
        time_str = f"{t.start_time}-{t.end_time}" if t.start_time and t.end_time else "未定时间"
        ctx += f"  - [{t.priority}] {t.title} ({time_str}, 状态:{t.status})\n"
    if not day_tasks:
        ctx += "  (无任务)\n"

    ctx += f"\n空闲时间段:\n"
    for slot in free_slots:
        ctx += f"  {slot['start']} - {slot['end']}\n"
    if not free_slots:
        ctx += "  (无空闲)\n"

    ctx += f"\n未来3天负载:\n" + "\n".join(future_load)

    if task:
        ctx += f"\n\n待安排的任务:\n  标题: {task.title}\n  描述: {task.description or '无'}\n  截止: {task.deadline or '无'}\n  预估耗时: {task.estimated_minutes or '未知'}分钟"

    return ctx


SCHEDULE_SYSTEM_PROMPT = """你是一个智能日程调度助手。你需要根据上下文信息，为用户安排任务的时间。

返回严格 JSON 格式：
{
  "scheduled_date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "priority": "P0/P1/P2/P3",
  "estimated_minutes": 数字,
  "reason": "安排理由"
}

注意：
- 优先安排在工作时间段内
- 高优先级任务安排在上午（精力充沛时段）
- 避免与已有任务时间冲突
- 如果目标日期没有空闲，自动顺延到下一个有空闲的日期
- 考虑工作日/周末/节假日
- estimated_minutes 如果用户未指定，根据任务内容合理估算
"""


CHAT_SYSTEM_PROMPT = """你是一个智能日程管理助手。你的核心职责是通过 action 字段**直接执行操作**，而不是仅在 reply 中描述你要做什么。

当前日期: {today}

## 任务状态

任务有三种状态，对应看板的三列：
- "todo" — 待办（刚创建、还没开始）
- "in_progress" — 进行中（已安排具体时间并开始执行）
- "done" — 已完成

状态判断规则：
- 创建任务时：如果安排了具体的 start_time 且时间在当前时刻附近或已过，status 设为 "in_progress"；否则设为 "todo"
- 用户说"开始做XX"、"现在做XX"→ 状态改为 "in_progress"
- 用户说"做完了"、"XX完成了"→ 状态改为 "done"
- 给待办任务安排时间时，如果是安排在今天且时间已到，顺便改为 "in_progress"

## 操作格式（严格 JSON）

创建任务:
{{"action": "create", "task": {{"title": "标题", "scheduled_date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM", "priority": "P0-P3", "estimated_minutes": 数字, "category": "分类", "status": "todo 或 in_progress"}}, "reply": "简短确认"}}

修改任务（可修改的字段：title, scheduled_date, start_time, end_time, priority, estimated_minutes, category, status）:
{{"action": "update", "task_id": 任务ID, "updates": {{"字段": "新值"}}, "reply": "简短确认"}}

删除任务:
{{"action": "delete", "task_id": 任务ID, "reply": "简短确认"}}

重新调度（仅用于"帮我找个合适的时间"等模糊请求，会调用 AI 自动排期）:
{{"action": "reschedule", "task_id": 任务ID, "hint": "调度提示", "reply": "简短确认"}}

普通对话（仅当不涉及任何任务操作时）:
{{"action": "none", "reply": "你的回复"}}

## 关键规则

1. **立即执行，不要询问确认**：当用户意图明确时（如"帮我创建XXX任务"、"明天下午开会"），直接返回对应的 action，不要在 reply 中说"我来帮你创建"然后用 action: "none"。
2. **自动补全缺失信息**：用户没说优先级就根据内容判断，没说时间就根据任务性质合理安排，没说日期就默认今天。
3. **日期转换**："今天"={today}，"明天"、"后天"、"下周一"等都要转换为具体 YYYY-MM-DD。
4. **reply 要简洁**：确认已执行的操作即可，如"已创建：读论文，今天14:00-16:00"。
5. 只有当用户的请求确实模糊到无法判断要做什么操作时，才用 action: "none" 进行追问。
6. task 中 start_time/end_time 可以省略，但如果用户提到了时间必须填写。
7. **给任务安排时间时，同时在 updates 中设置合适的 status**。
8. **update vs reschedule 的区分**：
   - 用户明确说了具体时间（"改到三点"、"推迟到5点"、"改成明天上午"），用 **update** 直接修改字段
   - 用户没说具体时间、让你自动安排（"帮我重新安排一下"、"找个合适的时间"、"今天太忙了换个时间"），才用 **reschedule**
   - 简单来说：用户给了明确时间 → update，用户没给时间让你决定 → reschedule

## 示例

用户: "明天下午三点开会"
{{"action": "create", "task": {{"title": "开会", "scheduled_date": "2026-04-19", "start_time": "15:00", "end_time": "16:00", "priority": "P1", "estimated_minutes": 60, "status": "todo"}}, "reply": "已创建：明天15:00-16:00 开会"}}

用户: "给读论文那个任务安排下午2点到4点"
{{"action": "update", "task_id": 1, "updates": {{"start_time": "14:00", "end_time": "16:00", "status": "in_progress"}}, "reply": "已安排：14:00-16:00 读论文，状态改为进行中"}}

用户: "改到三点吧"
{{"action": "update", "task_id": 1, "updates": {{"start_time": "15:00", "end_time": "17:00"}}, "reply": "已改到15:00-17:00"}}

用户: "这个任务帮我重新安排一下，今天太忙了"
{{"action": "reschedule", "task_id": 1, "hint": "今天太忙", "reply": "好的，正在为你重新安排"}}

用户: "论文读完了"
{{"action": "update", "task_id": 1, "updates": {{"status": "done"}}, "reply": "已标记完成：读论文"}}
"""


async def ai_schedule_task(db: AsyncSession, task: Task, hint: str = "") -> dict:
    """为单个任务调用 AI 排期"""
    config = await get_active_ai_config(db)
    if not config:
        return {"error": "请先在设置中配置并激活一个 AI 服务"}

    client = get_client(config)
    target_date = task.scheduled_date or date.today()
    context = await build_schedule_context(db, target_date, task)

    messages = [
        {"role": "system", "content": SCHEDULE_SYSTEM_PROMPT},
        {"role": "user", "content": f"请为以下任务安排时间：\n\n{context}" + (f"\n\n用户补充: {hint}" if hint else "")},
    ]

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=config.model,
                messages=messages,
                response_format={"type": "json_object"},
            ),
        )
        result = json.loads(response.choices[0].message.content, strict=False)
        return result
    except Exception as e:
        return {"error": str(e)}


def _build_chat_history(history: list[dict]) -> list[dict]:
    """将前端传来的对话记录转为 AI 消息格式"""
    result = []
    for msg in history:
        if msg["role"] == "assistant":
            result.append({"role": "assistant", "content": json.dumps(
                {"action": "none", "reply": msg["content"]}, ensure_ascii=False
            )})
        else:
            result.append({"role": "user", "content": msg["content"]})
    return result


async def ai_chat(db: AsyncSession, user_message: str, recent_tasks: list[Task], history: list[dict] = None) -> dict:
    """处理 AI 对话"""
    config = await get_active_ai_config(db)
    if not config:
        return {"action": "none", "reply": "请先在设置页面中配置并激活一个 AI 服务。"}

    client = get_client(config)
    today = date.today().isoformat()

    # 组装当前任务上下文
    task_context = "当前任务列表:\n"
    for t in recent_tasks:
        time_str = f"{t.start_time}-{t.end_time}" if t.start_time and t.end_time else "未定时间"
        task_context += f"  ID:{t.id} [{t.priority}] {t.title} | 日期:{t.scheduled_date} | {time_str} | 状态:{t.status}\n"
        if t.children:
            for c in t.children:
                ctime = f"{c.start_time}-{c.end_time}" if c.start_time and c.end_time else "未定时间"
                task_context += f"    子任务 ID:{c.id} [{c.priority}] {c.title} | {ctime} | 状态:{c.status}\n"

    system = CHAT_SYSTEM_PROMPT.format(today=today)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"[系统信息] {task_context}"},
        {"role": "assistant", "content": json.dumps({"action": "none", "reply": "好的，我已了解当前任务情况。"}, ensure_ascii=False)},
    ]
    # 追加前端传来的当前会话历史
    if history:
        messages.extend(_build_chat_history(history))
    # 追加当前用户消息
    messages.append({"role": "user", "content": user_message})

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=config.model,
                messages=messages,
                response_format={"type": "json_object"},
            ),
        )
        result = json.loads(response.choices[0].message.content, strict=False)
        return result
    except Exception as e:
        return {"action": "none", "reply": f"AI 服务出错: {str(e)}"}


async def ai_daily_suggestion(db: AsyncSession) -> dict:
    """获取今日聚焦建议（非流式）"""
    config = await get_active_ai_config(db)
    if not config:
        return {"suggestion": "请先在设置中配置并激活一个 AI 服务。"}

    client = get_client(config)
    today = date.today()
    context = await build_schedule_context(db, today)

    messages = [
        {"role": "system", "content": "你是一个日程管理助手。根据用户今天的任务安排，给出简洁的聚焦建议（最重要的3件事 + 建议执行顺序）。直接给出建议，不要 JSON 格式。"},
        {"role": "user", "content": f"今天是 {today}，以下是我的任务情况：\n\n{context}\n\n请给出今日聚焦建议。"},
    ]

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=config.model,
                messages=messages,
            ),
        )
        return {"suggestion": response.choices[0].message.content}
    except Exception as e:
        return {"suggestion": f"获取建议失败: {str(e)}"}


async def prepare_daily_suggestion_stream(db: AsyncSession):
    """准备每日建议的流式调用参数（异步阶段：读DB），返回同步流式生成器"""
    config = await get_active_ai_config(db)
    if not config:
        def _fallback():
            yield "请先在设置中配置并激活一个 AI 服务。"
        return _fallback()

    client = get_client(config)
    today = date.today()
    context = await build_schedule_context(db, today)

    messages = [
        {"role": "system", "content": "你是一个日程管理助手。根据用户今天的任务安排，给出简洁的聚焦建议（最重要的3件事 + 建议执行顺序）。直接给出建议，不要 JSON 格式。"},
        {"role": "user", "content": f"今天是 {today}，以下是我的任务情况：\n\n{context}\n\n请给出今日聚焦建议。"},
    ]

    def _stream():
        try:
            stream = client.chat.completions.create(
                model=config.model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"获取建议失败: {str(e)}"

    return _stream()


async def prepare_chat_stream(db: AsyncSession, user_message: str, recent_tasks: list[Task], history: list[dict] = None):
    """准备聊天的流式调用参数（异步阶段：读DB），返回同步流式生成器。
    生成器 yield (type, data):
       ("token", str) = 流式文本片段
       ("result", dict) = 最终解析的完整 JSON 结果
    """
    config = await get_active_ai_config(db)
    if not config:
        def _fallback():
            yield ("result", {"action": "none", "reply": "请先在设置页面中配置并激活一个 AI 服务。"})
        return _fallback()

    client = get_client(config)
    today = date.today().isoformat()

    task_context = "当前任务列表:\n"
    for t in recent_tasks:
        time_str = f"{t.start_time}-{t.end_time}" if t.start_time and t.end_time else "未定时间"
        task_context += f"  ID:{t.id} [{t.priority}] {t.title} | 日期:{t.scheduled_date} | {time_str} | 状态:{t.status}\n"
        if t.children:
            for c in t.children:
                ctime = f"{c.start_time}-{c.end_time}" if c.start_time and c.end_time else "未定时间"
                task_context += f"    子任务 ID:{c.id} [{c.priority}] {c.title} | {ctime} | 状态:{c.status}\n"

    system = CHAT_SYSTEM_PROMPT.format(today=today)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"[系统信息] {task_context}"},
        {"role": "assistant", "content": json.dumps({"action": "none", "reply": "好的，我已了解当前任务情况。"}, ensure_ascii=False)},
    ]
    if history:
        messages.extend(_build_chat_history(history))
    messages.append({"role": "user", "content": user_message})

    def _stream():
        try:
            stream = client.chat.completions.create(
                model=config.model,
                messages=messages,
                response_format={"type": "json_object"},
                stream=True,
            )
            full_content = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_content += token
                    yield ("token", token)

            try:
                result = json.loads(full_content, strict=False)
            except json.JSONDecodeError:
                result = {"action": "none", "reply": full_content}
            yield ("result", result)
        except Exception as e:
            yield ("result", {"action": "none", "reply": f"AI 服务出错: {str(e)}"})

    return _stream()
