<template>
  <div class="h-full overflow-y-auto">
    <div class="p-6 max-w-5xl mx-auto">
      <div class="flex items-center gap-3 mb-6">
        <button @click="$router.push('/clusters')" class="text-gray-400 hover:text-gray-600">← 返回</button>
        <h1 class="text-xl font-bold">{{ cluster?.icon }} {{ cluster?.name }}</h1>
      </div>

      <div v-if="!cluster" class="text-center py-16 text-gray-400">加载中...</div>

      <template v-else>
        <!-- 概述 -->
        <div class="bg-white rounded-xl p-4 shadow mb-6">
          <div class="text-sm text-gray-600">{{ cluster.description || '暂无描述' }}</div>
          <div class="text-xs text-gray-400 mt-2">共享目录：{{ cluster.shared_dir }}</div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 成员列表 -->
          <div class="bg-white rounded-xl p-4 shadow">
            <div class="flex items-center justify-between mb-3">
              <h2 class="font-bold">成员（{{ cluster.members?.length || 0 }}）</h2>
              <button @click="showAddMember = true" class="text-sm text-blue-500 hover:text-blue-700">+ 添加</button>
            </div>
            <div v-if="!cluster.members?.length" class="text-gray-400 text-sm text-center py-4">暂无成员</div>
            <div v-for="m in cluster.members" :key="m.id"
              class="flex items-center gap-2 py-2 border-b last:border-0 text-sm">
              <span class="text-xs bg-gray-100 px-2 py-0.5 rounded">{{ m.role }}</span>
              <span class="font-mono text-xs">Agent #{{ m.agent_id }}</span>
              <span v-if="m.workspace_enabled" class="text-xs text-green-500">工作空间</span>
              <button @click="handleRemoveMember(m.id)" class="ml-auto text-red-400 hover:text-red-600 text-xs">移除</button>
            </div>
          </div>

          <!-- 工作流列表 -->
          <div class="bg-white rounded-xl p-4 shadow">
            <div class="flex items-center justify-between mb-3">
              <h2 class="font-bold">工作流（{{ cluster.workflows?.length || 0 }}）</h2>
              <button @click="showCreateWorkflow = true" class="text-sm text-blue-500 hover:text-blue-700">+ 创建</button>
            </div>
            <div v-if="!cluster.workflows?.length" class="text-gray-400 text-sm text-center py-4">暂无工作流</div>
            <div v-for="w in cluster.workflows" :key="w.id"
              class="py-2 border-b last:border-0 cursor-pointer hover:bg-gray-50 px-2 rounded"
              @click="$router.push(`/clusters/${clusterId}/workflows/${w.id}`)">
              <div class="flex items-center justify-between">
                <span class="font-medium text-sm">{{ w.name }}</span>
                <span class="text-xs text-gray-400">{{ w.step_count }} 步骤</span>
              </div>
              <div class="text-xs text-gray-400 line-clamp-1">{{ w.description }}</div>
            </div>
          </div>
        </div>

        <!-- 任务列表 -->
        <div class="bg-white rounded-xl p-4 shadow mt-6">
          <h2 class="font-bold mb-3">任务</h2>
          <div v-if="!tasks.length" class="text-gray-400 text-sm text-center py-4">暂无任务</div>
          <div v-for="t in tasks" :key="t.id"
            class="flex items-center gap-3 py-2 border-b last:border-0 text-sm">
            <span class="text-xs px-2 py-0.5 rounded" :class="statusClass(t.status)">{{ t.status }}</span>
            <span class="flex-1">{{ t.title }}</span>
            <span class="text-xs text-gray-400">{{ t.current_step }}/{{ t.total_steps }}</span>
            <button v-if="t.status === 'pending'" @click="handleExecute(t.id)"
              class="text-blue-500 hover:text-blue-700 text-xs">执行</button>
          </div>
        </div>
      </template>

      <!-- 添加成员弹窗 -->
      <div v-if="showAddMember" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showAddMember = false">
        <div class="bg-white rounded-xl p-6 w-80">
          <h2 class="text-lg font-bold mb-4">添加成员</h2>
          <select v-model.number="memberForm.agent_id" class="w-full border rounded-lg px-3 py-2 mb-3">
            <option value="0">选择智能体</option>
            <option v-for="a in agents" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
          <select v-model="memberForm.role" class="w-full border rounded-lg px-3 py-2 mb-3">
            <option value="member">成员</option>
            <option value="leader">负责人</option>
            <option value="observer">观察者</option>
          </select>
          <div class="flex gap-2">
            <button @click="handleAddMember" :disabled="!memberForm.agent_id" class="bg-blue-500 text-white px-4 py-2 rounded-lg disabled:opacity-50">添加</button>
            <button @click="showAddMember = false" class="bg-gray-100 px-4 py-2 rounded-lg">取消</button>
          </div>
        </div>
      </div>

      <!-- 创建工作流弹窗 -->
      <div v-if="showCreateWorkflow" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showCreateWorkflow = false">
        <div class="bg-white rounded-xl p-6 w-96">
          <h2 class="text-lg font-bold mb-4">创建工作流</h2>
          <div class="space-y-3">
            <input v-model="wfForm.name" class="w-full border rounded-lg px-3 py-2" placeholder="工作流名称" />
            <textarea v-model="wfForm.description" class="w-full border rounded-lg px-3 py-2" rows="3" placeholder="描述工作流的流程"></textarea>
          </div>
          <div class="flex gap-2 mt-4">
            <button @click="handleCreateWorkflow" :disabled="!wfForm.name" class="bg-blue-500 text-white px-4 py-2 rounded-lg disabled:opacity-50">创建</button>
            <button @click="showCreateWorkflow = false" class="bg-gray-100 px-4 py-2 rounded-lg">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getCluster, getAgents, addClusterMember, removeClusterMember, createClusterTask, getClusterTasks, executeClusterTask, unwrap } from '../api.js'
import { createWorkflow } from '../api.js'

const route = useRoute()
const clusterId = Number(route.params.id)
const cluster = ref(null)
const agents = ref([])
const tasks = ref([])
const showAddMember = ref(false)
const showCreateWorkflow = ref(false)
const memberForm = ref({ agent_id: 0, role: 'member' })
const wfForm = ref({ name: '', description: '' })

function statusClass(s) {
  return {
    'pending': 'bg-gray-100 text-gray-600',
    'running': 'bg-blue-100 text-blue-600',
    'completed': 'bg-green-100 text-green-600',
    'failed': 'bg-red-100 text-red-600',
  }[s] || 'bg-gray-100'
}

async function load() {
  try {
    cluster.value = (await getCluster(clusterId)).data
    agents.value = unwrap(await getAgents()) || []
    tasks.value = unwrap(await getClusterTasks(clusterId)) || []
  } catch (e) { /* ignore */ }
}

async function handleAddMember() {
  try {
    await addClusterMember({ cluster_id: clusterId, ...memberForm.value })
    showAddMember.value = false
    memberForm.value = { agent_id: 0, role: 'member' }
    await load()
  } catch (e) { /* ignore */ }
}

async function handleRemoveMember(id) {
  try { await removeClusterMember(id); await load() }
  catch (e) { /* ignore */ }
}

async function handleCreateWorkflow() {
  try {
    await createWorkflow({ cluster_id: clusterId, ...wfForm.value, steps: [], hooks: [] })
    showCreateWorkflow.value = false
    wfForm.value = { name: '', description: '' }
    await load()
  } catch (e) { /* ignore */ }
}

async function handleExecute(taskId) {
  try { await executeClusterTask(taskId); await load() }
  catch (e) { /* ignore */ }
}

onMounted(load)
</script>