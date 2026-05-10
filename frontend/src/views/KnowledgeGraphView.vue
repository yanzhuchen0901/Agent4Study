<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import GraphBreadcrumb from '../components/GraphBreadcrumb.vue'
import GraphCanvas from '../components/GraphCanvas.vue'
import GraphFilter from '../components/GraphFilter.vue'
import LevelSwitcher from '../components/LevelSwitcher.vue'
import {
  buildGraph,
  buildHierarchy,
  getHierarchySummary,
  getParsedTextbook,
  getRawTextbookUrl,
  listGraphEdges,
  listGraphNodes,
  queryGraph,
  searchGraphNodes,
} from '../api/client'

const currentLevel = ref('knowledge')
const drillTextbookId = ref('')
const drillChapterId = ref('')
const textbookId = ref('')
const question = ref('')
const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)
const chapterStart = ref(null)
const chapterLinkStatus = ref('')
const highlightedNodeIds = ref([])
const queryResult = ref(null)
const status = ref('')
const isBusy = ref(false)
const hierarchySummary = ref(null)
const filters = ref({ category: '', relationType: '', keyword: '', layout: localStorage.getItem('a4s.graphLayout') || 'cose' })

const categories = computed(() => {
  if (currentLevel.value !== 'knowledge') return []
  return [...new Set(nodes.value.map((node) => node.category).filter(Boolean))]
})
const relationTypes = computed(() => [...new Set(edges.value.map((edge) => edge.relation_type).filter(Boolean))])

const breadcrumbItems = computed(() => {
  const items = [{ name: '全部教材', level: 'book', textbookId: '', chapterId: '' }]
  if (currentLevel.value === 'chapter' || currentLevel.value === 'knowledge') {
    if (drillTextbookId.value) {
      const bookNode = nodes.value.find((n) => n.level === 'book' && n.textbook_id === drillTextbookId.value)
      items.push({ name: bookNode?.name || drillTextbookId.value, level: 'chapter', textbookId: drillTextbookId.value, chapterId: '' })
    }
  }
  if (currentLevel.value === 'knowledge' && drillChapterId.value) {
    const chNode = nodes.value.find((n) => n.level === 'chapter' && n.chapter_id === drillChapterId.value)
    items.push({ name: chNode?.name || drillChapterId.value, level: 'knowledge', textbookId: drillTextbookId.value, chapterId: drillChapterId.value })
  }
  return items
})

const filteredNodes = computed(() => {
  if (currentLevel.value !== 'knowledge') return nodes.value
  const keyword = filters.value.keyword.trim().toLowerCase()
  return nodes.value.filter((node) => {
    const categoryOk = !filters.value.category || node.category === filters.value.category
    const keywordOk = !keyword || [node.name, node.definition, node.chapter].some((value) => (value || '').toLowerCase().includes(keyword))
    return categoryOk && keywordOk
  })
})

const filteredNodeIds = computed(() => new Set(filteredNodes.value.map((node) => node.id)))
const filteredEdges = computed(() => {
  if (currentLevel.value !== 'knowledge') return edges.value
  return edges.value.filter((edge) => {
    const relationOk = !filters.value.relationType || edge.relation_type === filters.value.relationType
    return relationOk && filteredNodeIds.value.has(edge.source) && filteredNodeIds.value.has(edge.target)
  })
})

async function loadLevelData() {
  let tbId = ''
  let chId = ''
  if (currentLevel.value === 'book') {
    tbId = ''
    chId = ''
  } else if (currentLevel.value === 'chapter') {
    tbId = drillTextbookId.value
    chId = ''
  } else {
    tbId = drillTextbookId.value
    chId = drillChapterId.value
  }
  try {
    const [loadedNodes, loadedEdges] = await Promise.all([
      listGraphNodes(tbId, chId, currentLevel.value),
      listGraphEdges(tbId, '', currentLevel.value),
    ])
    nodes.value = loadedNodes
    edges.value = loadedEdges
  } catch {
    nodes.value = []
    edges.value = []
  }
}

async function refreshGraph() {
  nodes.value = await listGraphNodes(textbookId.value)
  edges.value = await listGraphEdges(textbookId.value)
}

function handleLevelChange(newLevel) {
  currentLevel.value = newLevel
  if (newLevel === 'book') {
    drillTextbookId.value = ''
    drillChapterId.value = ''
  }
  highlightedNodeIds.value = []
  selectedNode.value = null
  loadLevelData()
}

function handleBreadcrumbNavigate(item) {
  if (!item.level) return
  currentLevel.value = item.level
  drillTextbookId.value = item.textbookId || ''
  drillChapterId.value = item.chapterId || ''
  highlightedNodeIds.value = []
  selectedNode.value = null
  loadLevelData()
}

function handleNodeSelected(node) {
  selectedNode.value = node
  if (currentLevel.value === 'book') {
    drillTextbookId.value = node.textbook_id
    currentLevel.value = 'chapter'
    loadLevelData()
  } else if (currentLevel.value === 'chapter') {
    drillTextbookId.value = node.textbook_id
    drillChapterId.value = node.chapter_id
    currentLevel.value = 'knowledge'
    loadLevelData()
  } else {
    highlightedNodeIds.value = [node.id]
    chapterStart.value = null
    chapterLinkStatus.value = ''
  }
}

async function handleBuildHierarchy() {
  isBusy.value = true
  status.value = '正在构建三层知识层级...'
  try {
    const result = await buildHierarchy()
    hierarchySummary.value = await getHierarchySummary()
    status.value = `层级构建完成: ${result.book_count} 教材 / ${result.chapter_count} 章节`
    await loadLevelData()
  } catch (error) {
    status.value = error.response?.data?.detail || '层级构建失败'
  } finally {
    isBusy.value = false
  }
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
    await loadLevelData()
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

async function openChapterStart() {
  if (!selectedNode.value) return
  chapterLinkStatus.value = ''
  try {
    const textbook = await getParsedTextbook(selectedNode.value.textbook_id)
    const chapter = (textbook.chapters || []).find((item) => item.chapter_id === selectedNode.value.chapter_id)
    const pageStart = Number(chapter?.page_start || 1)
    chapterStart.value = pageStart
    const filename = String(textbook.filename || '').toLowerCase()
    const baseUrl = getRawTextbookUrl(selectedNode.value.textbook_id)
    const url = filename.endsWith('.pdf') ? `${baseUrl}#page=${pageStart}` : baseUrl
    window.open(url, '_blank', 'noopener,noreferrer')
  } catch (error) {
    chapterLinkStatus.value = error.response?.data?.detail || '无法打开章节原文'
  }
}

watch(currentLevel, () => { filters.value.category = ''; filters.value.relationType = '' })

onMounted(async () => {
  try {
    hierarchySummary.value = await getHierarchySummary()
  } catch { /* ignore */ }
  await loadLevelData()
})
</script>

<template>
  <section class="graph-view">
    <div class="graph-main">
      <div class="section-header">
        <LevelSwitcher v-model="currentLevel" @update:model-value="handleLevelChange" />
        <GraphBreadcrumb :items="breadcrumbItems" @navigate="handleBreadcrumbNavigate" />
        <p class="eyebrow">Knowledge Graph</p>
        <h2>知识图谱</h2>
      </div>

      <div class="metric-grid compact">
        <div class="metric-card">
          <strong>{{ filteredNodes.length }}</strong>
          <span>节点</span>
        </div>
        <div class="metric-card">
          <strong>{{ filteredEdges.length }}</strong>
          <span>关系</span>
        </div>
        <div v-if="hierarchySummary" class="metric-card">
          <strong>{{ hierarchySummary.book.nodes }}</strong>
          <span>教材</span>
        </div>
        <div v-if="hierarchySummary" class="metric-card">
          <strong>{{ hierarchySummary.chapter.nodes }}</strong>
          <span>章节</span>
        </div>
      </div>

      <div class="form-row">
        <input v-model="textbookId" placeholder="输入 textbook_id 构建或筛选知识点图谱" />
        <button class="secondary-button" :disabled="isBusy" @click="handleBuild">构建图谱</button>
        <button class="secondary-button" :disabled="isBusy" @click="handleBuildHierarchy">构建层级</button>
        <button class="secondary-button" :disabled="isBusy" @click="loadLevelData">刷新</button>
      </div>

      <GraphFilter
        v-if="currentLevel === 'knowledge'"
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
      <section class="side-panel">
        <h3>节点详情</h3>
        <template v-if="selectedNode">
          <p><strong>{{ selectedNode.name }}</strong></p>
          <p>{{ selectedNode.definition }}</p>
          <p v-if="selectedNode.level === 'book'" class="muted-line">
            {{ selectedNode.category }} · {{ selectedNode.page }} 页
          </p>
          <p v-else-if="selectedNode.level === 'chapter'" class="muted-line">
            {{ selectedNode.category }} · {{ selectedNode.textbook_title || selectedNode.textbook_id }}
          </p>
          <p v-else class="muted-line">
            {{ selectedNode.category }} · {{ selectedNode.chapter }} · p.{{ selectedNode.page }}
          </p>
          <p v-if="selectedNode.level === 'knowledge'" class="muted-line">
            章节起始：
            <a href="#" @click.prevent="openChapterStart">p.{{ chapterStart || '?' }}（打开原文）</a>
          </p>
          <p v-if="chapterLinkStatus" class="warning-line">{{ chapterLinkStatus }}</p>
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
        <p class="legend-line prerequisite">先修 (prerequisite)</p>
        <p class="legend-line parallel">并行 (parallel)</p>
        <p class="legend-line contains">包含 (contains)</p>
        <p class="legend-line applies">适用 (applies_to)</p>
        <p class="legend-line" style="color:#0891b2">重叠 (overlap)</p>
      </section>
    </aside>
  </section>
</template>
