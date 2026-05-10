<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import { getHealth } from './api/client'

const route = useRoute()
const backendStatus = ref('checking')
const backendVersion = ref('-')

const tabs = [
  { name: '知识图谱', path: '/', stage: 'Graph' },
  { name: 'RAG 问答', path: '/rag', stage: 'RAG' },
  { name: '知识合并', path: '/merge', stage: 'Merge' },
  { name: 'Agent', path: '/agent', stage: 'Agent' },
  { name: '报告', path: '/report', stage: 'Report' },
  { name: '设置', path: '/settings', stage: 'Settings' },
]

const currentStage = computed(() => {
  const current = tabs.find((tab) => tab.path === route.path)
  return current?.stage ?? 'Task 1'
})

async function refreshHealth() {
  try {
    const health = await getHealth()
    backendStatus.value = health.status === 'ok' ? 'connected' : 'degraded'
    backendVersion.value = health.version ?? '-'
  } catch {
    backendStatus.value = 'offline'
    backendVersion.value = '-'
  }
}

onMounted(refreshHealth)
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Agent4Study</p>
        <h1>AI 教科书知识系统</h1>
      </div>
      <nav class="tabs" aria-label="Primary">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="tab-link"
        >
          {{ tab.name }}
        </RouterLink>
      </nav>
    </header>

    <main class="workspace">
      <RouterView />
    </main>

    <footer class="statusbar">
      <span>后端连接状态: {{ backendStatus }}</span>
      <span>版本: {{ backendVersion }}</span>
      <span>当前阶段: {{ currentStage }}</span>
    </footer>
  </div>
</template>
