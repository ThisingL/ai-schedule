export interface Task {
  id: number
  parent_id: number | null
  title: string
  description: string | null
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  status: 'todo' | 'in_progress' | 'done'
  category: string | null
  scheduled_date: string
  start_time: string | null
  end_time: string | null
  estimated_minutes: number | null
  deadline: string | null
  is_ai_generated: boolean
  ai_priority_reason: string | null
  sort_order: number
  created_at: string
  updated_at: string
  children: Task[]
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  related_task_ids: number[] | null
  created_at: string
}

export interface Settings {
  [key: string]: string
}
