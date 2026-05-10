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

const textbookShapes = ['ellipse', 'rectangle', 'diamond', 'round-triangle', 'star']

function degreeColor24(degree, minDegree, maxDegree) {
  if (!Number.isFinite(degree)) return 'hsl(210, 85%, 70%)'
  const steps = 24
  const clampedMin = Number.isFinite(minDegree) ? minDegree : 0
  const clampedMax = Number.isFinite(maxDegree) ? maxDegree : clampedMin
  const denom = Math.max(1, clampedMax - clampedMin)
  const ratio = Math.min(1, Math.max(0, (degree - clampedMin) / denom))
  const index = Math.round(ratio * (steps - 1))
  const t = index / (steps - 1)

  const hue = 210 * (1 - t)
  const lightness = 70 - 30 * t
  return `hsl(${hue.toFixed(0)}, 85%, ${lightness.toFixed(0)}%)`
}

const elements = computed(() => {
  const textbooks = [...new Set(props.nodes.map((node) => node.textbook_id || '').filter(Boolean))]
  const shapeByTextbook = Object.fromEntries(
    textbooks.map((id, index) => [id, textbookShapes[index % textbookShapes.length]]),
  )

  const degreeByNodeId = new Map()
  for (const edge of props.edges) {
    const source = edge.source
    const target = edge.target
    if (source) degreeByNodeId.set(source, (degreeByNodeId.get(source) || 0) + 1)
    if (target) degreeByNodeId.set(target, (degreeByNodeId.get(target) || 0) + 1)
  }
  const degrees = props.nodes.map((node) => degreeByNodeId.get(node.id) || 0)
  const minDegree = degrees.length ? Math.min(...degrees) : 0
  const maxDegree = degrees.length ? Math.max(...degrees) : 0

  return [
    ...props.nodes.map((node) => {
      const degree = degreeByNodeId.get(node.id) || 0
      return {
        data: {
          ...node,
          label: node.name,
          degree,
          color: degreeColor24(degree, minDegree, maxDegree),
          size: 36 + Math.min((node.frequency || 1) * 5, 32),
          shape: shapeByTextbook[node.textbook_id || ''] || 'ellipse',
        },
      }
    }),
    ...props.edges.map((edge) => ({
      data: {
        ...edge,
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
            shape: 'data(shape)',
            color: '#111827',
            'font-size': 11,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,
            'border-width': 2,
            'border-color': '#e2e8f0',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
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
        { selector: 'node.highlighted', style: { 'border-width': 4, 'border-color': '#0f172a', 'z-index': 10 } },
        { selector: 'edge.highlighted', style: { width: 6, 'arrow-scale': 1.35, 'z-index': 10 } },
        { selector: '.faded', style: { opacity: 0.22 } },
      ],
    })
    cy.on('tap', 'node', (event) => {
      emit('node-selected', event.target.data())
    })
    cy.on('dblclick', 'node', (event) => {
      const node = event.target
      const neighborIds = new Set()
      neighborIds.add(node.id())
      node.neighborhood().nodes().forEach((n) => neighborIds.add(n.id()))
      emit('node-selected', node.data())
      const ids = [...neighborIds]
      const collection = cy.collection(
        ids.map((id) => cy.getElementById(id)).filter((el) => el.length),
      )
      if (collection.length) {
        cy.elements().addClass('faded')
        collection.removeClass('faded').addClass('highlighted')
        collection.connectedEdges().removeClass('faded').addClass('highlighted')
        cy.animate({ fit: { eles: collection, padding: 90 } }, { duration: 300 })
      }
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
