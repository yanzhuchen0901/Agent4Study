<script setup>
defineProps({
  modelValue: { type: String, default: 'knowledge' },
})

const emit = defineEmits(['update:modelValue'])

const levels = [
  { key: 'book', label: '教材层' },
  { key: 'chapter', label: '章节层' },
  { key: 'knowledge', label: '知识点层' },
]
</script>

<template>
  <div class="level-switcher">
    <button
      v-for="lv in levels"
      :key="lv.key"
      :class="['level-btn', { active: modelValue === lv.key }]"
      @click="emit('update:modelValue', lv.key)"
    >
      {{ lv.label }}
    </button>
  </div>
</template>
