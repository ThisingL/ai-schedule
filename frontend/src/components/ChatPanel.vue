<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { NInput, NButton, NEmpty } from 'naive-ui'
import MarkdownIt from 'markdown-it'
import { useChatStore } from '../stores/chatStore'
import { useTaskStore } from '../stores/taskStore'
import type { ChatMessage } from '../types'

const md = new MarkdownIt({ breaks: true, linkify: true })

const chatStore = useChatStore()
const taskStore = useTaskStore()

onMounted(() => scrollToBottom(true))

const input = ref('')
const messagesRef = ref<HTMLElement>()
const streamingText = ref('')
const isStreaming = ref(false)
const lastError = ref(false) // 标记上次请求是否失败
let abortController: AbortController | null = null
let typewriterTimer: ReturnType<typeof setInterval> | null = null
let userAtBottom = true

// 监听用户是否滚到底部附近
function onScroll() {
  if (!messagesRef.value) return
  const el = messagesRef.value
  userAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60
}

// 自动跟随：只在用户处于底部时滚动
function scrollToBottom(force = false) {
  nextTick(() => {
    if (messagesRef.value && (force || userAtBottom)) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 消息列表变化时自动滚
watch(() => chatStore.messages.length, () => scrollToBottom())

function typewriterEffect(text: string, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    streamingText.value = ''
    isStreaming.value = true
    let i = 0
    const speed = Math.max(10, Math.min(30, 1500 / text.length))
    typewriterTimer = setInterval(() => {
      if (signal.aborted) {
        clearInterval(typewriterTimer!)
        typewriterTimer = null
        resolve()
        return
      }
      const chars = Math.max(1, Math.floor(text.length / 100))
      streamingText.value = text.slice(0, i + chars)
      i += chars
      scrollToBottom()
      if (i >= text.length) {
        streamingText.value = text
        isStreaming.value = false
        clearInterval(typewriterTimer!)
        typewriterTimer = null
        resolve()
      }
    }, speed)
  })
}

function cancelSend() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  if (typewriterTimer) {
    clearInterval(typewriterTimer)
    typewriterTimer = null
  }
  if (streamingText.value) {
    chatStore.addMessage({
      id: Date.now() + 1,
      role: 'assistant',
      content: streamingText.value,
      related_task_ids: null,
      created_at: new Date().toISOString(),
    })
  }
  streamingText.value = ''
  chatStore.loading = false
  isStreaming.value = false
  scrollToBottom(true)
}

// 核心发送逻辑，isRetry 表示重试（不重复添加用户消息）
async function doSend(text: string, isRetry = false) {
  if (chatStore.loading) return
  lastError.value = false

  if (!isRetry) {
    chatStore.addMessage({
      id: Date.now(),
      role: 'user',
      content: text,
      related_task_ids: null,
      created_at: new Date().toISOString(),
    })
  }

  input.value = ''
  scrollToBottom(true)

  chatStore.loading = true
  isStreaming.value = true
  streamingText.value = ''
  abortController = new AbortController()
  const signal = abortController.signal

  try {
    const data = await chatStore.sendMessage(text)
    if (signal.aborted) return
    await typewriterEffect(data.content, signal)
    if (signal.aborted) return
    chatStore.addMessage(data)
    streamingText.value = ''
    await taskStore.fetchTasks()
  } catch (e: any) {
    if (signal.aborted) return
    const detail = e?.response?.data?.detail
    const errContent = typeof detail === 'string' ? detail : (e?.message || 'AI 服务暂时不可用，请检查设置中的 API 配置。')
    chatStore.addMessage({
      id: Date.now() + 1,
      role: 'assistant',
      content: errContent,
      related_task_ids: null,
      created_at: new Date().toISOString(),
      _isError: true,
    } as any)
    streamingText.value = ''
    lastError.value = true
  }
  abortController = null
  chatStore.loading = false
  isStreaming.value = false
  scrollToBottom(true)
}

function send() {
  const text = input.value.trim()
  if (!text) return
  doSend(text)
}

function retry() {
  // 找到最后一条用户消息
  const msgs = chatStore.messages
  // 移除最后的错误回复
  if (msgs.length && msgs[msgs.length - 1].role === 'assistant') {
    msgs.pop()
  }
  // 找最后一条用户消息的内容
  const lastUserMsg = [...msgs].reverse().find(m => m.role === 'user')
  if (lastUserMsg) {
    doSend(lastUserMsg.content, true)
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.isComposing) return
  if (e.key === 'Enter' && e.shiftKey) return
  if (e.key === 'Enter') {
    e.preventDefault()
    send()
  }
}
</script>

<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span>AI 助手</span>
      <n-button
        size="tiny"
        quaternary
        @click="chatStore.newConversation()"
        :disabled="chatStore.loading || !chatStore.messages.length"
      >
        新建对话
      </n-button>
    </div>
    <div class="chat-messages" ref="messagesRef" @scroll="onScroll">
      <n-empty
        v-if="!chatStore.messages.length && !isStreaming"
        description="试试输入「明天下午开会」或「今天先做什么好」"
        size="small"
        style="margin-top: 40px"
      />
      <div
        v-for="(msg, idx) in chatStore.messages"
        :key="msg.id"
        class="message"
        :class="msg.role"
      >
        <div v-if="msg.role === 'user'" class="message-bubble">{{ msg.content }}</div>
        <div v-else class="message-bubble md-bubble" :class="{ 'error-bubble': (msg as any)._isError }" v-html="md.render(msg.content)" />
      </div>
      <!-- 重试按钮 -->
      <div v-if="lastError && !chatStore.loading" class="retry-bar">
        <n-button size="tiny" type="warning" secondary @click="retry">
          重新发送
        </n-button>
      </div>
      <!-- Streaming message -->
      <div v-if="isStreaming" class="message assistant">
        <div v-if="streamingText" class="message-bubble md-bubble" v-html="md.render(streamingText + '▍')" />
        <div v-else class="message-bubble typing">
          <span class="dot-loading">思考中</span>
        </div>
      </div>
    </div>
    <div class="chat-input">
      <n-input
        v-model:value="input"
        type="textarea"
        placeholder="输入指令，Shift+Enter 换行"
        @keydown="onKeydown"
        :disabled="chatStore.loading"
        :autosize="{ minRows: 1, maxRows: 4 }"
        size="small"
      />
      <n-button
        v-if="chatStore.loading"
        type="error"
        size="small"
        @click="cancelSend"
      >
        停止
      </n-button>
      <n-button
        v-else
        type="primary"
        size="small"
        @click="send"
        :disabled="!input.trim()"
      >
        发送
      </n-button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid #f0f0f0;
  color: #333;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.message { display: flex; }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }
.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.message.user .message-bubble {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message.assistant .message-bubble {
  background: #f4f4f5;
  color: #333;
  border-bottom-left-radius: 4px;
}
.md-bubble {
  white-space: normal;
}
.md-bubble :deep(p) { margin: 0 0 6px; }
.md-bubble :deep(p:last-child) { margin-bottom: 0; }
.md-bubble :deep(ul),
.md-bubble :deep(ol) { margin: 4px 0 6px; padding-left: 18px; }
.md-bubble :deep(li) { margin: 2px 0; }
.md-bubble :deep(strong) { font-weight: 600; }
.md-bubble :deep(code) { background: rgba(0,0,0,0.06); padding: 1px 4px; border-radius: 3px; font-size: 12px; }
.typing {
  color: #999;
  font-style: italic;
}
.dot-loading::after {
  content: '';
  animation: dots 1.5s steps(3) infinite;
}
@keyframes dots {
  0% { content: ''; }
  33% { content: '.'; }
  66% { content: '..'; }
  100% { content: '...'; }
}
.error-bubble {
  background: #fff2f0 !important;
  color: #cf1322 !important;
  border: 1px solid #ffccc7;
}
.retry-bar {
  display: flex;
  justify-content: center;
  padding: 4px 0;
}
.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #f0f0f0;
  align-items: flex-end;
}
</style>
