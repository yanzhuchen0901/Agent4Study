<script setup>
import CitationCard from './CitationCard.vue'

defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  busy: {
    type: Boolean,
    default: false,
  },
})

function renderMarkdown(text) {
  const escaped = String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return escaped
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br />')
}
</script>

<template>
  <section class="chat-panel">
    <div v-if="!messages.length" class="chat-empty">暂无对话，输入问题后开始检索教材知识。</div>
    <article
      v-for="message in messages"
      :key="message.id"
      :class="['chat-message', message.role]"
    >
      <div class="chat-bubble">
        <div class="chat-role">{{ message.role === 'user' ? '用户' : 'AI' }}</div>
        <div class="chat-content" v-html="renderMarkdown(message.content)"></div>
      </div>
      <div v-if="message.citations?.length" class="citation-list">
        <CitationCard
          v-for="(citation, index) in message.citations"
          :key="`${message.id}-${index}`"
          :citation="citation"
        />
      </div>
      <details v-if="message.sourceChunks?.length" class="source-details">
        <summary>查看原文片段</summary>
        <p v-for="(chunk, index) in message.sourceChunks" :key="index">{{ chunk }}</p>
      </details>
    </article>
    <div v-if="busy" class="chat-loading">正在生成回答...</div>
  </section>
</template>
