<script setup>
import { computed, onMounted, ref } from 'vue'

import GraphCanvas from '../components/GraphCanvas.vue'
import GraphFilter from '../components/GraphFilter.vue'
import {
  buildGraph,
  listGraphEdges,
  listGraphNodes,
  queryGraph,
  searchGraphNodes,
} from '../api/client'

const textbookId = ref('')
const question = ref('')
const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)
const highlightedNodeIds = ref([])
const queryResult = ref(null)
const status = ref('')
const isBusy = ref(false)
const filters = ref({ category: '', relationType: '', keyword: '', layout: localStorage.getItem('a4s.graphLayout') || 'cose' })

const categories = computed(() => [...new Set(nodes.value.map((node) => node.category).filter(Boolean))])
const relationTypes = computed(() => [...new Set(edges.value.map((edge) => edge.relation_type).filter(Boolean))])

const filteredNodes = computed(() => {
  const keyword = filters.value.keyword.trim().toLowerCase()
  return nodes.value.filter((node) => {
    const categoryOk = !filters.value.category || node.category === filters.value.category
    const keywordOk = !keyword || [node.name, node.definition, node.chapter].some((value) => (value || '').toLowerCase().includes(keyword))
    return categoryOk && keywordOk
  })
})

const filteredNodeIds = computed(() => new Set(filteredNodes.value.map((node) => node.id)))
const filteredEdges = computed(() =>
  edges.value.filter((edge) => {
    const relationOk = !filters.value.relationType || edge.relation_type === filters.value.relationType
    return relationOk && filteredNodeIds.value.has(edge.source) && filteredNodeIds.value.has(edge.target)
  }),
)

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
  const keyword = filters.value.keyword.trim()
  if (!keyword) {
    highlightedNodeIds.value = []
    return
  }
  const localMatches = filteredNodes.value.map((node) => node.id)
  highlightedNodeIds.value = localMatches
  if (!localMatches.length) {
    const results = await searchGraphNodes(keyword)
    highlightedNodeIds.value = results.map((node) => node.id)
  }
}

async function handleQuery() {
  if (!question.value.trim()) {
    status.value = '请输入图查询问题'
    return
  }
  isBusy.value = true
  try {
    queryResult.value = await queryGraph(question.value)
    highlightedNodeIds.value = queryResult.value.matched_node_ids || []
    status.value = queryResult.value.answer
  } catch (error) {
    status.value = error.response?.data?.detail || '查询失败'
  } finally {
    isBusy.value = false
  }
}

function handleNodeSelected(node) {
  selectedNode.value = node
  highlightedNodeIds.value = [node.id]
}

onMounted(refreshGraph)
</script>

<template>
  <section class="graph-view">
    <div class="graph-main">
      <div class="section-header">
        <p class="eyebrow">Knowledge Graph</p>
        <h2>知识图谱</h2>
      </div>

      <div class="form-row">
        <input v-model="textbookId" placeholder="输入 textbook_id 构建或筛选图谱" />
        <button class="secondary-button" :disabled="isBusy" @click="handleBuild">构建图谱</button>
        <button class="secondary-button" :disabled="isBusy" @click="refreshGraph">刷新</button>
      </div>

      <GraphFilter
        v-model="filters"
        :categories="categories"
        :relation-types="relationTypes"
        @search="handleSearch"
      />

      <GraphCanvas
        :nodes="filteredNodes"
        :edges="filteredEdges"
        :layout-name="filters.layout"
        :highlighted-node-ids="highlightedNodeIds"
        @node-selected="handleNodeSelected"
      />
    </div>

    <aside class="graph-side">
      <div class="metric-grid compact">
        <div class="metric-card">
          <strong>{{ filteredNodes.length }}</strong>
          <span>节点</span>
        </div>
        <div class="metric-card">
          <strong>{{ filteredEdges.length }}</strong>
          <span>关系</span>
        </div>
      </div>

      <section class="side-panel">
        <h3>节点详情</h3>
        <template v-if="selectedNode">
          <p><strong>{{ selectedNode.name }}</strong></p>
          <p>{{ selectedNode.definition }}</p>
          <p class="muted-line">{{ selectedNode.category }} · {{ selectedNode.chapter }} · p.{{ selectedNode.page }}</p>
          <p class="muted-line">来源: {{ selectedNode.textbook_title || selectedNode.textbook_id }}</p>
        </template>
        <p v-else class="muted-line">点击画布中的节点查看详情。</p>
      </section>

      <section class="side-panel">
        <h3>自然语言图查询</h3>
        <textarea v-model="question" rows="4" placeholder="例如：算法有哪些相关知识？"></textarea>
        <button class="secondary-button" :disabled="isBusy" @click="handleQuery">查询</button>
        <p class="muted-line">{{ status }}</p>
        <div v-if="queryResult?.error" class="warning-line">LLM 回退: {{ queryResult.error }}</div>
      </section>

      <section class="side-panel">
        <h3>图例</h3>
        <p class="legend-line prerequisite">先修</p>
        <p class="legend-line parallel">并行</p>
        <p class="legend-line contains">包含</p>
        <p class="legend-line applies">适用</p>
      </section>
    </aside>
  </section>
</template>
