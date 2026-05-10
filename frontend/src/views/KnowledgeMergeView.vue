<script setup>
import { onMounted, ref } from 'vue'

import { getMergeStatus, mergeGraph } from '../api/client'

const status = ref(null)
const message = ref('')
const isBusy = ref(false)

async function refreshStatus() {
  status.value = await getMergeStatus()
}

async function handleMerge() {
  isBusy.value = true
  message.value = '正在执行跨教材合并...'
  try {
    status.value = await mergeGraph()
    message.value = '合并完成'
  } catch (error) {
    message.value = error.response?.data?.detail || '合并失败'
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
      <button class="secondary-button" :disabled="isBusy" @click="handleMerge">执行合并</button>
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
        <span>决策</span>
      </div>
      <div class="metric-card">
        <strong>{{ Math.round(status.deduplication_rate * 100) }}%</strong>
        <span>估算去重率</span>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>决策 ID</th>
            <th>动作</th>
            <th>置信度</th>
            <th>原因</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="decision in status?.decisions || []" :key="decision.decision_id">
            <td>{{ decision.decision_id }}</td>
            <td>{{ decision.action }}</td>
            <td>{{ decision.confidence }}</td>
            <td>{{ decision.reason }}</td>
          </tr>
          <tr v-if="!status?.decisions?.length">
            <td colspan="4" class="empty-cell">暂无合并决策</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
