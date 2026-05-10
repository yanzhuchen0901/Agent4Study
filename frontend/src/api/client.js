import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/',
  timeout: 10000,
})

export async function getHealth() {
  const response = await apiClient.get('/health')
  return response.data
}

export async function uploadTextbook(file, textbookId = '') {
  const form = new FormData()
  form.append('file', file)
  if (textbookId) {
    form.append('textbook_id', textbookId)
  }
  const response = await apiClient.post('/api/ingestion/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function listTextbooks() {
  const response = await apiClient.get('/api/ingestion/list')
  return response.data
}

export async function deleteTextbook(textbookId) {
  const response = await apiClient.delete(`/api/ingestion/${textbookId}`)
  return response.data
}

export async function buildGraph(textbookId) {
  const response = await apiClient.post('/api/graph/build', { textbook_id: textbookId })
  return response.data
}

export async function listGraphNodes(textbookId = '') {
  const response = await apiClient.get('/api/graph/nodes', {
    params: textbookId ? { textbook_id: textbookId } : {},
  })
  return response.data
}

export async function listGraphEdges(textbookId = '') {
  const response = await apiClient.get('/api/graph/edges', {
    params: textbookId ? { textbook_id: textbookId } : {},
  })
  return response.data
}

export async function searchGraphNodes(query) {
  const response = await apiClient.get('/api/graph/search', { params: { q: query } })
  return response.data
}

export async function mergeGraph() {
  const response = await apiClient.post('/api/graph/merge')
  return response.data
}

export async function getMergeStatus() {
  const response = await apiClient.get('/api/graph/merge/status')
  return response.data
}

export async function queryGraph(question, depth = 2) {
  const response = await apiClient.post('/api/graph/query', { question, depth })
  return response.data
}
