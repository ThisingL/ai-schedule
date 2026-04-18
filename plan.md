# 智能日程助理 (AI Schedule) - 项目计划

## 一、项目概述

一个面向个人使用的智能日程管理 Web 应用。核心理念：**让 AI 帮你思考任务该怎么安排，你只需要专注于执行。**

主要解决的问题：
- 手动安排日程费脑力，容易遗漏优先级判断
- 当天未完成的任务需要手动重新安排，繁琐且容易遗忘
- 想要一个清晰的视图，一眼看到"今天该做什么"以及"时间是怎么分配的"

## 二、技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | Python + FastAPI | 异步高性能，API 开发友好 |
| 前端框架 | Vue 3 + Vite + TypeScript | 轻量易上手，运行配置简单 |
| 前端 UI | Naive UI（或 Element Plus） | 开箱即用的组件库，含日历、拖拽等组件 |
| 数据库 | SQLite + SQLAlchemy | 零配置，随项目走，个人使用完全够用 |
| AI 服务 | 硅基流动 API（OpenAI 兼容） | 使用顶尖模型，通过 openai Python SDK 调用（仅需修改 base_url） |
| 包管理 | 后端 uv / pip，前端 npm | - |

## 三、版本规划

### v0.1.0 — 核心功能版本（首版目标）

> 一个完整可用的智能日程助理，包含看板、日历、AI 调度全部核心能力。

**包含功能：**

1. **任务管理（CRUD）**
   - 手动创建/编辑/删除任务（表单方式）
   - AI 对话创建任务（聊天框输入自然语言，如"明天下午三点和张总开会，大概一小时"）
   - 任务状态流转：待办 → 进行中 → 已完成
   - 支持将任务标记为未完成，触发 AI 重新调度
   - **子任务支持**：
     - 任务可拆分为多个子任务，子任务拥有独立的状态、时间、优先级
     - 当所有子任务标记为"已完成"时，父任务自动变为"已完成"状态
     - AI 调度以子任务为粒度进行排期
     - 看板中，同一父任务的子任务排列在一块，顶部显示父任务标题栏（带进度指示，如"3/5 已完成"），视觉上可清晰识别归属关系
     - 支持手动创建子任务，也支持 AI 对话拆分（如"把这个任务拆成3个子任务"）


2. **看板视图**
   - 三列看板：待办 | 进行中 | 已完成
   - 支持拖拽切换状态（任务拖入"进行中"列时，若有 start_time/end_time 则同步显示在日历视图中）
   - **待办列三段分组**（从上到下，各区域大小可动态调整，分隔线可拖动）：
     - **今日任务**：scheduled_date = 今天的任务，默认样式，置顶最醒目
     - **往期未完成**：scheduled_date < 今天的未完成任务，用醒目标签/颜色（如橙色边框 + "逾期"标签）标识
     - **未来任务**：scheduled_date > 今天的任务，用较浅的颜色或标签（如"4/20"日期标签）标识
   - 每个任务卡片显示：标题、优先级标记、时间段、预估耗时、分类标签
3. **日历视图（周课程表样式）**
   - 固定为周视图，横轴为周一~周日，纵轴为 0:00~24:00 时间轴从上到下排列
   - **展示内容**：仅显示"进行中"且有具体 start_time 和 end_time 的任务，以时间块形式填充在对应的日期和时间段位置（类似课程表/Google Calendar）
   - 可点击时间块查看/编辑任务详情
   - 可视化展示空闲时间段（未被占用的时间区域）
   - 可在空白时间段点击快速创建任务

4. **AI 智能调度**
   - **优先级判断**：新建任务时，AI 根据任务内容、截止日期、当前任务负载自动评估优先级（P0-P3）
   - **智能排期**：用户未指定时间时，AI 综合考虑以下因素自动安排：
     - 当天/近几天已有任务分布
     - 工作日 vs 周末 vs 法定节假日（接入中国节假日数据）
     - 任务优先级和截止日期紧迫度
     - 预估耗时（用户未指定时由 AI 估算）
   - **未完成任务重调度**：
     - 每个任务卡片上提供"重新安排"按钮，点击后展开一个输入框，用户可输入补充说明（如"推迟到下周""安排在早上"）辅助 AI 调度，也可留空直接提交，由 AI 自行判断最佳时间
     - **过期任务自动归集**：未完成的过期任务（scheduled_date < 今天 且 status != done）不会自动重调度，而是自动出现在当天的待办池中，用户可手动点击"重新安排"让 AI 调度到合适时间，也可直接操作完成

   - **冲突检测**：新任务与已有任务时间冲突时，AI 给出调整建议
   - **每日建议**：打开应用时，AI 给出"今日聚焦建议"（最重要的 3 件事 + 建议执行顺序）

5. **AI 对话交互**
   - 页面侧边栏/底部聊天框
   - 支持自然语言：创建任务、查询日程、请求调度建议
   - 对话历史记录保留（当天）
   - AI 操作后展示结果，用户可手动修正

6. **基础设置**
   - 工作时间段配置（如 09:00-18:00）
   - **AI 服务配置面板**：支持用户在界面上配置以下字段，保存到数据库，后端调用 AI 时读取：
     - API Key（密码框，保存后脱敏显示）
     - API 接口地址（Base URL，默认预填硅基流动地址，可改为任意 OpenAI 兼容接口）
     - 模型名称（如 `deepseek-ai/DeepSeek-V3`，支持手动输入）
   - 分类标签管理（工作、学习、生活、健康等）

### v0.2.0 — 增强功能版本（后续迭代）

- 邮件提醒功能（SMTP 发送，APScheduler 定时检查）
- 任务统计与分析（本周完成率、时间分配饼图等）
- 周回顾 / 月回顾报告（AI 生成）
- 重复任务支持（每天/每周/每月）
- 数据导入导出（JSON/CSV）

### v0.3.0 — 体验优化版本（远期）

- 深色模式
- 移动端适配（响应式）
- 更精细的 AI 学习（基于历史行为优化建议）
- 多日历视图（月视图）

## 四、数据模型设计

### 任务表 (tasks)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 自增主键 |
| parent_id | Integer, FK(tasks.id), nullable | 父任务 ID（为空表示顶层任务，非空表示子任务） |
| title | String | 任务标题 |
| description | Text, nullable | 任务描述/备注 |
| priority | Enum(P0,P1,P2,P3) | 优先级。P0=紧急重要, P1=重要不紧急, P2=紧急不重要, P3=不紧急不重要 |
| status | Enum(todo,in_progress,done) | 任务状态 |
| category | String, nullable | 分类标签（工作/学习/生活等） |
| scheduled_date | Date | 计划执行日期 |
| start_time | Time, nullable | 计划开始时间 |
| end_time | Time, nullable | 计划结束时间 |
| estimated_minutes | Integer, nullable | 预估耗时（分钟） |
| deadline | DateTime, nullable | 截止日期 |
| is_ai_generated | Boolean | 是否由 AI 创建/安排 |
| ai_priority_reason | Text, nullable | AI 判断优先级的理由（可展示给用户） |
| sort_order | Integer | 看板内排序权重 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### AI 对话记录表 (chat_messages)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 自增主键 |
| role | Enum(user,assistant) | 消息角色 |
| content | Text | 消息内容 |
| related_task_ids | JSON, nullable | 本次对话涉及的任务 ID 列表 |
| created_at | DateTime | 发送时间 |

### 用户设置表 (settings)

| 字段 | 类型 | 说明 |
|------|------|------|
| key | String, PK | 配置键名 |
| value | Text | 配置值（JSON 存储） |

> 存储内容举例：work_hours（工作时间段）、ai_api_key（API 密钥）、ai_base_url（API 接口地址）、ai_model（模型名称）、categories（自定义分类列表）等

## 五、API 设计

### 任务相关

```
POST   /api/tasks              创建任务（body 中 parent_id 可选，指定则创建为子任务）
GET    /api/tasks              查询任务列表（支持按日期、状态筛选，返回时子任务嵌套在父任务下）
GET    /api/tasks/{id}         查询单个任务（含其子任务列表）
PUT    /api/tasks/{id}         更新任务
DELETE /api/tasks/{id}         删除任务（若为父任务，同时删除所有子任务）
PATCH  /api/tasks/{id}/status  快速更新状态（拖拽用；子任务全部完成时自动更新父任务状态）
```

### AI 相关

```
POST   /api/ai/chat               发送对话（AI 解析并执行操作）
POST   /api/ai/schedule           请求 AI 为指定任务排期
POST   /api/ai/reschedule/{id}    单个任务重调度
GET    /api/ai/daily-suggestion    获取今日聚焦建议
```

### 日历相关

```
GET    /api/calendar/week?date=    获取指定周的任务时间分布
GET    /api/calendar/day?date=     获取指定天的时间轴数据
GET    /api/calendar/free-slots    获取空闲时间段
```

### 设置相关

```
GET    /api/settings              获取所有设置
PUT    /api/settings              更新设置
```

## 六、AI 调度策略设计

AI 调度的核心是通过 Prompt 将当前任务上下文传递给大模型，让模型以结构化 JSON 返回调度结果。

### 输入给 AI 的上下文信息

每次调度请求，组装以下信息作为 prompt 的一部分：

```
1. 当前待安排的任务（标题、描述、截止日期、预估耗时）
2. 目标日期已有的任务列表（含时间段）
3. 目标日期的空闲时间段
4. 用户设置的工作时间段
5. 目标日期是工作日 / 周末 / 节假日
6. 未来 3-5 天的任务负载概况
```

### AI 返回的结构化结果

```json
{
  "action": "schedule",
  "tasks": [
    {
      "task_id": 1,
      "scheduled_date": "2026-04-18",
      "start_time": "09:00",
      "end_time": "10:30",
      "priority": "P1",
      "estimated_minutes": 90,
      "reason": "该任务截止日期临近且重要度高，建议上午精力充沛时优先处理"
    }
  ],
  "suggestion": "今天有 3 个任务，建议上午集中处理 P0 和 P1 任务..."
}
```

### 对话意图识别

AI 对话模块需识别以下意图：

| 意图 | 示例输入 | 触发动作 |
|------|----------|----------|
| 创建任务 | "明天下午和张总开会" | 解析时间+标题，调用创建 API |
| 查询日程 | "我明天有什么安排" | 查询并返回任务列表 |
| 调整任务 | "把开会改到后天" | 更新任务时间 |
| 请求建议 | "今天先做什么好" | 调用每日建议 |
| 删除任务 | "取消明天的开会" | 删除对应任务 |
| 重新调度 | "今天没做完的帮我安排一下" | 触发重调度 |

## 七、项目目录结构

```
ai-schedule/
├── plan.md                     # 本文件
├── CHANGELOG.md                # 版本变更记录
├── README.md                   # 项目说明
│
├── backend/                    # 后端 (FastAPI)
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库初始化
│   │   ├── models/             # SQLAlchemy 模型
│   │   │   ├── task.py
│   │   │   ├── chat.py
│   │   │   └── setting.py
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   │   ├── task.py
│   │   │   └── chat.py
│   │   ├── routers/            # API 路由
│   │   │   ├── tasks.py
│   │   │   ├── ai.py
│   │   │   ├── calendar.py
│   │   │   └── settings.py
│   │   ├── services/           # 业务逻辑
│   │   │   ├── task_service.py
│   │   │   ├── ai_service.py   # AI 调用 + Prompt 组装
│   │   │   └── calendar_service.py
│   │   └── utils/
│   │       ├── holidays.py     # 中国节假日判断
│   │       └── time_utils.py   # 时间处理工具
│   ├── requirements.txt
│   └── .env.example            # 环境变量模板（仅基础配置，AI API Key 等通过前端设置面板配置）
│
├── frontend/                   # 前端 (Vue 3)
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── views/
│   │   │   ├── Dashboard.vue   # 主页（看板 + 日历切换）
│   │   │   └── Settings.vue    # 设置页
│   │   ├── components/
│   │   │   ├── KanbanBoard.vue # 看板组件
│   │   │   ├── CalendarView.vue# 日历组件
│   │   │   ├── TaskCard.vue    # 任务卡片
│   │   │   ├── TaskForm.vue    # 任务表单（创建/编辑）
│   │   │   ├── ChatPanel.vue   # AI 对话面板
│   │   │   └── DailySuggestion.vue # 每日建议
│   │   ├── composables/        # Vue 组合式函数
│   │   │   ├── useTasks.ts
│   │   │   └── useChat.ts
│   │   ├── stores/             # Pinia 状态管理
│   │   │   ├── taskStore.ts
│   │   │   └── chatStore.ts
│   │   ├── api/                # API 调用封装
│   │   │   └── index.ts
│   │   └── types/              # TypeScript 类型定义
│   │       └── index.ts
│   ├── package.json
│   └── vite.config.ts
│
└── .gitignore
```

## 八、关键技术实现要点

### 1. 硅基流动 API 调用

硅基流动兼容 OpenAI 接口，使用 `openai` Python SDK：

```python
from openai import OpenAI

# 从数据库 settings 表读取用户配置，无需硬编码
client = OpenAI(
    api_key=settings["ai_api_key"],       # 用户在设置面板中配置
    base_url=settings["ai_base_url"]      # 用户自定义的 API 接口地址
)

response = client.chat.completions.create(
    model=settings["ai_model"],           # 用户选择的模型名称
    messages=[...],
    response_format={"type": "json_object"}  # 强制 JSON 输出
)
```

### 2. 看板拖拽

前端使用 `vuedraggable`（基于 Sortable.js）实现拖拽，拖拽完成后调用 `PATCH /api/tasks/{id}/status` 更新状态。

### 3. 日历组件

使用 `FullCalendar Vue 3` 组件，支持周视图 / 日视图，任务以时间块形式展示。

### 4. 中国节假日

使用开源节假日数据（如 `chinese-calendar` Python 包，或离线 JSON 数据），判断指定日期是工作日、周末还是法定假日。

### 5. AI 对话的 Function Calling 模式

为保证 AI 返回可执行的结构化结果，采用 System Prompt + JSON Schema 约束的方式：
- System Prompt 中定义可用操作（创建、修改、删除、查询、调度）
- 要求 AI 返回固定格式 JSON
- 后端解析 JSON 并执行对应操作
- 将执行结果反馈给用户

## 九、开发顺序（v0.1.0）

按以下顺序推进，每步都可独立验证：

```
第 1 步：项目初始化
  - FastAPI 项目骨架 + SQLite 数据库初始化
  - Vue 3 + Vite 项目骨架
  - 前后端联调跑通（hello world 级别）

第 2 步：任务 CRUD
  - 后端任务 API 全套
  - 前端任务表单（创建/编辑/删除）
  - 基础列表展示

第 3 步：看板视图
  - 三列看板布局
  - 拖拽状态切换
  - 按日期筛选

第 4 步：日历视图
  - FullCalendar 集成
  - 周视图 / 日视图
  - 任务时间块展示
  - 看板 ↔ 日历 tab 切换

第 5 步：AI 核心 — 调度引擎
  - 硅基流动 API 接入
  - Prompt 模板设计
  - 优先级判断 + 智能排期
  - 未完成任务重调度

第 6 步：AI 对话交互
  - 聊天面板 UI
  - 意图识别 + 操作执行
  - 对话记录存储

第 7 步：收尾
  - 每日聚焦建议
  - 设置页面
  - 节假日数据接入
  - 整体联调 + 体验优化
  - 打标签 v0.1.0 发布
```

## 十、运行方式（目标）

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入 API Key
uvicorn app.main:app --reload

# 前端（Vite 配置端口为 6666）
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:6666` 即可使用。
