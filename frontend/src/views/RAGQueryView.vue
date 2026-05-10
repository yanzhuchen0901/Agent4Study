<script setup>
import { onMounted, ref } from 'vue'

import ChatPanel from '../components/ChatPanel.vue'
import { getRAGStatus, indexRAG, queryRAG } from '../api/client'

const textbookId = ref('')
const question = ref('')
const topK = ref(Number(localStorage.getItem('a4s.defaultTopK') || 5))
const status = ref(null)
const messages = ref([])
const message = ref('')
const isBusy = ref(false)

async function refreshStatus() {
  status.value = await getRAGStatus()
}

async function handleIndex() {
  if (!textbookId.value.trim()) {
    message.value = '请输入 textbook_id'
    return
  }
  isBusy.value = true
  message.value = '正在建立 RAG 索引...'
  try {
    const indexed = await indexRAG(textbookId.value.trim())
    await refreshStatus()
    message.value = `索引完成: ${indexed.chunks} chunks / ${indexed.dimension} 维`
  } catch (error) {
    message.value = error.response?.data?.detail || '索引失败'
  } finally {
    isBusy.value = false
  }
}

async function handleQuery() {
  if (!question.value.trim()) {
    message.value = '请输入问题'
    return
  }
  isBusy.value = true
  message.value = '正在检索并生成回答...'
  const currentQuestion = question.value.trim()
  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: currentQuestion,
  })
  question.value = ''
  try {
    const result = await queryRAG(currentQuestion, topK.value)
    messages.value.push({
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: result.answer,
      citations: result.citations,
      sourceChunks: result.source_chunks,
    })
    message.value = '回答完成'
  } catch (error) {
    message.value = error.response?.data?.detail || '问答失败'
  } finally {
    isBusy.value = false
  }
}

onMounted(refreshStatus)
</script>

<template>
  <section class="rag-view">
    <div class="section-header">
      <p class="eyebrow">RAG</p>
      <h2>RAG 问答</h2>
    </div>

    <div class="metric-grid compact">
      <div class="metric-card">
        <strong>{{ status?.chunks || 0 }}</strong>
        <span>知识块</span>
      </div>
      <div class="metric-card">
        <strong>{{ status?.dimension || 0 }}</strong>
        <span>向量维度</span>
      </div>
    </div>

    <div class="form-row">
      <input v-model="textbookId" placeholder="输入已解析教材 textbook_id" />
      <button class="secondary-button" :disabled="isBusy" @click="handleIndex">建立索引</button>
      <button class="secondary-button" :disabled="isBusy" @click="refreshStatus">刷新状态</button>
    </div>

    <ChatPanel :messages="messages" :busy="isBusy" />

    <div class="side-panel">
      <textarea v-model="question" rows="4" placeholder="输入教材问题，例如：什么是排序算法？"></textarea>
      <div class="form-row">
        <input v-model.number="topK" type="number" min="1" max="10" />
        <button class="secondary-button" :disabled="isBusy" @click="handleQuery">发送</button>
      </div>
      <p class="muted-line">{{ message }}</p>
    </div>
  </section>
</template>
