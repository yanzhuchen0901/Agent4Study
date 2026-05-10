<script setup>
defineProps({
  categories: { type: Array, default: () => [] },
  relationTypes: { type: Array, default: () => [] },
  modelValue: {
    type: Object,
    default: () => ({ category: '', relationType: '', keyword: '', layout: 'cose' }),
  },
})

const relationTypeLabels = {
  prerequisite: '先修',
  parallel: '并行',
  contains: '包含',
  applies_to: '适用',
}

const emit = defineEmits(['update:modelValue', 'search'])

function updateField(field, value) {
  emit('update:modelValue', { ...modelValueFallback(), [field]: value })
}

function modelValueFallback() {
  return { category: '', relationType: '', keyword: '', layout: 'cose' }
}
</script>

<template>
  <div class="graph-filter">
    <input
      :value="modelValue.keyword"
      placeholder="搜索节点"
      @input="updateField('keyword', $event.target.value)"
      @keyup.enter="$emit('search')"
    />
    <select :value="modelValue.category" @change="updateField('category', $event.target.value)">
      <option value="">全部分类</option>
      <option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
    </select>
    <select :value="modelValue.relationType" @change="updateField('relationType', $event.target.value)">
      <option value="">全部关系</option>
      <option v-for="type in relationTypes" :key="type" :value="type">{{ relationTypeLabels[type] || type }}</option>
    </select>
    <select :value="modelValue.layout" @change="updateField('layout', $event.target.value)">
      <option value="cose">力导向</option>
      <option value="breadthfirst">层次</option>
      <option value="circle">圆形</option>
    </select>
    <button class="secondary-button" @click="$emit('search')">定位</button>
  </div>
</template>
