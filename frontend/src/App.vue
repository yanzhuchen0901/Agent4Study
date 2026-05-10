<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import { getHealth, getMergeStatus, getRAGStatus, listGraphNodes, listTextbooks } from './api/client'

const route = useRoute()
const backendStatus = ref('checking')
const backendVersion = ref('-')
const textbookCount = ref(0)
const nodeCount = ref(0)
const ragChunks = ref(0)
const dedupRate = ref(0)
const globalError = ref('')

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

async function refreshGlobalStats() {
  const [books, nodes, ragStatus, mergeStatus] = await Promise.allSettled([
    listTextbooks(),
    listGraphNodes(),
    getRAGStatus(),
    getMergeStatus(),
  ])
  if (books.status === 'fulfilled') {
    textbookCount.value = books.value.length
  }
  if (nodes.status === 'fulfilled') {
    nodeCount.value = nodes.value.length
  }
  if (ragStatus.status === 'fulfilled') {
    ragChunks.value = ragStatus.value.chunks || 0
  }
  if (mergeStatus.status === 'fulfilled') {
    dedupRate.value = mergeStatus.value.deduplication_rate || 0
  }
}

function handleGlobalError(event) {
  globalError.value = event.detail
  window.setTimeout(() => {
    globalError.value = ''
  }, 3600)
}

onMounted(() => {
  refreshHealth()
  refreshGlobalStats()
  window.addEventListener('a4s-api-error', handleGlobalError)
})

onUnmounted(() => {
  window.removeEventListener('a4s-api-error', handleGlobalError)
})
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
      <div v-if="globalError" class="global-error">{{ globalError }}</div>
      <RouterView />
    </main>

    <footer class="statusbar">
      <span>后端连接状态: {{ backendStatus }}</span>
      <span>版本: {{ backendVersion }}</span>
      <span>当前阶段: {{ currentStage }}</span>
      <span>教材: {{ textbookCount }}</span>
      <span>节点: {{ nodeCount }}</span>
      <span>RAG chunks: {{ ragChunks }}</span>
      <span>去重率: {{ Math.round(dedupRate * 100) }}%</span>
    </footer>
  </div>
</template>
