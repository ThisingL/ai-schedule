<div align="center">

# AI Schedule

**An intelligent schedule management app powered by AI**

Manage your tasks with a Kanban board, calendar view, and an AI assistant that understands natural language.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen?logo=vue.js&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](#features) | [中文](#功能特性)

</div>

---

## Features

- **Kanban Board** - Three-column layout (Todo / In Progress / Done) with drag-and-drop support
- **Calendar View** - Weekly schedule view with hourly time slots, click to create tasks
- **AI Chat Assistant** - Create, update, delete, and reschedule tasks through natural language conversation
- **Smart Scheduling** - AI-powered time slot allocation with conflict detection and priority analysis
- **Parent-Child Tasks** - Bind tasks as subtasks with automatic parent status management
- **Daily Focus** - AI-generated daily suggestions that appear on page load
- **Holiday Awareness** - Built-in Chinese holiday calendar for smarter scheduling
- **Flexible AI Backend** - Compatible with any OpenAI-compatible API (SiliconFlow, OpenAI, etc.)

## Demo

> **Kanban Board** - Drag tasks between columns, manage subtasks inline

```
┌─── Todo ───────────┐ ┌─── In Progress ────┐ ┌─── Done ───────────┐
│ ┌ Today ──────────┐ │ │                    │ │                    │
│ │ [P1] Write paper│ │ │ [P0] Read thesis   │ │ [P2] Buy groceries │
│ │   ├ Intro  ░░░  │ │ │  14:00-16:00       │ │  ✓ 2026-04-17      │
│ │   └ Review ✓    │ │ │  belongs: Research │ │                    │
│ ├ Overdue ────────┤ │ │                    │ │                    │
│ │ [P2] Fix bug    │ │ │                    │ │                    │
│ ├ Future ─────────┤ │ │                    │ │                    │
│ │ [P3] Clean desk │ │ │                    │ │                    │
└────────────────────┘ └────────────────────┘ └────────────────────┘
```

> **AI Chat** - Just describe what you need

```
You: "Tomorrow afternoon at 3, team meeting for 1 hour"
AI:  "Created: Team Meeting, tomorrow 15:00-16:00, P1" ✓

You: "Move it to 4pm"
AI:  "Updated to 16:00-17:00" ✓

You: "Meeting is done"
AI:  "Marked as complete: Team Meeting" ✓
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Vue 3 + TypeScript + Naive UI + Pinia + Vite |
| **Backend** | FastAPI + SQLAlchemy (async) + aiosqlite |
| **Database** | SQLite |
| **AI** | OpenAI-compatible API (SiliconFlow, OpenAI, etc.) |

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- An OpenAI-compatible API key (e.g., [SiliconFlow](https://siliconflow.cn))

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/ai-schedule.git
cd ai-schedule
```

**Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and go to Settings to configure your AI API key.

### Configuration

On first launch, navigate to the **Settings** page to:

1. **Add AI Configuration** - Enter your API Key, Base URL, and Model name
2. **Activate** the configuration by clicking the config card
3. **Set Work Hours** - Define your daily work time range
4. **Manage Categories** - Add task categories for better organization

## Project Structure

```
ai-schedule/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── database.py          # Async SQLite setup
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── task.py          # Task with parent-child relations
│   │   │   ├── ai_config.py     # AI service configurations
│   │   │   └── setting.py       # App settings (work hours, etc.)
│   │   ├── routers/
│   │   │   ├── tasks.py         # Task CRUD endpoints
│   │   │   ├── ai.py            # AI chat, scheduling, suggestions
│   │   │   ├── calendar.py      # Calendar & free slots
│   │   │   ├── settings.py      # Settings management
│   │   │   └── ai_configs.py    # AI config management
│   │   ├── services/
│   │   │   ├── ai_service.py    # AI prompt engineering & API calls
│   │   │   ├── task_service.py  # Task business logic
│   │   │   └── calendar_service.py
│   │   ├── schemas/             # Pydantic models
│   │   └── utils/
│   │       └── holidays.py      # Chinese holiday detection
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── KanbanBoard.vue  # Kanban with drag-and-drop
│   │   │   ├── CalendarView.vue # Weekly calendar
│   │   │   ├── TaskCard.vue     # Task card with subtask support
│   │   │   ├── TaskForm.vue     # Create/edit task modal
│   │   │   ├── ChatPanel.vue    # AI chat interface
│   │   │   └── DailySuggestion.vue  # Daily focus popup
│   │   ├── stores/              # Pinia stores
│   │   ├── views/               # Dashboard & Settings pages
│   │   ├── api/                 # Axios API layer
│   │   └── types/               # TypeScript interfaces
│   └── package.json
└── README.md
```

## Core Concepts

### Task Hierarchy

Tasks support a parent-child relationship:

- **Parent tasks** act as containers — their status is automatically determined by their children
- **Subtasks** are full tasks that can be independently dragged to change status
- When all subtasks are completed, the parent auto-completes
- Unbinding a subtask's completion reverts the parent to "Todo"

### AI Actions

The AI assistant can execute these actions through natural conversation:

| Action | Trigger Examples |
|--------|-----------------|
| `create` | "Tomorrow 3pm, team meeting" |
| `update` | "Move it to 4pm", "Change priority to P0" |
| `delete` | "Cancel the meeting" |
| `reschedule` | "Find me a better time for this" |

The AI distinguishes between explicit time changes (`update`) and vague requests (`reschedule`). Explicit changes are applied directly; vague requests trigger the smart scheduling engine.

### Smart Scheduling

When the AI schedules a task, it considers:

- Current day's existing tasks and time conflicts
- Free time slots within work hours
- Task priority (high priority → morning slots)
- Future workload across the next 3 days
- Workdays vs. weekends vs. holidays

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | GET | List all tasks |
| `/api/tasks` | POST | Create a task |
| `/api/tasks/:id` | PUT | Update a task |
| `/api/tasks/:id` | DELETE | Delete a task |
| `/api/tasks/:id/status` | PATCH | Update task status |
| `/api/ai/chat` | POST | AI chat (single response) |
| `/api/ai/chat/stream` | POST | AI chat (SSE streaming) |
| `/api/ai/reschedule/:id` | POST | AI reschedule a task |
| `/api/ai/daily-suggestion/stream` | GET | Daily suggestion (SSE) |
| `/api/calendar/week` | GET | Weekly task view |
| `/api/calendar/free-slots` | GET | Available time slots |
| `/api/settings` | GET/PUT | App settings |
| `/api/ai-configs` | GET/POST | AI configurations |
| `/api/health` | GET | Health check |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Vue 3](https://vuejs.org/) - The progressive JavaScript framework
- [Naive UI](https://www.naiveui.com/) - A Vue 3 component library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SiliconFlow](https://siliconflow.cn/) - AI model API provider

---

<div align="center">

Built with AI, for better AI-powered productivity.

</div>
