<script setup>
import { onMounted, ref } from 'vue'

import UploadZone from '../components/UploadZone.vue'
import { deleteTextbook, getSettings, listTextbooks, uploadTextbook } from '../api/client'

const textbooks = ref([])
const runtimeSettings = ref(null)
const status = ref('')
const isBusy = ref(false)
const preferences = ref({
  apiBase: localStorage.getItem('a4s.apiBase') || '/',
  defaultTopK: Number(localStorage.getItem('a4s.defaultTopK') || 5),
  graphLayout: localStorage.getItem('a4s.graphLayout') || 'cose',
  enableSse: localStorage.getItem('a4s.enableSse') !== 'false',
  llmBaseUrl: localStorage.getItem('a4s.llmBaseUrl') || '',
  llmApiKey: localStorage.getItem('a4s.llmApiKey') || '',
  llmModel: localStorage.getItem('a4s.llmModel') || '',
})

async function refreshList() {
  textbooks.value = await listTextbooks()
}

async function refreshSettings() {
  runtimeSettings.value = await getSettings()
}

async function handleFiles(files) {
  isBusy.value = true
  status.value = `正在解析 ${files.length} 个文件...`
  try {
    for (const file of files) {
      await uploadTextbook(file)
    }
    await refreshList()
    status.value = '解析完成'
  } catch (error) {
    status.value = error.response?.data?.detail || '解析失败'
  } finally {
    isBusy.value = false
  }
}

async function removeTextbook(textbookId) {
  isBusy.value = true
  try {
    await deleteTextbook(textbookId)
    await refreshList()
    status.value = '已删除'
  } catch (error) {
    status.value = error.response?.data?.detail || '删除失败'
  } finally {
    isBusy.value = false
  }
}

function savePreferences() {
  localStorage.setItem('a4s.apiBase', preferences.value.apiBase)
  localStorage.setItem('a4s.defaultTopK', String(preferences.value.defaultTopK))
  localStorage.setItem('a4s.graphLayout', preferences.value.graphLayout)
  localStorage.setItem('a4s.enableSse', String(preferences.value.enableSse))
  localStorage.setItem('a4s.llmBaseUrl', preferences.value.llmBaseUrl)
  localStorage.setItem('a4s.llmApiKey', preferences.value.llmApiKey)
  localStorage.setItem('a4s.llmModel', preferences.value.llmModel)
  status.value = '前端偏好已保存'
}

onMounted(async () => {
  await Promise.all([refreshList(), refreshSettings()])
})
</script>

<template>
  <section class="tool-view">
    <div class="section-header">
      <p class="eyebrow">Settings</p>
      <h2>上传与设置</h2>
    </div>

    <div class="settings-grid">
      <section class="side-panel">
        <h3>教材上传</h3>
        <UploadZone :busy="isBusy" @files-selected="handleFiles" />
        <div class="toolbar-line">
          <button class="secondary-button" :disabled="isBusy" @click="refreshList">刷新列表</button>
          <span>{{ status }}</span>
        </div>
      </section>

      <section class="side-panel">
        <h3>运行配置</h3>
        <div v-if="runtimeSettings" class="settings-list">
          <span>LLM: {{ runtimeSettings.llm_provider }} / {{ runtimeSettings.llm_model || '-' }}</span>
          <span>Base URL: {{ runtimeSettings.llm_base_url }}</span>
          <span>API Key: {{ runtimeSettings.llm_api_key_configured ? '已配置' : '未配置' }}</span>
          <span>Embedding: {{ runtimeSettings.embedding_model }}</span>
          <span>Data: {{ runtimeSettings.data_dir }}</span>
        </div>
      </section>

      <section class="side-panel">
        <h3>前端偏好</h3>
        <div class="settings-form">
          <label>LLM Base URL <input v-model="preferences.llmBaseUrl" placeholder="https://api.openai.com/v1" /></label>
          <label>LLM API Key <input v-model="preferences.llmApiKey" type="password" placeholder="sk-..." /></label>
          <label>LLM Model <input v-model="preferences.llmModel" placeholder="gpt-4.1-mini" /></label>
          <label>API 地址 <input v-model="preferences.apiBase" /></label>
          <label>默认 top_k <input v-model.number="preferences.defaultTopK" type="number" min="1" max="10" /></label>
          <label>
            图谱布局
            <select v-model="preferences.graphLayout">
              <option value="cose">cose</option>
              <option value="breadthfirst">breadthfirst</option>
              <option value="circle">circle</option>
            </select>
          </label>
          <label class="inline-toggle">
            <input v-model="preferences.enableSse" type="checkbox" />
            <span>启用 Agent SSE</span>
          </label>
          <button class="secondary-button" @click="savePreferences">保存偏好</button>
        </div>
      </section>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>教材 ID</th>
            <th>文件名</th>
            <th>标题</th>
            <th>章节</th>
            <th>页数</th>
            <th>字数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="book in textbooks" :key="book.textbook_id">
            <td>{{ book.textbook_id }}</td>
            <td>{{ book.filename }}</td>
            <td>{{ book.title }}</td>
            <td>{{ book.chapter_count }}</td>
            <td>{{ book.total_pages }}</td>
            <td>{{ book.total_chars }}</td>
            <td>
              <button class="danger-button" :disabled="isBusy" @click="removeTextbook(book.textbook_id)">
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!textbooks.length">
            <td colspan="7" class="empty-cell">暂无已解析教材</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
