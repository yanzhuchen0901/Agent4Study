<script setup>
defineProps({
  citation: {
    type: Object,
    required: true,
  },
})

function percent(value) {
  const score = Number(value || 0)
  return `${Math.round(score * 100)}%`
}
</script>

<template>
  <article class="citation-card">
    <strong>{{ citation.textbook || '教材' }}</strong>
    <span>{{ citation.chapter || '章节未知' }} · p.{{ citation.page || '-' }} · {{ percent(citation.relevance_score) }}</span>
  </article>
</template>
