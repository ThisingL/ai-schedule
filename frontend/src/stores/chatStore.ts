import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { ChatMessage } from '../types'
import { aiApi } from '../api'

const STORAGE_KEY = 'chat_messages'

function getTodayStr() {
  return new Date().toISOString().slice(0, 10)
}

function loadFromStorage(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const { date, data } = JSON.parse(raw)
    if (date === getTodayStr() && Array.isArray(data)) return data
  } catch {}
  return []
}

function saveToStorage(msgs: ChatMessage[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    date: getTodayStr(),
    data: msgs,
  }))
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>(loadFromStorage())
  const loading = ref(false)

  // 消息变化时自动持久化到 localStorage
  watch(messages, (val) => saveToStorage(val), { deep: true })

  async function sendMessage(content: string) {
    const history = messages.value.map(m => ({ role: m.role, content: m.content }))
    const { data } = await aiApi.chat(content, history)
    return data
  }

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function newConversation() {
    messages.value = []
  }

  return { messages, loading, sendMessage, addMessage, newConversation }
})
