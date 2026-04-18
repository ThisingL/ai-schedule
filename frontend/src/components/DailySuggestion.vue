<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NButton } from 'naive-ui'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: true })

const CACHE_KEY = 'daily_suggestion'
const DISMISS_KEY = 'daily_suggestion_dismissed'
const suggestion = ref('')
const loading = ref(false)
const visible = ref(false)

const renderedHtml = computed(() => suggestion.value ? md.render(suggestion.value) : '')

function getTodayStr() {
  return new Date().toISOString().slice(0, 10)
}

function isDismissedToday(): boolean {
  try {
    return localStorage.getItem(DISMISS_KEY) === getTodayStr()
  } catch { return false }
}

function loadCache(): string | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const { date, text } = JSON.parse(raw)
    if (date === getTodayStr() && text) return text
  } catch {}
  return null
}

function saveCache(text: string) {
  localStorage.setItem(CACHE_KEY, JSON.stringify({ date: getTodayStr(), text }))
}

function dismiss() {
  visible.value = false
  localStorage.setItem(DISMISS_KEY, getTodayStr())
}

async function fetchSuggestionStream() {
  loading.value = true
  suggestion.value = ''

  try {
    const resp = await fetch('/api/ai/daily-suggestion/stream')
    if (!resp.ok || !resp.body) throw new Error('stream failed')

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'token') {
            suggestion.value += data.content
          }
        } catch {}
      }
    }

    if (suggestion.value) saveCache(suggestion.value)
  } catch {
    if (!suggestion.value) suggestion.value = 'AI 服务暂时不可用'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (isDismissedToday()) return

  const cached = loadCache()
  if (cached) {
    suggestion.value = cached
    visible.value = true
  } else {
    visible.value = true
    fetchSuggestionStream()
  }
})
</script>

<template>
  <Transition name="slide-fade">
    <div v-if="visible" class="suggestion-overlay" @click.self="dismiss">
      <div class="suggestion-card">
        <div class="card-header">
          <span class="card-title">&#9733; 今日聚焦建议</span>
          <button class="close-btn" @click="dismiss">&times;</button>
        </div>
        <div class="card-body">
          <div v-if="suggestion" class="md-content" v-html="renderedHtml" />
          <div v-else-if="loading" class="loading-text">
            正在生成建议<span class="cursor-blink">...</span>
          </div>
        </div>
        <div class="card-footer">
          <n-button size="small" type="primary" @click="dismiss">知道了</n-button>
          <n-button size="small" quaternary @click="fetchSuggestionStream" :loading="loading">
            换一个
          </n-button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.suggestion-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
}

.suggestion-card {
  width: 560px;
  max-width: 90vw;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px 12px;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f5ff 100%);
  border-bottom: 1px solid #e8e8e8;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1890ff;
}
.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  line-height: 1;
  padding: 0 2px;
}
.close-btn:hover { color: #333; }

.card-body {
  padding: 16px 18px;
  max-height: 360px;
  overflow-y: auto;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px 14px;
  justify-content: flex-end;
}

.loading-text {
  font-size: 13px;
  color: #999;
}
.cursor-blink {
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}

/* transition */
.slide-fade-enter-active {
  transition: opacity 0.25s ease;
}
.slide-fade-enter-active .suggestion-card {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.slide-fade-leave-active {
  transition: opacity 0.2s ease;
}
.slide-fade-leave-active .suggestion-card {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.slide-fade-enter-from {
  opacity: 0;
}
.slide-fade-enter-from .suggestion-card {
  transform: translateY(-20px) scale(0.96);
  opacity: 0;
}
.slide-fade-leave-to {
  opacity: 0;
}
.slide-fade-leave-to .suggestion-card {
  transform: translateY(-10px) scale(0.98);
  opacity: 0;
}

.md-content {
  font-size: 13px;
  line-height: 1.7;
  color: #444;
}
.md-content :deep(p) { margin: 0 0 8px; }
.md-content :deep(p:last-child) { margin-bottom: 0; }
.md-content :deep(ul),
.md-content :deep(ol) { margin: 4px 0 8px; padding-left: 20px; }
.md-content :deep(li) { margin: 2px 0; }
.md-content :deep(strong) { color: #333; font-weight: 600; }
.md-content :deep(h1),
.md-content :deep(h2),
.md-content :deep(h3) { margin: 8px 0 4px; font-size: 14px; font-weight: 600; color: #333; }
.md-content :deep(code) { background: rgba(0,0,0,0.06); padding: 1px 4px; border-radius: 3px; font-size: 12px; }
.md-content :deep(hr) { border: none; border-top: 1px solid #d9d9d9; margin: 8px 0; }
</style>
