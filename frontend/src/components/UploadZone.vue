<script setup>
const emit = defineEmits(['files-selected'])

function emitFiles(fileList) {
  const files = Array.from(fileList || [])
  if (files.length) {
    emit('files-selected', files)
  }
}

function onDrop(event) {
  event.preventDefault()
  emitFiles(event.dataTransfer.files)
}
</script>

<template>
  <label
    class="upload-zone"
    @dragover.prevent
    @drop="onDrop"
  >
    <input
      class="file-input"
      type="file"
      multiple
      accept=".pdf,.md,.markdown,.txt,.docx,.xlsx,.xls"
      @change="emitFiles($event.target.files)"
    />
    <strong>上传教材文件</strong>
    <span>支持 PDF / Markdown / TXT / DOCX / Excel，可拖拽或点击选择。</span>
  </label>
</template>
