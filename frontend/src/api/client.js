import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/',
  timeout: 10000,
})

export async function getHealth() {
  const response = await apiClient.get('/health')
  return response.data
}
