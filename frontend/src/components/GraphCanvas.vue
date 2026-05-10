<script setup>
import cytoscape from 'cytoscape'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  layoutName: { type: String, default: 'cose' },
  highlightedNodeIds: { type: Array, default: () => [] },
})

const emit = defineEmits(['node-selected', 'expand-neighbors'])
const container = ref(null)
let cy = null
let layout = null

const textbookShapes = ['ellipse', 'rectangle', 'diamond', 'round-triangle', 'star']
const levelShape = { book: 'rectangle', chapter: 'round-triangle' }

function degreeColor24(degree, minDegree, maxDegree) {
  if (!Number.isFinite(degree)) return '#6fb1fc'
  const steps = 24
  const clampedMin = Number.isFinite(minDegree) ? minDegree : 0
  const clampedMax = Number.isFinite(maxDegree) ? maxDegree : clampedMin
  const denom = Math.max(1, clampedMax - clampedMin)
  const ratio = Math.min(1, Math.max(0, (degree - clampedMin) / denom))
  const t = ratio
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
    const s = edge.source, t = edge.target
    if (s) degreeByNodeId.set(s, (degreeByNodeId.get(s) || 0) + 1)
    if (t) degreeByNodeId.set(t, (degreeByNodeId.get(t) || 0) + 1)
  }
  const degrees = props.nodes.map((n) => degreeByNodeId.get(n.id) || 0)
  const minDegree = degrees.length ? Math.min(...degrees) : 0
  const maxDegree = degrees.length ? Math.max(...degrees) : 1

  return [
    ...props.nodes.map((node) => {
      const degree = degreeByNodeId.get(node.id) || 0
      const nLevel = node.level || 'knowledge'
      const isB = nLevel === 'book'
      const isC = nLevel === 'chapter'
      return {
        data: {
          ...node,
          label: node.name,
          degree,
          color: isB ? '#2563eb' : isC ? '#d97706' : degreeColor24(degree, minDegree, maxDegree),
          size: isB ? 50 + Math.min((node.frequency || 1) * 2, 20)
            : isC ? 40 + Math.min((node.frequency || 1) * 2, 16)
            : 36 + Math.min((node.frequency || 1) * 5, 32),
          shape: levelShape[nLevel] || shapeByTextbook[node.textbook_id || ''] || 'ellipse',
        },
      }
    }),
    ...props.edges.map((edge) => ({ data: { ...edge } })),
  ]
})

function stopLayout() {
  if (layout && layout.stop) { try { layout.stop() } catch {} }
  layout = null
}

function runLayout(animate = false) {
  if (!cy) return
  stopLayout()
  const options = {
    name: props.layoutName,
    animate,
    animationDuration: animate ? 400 : 0,
    fit: true,
    padding: 40,
    nodeRepulsion: () => 12000,
    nodeGravityBuffer: 8,
    numIter: 250,
    idealEdgeLength: () => 120,
    gravity: 0.25,
    gravityRange: 3.8,
    gravityCompound: 1.0,
  }
  if (props.layoutName === 'cose') {
    options.nodeRepulsion = () => 15000
    options.gravity = 0.3
    options.idealEdgeLength = () => 150
  }
  layout = cy.layout(options)
  layout.run()
}

function applyHighlight() {
  if (!cy) return
  cy.elements().removeClass('highlighted faded')
  if (!props.highlightedNodeIds.length) return
  const ids = props.highlightedNodeIds.filter(Boolean)
  if (!ids.length) return
  const highlighted = cy.collection(ids.map((id) => cy.getElementById(id)).filter((e) => e.length))
  if (!highlighted.length) return
  cy.elements().addClass('faded')
  highlighted.removeClass('faded').addClass('highlighted')
  highlighted.connectedEdges().removeClass('faded').addClass('highlighted')
  highlighted.connectedEdges().connectedNodes().removeClass('faded')
}

async function renderGraph() {
  await nextTick()
  if (!container.value) return
  if (!cy) {
    cy = cytoscape({
      container: container.value,
      style: [
        { selector: 'node', style: {
          'background-color': 'data(color)', label: 'data(label)',
          width: 'data(size)', height: 'data(size)', shape: 'data(shape)',
          color: '#334155', 'font-size': 11,
          'text-valign': 'bottom', 'text-halign': 'center', 'text-margin-y': 6,
          'border-width': 1.5, 'border-color': '#e2e8f0',
          'transition-property': 'opacity, background-color',
          'transition-duration': '200ms',
        }},
        { selector: 'edge', style: {
          width: 2, 'curve-style': 'bezier', 'target-arrow-shape': 'triangle',
          'line-color': '#94a3b8', 'target-arrow-color': '#94a3b8',
          'transition-property': 'opacity, width',
          'transition-duration': '200ms',
        }},
        { selector: 'edge[relation_type = "prerequisite"]', style: { 'line-color': '#dc2626', 'target-arrow-color': '#dc2626' } },
        { selector: 'edge[relation_type = "parallel"]', style: { 'line-color': '#16a34a', 'target-arrow-color': '#16a34a' } },
        { selector: 'edge[relation_type = "contains"]', style: { 'line-color': '#d97706', 'target-arrow-color': '#d97706' } },
        { selector: 'edge[relation_type = "applies_to"]', style: { 'line-color': '#7c3aed', 'target-arrow-color': '#7c3aed' } },
        { selector: 'edge[relation_type = "overlap"]', style: { 'line-color': '#0891b2', 'target-arrow-color': '#0891b2', 'line-style': 'dashed' } },
        { selector: 'node.highlighted', style: { 'shadow-blur': 12, 'shadow-color': '#2563eb', 'shadow-opacity': 0.5, 'shadow-offset-x': 0, 'shadow-offset-y': 0, 'z-index': 10 } },
        { selector: 'edge.highlighted', style: { width: 4, 'arrow-scale': 1.2, 'z-index': 10 } },
        { selector: '.faded', style: { opacity: 0.18 } },
      ],
    })
    cy.on('tap', 'node', (e) => emit('node-selected', e.target.data()))
    cy.on('dblclick', 'node', (e) => {
      const n = e.target
      emit('node-selected', n.data())
      const ids = [n.id(), ...n.neighborhood().nodes().map((node) => node.id())]
      emit('expand-neighbors', [...new Set(ids)])
    })
    cy.on('dragfree', 'node', () => {
      stopLayout()
    })
    cy.add(elements.value)
    runLayout(true)
    applyHighlight()
  } else {
    // Re-render: batch-replace elements atomically, no animated layout
    stopLayout()
    cy.startBatch()
    cy.elements().remove()
    cy.add(elements.value)
    cy.endBatch()
    runLayout(false)
    applyHighlight()
  }
}

watch(() => [props.nodes, props.edges], renderGraph, { deep: true, immediate: true })
watch(() => props.layoutName, () => { if (cy) runLayout(true) })
watch(() => props.highlightedNodeIds, applyHighlight, { deep: true })

onBeforeUnmount(() => {
  stopLayout()
  if (cy) { cy.destroy(); cy = null }
})
</script>

<template>
  <div ref="container" class="graph-canvas">
    <div v-if="!nodes.length" class="graph-empty">暂无图谱数据</div>
  </div>
</template>
