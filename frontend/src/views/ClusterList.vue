<template>
  <div class="h-full overflow-y-auto">
    <div class="p-6">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">智能体集群</h1>
        <button @click="showCreate = true" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition">+ 创建集群</button>
      </div>

      <div v-if="loading" class="text-center py-16 text-gray-400">⏳ 加载中...</div>

      <div v-else-if="!clusters.length" class="text-center py-16 text-gray-400">
        <div class="text-4xl mb-3">🌐</div>
        <div class="text-lg mb-2">还没有集群</div>
        <p class="text-sm mb-4">集群可以让多个智能体协作完成复杂工作流</p>
        <button @click="showCreate = true" class="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm">创建第一个集群</button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="c in clusters" :key="c.id"
          class="bg-white rounded-xl p-4 shadow hover:shadow-md transition cursor-pointer"
          @click="$router.push(`/clusters/${c.id}`)">
          <div class="flex items-center gap-3 mb-2">
            <span class="text-3xl">{{ c.icon }}</span>
            <div>
              <div class="font-bold text-lg">{{ c.name }}</div>
              <div class="text-xs text-gray-400">{{ c.member_count }} 个成员</div>
            </div>
          </div>
          <div class="text-sm text-gray-500 line-clamp-2 min-h-[2.5rem]">{{ c.description || '暂无描述' }}</div>
        </div>
      </div>

      <!-- 创建弹窗 -->
      <div v-if="showCreate" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showCreate = false">
        <div class="bg-white rounded-xl p-6 w-96">
          <h2 class="text-lg font-bold mb-4">创建集群</h2>
          <div class="space-y-3">
            <input v-model="form.name" class="w-full border rounded-lg px-3 py-2" placeholder="集群名称" />
            <textarea v-model="form.description" class="w-full border rounded-lg px-3 py-2" rows="3" placeholder="描述集群的用途"></textarea>
            <input v-model="form.icon" class="w-20 border rounded-lg px-3 py-2 text-center text-xl" placeholder="🌐" />
          </div>
          <div class="flex gap-2 mt-4">
            <button @click="handleCreate" :disabled="!form.name" class="bg-blue-500 text-white px-4 py-2 rounded-lg disabled:opacity-50">创建</button>
            <button @click="showCreate = false" class="bg-gray-100 px-4 py-2 rounded-lg">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getClusters, createCluster, unwrap } from '../api.js'

const clusters = ref([])
const loading = ref(true)
const showCreate = ref(false)
const form = ref({ name: '', description: '', icon: '🌐' })

async function load() {
  loading.value = true
  try { clusters.value = unwrap(await getClusters()) || [] }
  catch (e) { /* ignore */ }
  finally { loading.value = false }
}

async function handleCreate() {
  try {
    await createCluster(form.value)
    showCreate.value = false
    form.value = { name: '', description: '', icon: '🌐' }
    await load()
  } catch (e) { /* ignore */ }
}

onMounted(load)
</script>