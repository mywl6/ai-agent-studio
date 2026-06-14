<template>
  <div class="h-full overflow-y-auto">
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">智能体广场</h1>
        <button @click="$router.push('/agents/0/config')" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition">+ 创建智能体</button>
      </div>

      <div v-if="loading" class="text-center py-16 text-gray-400">
        <div class="text-3xl mb-2 animate-pulse">⏳</div>
        <div>加载中...</div>
      </div>

      <div v-else-if="!agents.length" class="text-center py-16 text-gray-400">
        <div class="text-4xl mb-3">🤖</div>
        <div class="text-lg mb-2">还没有智能体</div>
        <button @click="$router.push('/agents/0/config')" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition text-sm">创建第一个智能体</button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="agent in agents" :key="agent.id" class="bg-white rounded-xl p-4 shadow hover:shadow-md transition">
          <div class="text-4xl mb-2 text-center">{{ agent.avatar }}</div>
          <div class="font-bold text-lg text-center">{{ agent.name }}</div>
          <div class="text-gray-500 text-sm text-center mt-1 line-clamp-2 min-h-[2.5rem]">{{ agent.description || '暂无描述' }}</div>
          <div class="flex items-center justify-center gap-2 mt-3">
            <span class="text-xs bg-gray-100 px-2 py-0.5 rounded">{{ agent.model_id }}</span>
            <span class="text-xs text-gray-400">{{ agent.tool_count }} 工具</span>
          </div>
          <div class="flex gap-2 mt-4">
            <button @click="goChat(agent)" class="flex-1 bg-blue-500 text-white text-sm py-1.5 rounded-lg hover:bg-blue-600 transition">对话</button>
            <button @click="$router.push(`/agents/${agent.id}/config`)" class="flex-1 bg-gray-100 text-gray-700 text-sm py-1.5 rounded-lg hover:bg-gray-200 transition">编辑</button>
            <button @click="handleClone(agent)" class="text-gray-400 hover:text-gray-600 transition" title="复制">📋</button>
            <button @click="handleDelete(agent)" class="text-red-400 hover:text-red-600 transition" title="删除">🗑️</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAgents, deleteAgent as delAgent, cloneAgent, unwrap } from '../api.js'

const router = useRouter()
const agents = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    agents.value = unwrap(await getAgents())
  } catch (e) { /* ignore */ }
  finally { loading.value = false }
}

function goChat(agent) {
  router.push({ path: '/', query: { agent_id: agent.id } })
}

async function handleDelete(agent) {
  if (!confirm(`确定删除智能体「${agent.name}」？`)) return
  try {
    await delAgent(agent.id)
    await load()
  } catch (e) { /* ignore */ }
}

async function handleClone(agent) {
  try {
    await cloneAgent(agent.id)
    await load()
  } catch (e) { /* ignore */ }
}

onMounted(load)
</script>