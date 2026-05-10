<script setup>
import { onMounted, ref } from 'vue'

import { buildGraph, listGraphEdges, listGraphNodes, searchGraphNodes } from '../api/client'

const textbookId = ref('')
const searchQuery = ref('')
const nodes = ref([])
const edges = ref([])
const searchResults = ref([])
const status = ref('')
const isBusy = ref(false)

async function refreshGraph() {
  nodes.value = await listGraphNodes(textbookId.value)
  edges.value = await listGraphEdges(textbookId.value)
}

async function handleBuild() {
  if (!textbookId.value) {
    status.value = '请输入 textbook_id'
    return
  }
  isBusy.value = true
  status.value = '正在构建知识图谱...'
  try {
    const result = await buildGraph(textbookId.value)
    await refreshGraph()
    status.value = `构建完成: ${result.nodes.length} 节点 / ${result.edges.length} 关系`
  } catch (error) {
    status.value = error.response?.data?.detail || '构建失败'
  } finally {
    isBusy.value = false
  }
}

async function handleSearch() {
  if (!searchQuery.value) {
    searchResults.value = []
    return
  }
  searchResults.value = await searchGraphNodes(searchQuery.value)
}

onMounted(refreshGraph)
</script>

<template>
  <section class="tool-view">
    <div class="section-header">
      <p class="eyebrow">Knowledge Graph</p>
      <h2>知识图谱构建</h2>
    </div>

    <div class="form-row">
      <input v-model="textbookId" placeholder="输入已解析教材 textbook_id，例如 book_01" />
      <button class="secondary-button" :disabled="isBusy" @click="handleBuild">构建图谱</button>
      <button class="secondary-button" :disabled="isBusy" @click="refreshGraph">刷新</button>
    </div>
    <p class="muted-line">{{ status }}</p>

    <div class="metric-grid">
      <div class="metric-card">
        <strong>{{ nodes.length }}</strong>
        <span>节点</span>
      </div>
      <div class="metric-card">
        <strong>{{ edges.length }}</strong>
        <span>关系</span>
      </div>
    </div>

    <div class="form-row">
      <input v-model="searchQuery" placeholder="搜索知识点名称、定义或分类" @keyup.enter="handleSearch" />
      <button class="secondary-button" @click="handleSearch">搜索</button>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>名称</th>
            <th>分类</th>
            <th>章节</th>
            <th>定义</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="node in searchResults.length ? searchResults : nodes.slice(0, 20)" :key="node.id">
            <td>{{ node.name }}</td>
            <td>{{ node.category }}</td>
            <td>{{ node.chapter }}</td>
            <td>{{ node.definition }}</td>
          </tr>
          <tr v-if="!nodes.length">
            <td colspan="4" class="empty-cell">暂无图谱节点</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
