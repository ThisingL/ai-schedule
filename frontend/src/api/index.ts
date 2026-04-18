import axios from 'axios'
import type { Task, ChatMessage } from '../types'

const api = axios.create({
  baseURL: '/api',
})

// 任务相关
export const taskApi = {
  list(params?: { date?: string; status?: string }) {
    return api.get<Task[]>('/tasks', { params })
  },
  get(id: number) {
    return api.get<Task>(`/tasks/${id}`)
  },
  create(data: Partial<Task>) {
    return api.post<Task>('/tasks', data)
  },
  update(id: number, data: Partial<Task>) {
    return api.put<Task>(`/tasks/${id}`, data)
  },
  delete(id: number) {
    return api.delete(`/tasks/${id}`)
  },
  updateStatus(id: number, status: string) {
    return api.patch<Task>(`/tasks/${id}/status`, { status })
  },
}

// AI 相关
export const aiApi = {
  chat(message: string, history: { role: string; content: string }[] = []) {
    return api.post<ChatMessage>('/ai/chat', { message, history })
  },
  schedule(taskId: number) {
    return api.post('/ai/schedule', { task_id: taskId })
  },
  reschedule(id: number, hint?: string) {
    return api.post(`/ai/reschedule/${id}`, { hint })
  },
  dailySuggestion() {
    return api.get('/ai/daily-suggestion')
  },
}

// 日历相关
export const calendarApi = {
  week(date: string) {
    return api.get('/calendar/week', { params: { date } })
  },
  day(date: string) {
    return api.get('/calendar/day', { params: { date } })
  },
  freeSlots(date?: string) {
    return api.get('/calendar/free-slots', { params: { date } })
  },
}

// 设置相关
export const settingsApi = {
  getAll() {
    return api.get('/settings')
  },
  update(data: Record<string, string>) {
    return api.put('/settings', data)
  },
}

// AI 配置相关
export const aiConfigApi = {
  list() {
    return api.get('/ai-configs')
  },
  create(data: { name: string; api_key: string; base_url: string; model: string }) {
    return api.post('/ai-configs', data)
  },
  update(id: number, data: { name?: string; api_key?: string; base_url?: string; model?: string }) {
    return api.put(`/ai-configs/${id}`, data)
  },
  delete(id: number) {
    return api.delete(`/ai-configs/${id}`)
  },
  activate(id: number) {
    return api.post(`/ai-configs/${id}/activate`)
  },
  test(data: { config_id?: number; api_key?: string; base_url?: string; model?: string }) {
    return api.post('/ai-configs/test', data)
  },
}
