<script setup>
import { onMounted, ref } from 'vue'

import UploadZone from '../components/UploadZone.vue'
import { deleteTextbook, listTextbooks, uploadTextbook } from '../api/client'

const textbooks = ref([])
const status = ref('')
const isBusy = ref(false)

async function refreshList() {
  textbooks.value = await listTextbooks()
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

onMounted(refreshList)
</script>

<template>
  <section class="tool-view">
    <div class="section-header">
      <p class="eyebrow">Ingestion</p>
      <h2>教材解析</h2>
    </div>

    <UploadZone @files-selected="handleFiles" />

    <div class="toolbar-line">
      <button class="secondary-button" :disabled="isBusy" @click="refreshList">刷新列表</button>
      <span>{{ status }}</span>
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
