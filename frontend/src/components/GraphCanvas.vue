<script setup>
import cytoscape from 'cytoscape'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  layoutName: { type: String, default: 'cose' },
  highlightedNodeIds: { type: Array, default: () => [] },
})

const emit = defineEmits(['node-selected'])
const container = ref(null)
let cy = null

const categoryColors = ['#2563eb', '#16a34a', '#d97706', '#7c3aed', '#dc2626', '#0891b2']

const elements = computed(() => {
  const categories = [...new Set(props.nodes.map((node) => node.category || '核心概念'))]
  const colorByCategory = Object.fromEntries(
    categories.map((category, index) => [category, categoryColors[index % categoryColors.length]]),
  )
  return [
    ...props.nodes.map((node) => ({
      data: {
        ...node,
        label: node.name,
        color: colorByCategory[node.category || '核心概念'],
        size: 36 + Math.min((node.frequency || 1) * 5, 32),
      },
    })),
    ...props.edges.map((edge) => ({
      data: {
        ...edge,
        label: edge.relation_type,
      },
    })),
  ]
})

function runLayout() {
  if (!cy) return
  cy.layout({
    name: props.layoutName,
    animate: true,
    fit: true,
    padding: 40,
    nodeRepulsion: 8000,
  }).run()
}

function applyHighlight() {
  if (!cy) return
  cy.elements().removeClass('highlighted faded')
  if (!props.highlightedNodeIds.length) return
  const highlighted = cy.collection(
    props.highlightedNodeIds
      .map((id) => cy.getElementById(id))
      .filter((element) => element.length),
  )
  cy.elements().addClass('faded')
  highlighted.removeClass('faded').addClass('highlighted')
  highlighted.connectedEdges().removeClass('faded').addClass('highlighted')
  highlighted.connectedEdges().connectedNodes().removeClass('faded')
  if (highlighted.length) {
    cy.animate({ fit: { eles: highlighted, padding: 90 } }, { duration: 250 })
  }
}

async function renderGraph() {
  await nextTick()
  if (!container.value) return
  if (!cy) {
    cy = cytoscape({
      container: container.value,
      elements: elements.value,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            label: 'data(label)',
            width: 'data(size)',
            height: 'data(size)',
            color: '#111827',
            'font-size': 11,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            label: 'data(label)',
            'font-size': 9,
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': '#94a3b8',
            'target-arrow-color': '#94a3b8',
          },
        },
        { selector: 'edge[relation_type = "prerequisite"]', style: { 'line-color': '#dc2626', 'target-arrow-color': '#dc2626' } },
        { selector: 'edge[relation_type = "parallel"]', style: { 'line-color': '#16a34a', 'target-arrow-color': '#16a34a' } },
        { selector: 'edge[relation_type = "contains"]', style: { 'line-color': '#d97706', 'target-arrow-color': '#d97706' } },
        { selector: 'edge[relation_type = "applies_to"]', style: { 'line-color': '#7c3aed', 'target-arrow-color': '#7c3aed' } },
        { selector: '.highlighted', style: { 'border-width': 4, 'border-color': '#0f172a', 'z-index': 10 } },
        { selector: '.faded', style: { opacity: 0.22 } },
      ],
    })
    cy.on('tap', 'node', (event) => {
      emit('node-selected', event.target.data())
    })
  } else {
    cy.elements().remove()
    cy.add(elements.value)
  }
  runLayout()
  applyHighlight()
}

watch(() => [props.nodes, props.edges], renderGraph, { deep: true, immediate: true })
watch(() => props.layoutName, runLayout)
watch(() => props.highlightedNodeIds, applyHighlight, { deep: true })

onBeforeUnmount(() => {
  if (cy) {
    cy.destroy()
    cy = null
  }
})
</script>

<template>
  <div ref="container" class="graph-canvas">
    <div v-if="!nodes.length" class="graph-empty">暂无图谱数据</div>
  </div>
</template>
