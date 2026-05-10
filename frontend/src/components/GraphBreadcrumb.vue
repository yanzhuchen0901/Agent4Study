<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})

const emit = defineEmits(['navigate'])
</script>

<template>
  <nav class="graph-breadcrumb">
    <span v-for="(item, index) in items" :key="index">
      <a
        v-if="index < items.length - 1"
        href="#"
        class="crumb-link"
        @click.prevent="emit('navigate', item)"
      >
        {{ item.name }}
      </a>
      <span v-else class="crumb-current">{{ item.name }}</span>
      <span v-if="index < items.length - 1" class="crumb-sep">&gt;</span>
    </span>
  </nav>
</template>
