import axios from 'axios'

export const apiClient = axios.create({
    baseURL: '/',
    timeout: 10000,
})

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        window.dispatchEvent(
            new CustomEvent('a4s-api-error', {
                detail: error.response?.data?.detail || error.message || '网络请求失败',
            }),
        )
        return Promise.reject(error)
    },
)

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

export async function getParsedTextbook(textbookId) {
    const response = await apiClient.get(`/api/ingestion/parsed/${textbookId}`)
    return response.data
}

export function getRawTextbookUrl(textbookId) {
    return `/api/ingestion/raw/${textbookId}`
}

export async function deleteTextbook(textbookId) {
    const response = await apiClient.delete(`/api/ingestion/${textbookId}`)
    return response.data
}

export function getLLMConfig() {
    const apiKey = (localStorage.getItem('a4s.llmApiKey') || '').trim()
    const baseUrl = (localStorage.getItem('a4s.llmBaseUrl') || '').trim()
    const model = (localStorage.getItem('a4s.llmModel') || '').trim()

    const config = {}
    if (apiKey) config.api_key = apiKey
    if (baseUrl) config.base_url = baseUrl
    if (model) config.model = model
    return Object.keys(config).length ? config : null
}

export async function buildGraph(textbookId) {
    const response = await apiClient.post('/api/graph/build', { textbook_id: textbookId, llm_config: getLLMConfig() })
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
    const response = await apiClient.post('/api/graph/merge', { llm_config: getLLMConfig() })
    return response.data
}

export async function previewMergeGraph() {
    const response = await apiClient.post('/api/graph/merge/preview', { llm_config: getLLMConfig() })
    return response.data
}

export async function confirmMergeGraph(decisions) {
    const response = await apiClient.post('/api/graph/merge/confirm', { decisions, llm_config: getLLMConfig() })
    return response.data
}

export async function getMergeStatus() {
    const response = await apiClient.get('/api/graph/merge/status')
    return response.data
}

export async function queryGraph(question, depth = 2) {
    const response = await apiClient.post('/api/graph/query', { question, depth, llm_config: getLLMConfig() })
    return response.data
}

export async function indexRAG(textbookId) {
    const response = await apiClient.post('/api/rag/index', { textbook_id: textbookId })
    return response.data
}

export async function queryRAG(query, topK = 5) {
    const response = await apiClient.post('/api/rag/query', { query, top_k: topK, llm_config: getLLMConfig() })
    return response.data
}

export async function getRAGStatus() {
    const response = await apiClient.get('/api/rag/status')
    return response.data
}

export async function queryAgent(question) {
    const response = await apiClient.post('/api/agent/query', { question, llm_config: getLLMConfig() })
    return response.data
}

export async function getSettings() {
    const response = await apiClient.get('/api/settings')
    return response.data
}

export async function getReportMarkdown() {
    const response = await apiClient.get('/api/report/markdown')
    return response.data
}