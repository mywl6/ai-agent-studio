<template>
  <div class="h-full overflow-y-auto">
    <div class="p-6 max-w-4xl mx-auto">
      <div class="flex items-center gap-3 mb-6">
        <button @click="$router.back()" class="text-gray-400 hover:text-gray-600">← 返回</button>
        <h1 class="text-xl font-bold">工作流：{{ workflow?.name }}</h1>
      </div>

      <div v-if="!workflow" class="text-center py-16 text-gray-400">加载中...</div>

      <template v-else>
        <div class="bg-white rounded-xl p-4 shadow mb-6">
          <div class="text-sm text-gray-600 mb-4">{{ workflow.description || '暂无描述' }}</div>
          <div class="flex gap-2">
            <button @click="handleOptimize" :disabled="optimizing"
              class="bg-purple-500 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-purple-600 disabled:opacity-50">
              {{ optimizing ? '优化中...' : 'AI 优化工作流' }}
            </button>
          </div>
        </div>

        <!-- 步骤列表 -->
        <div class="bg-white rounded-xl p-4 shadow mb-6">
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-bold">步骤（{{ workflow.steps?.length || 0 }}）</h2>
          </div>
          <div v-if="!workflow.steps?.length" class="text-gray-400 text-sm text-center py-4">
            暂无步骤，点击"AI 优化工作流"自动生成
          </div>
          <div v-for="(step, i) in workflow.steps" :key="i"
            class="border rounded-lg p-3 mb-2 text-sm">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-bold">{{ step.order || i + 1 }}</span>
              <span class="font-medium">{{ step.name || `步骤 ${i + 1}` }}</span>
              <span class="text-xs bg-gray-100 px-2 py-0.5 rounded">{{ step.type || 'task' }}</span>
              <span v-if="step.agent_id" class="text-xs text-gray-400">Agent #{{ step.agent_id }}</span>
            </div>
            <div v-if="step.config" class="mt-1 text-xs text-gray-400">{{ JSON.stringify(step.config) }}</div>
            <!-- 步骤钩子 -->
            <div v-if="step.hooks?.length" class="mt-2 flex gap-1 flex-wrap">
              <span v-for="(h, hi) in step.hooks" :key="hi"
                class="text-xs bg-yellow-50 border border-yellow-200 px-1.5 py-0.5 rounded">
                🪝 {{ h.trigger }}: {{ h.type }}
              </span>
            </div>
          </div>
        </div>

        <!-- 全局钩子 -->
        <div class="bg-white rounded-xl p-4 shadow">
          <h2 class="font-bold mb-3">钩子（{{ workflow.hooks?.length || 0 }}）</h2>
          <div v-if="!workflow.hooks?.length" class="text-gray-400 text-sm text-center py-4">暂无全局钩子</div>
          <div v-for="(h, i) in workflow.hooks" :key="i"
            class="flex items-center gap-2 py-1.5 border-b last:border-0 text-sm">
            <span class="text-xs bg-yellow-100 px-2 py-0.5 rounded">{{ h.trigger }}</span>
            <span>{{ h.type }}</span>
            <span class="text-xs text-gray-400">{{ JSON.stringify(h.config) }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getWorkflow, updateWorkflow, optimizeWorkflow } from '../api.js'

const route = useRoute()
const workflow = ref(null)
const optimizing = ref(false)

async function load() {
  try {
    const wid = Number(route.params.wid)
    workflow.value = (await getWorkflow(wid)).data
  } catch (e) { /* ignore */ }
}

async function handleOptimize() {
  optimizing.value = true
  try {
    const wid = Number(route.params.wid)
    const r = await optimizeWorkflow(wid)
    workflow.value.steps = r.data.steps
    workflow.value.hooks = r.data.hooks
    workflow.value.is_optimized = true
  } catch (e) { /* ignore */ }
  finally { optimizing.value = false }
}

onMounted(load)
</script>