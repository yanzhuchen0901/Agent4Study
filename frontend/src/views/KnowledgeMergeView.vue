<script setup>
import { computed, onMounted, ref } from 'vue'

import { confirmMergeGraph, getMergeStatus, listGraphNodes, mergeGraph, previewMergeGraph } from '../api/client'

const status = ref(null)
const nodes = ref([])
const message = ref('')
const isBusy = ref(false)
const reviewedActions = ref({})
const approvals = ref({})

const nodeById = computed(() => Object.fromEntries(nodes.value.map((node) => [node.id, node])))

function nodeLabel(nodeId) {
  const node = nodeById.value[nodeId]
  return node ? `${node.name}（${node.textbook_title || node.textbook_id}）` : nodeId
}

async function refreshStatus() {
  status.value = await getMergeStatus()
  nodes.value = await listGraphNodes()
  hydrateReviews()
}

function hydrateReviews() {
  reviewedActions.value = {}
  approvals.value = {}
  for (const decision of status.value?.decisions || []) {
    reviewedActions.value[decision.decision_id] = decision.action
    approvals.value[decision.decision_id] = decision.action === 'merge'
  }
}

async function handleLegacyMerge() {
  isBusy.value = true
  message.value = '正在执行兼容合并...'
  try {
    status.value = await mergeGraph()
    nodes.value = await listGraphNodes()
    hydrateReviews()
    message.value = '合并完成'
  } catch (error) {
    message.value = error.response?.data?.detail || '合并失败'
  } finally {
    isBusy.value = false
  }
}

async function handlePreview() {
  isBusy.value = true
  message.value = '正在生成合并候选...'
  try {
    status.value = await previewMergeGraph()
    nodes.value = await listGraphNodes()
    hydrateReviews()
    message.value = '候选已生成，确认后才会修改图谱'
  } catch (error) {
    message.value = error.response?.data?.detail || '生成候选失败'
  } finally {
    isBusy.value = false
  }
}

async function handleConfirm() {
  isBusy.value = true
  message.value = '正在应用人工确认结果...'
  try {
    const decisions = (status.value?.decisions || []).map((decision) => ({
      decision_id: decision.decision_id,
      action: reviewedActions.value[decision.decision_id] || decision.action,
      approved: Boolean(approvals.value[decision.decision_id]),
    }))
    status.value = await confirmMergeGraph(decisions)
    nodes.value = await listGraphNodes()
    hydrateReviews()
    message.value = '确认完成'
  } catch (error) {
    message.value = error.response?.data?.detail || '确认失败'
  } finally {
    isBusy.value = false
  }
}

onMounted(refreshStatus)
</script>

<template>
  <section class="tool-view">
    <div class="section-header">
      <p class="eyebrow">Merge</p>
      <h2>知识合并</h2>
    </div>

    <div class="toolbar-line">
      <button class="secondary-button" :disabled="isBusy" @click="handlePreview">生成候选</button>
      <button class="secondary-button" :disabled="isBusy" @click="handleConfirm">确认应用</button>
      <button class="secondary-button" :disabled="isBusy" @click="handleLegacyMerge">兼容合并</button>
      <button class="secondary-button" :disabled="isBusy" @click="refreshStatus">刷新状态</button>
      <span>{{ message }}</span>
    </div>

    <div v-if="status" class="metric-grid">
      <div class="metric-card">
        <strong>{{ status.node_count }}</strong>
        <span>节点</span>
      </div>
      <div class="metric-card">
        <strong>{{ status.edge_count }}</strong>
        <span>关系</span>
      </div>
      <div class="metric-card">
        <strong>{{ status.merge_decision_count }}</strong>
        <span>候选/决策</span>
      </div>
      <div class="metric-card">
        <strong>{{ Math.round(status.deduplication_rate * 100) }}%</strong>
        <span>估算去重率</span>
      </div>
    </div>

    <div class="merge-review-list">
      <article v-for="decision in status?.decisions || []" :key="decision.decision_id" class="merge-card">
        <div class="step-head">
          <strong>{{ decision.decision_id }}</strong>
          <span class="status-pill completed">{{ Math.round(decision.confidence * 100) }}%</span>
        </div>
        <div class="tag-list">
          <span v-for="nodeId in decision.affected_nodes" :key="nodeId" class="soft-tag">{{ nodeLabel(nodeId) }}</span>
        </div>
        <p>{{ decision.reason }}</p>
        <div class="merge-actions">
          <select v-model="reviewedActions[decision.decision_id]">
            <option value="merge">merge</option>
            <option value="keep">keep</option>
            <option value="remove">remove</option>
          </select>
          <label class="inline-toggle">
            <input v-model="approvals[decision.decision_id]" type="checkbox" />
            <span>批准应用</span>
          </label>
        </div>
      </article>
      <p v-if="!status?.decisions?.length" class="empty-cell">暂无合并候选</p>
    </div>
  </section>
</template>
