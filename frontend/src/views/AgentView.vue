<script setup>
import mermaid from 'mermaid'
import { nextTick, ref } from 'vue'

import { queryAgent } from '../api/client'

mermaid.initialize({
  startOnLoad: false,
  securityLevel: 'strict',
  theme: 'base',
  themeVariables: {
    primaryColor: '#e0f2fe',
    primaryTextColor: '#0f172a',
    primaryBorderColor: '#0284c7',
    lineColor: '#64748b',
    secondaryColor: '#f8fafc',
  },
})

const question = ref('')
const result = ref(null)
const message = ref('')
const isBusy = ref(false)
const workflowSvg = ref('')

function summarizeOutput(output) {
  if (!output) {
    return '无输出'
  }
  if (output.error) {
    return output.error
  }
  if (output.answer) {
    return output.answer
  }
  return JSON.stringify(output)
}

async function renderWorkflow(source) {
  workflowSvg.value = ''
  if (!source) {
    return
  }
  await nextTick()
  try {
    const renderId = `agent-workflow-${Date.now()}`
    const { svg } = await mermaid.render(renderId, source)
    workflowSvg.value = svg
  } catch (error) {
    workflowSvg.value = `<pre>${source}</pre>`
  }
}

async function handleQuery() {
  if (!question.value.trim()) {
    message.value = '请输入问题'
    return
  }
  isBusy.value = true
  message.value = 'Agent 正在分解问题、检索知识库并综合回答...'
  workflowSvg.value = ''
  try {
    result.value = await queryAgent(question.value.trim())
    await renderWorkflow(result.value.workflow_mermaid)
    message.value = 'Agent 回答完成'
  } catch (error) {
    result.value = null
    message.value = error.response?.data?.detail || 'Agent 查询失败'
  } finally {
    isBusy.value = false
  }
}
</script>

<template>
  <section class="agent-view">
    <div class="section-header">
      <p class="eyebrow">Agent Workflow</p>
      <h2>Agent</h2>
    </div>

    <div class="agent-grid">
      <section class="side-panel agent-query-panel">
        <h3>复杂问题</h3>
        <textarea
          v-model="question"
          rows="6"
          placeholder="输入需要综合教材内容、图谱关系和 RAG 证据的问题"
          @keydown.ctrl.enter="handleQuery"
        ></textarea>
        <button class="secondary-button" :disabled="isBusy" @click="handleQuery">
          {{ isBusy ? '执行中' : '开始分析' }}
        </button>
        <p class="muted-line">{{ message }}</p>
      </section>

      <section class="side-panel">
        <h3>执行流程</h3>
        <div v-if="workflowSvg" class="workflow-diagram" v-html="workflowSvg"></div>
        <p v-else class="muted-line">提交问题后展示 Agent 编排流程。</p>
      </section>
    </div>

    <div v-if="result" class="agent-result">
      <section class="side-panel">
        <h3>综合回答</h3>
        <p class="answer-block">{{ result.answer }}</p>
      </section>

      <section class="side-panel">
        <h3>问题拆解</h3>
        <div class="tag-list">
          <span v-for="item in result.sub_questions" :key="item" class="soft-tag">{{ item }}</span>
        </div>
      </section>

      <section class="side-panel">
        <h3>执行轨迹</h3>
        <div class="step-list">
          <article v-for="(step, index) in result.steps" :key="`${step.name}-${index}`" class="step-card">
            <div class="step-head">
              <strong>{{ step.name }}</strong>
              <span :class="['status-pill', step.status]">{{ step.status }}</span>
            </div>
            <p>{{ step.query }}</p>
            <small>{{ step.type.toUpperCase() }}</small>
            <details>
              <summary>查看输出</summary>
              <p>{{ summarizeOutput(step.output) }}</p>
            </details>
          </article>
        </div>
      </section>

      <section class="side-panel">
        <h3>引用来源</h3>
        <div v-if="result.citations.length" class="citation-list">
          <div v-for="(citation, index) in result.citations" :key="index" class="citation-card">
            <strong>{{ citation.textbook || '教材' }}</strong>
            <span>{{ citation.chapter || '章节未知' }} · p.{{ citation.page || '-' }}</span>
          </div>
        </div>
        <p v-else class="muted-line">当前回答没有可展示引用。</p>
      </section>
    </div>
  </section>
</template>
