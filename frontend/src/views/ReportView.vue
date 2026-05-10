<script setup>
import { onMounted, ref } from 'vue'

import { getReportMarkdown } from '../api/client'

const report = ref(null)
const message = ref('')

function renderMarkdown(text) {
  const escaped = String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return escaped
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
    .replace(/\n/g, '<br />')
}

async function loadReport() {
  try {
    report.value = await getReportMarkdown()
    message.value = `来源: ${report.value.source}`
  } catch (error) {
    message.value = error.response?.data?.detail || '报告读取失败'
  }
}

onMounted(loadReport)
</script>

<template>
  <section class="tool-view">
    <div class="section-header">
      <p class="eyebrow">Report</p>
      <h2>报告</h2>
    </div>
    <div class="toolbar-line">
      <button class="secondary-button" @click="loadReport">刷新报告</button>
      <span>{{ message }}</span>
    </div>
    <article v-if="report" class="markdown-preview" v-html="renderMarkdown(report.markdown)"></article>
  </section>
</template>
