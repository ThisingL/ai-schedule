<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NLayout, NLayoutHeader, NLayoutContent, NLayoutSider,
  NTabs, NTabPane, NButton, NSpace, NIcon,
} from 'naive-ui'
import KanbanBoard from '../components/KanbanBoard.vue'
import CalendarView from '../components/CalendarView.vue'
import ChatPanel from '../components/ChatPanel.vue'
import DailySuggestion from '../components/DailySuggestion.vue'
import { useSettingsStore } from '../stores/settingsStore'

const router = useRouter()
const settingsStore = useSettingsStore()
onMounted(() => settingsStore.fetchSettings())
const activeTab = ref<string>('kanban')
const showChat = ref(true)
</script>

<template>
  <n-layout class="dashboard" position="absolute">
    <n-layout-header bordered class="dashboard-header">
      <div class="header-left">
        <span class="logo">AI Schedule</span>
      </div>
      <n-tabs v-model:value="activeTab" type="segment" size="small" class="header-tabs">
        <n-tab-pane name="kanban" tab="看板" :display-directive="'show:lazy'" />
        <n-tab-pane name="calendar" tab="日历" :display-directive="'show:lazy'" />
      </n-tabs>
      <n-space class="header-right" :size="8" align="center">
        <n-button
          size="small"
          :type="showChat ? 'default' : 'primary'"
          secondary
          @click="showChat = !showChat"
        >
          {{ showChat ? '隐藏助手' : 'AI 助手' }}
        </n-button>
        <n-button size="small" quaternary @click="router.push('/settings')">
          设置
        </n-button>
      </n-space>
    </n-layout-header>

    <n-layout has-sider sider-placement="right" class="dashboard-body">
      <n-layout-content class="main-area">
        <div class="view-container">
          <KanbanBoard v-if="activeTab === 'kanban'" />
          <CalendarView v-else />
        </div>
      </n-layout-content>
      <n-layout-sider
        v-if="showChat"
        :width="360"
        bordered
        :native-scrollbar="false"
        class="chat-sider"
      >
        <ChatPanel />
      </n-layout-sider>
    </n-layout>
  </n-layout>
  <DailySuggestion />
</template>

<style scoped>
.dashboard {
  height: 100vh;
}
.dashboard-header {
  display: flex;
  align-items: center;
  padding: 8px 20px;
  gap: 20px;
  background: #fff;
  height: 52px;
}
.header-left {
  display: flex;
  align-items: center;
}
.logo {
  font-size: 17px;
  font-weight: 700;
  background: linear-gradient(135deg, #1890ff, #722ed1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header-tabs {
  max-width: 200px;
}
.header-right {
  margin-left: auto;
}
.dashboard-body {
  height: calc(100vh - 52px);
}
.main-area {
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.view-container {
  flex: 1;
  overflow: hidden;
}
.chat-sider {
  background: #fff;
}
</style>
