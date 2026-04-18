<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NPageHeader, NCard, NForm, NFormItem, NInput, NButton,
  NTimePicker, NDynamicTags, NSpace, NSpin, NTag, NDescriptions,
  NDescriptionsItem, NPopconfirm, NAlert, NEmpty, NDivider,
  useMessage,
} from 'naive-ui'
import { settingsApi, aiConfigApi } from '../api'

const router = useRouter()
const message = useMessage()

// AI configs
interface AiConfigItem {
  id: number
  name: string
  api_key_display: string
  base_url: string
  model: string
  is_active: boolean
}

const configs = ref<AiConfigItem[]>([])
const loadingConfigs = ref(true)
const showAddForm = ref(false)
const editingId = ref<number | null>(null)
const testingId = ref<number | null>(null)

const addForm = ref({ name: '', api_key: '', base_url: 'https://api.siliconflow.cn/v1', model: 'deepseek-ai/DeepSeek-V3' })
const editForm = ref({ name: '', api_key: '', base_url: '', model: '' })

// Other settings
const form = ref({
  work_hours_start: '09:00',
  work_hours_end: '18:00',
  categories: ['工作', '学习', '生活', '健康'] as string[],
})
const saving = ref(false)
const loading = ref(true)

async function loadConfigs() {
  loadingConfigs.value = true
  try {
    const { data } = await aiConfigApi.list()
    configs.value = data
  } catch {}
  loadingConfigs.value = false
}

async function loadSettings() {
  try {
    const { data } = await settingsApi.getAll()
    if (data.work_hours) {
      try {
        const wh = JSON.parse(data.work_hours)
        form.value.work_hours_start = wh.start || '09:00'
        form.value.work_hours_end = wh.end || '18:00'
      } catch {}
    }
    if (data.categories) {
      try {
        const cats = JSON.parse(data.categories)
        if (Array.isArray(cats)) form.value.categories = cats
      } catch {}
    }
  } catch {}
  loading.value = false
}

onMounted(() => {
  loadConfigs()
  loadSettings()
})

// Add config
function openAddForm() {
  addForm.value = { name: '', api_key: '', base_url: 'https://api.siliconflow.cn/v1', model: 'deepseek-ai/DeepSeek-V3' }
  showAddForm.value = true
  editingId.value = null
}

async function submitAdd() {
  if (!addForm.value.name.trim()) { message.warning('请输入配置名称'); return }
  if (!addForm.value.api_key.trim()) { message.warning('请输入 API Key'); return }
  try {
    await aiConfigApi.create(addForm.value)
    message.success('配置已创建')
    showAddForm.value = false
    await loadConfigs()
  } catch {
    message.error('创建失败')
  }
}

// Edit config
function startEdit(c: AiConfigItem) {
  editingId.value = c.id
  editForm.value = { name: c.name, api_key: '', base_url: c.base_url, model: c.model }
  showAddForm.value = false
}

async function submitEdit() {
  if (!editingId.value) return
  if (!editForm.value.name.trim()) { message.warning('请输入配置名称'); return }
  try {
    const payload: Record<string, string> = {
      name: editForm.value.name,
      base_url: editForm.value.base_url,
      model: editForm.value.model,
    }
    if (editForm.value.api_key) payload.api_key = editForm.value.api_key
    await aiConfigApi.update(editingId.value, payload)
    message.success('配置已更新')
    editingId.value = null
    await loadConfigs()
  } catch {
    message.error('更新失败')
  }
}

// Delete config
async function deleteConfig(id: number) {
  try {
    await aiConfigApi.delete(id)
    message.success('配置已删除')
    if (editingId.value === id) editingId.value = null
    await loadConfigs()
  } catch {
    message.error('删除失败')
  }
}

// Activate config
async function activateConfig(id: number) {
  try {
    await aiConfigApi.activate(id)
    message.success('已切换配置')
    await loadConfigs()
  } catch {
    message.error('切换失败')
  }
}

// Test config
async function testConfig(c: AiConfigItem) {
  testingId.value = c.id
  try {
    const { data } = await aiConfigApi.test({ config_id: c.id })
    if (data.ok) {
      message.success(data.message)
    } else {
      message.error(data.message)
    }
  } catch {
    message.error('测试请求失败')
  } finally {
    testingId.value = null
  }
}

// Test from add/edit form
async function testFormConfig(formData: { api_key: string; base_url: string; model: string }) {
  if (!formData.api_key && !editingId.value) { message.warning('请先输入 API Key'); return }
  testingId.value = -1
  try {
    const payload: Record<string, any> = {
      base_url: formData.base_url,
      model: formData.model,
    }
    if (formData.api_key) payload.api_key = formData.api_key
    if (editingId.value && !formData.api_key) payload.config_id = editingId.value
    const { data } = await aiConfigApi.test(payload)
    if (data.ok) {
      message.success(data.message)
    } else {
      message.error(data.message)
    }
  } catch {
    message.error('测试请求失败')
  } finally {
    testingId.value = null
  }
}

// Save other settings
async function saveOtherSettings() {
  saving.value = true
  try {
    await settingsApi.update({
      work_hours: JSON.stringify({
        start: form.value.work_hours_start,
        end: form.value.work_hours_end,
      }),
      categories: JSON.stringify(form.value.categories),
    })
    message.success('保存成功')
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <n-page-header title="设置" @back="router.push('/')" />

    <n-space vertical :size="20" style="margin-top: 20px">

      <!-- AI 服务配置 -->
      <n-card size="medium">
        <template #header>
          <n-space align="center" justify="space-between" style="width: 100%">
            <span>AI 服务配置</span>
            <n-button size="small" type="primary" @click="openAddForm" v-if="!showAddForm">
              + 新增配置
            </n-button>
          </n-space>
        </template>

        <!-- 新增表单 -->
        <n-card v-if="showAddForm" size="small" style="margin-bottom: 16px" :bordered="true">
          <template #header><span style="font-size: 14px">新增 AI 配置</span></template>
          <n-form label-placement="left" label-width="110" :show-feedback="false">
            <n-form-item label="配置名称">
              <n-input v-model:value="addForm.name" placeholder="如：SiliconFlow DeepSeek-V3" />
            </n-form-item>
            <n-form-item label="API Key">
              <n-input v-model:value="addForm.api_key" type="password" show-password-on="click" placeholder="请输入 API Key" />
            </n-form-item>
            <n-form-item label="API 接口地址">
              <n-input v-model:value="addForm.base_url" placeholder="https://api.siliconflow.cn/v1" />
            </n-form-item>
            <n-form-item label="模型名称">
              <n-input v-model:value="addForm.model" placeholder="deepseek-ai/DeepSeek-V3" />
            </n-form-item>
          </n-form>
          <n-space :size="8" style="margin-top: 8px">
            <n-button type="primary" size="small" @click="submitAdd">创建</n-button>
            <n-button size="small" :loading="testingId === -1" @click="testFormConfig(addForm)" type="info" secondary>
              测试连接
            </n-button>
            <n-button size="small" @click="showAddForm = false">取消</n-button>
          </n-space>
        </n-card>

        <!-- 配置列表 -->
        <n-spin :show="loadingConfigs">
          <n-empty v-if="!configs.length && !loadingConfigs" description="暂无 AI 配置，点击上方按钮添加" />

          <n-space vertical :size="12">
            <n-card
              v-for="c in configs"
              :key="c.id"
              size="small"
              :bordered="true"
              :class="{ 'active-config': c.is_active }"
              class="config-card"
              @click="!c.is_active && editingId !== c.id && activateConfig(c.id)"
            >
              <!-- 展示模式 -->
              <template v-if="editingId !== c.id">
                <div class="config-header">
                  <n-space align="center" :size="8">
                    <span class="config-name">{{ c.name }}</span>
                    <n-tag v-if="c.is_active" type="success" size="small" round>当前使用</n-tag>
                  </n-space>
                </div>
                <n-descriptions :column="1" size="small" label-placement="left" class="config-desc">
                  <n-descriptions-item label="API Key">
                    <code class="config-value">{{ c.api_key_display }}</code>
                  </n-descriptions-item>
                  <n-descriptions-item label="接口地址">
                    <code class="config-value">{{ c.base_url }}</code>
                  </n-descriptions-item>
                  <n-descriptions-item label="模型">
                    <code class="config-value">{{ c.model }}</code>
                  </n-descriptions-item>
                </n-descriptions>
                <n-space :size="8" style="margin-top: 10px" @click.stop>
                  <n-button size="tiny" @click="startEdit(c)">编辑</n-button>
                  <n-button size="tiny" type="info" secondary :loading="testingId === c.id" @click="testConfig(c)">
                    测试连接
                  </n-button>
                  <n-popconfirm @positive-click="deleteConfig(c.id)" positive-text="确认删除" negative-text="取消">
                    <template #trigger>
                      <n-button size="tiny" type="error" secondary>删除</n-button>
                    </template>
                    确定删除「{{ c.name }}」配置？
                  </n-popconfirm>
                </n-space>
              </template>

              <!-- 编辑模式 -->
              <template v-else>
                <n-form label-placement="left" label-width="110" :show-feedback="false">
                  <n-form-item label="配置名称">
                    <n-input v-model:value="editForm.name" placeholder="配置名称" />
                  </n-form-item>
                  <n-form-item label="API Key">
                    <n-input v-model:value="editForm.api_key" type="password" show-password-on="click" placeholder="留空则不修改" />
                  </n-form-item>
                  <n-form-item label="API 接口地址">
                    <n-input v-model:value="editForm.base_url" placeholder="https://api.siliconflow.cn/v1" />
                  </n-form-item>
                  <n-form-item label="模型名称">
                    <n-input v-model:value="editForm.model" placeholder="deepseek-ai/DeepSeek-V3" />
                  </n-form-item>
                </n-form>
                <n-space :size="8" style="margin-top: 8px">
                  <n-button type="primary" size="small" @click="submitEdit">保存</n-button>
                  <n-button size="small" :loading="testingId === -1" @click="testFormConfig(editForm)" type="info" secondary>
                    测试连接
                  </n-button>
                  <n-button size="small" @click="editingId = null">取消</n-button>
                </n-space>
              </template>
            </n-card>
          </n-space>
        </n-spin>
      </n-card>

      <!-- 工作时间 -->
      <n-card title="工作时间" size="medium">
        <n-spin :show="loading">
          <n-form label-placement="left" label-width="120" :show-feedback="false">
            <n-form-item label="开始时间">
              <n-time-picker
                v-model:formatted-value="form.work_hours_start"
                value-format="HH:mm"
                format="HH:mm"
                :actions="[]"
                style="width: 200px"
              />
            </n-form-item>
            <n-form-item label="结束时间">
              <n-time-picker
                v-model:formatted-value="form.work_hours_end"
                value-format="HH:mm"
                format="HH:mm"
                :actions="[]"
                style="width: 200px"
              />
            </n-form-item>
          </n-form>
        </n-spin>
      </n-card>

      <!-- 分类标签 -->
      <n-card title="分类标签" size="medium">
        <n-dynamic-tags v-model:value="form.categories" />
      </n-card>

      <!-- 保存其他设置 -->
      <div class="save-area">
        <n-button type="primary" :loading="saving" @click="saveOtherSettings" size="large">
          保存设置
        </n-button>
      </div>
    </n-space>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px;
}
.config-card {
  transition: border-color 0.2s, box-shadow 0.2s;
  cursor: pointer;
}
.config-card:hover:not(.active-config) {
  border-color: #1890ff;
  box-shadow: 0 0 0 1px rgba(24, 144, 255, 0.2);
}
.config-card.active-config {
  border-color: #18a058;
  background: #f6ffed;
}
.config-header {
  margin-bottom: 8px;
}
.config-name {
  font-size: 15px;
  font-weight: 600;
}
.config-desc {
  margin-top: 4px;
}
.config-value {
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
}
.save-area {
  display: flex;
  justify-content: flex-end;
}
</style>
