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
