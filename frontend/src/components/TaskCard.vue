<script setup lang="ts">
import { computed } from 'vue'
import {
  NCard, NTag, NProgress, NButton,
  NPopconfirm, NSpace, NText,
} from 'naive-ui'
import type { Task } from '../types'

const props = defineProps<{
  task: Task
  showDate?: boolean
  isOverdue?: boolean
  parentTitle?: string
  dropTarget?: boolean
  dragOver?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', task: Task): void
  (e: 'statusChange', taskId: number, status: string): void
  (e: 'delete', taskId: number): void
  (e: 'taskDragOver', event: DragEvent, task: Task): void
  (e: 'taskDragLeave'): void
  (e: 'taskDrop', event: DragEvent, task: Task): void
}>()

const hasChildren = computed(() => !!(props.task.children?.length))
// 父任务不可拖动
const isDraggable = computed(() => !hasChildren.value)

const priorityType = computed((): 'error' | 'warning' | 'info' | 'default' => {
  const map: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
    P0: 'error', P1: 'warning', P2: 'info', P3: 'default',
  }
  return map[props.task.priority] || 'default'
})

function childPriorityType(priority: string): 'error' | 'warning' | 'info' | 'default' {
  const map: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
    P0: 'error', P1: 'warning', P2: 'info', P3: 'default',
  }
  return map[priority] || 'default'
}

const statusLabel: Record<string, { text: string; type: 'info' | 'success' | 'default' }> = {
  todo: { text: '待办', type: 'default' },
  in_progress: { text: '进行中', type: 'info' },
  done: { text: '已完成', type: 'success' },
}

const timeDisplay = computed(() => {
  if (props.task.start_time && props.task.end_time) {
    return `${props.task.start_time.slice(0, 5)} - ${props.task.end_time.slice(0, 5)}`
  }
  return null
})

const childDone = computed(() => {
  if (!props.task.children?.length) return 0
  return props.task.children.filter(c => c.status === 'done').length
})

const childTotal = computed(() => props.task.children?.length || 0)

const childPercent = computed(() => {
  if (!childTotal.value) return 0
  return Math.round((childDone.value / childTotal.value) * 100)
})

function onDragStart(e: DragEvent) {
  if (!isDraggable.value) {
    e.preventDefault()
    return
  }
  if (e.dataTransfer) {
    e.dataTransfer.setData('taskId', String(props.task.id))
    e.dataTransfer.effectAllowed = 'move'
  }
  ;(e.currentTarget as HTMLElement).style.opacity = '0.4'
}

function onChildDragStart(e: DragEvent, child: Task) {
  e.stopPropagation()
  if (e.dataTransfer) {
    e.dataTransfer.setData('taskId', String(child.id))
    e.dataTransfer.effectAllowed = 'move'
  }
  ;(e.currentTarget as HTMLElement).style.opacity = '0.4'
}
</script>

<template>
  <n-card
    size="small"
    hoverable
    class="task-card"
    :class="{
      overdue: isOverdue,
      done: task.status === 'done',
      'not-draggable': !isDraggable,
      'drop-highlight': dragOver,
    }"
    :draggable="isDraggable"
    @dragstart="onDragStart"
    @dragend="(e: DragEvent) => { (e.currentTarget as HTMLElement).style.opacity = '1' }"
    @click="emit('edit', task)"
    @dragover="dropTarget ? emit('taskDragOver', $event, task) : undefined"
    @dragleave="dropTarget ? emit('taskDragLeave') : undefined"
    @drop="dropTarget ? emit('taskDrop', $event, task) : undefined"
  >
    <!-- Parent label (for subtasks shown independently) -->
    <n-tag v-if="parentTitle" size="tiny" :bordered="false" type="warning" class="parent-label">
      属于: {{ parentTitle }}
    </n-tag>

    <!-- Header: priority + title + delete -->
    <div class="card-header">
      <n-tag :type="priorityType" size="small" :bordered="false" round>
        {{ task.priority }}
      </n-tag>
      <span class="task-title">{{ task.title }}</span>
      <n-popconfirm
        v-if="!hasChildren"
        @positive-click="emit('delete', task.id)"
        positive-text="删除"
        negative-text="取消"
      >
        <template #trigger>
          <n-button quaternary size="tiny" class="delete-btn" @click.stop>
            &times;
          </n-button>
        </template>
        确定删除此任务？
      </n-popconfirm>
    </div>

    <!-- Meta tags -->
    <n-space :size="4" style="margin-top: 8px" v-if="timeDisplay || task.estimated_minutes || task.category || showDate">
      <n-tag v-if="timeDisplay" size="tiny" :bordered="false" type="info">
        {{ timeDisplay }}
      </n-tag>
      <n-tag v-if="task.estimated_minutes" size="tiny" :bordered="false">
        {{ task.estimated_minutes }}分钟
      </n-tag>
      <n-tag v-if="task.category" size="tiny" :bordered="false" type="success">
        {{ task.category }}
      </n-tag>
      <n-tag v-if="showDate" size="tiny" :bordered="false" type="warning">
        {{ task.scheduled_date }}
      </n-tag>
    </n-space>

    <!-- Overdue badge -->
    <n-tag v-if="isOverdue" size="tiny" type="warning" class="overdue-badge">
      逾期
    </n-tag>

    <!-- Child progress -->
    <div v-if="childTotal" class="child-progress">
      <n-text depth="3" style="font-size: 12px">
        子任务 {{ childDone }}/{{ childTotal }} 已完成
      </n-text>
      <n-progress
        :percentage="childPercent"
        :show-indicator="false"
        :height="4"
        type="line"
        status="success"
      />
    </div>

    <!-- Subtask cards -->
    <div v-if="task.children?.length" class="subtask-list">
      <div
        v-for="child in task.children"
        :key="child.id"
        class="subtask-card"
        :class="{ done: child.status === 'done' }"
        draggable="true"
        @dragstart="onChildDragStart($event, child as Task)"
        @dragend="(e: DragEvent) => { (e.currentTarget as HTMLElement).style.opacity = '1' }"
        @click.stop="emit('edit', child as Task)"
      >
        <n-tag :type="childPriorityType(child.priority)" size="tiny" :bordered="false" round>
          {{ child.priority }}
        </n-tag>
        <span class="subtask-title" :class="{ done: child.status === 'done' }">
          {{ child.title }}
        </span>
        <n-tag size="tiny" :bordered="false" :type="statusLabel[child.status]?.type || 'default'">
          {{ statusLabel[child.status]?.text || child.status }}
        </n-tag>
      </div>
    </div>
  </n-card>
</template>

<style scoped>
.task-card {
  cursor: pointer;
  position: relative;
}
.task-card.not-draggable {
  cursor: default;
}
.task-card.overdue {
  border-left: 3px solid #f0a020;
}
.task-card.done {
  opacity: 0.6;
}
.task-card.drop-highlight {
  outline: 2px dashed #1890ff;
  outline-offset: -2px;
  background: #e6f7ff;
}

.parent-label {
  margin-bottom: 6px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.task-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
  font-size: 16px;
}
.task-card:hover .delete-btn {
  opacity: 1;
}

.overdue-badge {
  position: absolute;
  top: 8px;
  right: 8px;
}

.child-progress {
  margin-top: 8px;
}
.subtask-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.subtask-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: grab;
  transition: background 0.15s, box-shadow 0.15s;
}
.subtask-card:hover {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.subtask-card.done {
  opacity: 0.6;
}
.subtask-title {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.subtask-title.done {
  text-decoration: line-through;
  color: #999;
}
</style>
