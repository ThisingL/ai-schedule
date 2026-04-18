<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  NModal, NCard, NForm, NFormItem, NInput, NButton,
  NSelect, NDatePicker, NTimePicker, NInputNumber, NSpace,
  NCheckbox, NText, NPopconfirm,
} from 'naive-ui'
import type { Task } from '../types'
import { useSettingsStore } from '../stores/settingsStore'
import { useTaskStore } from '../stores/taskStore'

const settingsStore = useSettingsStore()
const taskStore = useTaskStore()
const categoryOptions = computed(() =>
  settingsStore.categories.map(c => ({ label: c, value: c }))
)

// 从 store 响应式获取最新 task 数据（解绑/绑定后自动刷新）
const liveTask = computed(() => {
  if (!props.task) return null
  return taskStore.tasks.find(t => t.id === props.task!.id) || props.task
})

// 可绑定为子任务的候选列表：排除自身、已有子任务、以及本身已是别人子任务的
const bindableOptions = computed(() => {
  if (!liveTask.value) return []
  const selfId = liveTask.value.id
  const childIds = new Set((liveTask.value.children || []).map(c => c.id))
  return taskStore.tasks
    .filter(t => t.id !== selfId && !childIds.has(t.id) && !t.parent_id)
    .map(t => ({
      label: `[${t.priority}] ${t.title}（${t.scheduled_date}）`,
      value: t.id,
    }))
})

const selectedTaskId = ref<number | null>(null)

async function bindSubtask() {
  if (!selectedTaskId.value || !props.task) return
  await taskStore.updateTask(selectedTaskId.value, { parent_id: props.task.id } as Partial<Task>)
  selectedTaskId.value = null
}

async function unbindSubtask(childId: number) {
  await taskStore.updateTask(childId, { parent_id: null } as Partial<Task>)
}

async function toggleSubtask(child: Task, checked: boolean) {
  await taskStore.updateStatus(child.id, checked ? 'done' : 'todo')
}

const props = defineProps<{
  visible: boolean
  task?: Task | null
  parentId?: number | null
  defaultDate?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: Partial<Task>): void
}>()

const form = ref({
  title: '',
  description: '',
  priority: 'P2',
  status: 'todo',
  category: null as string | null,
  scheduled_date: '',
  start_time: null as string | null,
  end_time: null as string | null,
  estimated_minutes: null as number | null,
  deadline: null as string | null,
})

const datetimeFormat = "yyyy-MM-dd'T'HH:mm"

const statusOptions = [
  { label: '待办', value: 'todo' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'done' },
]

const priorityOptions = [
  { label: 'P0 紧急重要', value: 'P0' },
  { label: 'P1 重要不紧急', value: 'P1' },
  { label: 'P2 紧急不重要', value: 'P2' },
  { label: 'P3 不紧急不重要', value: 'P3' },
]

watch(() => props.visible, (v) => {
  if (v && props.task) {
    form.value = {
      title: props.task.title,
      description: props.task.description || '',
      priority: props.task.priority,
      status: props.task.status || 'todo',
      category: props.task.category || null,
      scheduled_date: props.task.scheduled_date,
      start_time: props.task.start_time?.slice(0, 5) || null,
      end_time: props.task.end_time?.slice(0, 5) || null,
      estimated_minutes: props.task.estimated_minutes,
      deadline: props.task.deadline?.slice(0, 16) || null,
    }
  } else if (v) {
    form.value = {
      title: '',
      description: '',
      priority: 'P2',
      status: 'todo',
      category: null,
      scheduled_date: props.defaultDate || new Date().toISOString().slice(0, 10),
      start_time: null,
      end_time: null,
      estimated_minutes: null,
      deadline: null,
    }
  }
})

function submit() {
  if (!form.value.title.trim()) return
  const data: Partial<Task> = {
    title: form.value.title,
    description: form.value.description || undefined,
    priority: form.value.priority as Task['priority'],
    status: form.value.status as Task['status'],
    category: form.value.category || undefined,
    scheduled_date: form.value.scheduled_date,
    start_time: form.value.start_time ?? undefined,
    end_time: form.value.end_time ?? undefined,
    estimated_minutes: form.value.estimated_minutes ?? undefined,
    deadline: form.value.deadline ?? undefined,
  }
  if (props.parentId) {
    data.parent_id = props.parentId
  }
  if (props.task) {
    data.id = props.task.id
  }
  emit('save', data)
}

function onUpdateShow(val: boolean) {
  if (!val) emit('close')
}
</script>

<template>
  <n-modal
    :show="visible"
    @update:show="onUpdateShow"
    :mask-closable="true"
    preset="card"
    :title="task ? '编辑任务' : (parentId ? '添加子任务' : '新建任务')"
    style="width: 520px; max-width: 90vw"
    :bordered="false"
    size="medium"
  >
    <n-form label-placement="top" :show-feedback="false">
      <n-form-item label="标题" required>
        <n-input v-model:value="form.title" placeholder="任务标题" />
      </n-form-item>

      <n-form-item label="描述">
        <n-input
          v-model:value="form.description"
          type="textarea"
          placeholder="任务描述（可选）"
          :rows="2"
        />
      </n-form-item>

      <n-space :size="12">
        <n-form-item label="优先级" style="flex: 1">
          <n-select
            v-model:value="form.priority"
            :options="priorityOptions"
            style="width: 180px"
          />
        </n-form-item>
        <n-form-item label="分类" style="flex: 1">
          <n-select
            v-model:value="form.category"
            :options="categoryOptions"
            placeholder="选择分类"
            clearable
            tag
            style="width: 180px"
          />
        </n-form-item>
      </n-space>

      <n-form-item v-if="task" label="状态">
        <n-select
          v-model:value="form.status"
          :options="statusOptions"
          style="width: 180px"
        />
      </n-form-item>

      <n-form-item label="计划日期" required>
        <n-date-picker
          v-model:formatted-value="form.scheduled_date"
          value-format="yyyy-MM-dd"
          type="date"
          style="width: 200px"
        />
      </n-form-item>

      <n-space :size="12">
        <n-form-item label="开始时间">
          <n-time-picker
            v-model:formatted-value="form.start_time"
            value-format="HH:mm"
            format="HH:mm"
            :actions="[]"
            style="width: 160px"
          />
        </n-form-item>
        <n-form-item label="结束时间">
          <n-time-picker
            v-model:formatted-value="form.end_time"
            value-format="HH:mm"
            format="HH:mm"
            :actions="[]"
            style="width: 160px"
          />
        </n-form-item>
      </n-space>

      <n-space :size="12">
        <n-form-item label="预估耗时(分钟)">
          <n-input-number
            v-model:value="form.estimated_minutes"
            :min="1"
            placeholder="如 60"
            style="width: 160px"
          />
        </n-form-item>
        <n-form-item label="截止日期">
          <n-date-picker
            v-model:formatted-value="form.deadline"
            :value-format="datetimeFormat"
            type="datetime"
            style="width: 220px"
          />
        </n-form-item>
      </n-space>
    </n-form>

    <!-- 子任务区域（仅编辑模式） -->
    <div v-if="liveTask" class="subtask-section">
      <div class="subtask-header">子任务</div>
      <div v-if="liveTask.children?.length" class="subtask-list">
        <div v-for="child in liveTask.children" :key="child.id" class="subtask-item">
          <n-checkbox
            :checked="child.status === 'done'"
            @update:checked="(val: boolean) => toggleSubtask(child, val)"
            size="small"
          >
            <n-text
              :depth="child.status === 'done' ? 3 : 1"
              :delete="child.status === 'done'"
              style="font-size: 13px"
            >
              {{ child.title }}
            </n-text>
          </n-checkbox>
          <n-popconfirm
            @positive-click="unbindSubtask(child.id)"
            positive-text="解绑"
            negative-text="取消"
          >
            <template #trigger>
              <n-button quaternary size="tiny" class="subtask-delete">解绑</n-button>
            </template>
            将此任务从子任务中移除？（任务本身不会被删除）
          </n-popconfirm>
        </div>
      </div>
      <div class="subtask-add">
        <n-select
          v-model:value="selectedTaskId"
          :options="bindableOptions"
          placeholder="选择已有任务绑定为子任务"
          size="small"
          filterable
          clearable
          style="flex: 1"
        />
        <n-button size="small" type="primary" :disabled="!selectedTaskId" @click="bindSubtask">
          绑定
        </n-button>
      </div>
    </div>

    <template #footer>
      <n-space justify="end" :size="8">
        <n-button @click="emit('close')">取消</n-button>
        <n-button type="primary" @click="submit">
          {{ task ? '保存' : '创建' }}
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<style scoped>
.subtask-section {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e8e8e8;
}
.subtask-header {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}
.subtask-list {
  margin-bottom: 8px;
}
.subtask-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}
.subtask-delete {
  opacity: 0;
  font-size: 16px;
  transition: opacity 0.2s;
}
.subtask-item:hover .subtask-delete {
  opacity: 1;
}
.subtask-add {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
