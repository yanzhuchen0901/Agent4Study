import { createRouter, createWebHistory } from 'vue-router'

import AgentView from '../views/AgentView.vue'
import KnowledgeGraphView from '../views/KnowledgeGraphView.vue'
import KnowledgeMergeView from '../views/KnowledgeMergeView.vue'
import RAGQueryView from '../views/RAGQueryView.vue'
import ReportView from '../views/ReportView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  { path: '/', name: 'knowledge-graph', component: KnowledgeGraphView },
  { path: '/rag', name: 'rag-query', component: RAGQueryView },
  { path: '/merge', name: 'knowledge-merge', component: KnowledgeMergeView },
  { path: '/agent', name: 'agent', component: AgentView },
  { path: '/report', name: 'report', component: ReportView },
  { path: '/settings', name: 'settings', component: SettingsView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
