<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { NButton, NEmpty, NTag } from 'naive-ui'
import TaskCard from './TaskCard.vue'
import TaskForm from './TaskForm.vue'
import type { Task } from '../types'
import { useTaskStore } from '../stores/taskStore'

const taskStore = useTaskStore()

const showForm = ref(false)
const editingTask = ref<Task | null>(null)
const addSubtaskParentId = ref<number | null>(null)

onMounted(() => taskStore.fetchTasks())

const today = computed(() => new Date().toISOString().slice(0, 10))

// 待办列：独立 todo 任务 + 有子任务的父任务（未全部完成）
const todoTasks = computed(() =>
  taskStore.tasks.filter(t => t.status === 'todo')
)
const todayTodo = computed(() => todoTasks.value.filter(t => t.scheduled_date === today.value))
const overdueTodo = computed(() => todoTasks.value.filter(t => t.scheduled_date < today.value))
const futureTodo = computed(() => todoTasks.value.filter(t => t.scheduled_date > today.value))

// 进行中列：独立 in_progress 任务 + 从父任务中提取的 in_progress 子任务
const inProgressIndependent = computed(() =>
  taskStore.tasks.filter(t => t.status === 'in_progress' && !(t.children?.length))
)
const inProgressSubtasks = computed(() => {
  const result: (Task & { _parentTitle?: string })[] = []
  for (const t of taskStore.tasks) {
    if (!t.children?.length) continue
    for (const c of t.children) {
      if (c.status === 'in_progress') {
        result.push({ ...c, children: [], _parentTitle: t.title } as Task & { _parentTitle?: string })
      }
    }
  }
  return result
})
const inProgressTasks = computed(() => [...inProgressIndependent.value, ...inProgressSubtasks.value])

// 已完成列：独立 done 任务 + 自动完成的父任务
const doneTasks = computed(() =>
  taskStore.tasks.filter(t => t.status === 'done')
)

async function changeStatus(taskId: number, status: string) {
  await taskStore.updateStatus(taskId, status)
}

async function handleSave(data: Partial<Task>) {
  if (data.id) {
    await taskStore.updateTask(data.id, data)
  } else {
    await taskStore.createTask(data)
  }
  showForm.value = false
  editingTask.value = null
  addSubtaskParentId.value = null
}

function openEdit(task: Task) {
  editingTask.value = task
  showForm.value = true
}

function openAddSubtask(parentId: number) {
  addSubtaskParentId.value = parentId
  editingTask.value = null
  showForm.value = true
}

async function handleDelete(id: number) {
  await taskStore.deleteTask(id)
}

function openNew() {
  editingTask.value = null
  addSubtaskParentId.value = null
  showForm.value = true
}

// Drag & drop
const dragOverColumn = ref<string | null>(null)
const dragOverTaskId = ref<number | null>(null)

function onColumnDragOver(e: DragEvent, status: string) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
  dragOverColumn.value = status
}

function onColumnDragLeave() {
  dragOverColumn.value = null
}

async function onColumnDrop(e: DragEvent, status: string) {
  e.preventDefault()
  dragOverColumn.value = null
  const taskId = e.dataTransfer?.getData('taskId')
  if (taskId) {
    await changeStatus(Number(taskId), status)
  }
}

// 拖拽到任务卡片上（绑定为子任务）
function onTaskDragOver(e: DragEvent, task: Task) {
  if (task.parent_id) return
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
  dragOverTaskId.value = task.id
}

function onTaskDragLeave() {
  dragOverTaskId.value = null
}

async function onTaskDrop(e: DragEvent, targetTask: Task) {
  e.preventDefault()
  e.stopPropagation()
  dragOverTaskId.value = null
  const taskId = e.dataTransfer?.getData('taskId')
  if (!taskId) return
  const id = Number(taskId)
  if (id === targetTask.id) return

  // 检查被拖的任务是否有子任务（有子任务不能变成子任务）
  const draggedTask = taskStore.tasks.find(t => t.id === id)
  if (draggedTask && draggedTask.children?.length) return

  // 绑定为目标任务的子任务
  await taskStore.updateTask(id, { parent_id: targetTask.id } as Partial<Task>)
}
</script>

<template>
  <div class="kanban">
    <!-- 待办列 -->
    <div
      class="kanban-column"
      :class="{ 'drag-over': dragOverColumn === 'todo' }"
      @dragover="onColumnDragOver($event, 'todo')"
      @dragleave="onColumnDragLeave"
      @drop="onColumnDrop($event, 'todo')"
    >
      <div class="column-header">
        <span class="column-title">待办</span>
        <n-tag size="small" :bordered="false" round>{{ todoTasks.length }}</n-tag>
        <n-button size="tiny" type="primary" circle @click="openNew" style="margin-left: auto">
          +
        </n-button>
      </div>
      <div class="column-body">
        <div class="section">
          <div class="section-label today-label">今日</div>
          <div class="section-list">
            <TaskCard
              v-for="t in todayTodo" :key="t.id" :task="t"
              :drop-target="!t.parent_id"
              :drag-over="dragOverTaskId === t.id"
              @edit="openEdit" @status-change="changeStatus"
              @delete="handleDelete"
              @task-drag-over="onTaskDragOver"
              @task-drag-leave="onTaskDragLeave"
              @task-drop="onTaskDrop"
            />
            <n-empty v-if="!todayTodo.length" description="暂无今日任务" size="small" style="padding: 12px 0" />
          </div>
        </div>
        <div class="section">
          <div class="section-label overdue-label">往期未完成</div>
          <div class="section-list">
            <TaskCard
              v-for="t in overdueTodo" :key="t.id" :task="t" :is-overdue="true" :show-date="true"
              :drop-target="!t.parent_id"
              :drag-over="dragOverTaskId === t.id"
              @edit="openEdit" @status-change="changeStatus"
              @delete="handleDelete"
              @task-drag-over="onTaskDragOver"
              @task-drag-leave="onTaskDragLeave"
              @task-drop="onTaskDrop"
            />
            <n-empty v-if="!overdueTodo.length" description="无逾期任务" size="small" style="padding: 12px 0" />
          </div>
        </div>
        <div class="section">
          <div class="section-label future-label">未来</div>
          <div class="section-list">
            <TaskCard
              v-for="t in futureTodo" :key="t.id" :task="t" :show-date="true"
              :drop-target="!t.parent_id"
              :drag-over="dragOverTaskId === t.id"
              @edit="openEdit" @status-change="changeStatus"
              @delete="handleDelete"
              @task-drag-over="onTaskDragOver"
              @task-drag-leave="onTaskDragLeave"
              @task-drop="onTaskDrop"
            />
            <n-empty v-if="!futureTodo.length" description="无未来任务" size="small" style="padding: 12px 0" />
          </div>
        </div>
      </div>
    </div>

    <!-- 进行中列 -->
    <div
      class="kanban-column"
      :class="{ 'drag-over': dragOverColumn === 'in_progress' }"
      @dragover="onColumnDragOver($event, 'in_progress')"
      @dragleave="onColumnDragLeave"
      @drop="onColumnDrop($event, 'in_progress')"
    >
      <div class="column-header">
        <span class="column-title">进行中</span>
        <n-tag size="small" :bordered="false" type="info" round>{{ inProgressTasks.length }}</n-tag>
      </div>
      <div class="column-body simple-list">
        <TaskCard
          v-for="t in inProgressTasks" :key="t.id" :task="t"
          :parent-title="(t as any)._parentTitle"
          @edit="openEdit" @status-change="changeStatus"
          @delete="handleDelete"
        />
        <n-empty v-if="!inProgressTasks.length" description="无进行中任务" size="small" style="padding: 20px 0" />
      </div>
    </div>

    <!-- 已完成列 -->
    <div
      class="kanban-column"
      :class="{ 'drag-over': dragOverColumn === 'done' }"
      @dragover="onColumnDragOver($event, 'done')"
      @dragleave="onColumnDragLeave"
      @drop="onColumnDrop($event, 'done')"
    >
      <div class="column-header">
        <span class="column-title">已完成</span>
        <n-tag size="small" :bordered="false" type="success" round>{{ doneTasks.length }}</n-tag>
      </div>
      <div class="column-body simple-list">
        <TaskCard
          v-for="t in doneTasks" :key="t.id" :task="t" :show-date="true"
          @edit="openEdit" @status-change="changeStatus"
          @delete="handleDelete"
        />
        <n-empty v-if="!doneTasks.length" description="暂无已完成任务" size="small" style="padding: 20px 0" />
      </div>
    </div>

    <TaskForm
      :visible="showForm"
      :task="editingTask"
      :parent-id="addSubtaskParentId"
      :default-date="today"
      @close="showForm = false; editingTask = null; addSubtaskParentId = null"
      @save="handleSave"
    />
  </div>
</template>

<style scoped>
.kanban {
  display: flex;
  gap: 16px;
  height: 100%;
  user-select: none;
}
.kanban-column {
  flex: 1;
  min-width: 280px;
  background: #f0f1f3;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}
.column-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 8px;
}
.simple-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.section {
  margin-bottom: 4px;
}
.section-label {
  font-size: 11px;
  color: #999;
  padding: 8px 6px 4px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: sticky;
  top: 0;
  background: #f0f1f3;
  z-index: 1;
}
.section-label.today-label { color: #1890ff; }
.section-label.overdue-label { color: #f0a020; }
.section-label.future-label { color: #18a058; }
.section-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.kanban-column.drag-over {
  background: #e6f7ff;
  outline: 2px dashed #1890ff;
  outline-offset: -2px;
}
</style>
