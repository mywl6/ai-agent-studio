import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from './api.js'
import { unwrap } from './api.js'

export const useModelStore = defineStore('models', () => {
  const models = ref([])
  const loading = ref(false)
  const error = ref('')
  const defaultModel = computed(() => models.value.find(m => m.is_default))
  async function load() {
    loading.value = true; error.value = ''
    try { models.value = unwrap(await api.getModels()) }
    catch (e) { error.value = e.message }
    finally { loading.value = false }
  }
  return { models, defaultModel, loading, error, load }
})

export const useProviderStore = defineStore('providers', () => {
  const providers = ref([])
  const loading = ref(false)
  async function load() {
    loading.value = true
    try { providers.value = unwrap(await api.getProviders()) || [] }
    catch (e) { /* ignore */ }
    finally { loading.value = false }
  }
  return { providers, loading, load }
})

export const useAgentStore = defineStore('agents', () => {
  const agents = ref([])
  const currentAgent = ref(null)
  const loading = ref(false)
  async function load() {
    loading.value = true
    try { agents.value = unwrap(await api.getAgents()) }
    catch (e) { /* ignore */ }
    finally { loading.value = false }
  }
  function setCurrent(agent) { currentAgent.value = agent }
  return { agents, currentAgent, loading, load, setCurrent }
})

export const useToolStore = defineStore('tools', () => {
  const tools = ref([])
  const loading = ref(false)
  async function load(source = 'all') {
    loading.value = true
    try { tools.value = unwrap(await api.getTools(source)) }
    catch (e) { /* ignore */ }
    finally { loading.value = false }
  }
  return { tools, loading, load }
})

export const useCategoryStore = defineStore('categories', () => {
  const categories = ref([])
  async function load() {
    try { categories.value = unwrap(await api.getCategories()) || [] }
    catch (e) { /* ignore */ }
  }
  return { categories, load }
})

export const useClusterStore = defineStore('clusters', () => {
  const clusters = ref([])
  const currentCluster = ref(null)
  const loading = ref(false)
  async function load() {
    loading.value = true
    try { clusters.value = unwrap(await api.getClusters()) || [] }
    catch (e) { /* ignore */ }
    finally { loading.value = false }
  }
  async function loadDetail(id) {
    try { currentCluster.value = (await api.getCluster(id)).data }
    catch (e) { /* ignore */ }
  }
  return { clusters, currentCluster, loading, load, loadDetail }
})

export const useMCPServerStore = defineStore('mcp', () => {
  const servers = ref([])
  const loading = ref(false)
  async function load() {
    loading.value = true
    try { servers.value = (await api.getMCPServers()).data || [] }
    catch (e) { /* ignore */ }
    finally { loading.value = false }
  }
  return { servers, loading, load }
})

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const conversations = ref([])
  const currentConversationId = ref(null)
  const isLoading = ref(false)
  const streamingContent = ref('')

  function addMessage(msg) { messages.value.push(msg) }
  function clearMessages() { messages.value = []; currentConversationId.value = null; streamingContent.value = '' }

  async function loadConversations(agentId) {
    try { conversations.value = unwrap(await api.getConversations(agentId)) }
    catch (e) { /* ignore */ }
  }

  async function loadMessages(convId) {
    try {
      messages.value = unwrap(await api.getMessages(convId))
      currentConversationId.value = convId
    } catch (e) { /* ignore */ }
  }

  return { messages, conversations, currentConversationId, isLoading, streamingContent, addMessage, clearMessages, loadConversations, loadMessages }
})