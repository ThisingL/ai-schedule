<script setup lang="ts">
import { computed, ref } from 'vue'
import { NButton, NButtonGroup, NPopover, NTag, NText, NSpace } from 'naive-ui'
import type { Task } from '../types'
import { useTaskStore } from '../stores/taskStore'
import TaskForm from './TaskForm.vue'

const taskStore = useTaskStore()
const showForm = ref(false)
const editingTask = ref<Task | null>(null)
const clickedDate = ref('')
const clickedTime = ref('')

const weekStart = ref(getMonday(new Date()))

function getMonday(d: Date): string {
  const date = new Date(d)
  const day = date.getDay()
  const diff = date.getDate() - day + (day === 0 ? -6 : 1)
  date.setDate(diff)
  return date.toISOString().slice(0, 10)
}

const weekDays = computed(() => {
  const days: { date: string; label: string; dayName: string; dayNum: string; isToday: boolean }[] = []
  const start = new Date(weekStart.value)
  const today = new Date().toISOString().slice(0, 10)
  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  for (let i = 0; i < 7; i++) {
    const d = new Date(start)
    d.setDate(d.getDate() + i)
    const dateStr = d.toISOString().slice(0, 10)
    days.push({
      date: dateStr,
      label: `${dayNames[i]} ${d.getMonth() + 1}/${d.getDate()}`,
      dayName: dayNames[i],
      dayNum: `${d.getMonth() + 1}/${d.getDate()}`,
      isToday: dateStr === today,
    })
  }
  return days
})

const hours = Array.from({ length: 24 }, (_, i) => i)

const calendarTasks = computed(() => {
  return taskStore.tasks
    .flatMap(t => {
      const items: Task[] = []
      if (t.status === 'in_progress' && t.start_time && t.end_time) items.push(t)
      if (t.children) {
        for (const c of t.children) {
          if (c.status === 'in_progress' && c.start_time && c.end_time) items.push(c as Task)
        }
      }
      return items
    })
})

function getTasksForDay(date: string) {
  return calendarTasks.value.filter(t => t.scheduled_date === date)
}

function getTaskStyle(task: Task) {
  if (!task.start_time || !task.end_time) return {}
  const [sh, sm] = task.start_time.split(':').map(Number)
  const [eh, em] = task.end_time.split(':').map(Number)
  const top = (sh * 60 + sm) / (24 * 60) * 100
  const height = ((eh * 60 + em) - (sh * 60 + sm)) / (24 * 60) * 100
  return {
    top: `${top}%`,
    height: `${Math.max(height, 1.5)}%`,
  }
}

const priorityColors: Record<string, string> = {
  P0: '#fff1f0', P1: '#fff7e6', P2: '#e6f7ff', P3: '#f5f5f5',
}
const priorityBorders: Record<string, string> = {
  P0: '#ffa39e', P1: '#ffd591', P2: '#91d5ff', P3: '#d9d9d9',
}

function prevWeek() {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() - 7)
  weekStart.value = d.toISOString().slice(0, 10)
}
function nextWeek() {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + 7)
  weekStart.value = d.toISOString().slice(0, 10)
}
function goToday() {
  weekStart.value = getMonday(new Date())
}

function onCellClick(date: string, hour: number) {
  clickedDate.value = date
  clickedTime.value = `${String(hour).padStart(2, '0')}:00`
  editingTask.value = null
  showForm.value = true
}

function onTaskClick(task: Task) {
  editingTask.value = task
  showForm.value = true
}

async function handleSave(data: Partial<Task>) {
  if (data.id) {
    await taskStore.updateTask(data.id, data)
  } else {
    data.status = 'in_progress'
    if (!data.start_time && clickedTime.value) {
      data.start_time = clickedTime.value
      const h = parseInt(clickedTime.value.split(':')[0])
      data.end_time = `${String(Math.min(h + 1, 23)).padStart(2, '0')}:00`
    }
    await taskStore.createTask(data)
  }
  showForm.value = false
}
</script>

<template>
  <div class="calendar-view">
    <div class="cal-header">
      <n-button-group size="small">
        <n-button @click="prevWeek">&lt;</n-button>
        <n-button @click="goToday" strong>今天</n-button>
        <n-button @click="nextWeek">&gt;</n-button>
      </n-button-group>
      <n-text depth="3" style="margin-left: 12px; font-size: 14px">
        {{ weekDays[0]?.date }} ~ {{ weekDays[6]?.date }}
      </n-text>
    </div>

    <div class="cal-grid">
      <!-- 时间列 -->
      <div class="time-column">
        <div class="day-header-cell"></div>
        <div class="time-body">
          <div v-for="h in hours" :key="h" class="time-label">
            {{ String(h).padStart(2, '0') }}:00
          </div>
        </div>
      </div>

      <!-- 每天一列 -->
      <div
        v-for="day in weekDays" :key="day.date"
        class="day-column"
        :class="{ today: day.isToday }"
      >
        <div class="day-header-cell" :class="{ today: day.isToday }">
          <div class="day-name">{{ day.dayName }}</div>
          <div class="day-num" :class="{ today: day.isToday }">{{ day.dayNum }}</div>
        </div>
        <div class="day-body">
          <div
            v-for="h in hours" :key="h"
            class="hour-cell"
            @click="onCellClick(day.date, h)"
          />
          <!-- 任务块 -->
          <n-popover
            v-for="task in getTasksForDay(day.date)"
            :key="task.id"
            trigger="hover"
            placement="right"
          >
            <template #trigger>
              <div
                class="cal-task"
                :style="{
                  ...getTaskStyle(task),
                  background: priorityColors[task.priority] || '#e6f7ff',
                  borderLeft: '3px solid ' + (priorityBorders[task.priority] || '#91d5ff'),
                }"
                @click.stop="onTaskClick(task)"
              >
                <div class="cal-task-title">{{ task.title }}</div>
                <div class="cal-task-time">
                  {{ task.start_time?.slice(0, 5) }} - {{ task.end_time?.slice(0, 5) }}
                </div>
              </div>
            </template>
            <n-space vertical :size="4">
              <n-text strong>{{ task.title }}</n-text>
              <n-text depth="3">{{ task.start_time?.slice(0, 5) }} - {{ task.end_time?.slice(0, 5) }}</n-text>
              <n-tag v-if="task.priority" :type="task.priority === 'P0' ? 'error' : task.priority === 'P1' ? 'warning' : 'info'" size="small">
                {{ task.priority }}
              </n-tag>
              <n-text v-if="task.description" depth="2" style="font-size: 12px">{{ task.description }}</n-text>
            </n-space>
          </n-popover>
        </div>
      </div>
    </div>

    <TaskForm
      :visible="showForm"
      :task="editingTask"
      :default-date="clickedDate || weekDays[0]?.date"
      @close="showForm = false; editingTask = null"
      @save="handleSave"
    />
  </div>
</template>

<style scoped>
.calendar-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.cal-header {
  display: flex;
  align-items: center;
  padding: 8px 0;
  flex-shrink: 0;
}

.cal-grid {
  flex: 1;
  display: flex;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  background: #fff;
}

.time-column {
  width: 56px;
  flex-shrink: 0;
  border-right: 1px solid #e8e8e8;
}
.day-header-cell {
  height: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}
.day-header-cell.today {
  background: #e6f7ff;
}
.day-name {
  font-size: 11px;
  color: #888;
}
.day-num {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.day-num.today {
  color: #1890ff;
}

.time-body {
  position: relative;
}
.time-label {
  height: 40px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  font-size: 11px;
  color: #aaa;
  padding-top: 2px;
  border-bottom: 1px solid #f5f5f5;
}

.day-column {
  flex: 1;
  min-width: 100px;
  border-right: 1px solid #f0f0f0;
}
.day-column:last-child { border-right: none; }
.day-column.today { background: #fafffe; }

.day-body {
  position: relative;
}
.hour-cell {
  height: 40px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background 0.15s;
}
.hour-cell:hover { background: rgba(24, 144, 255, 0.04); }

.cal-task {
  position: absolute;
  left: 2px;
  right: 2px;
  border-radius: 6px;
  padding: 4px 6px;
  cursor: pointer;
  overflow: hidden;
  z-index: 1;
  font-size: 12px;
  transition: box-shadow 0.2s, transform 0.15s;
}
.cal-task:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  transform: scale(1.01);
}
.cal-task-title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cal-task-time { color: #888; font-size: 11px; }
</style>
