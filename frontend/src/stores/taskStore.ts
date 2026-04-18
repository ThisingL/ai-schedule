import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Task } from '../types'
import { taskApi } from '../api'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)

  async function fetchTasks(params?: { date?: string; status?: string }) {
    loading.value = true
    try {
      const { data } = await taskApi.list(params)
      tasks.value = data
    } finally {
      loading.value = false
    }
  }

  async function createTask(task: Partial<Task>) {
    const { data } = await taskApi.create(task)
    await fetchTasks()
    return data
  }

  async function updateTask(id: number, task: Partial<Task>) {
    const { data } = await taskApi.update(id, task)
    await fetchTasks()
    return data
  }

  async function deleteTask(id: number) {
    await taskApi.delete(id)
    await fetchTasks()
  }

  async function updateStatus(id: number, status: string) {
    const { data } = await taskApi.updateStatus(id, status)
    await fetchTasks()
    return data
  }

  return { tasks, loading, fetchTasks, createTask, updateTask, deleteTask, updateStatus }
})
