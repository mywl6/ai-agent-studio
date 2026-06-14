import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: `${BASE}/api`,
  timeout: 30000,
})

// ── 统一错误提取 ──
export function getErrMsg(e, fallback = '操作失败') {
  return e.response?.data?.detail || e.response?.data?.error || e.message || fallback
}

// ── 兼容分页/非分页响应 ──
export function unwrap(resp) {
  const data = resp.data
  return data?.items ?? data
}

// ── 提供商 ──
export const getProviders = () => api.get('/providers')
export const addProvider = (data) => api.post('/providers', data)
export const updateProvider = (id, data) => api.put(`/providers/${id}`, data)
export const deleteProvider = (id) => api.delete(`/providers/${id}`)
export const fetchProviderModels = (id) => api.post(`/providers/${id}/fetch_models`)

// ── 模型 ──
export const getModels = (providerId) => api.get('/models', { params: providerId ? { provider_id: providerId } : {} })
export const addModel = (data) => api.post('/models', data)
export const testModel = (id) => api.post(`/models/${id}/test`)
export const updateModel = (id, data) => api.put(`/models/${id}`, data)
export const deleteModel = (id) => api.delete(`/models/${id}`)
export const setDefaultModel = (id) => api.put(`/models/${id}/default`)

// ── 智能体 ──
export const getAgents = () => api.get('/agents')
export const getAgent = (id) => api.get(`/agents/${id}`)
export const createAgent = (data) => api.post('/agents', data)
export const updateAgent = (id, data) => api.put(`/agents/${id}`, data)
export const deleteAgent = (id) => api.delete(`/agents/${id}`)
export const cloneAgent = (id) => api.post(`/agents/${id}/clone`)

// ── 工具 ──
export const getTools = (source = 'all', category = '') => api.get('/tools', { params: { source, category } })
export const generateTool = (data) => api.post('/tools/generate', data)
export const testTool = (data) => api.post('/tools/test', data)
export const saveTool = (data) => api.post('/tools', data)
export const updateTool = (id, data) => api.put(`/tools/${id}`, data)
export const deleteTool = (id) => api.delete(`/tools/${id}`)
export const toggleTool = (id) => api.post(`/tools/${id}/toggle`)
export const reloadTools = () => api.post('/tools/reload')

// ── 分类 ──
export const getCategories = () => api.get('/categories')
export const createCategory = (data) => api.post('/categories', data)
export const updateCategory = (id, data) => api.put(`/categories/${id}`, data)
export const deleteCategory = (id) => api.delete(`/categories/${id}`)

// ── 对话 ──
export const chat = (data) => api.post('/chat', data)
export const getConversations = (agentId) => api.get('/conversations', { params: { agent_id: agentId } })
export const getMessages = (convId) => api.get(`/conversations/${convId}/messages`)
export const deleteConversation = (convId) => api.delete(`/conversations/${convId}`)

export function streamChat(agentId, message, conversationId = null, clusterId = null, searchEnabled = false, files = null) {
  const params = new URLSearchParams({ agent_id: agentId, message })
  if (conversationId) params.set('conversation_id', conversationId)
  if (clusterId) params.set('cluster_id', clusterId)
  if (searchEnabled) params.set('search_enabled', 'true')
  if (files) params.set('files', files)
  return fetch(`${BASE}/api/chat/stream?${params}`)
}

export const uploadChatFile = (formData) => api.post('/chat/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

export const createConversation = (formData) => api.post('/conversations', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
})

export const getFileContent = (convId, agentId, filename) =>
  api.get(`/conversations/${convId}/files/${encodeURIComponent(filename)}?agent_id=${agentId}`, {
    responseType: 'text',
  })

// ── 工作空间文件 ──
export const getConversationFiles = (convId, agentId) => api.get(`/conversations/${convId}/files`, { params: { agent_id: agentId } })
export const getConversationFileUrl = (convId, filepath, agentId) => {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  return `${base}/api/conversations/${convId}/files/${encodeURIComponent(filepath)}?agent_id=${agentId}`
}
export const uploadConversationFile = (convId, agentId, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/conversations/${convId}/files?agent_id=${agentId}`, form)
}

// ── 设置 ──
export const getSettings = () => api.get('/settings')
export const exportDb = () => api.get('/settings/export', { responseType: 'blob' })

// ── 集群 ──
export const getClusters = () => api.get('/clusters')
export const getCluster = (id) => api.get(`/clusters/${id}`)
export const createCluster = (data) => api.post('/clusters', data)
export const updateCluster = (id, data) => api.put(`/clusters/${id}`, data)
export const deleteCluster = (id) => api.delete(`/clusters/${id}`)

export const addClusterMember = (data) => api.post('/clusters/members', data)
export const removeClusterMember = (id) => api.delete(`/clusters/members/${id}`)
export const getAgentWorkspace = (clusterId, agentId) => api.get(`/clusters/${clusterId}/agents/${agentId}/workspace`)

export const getWorkflows = (clusterId) => api.get(`/clusters/${clusterId}/workflows`)
export const createWorkflow = (data) => api.post('/clusters/workflows', data)
export const getWorkflow = (id) => api.get(`/clusters/workflows/${id}`)
export const updateWorkflow = (id, data) => api.put(`/clusters/workflows/${id}`, data)
export const optimizeWorkflow = (id) => api.post(`/clusters/workflows/${id}/optimize`)

export const getClusterTasks = (clusterId, status = '') => api.get(`/clusters/${clusterId}/tasks`, { params: { status } })
export const createClusterTask = (data) => api.post('/clusters/tasks', data)
export const executeClusterTask = (id) => api.post(`/clusters/tasks/${id}/execute`)

// ── MCP ──
export const getMCPServers = () => api.get('/mcp')
export const createMCPServer = (data) => api.post('/mcp', data)
export const updateMCPServer = (id, data) => api.put(`/mcp/${id}`, data)
export const deleteMCPServer = (id) => api.delete(`/mcp/${id}`)
export const discoverMCPTools = (id) => api.post(`/mcp/${id}/discover`)