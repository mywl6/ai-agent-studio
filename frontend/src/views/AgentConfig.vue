<template>
  <div class="h-full overflow-y-auto">
    <div class="p-3 sm:p-6 max-w-4xl mx-auto">
      <!-- Header -->
      <div class="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
        <button @click="safeBack" class="text-gray-400 hover:text-gray-600 text-lg">←</button>
        <h1 class="text-lg sm:text-xl font-bold">{{ isEdit ? '编辑智能体' : '创建智能体' }}</h1>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-16 text-gray-400">
        <div class="text-3xl mb-2 animate-pulse">⏳</div>
        <div>加载中...</div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-16">
        <div class="text-3xl mb-2">❌</div>
        <div class="text-red-500 mb-4">{{ error }}</div>
        <button @click="load" class="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm">重试</button>
      </div>

      <!-- Form -->
      <div v-else class="bg-white rounded-xl p-3 sm:p-6 shadow">
        <!-- No model warning -->
        <div v-if="!models.length" class="mb-3 sm:mb-4 p-2.5 sm:p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs sm:text-sm text-yellow-700">
          ⚠️ 暂无可用模型，请先在「设置」中添加模型
          <router-link to="/settings" class="underline ml-1 sm:ml-2 font-medium">前往设置</router-link>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-x-4 sm:gap-x-6 gap-y-4 sm:gap-y-5">
          <!-- Left column -->
          <div class="space-y-4 sm:space-y-5">
            <!-- 名称 -->
            <div>
              <label class="block text-xs sm:text-sm font-medium mb-1">名称 *</label>
              <input v-model="form.name" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400" placeholder="智能体名称" />
            </div>

            <!-- 模型选择 - 两步级联 -->
            <div>
              <label class="block text-xs sm:text-sm font-medium mb-1">绑定模型 *</label>

              <!-- 已选模型显示 + 切换按钮 -->
              <div v-if="form.model_id && selectedModelInfo" class="flex items-center gap-2 mb-2">
                <span class="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">{{ selectedModelInfo.provider_name }}</span>
                <span class="text-sm font-medium">{{ selectedModelInfo.name }}</span>
                <button @click="resetModelSelection" class="text-xs text-gray-400 hover:text-red-500 ml-1">重新选择</button>
              </div>

              <!-- Step 1: 选择提供商 -->
              <div v-if="!modelStep2" class="border rounded-lg p-2">
                <div class="text-xs text-gray-400 mb-2 px-1">选择提供商</div>
                <div class="grid grid-cols-2 gap-1.5">
                  <button v-for="p in providerList" :key="p.name"
                    @click="selectProviderForModel(p)"
                    class="flex items-center gap-2 px-3 py-2 rounded-lg text-left hover:bg-gray-100 transition text-sm border border-transparent hover:border-gray-200">
                    <span class="text-base">{{ providerIcon(p.type) }}</span>
                    <div class="min-w-0">
                      <div class="font-medium truncate">{{ p.name }}</div>
                      <div class="text-xs text-gray-400">{{ p.models.length }} 个模型</div>
                    </div>
                  </button>
                </div>
                <div v-if="!providerList.length" class="text-xs text-gray-400 text-center py-3">暂无提供商</div>
              </div>

              <!-- Step 2: 选择模型 -->
              <div v-else class="border rounded-lg p-2">
                <div class="flex items-center gap-2 mb-2 px-1">
                  <button @click="modelStep2 = false" class="text-xs text-gray-400 hover:text-gray-600">← 返回</button>
                  <span class="text-xs text-gray-400">选择模型</span>
                  <span class="text-xs font-medium text-gray-600">{{ step2Provider?.name }}</span>
                </div>
                <div class="max-h-48 overflow-y-auto space-y-0.5">
                  <button v-for="m in step2Models" :key="m.id"
                    @click="selectModel(m)"
                    class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left hover:bg-gray-100 transition text-sm"
                    :class="{ 'bg-blue-50 border border-blue-200': form.model_id === m.id }">
                    <div class="min-w-0">
                      <div class="font-medium truncate">{{ m.name }}</div>
                      <div class="text-xs text-gray-400 font-mono">{{ m.model_id }}</div>
                    </div>
                    <span v-if="form.model_id === m.id" class="text-blue-500 text-sm shrink-0">✓</span>
                  </button>
                </div>
                <div v-if="!step2Models.length" class="text-xs text-gray-400 text-center py-3">该提供商暂无模型</div>
              </div>
            </div>

            <!-- 头像 + Temperature -->
            <div class="flex gap-3 sm:gap-4">
              <div class="w-16 sm:w-24 shrink-0">
                <label class="block text-xs sm:text-sm font-medium mb-1">头像</label>
                <input v-model="form.avatar" class="w-full border rounded-lg px-2 sm:px-3 py-2 text-center text-xl sm:text-2xl focus:outline-none focus:border-blue-400" placeholder="🤖" />
              </div>
              <div class="flex-1">
                <label class="block text-xs sm:text-sm font-medium mb-1">Temperature: {{ (form.temperature / 100).toFixed(2) }}</label>
                <input type="range" v-model.number="form.temperature" min="0" max="200" class="w-full" />
                <div class="flex justify-between text-xs text-gray-400"><span>严谨 0.0</span><span>创意 2.0</span></div>
              </div>
            </div>

            <!-- Token + History + Search -->
            <div class="flex gap-3 sm:gap-4">
              <div class="flex-1">
                <label class="block text-xs sm:text-sm font-medium mb-1">最大 Token</label>
                <input type="number" v-model.number="form.max_tokens" min="100" max="128000" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
              </div>
              <div class="flex-1">
                <label class="block text-xs sm:text-sm font-medium mb-1">历史轮数</label>
                <input type="number" v-model.number="form.max_history" min="1" max="50" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
              </div>
            </div>
            <div>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="form.search_enabled" class="rounded" />
                <span class="text-xs sm:text-sm font-medium">🌐 联网搜索</span>
              </label>
              <p class="text-[10px] sm:text-xs text-gray-400 mt-0.5 ml-5">AI 在对话中可自动联网获取最新信息</p>
            </div>
          </div>

          <!-- Right column -->
          <div class="space-y-4 sm:space-y-5">
            <!-- 描述 -->
            <div>
              <label class="block text-xs sm:text-sm font-medium mb-1">描述</label>
              <textarea v-model="form.description" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400" rows="3" placeholder="描述这个智能体的能力..."></textarea>
            </div>

            <!-- System Prompt -->
            <div class="flex-1 flex flex-col">
              <label class="block text-xs sm:text-sm font-medium mb-1">System Prompt</label>
              <textarea v-model="form.system_prompt" class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 flex-1 min-h-[100px] sm:min-h-[120px]" rows="5" placeholder="设定角色性格和能力..."></textarea>
            </div>
          </div>
        </div>

        <!-- 绑定工具 - 全宽 -->
        <div class="mt-4 sm:mt-5">
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs sm:text-sm font-medium">绑定工具（{{ form.tools.length }} 个已选）</label>
            <input v-model="toolSearch" class="w-32 sm:w-48 border rounded-lg px-2 sm:px-3 py-1.5 text-xs sm:text-sm focus:outline-none focus:border-blue-400" placeholder="搜索工具..." />
          </div>
          <div class="border rounded-lg max-h-64 overflow-y-auto">
            <div v-if="!tools.length" class="text-gray-400 text-sm text-center py-8">
              暂无可用工具，请先在工具市场创建
            </div>
            <template v-for="(catTools, catName) in filteredToolsByCategory" :key="catName">
              <div v-if="catTools.length" class="py-1">
                <div class="text-[10px] sm:text-xs font-bold text-gray-500 px-2 sm:px-3 py-1 sm:py-1.5 bg-gray-50 border-y">{{ catName }}</div>
                <div v-for="tool in catTools" :key="tool.name"
                  class="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2 cursor-pointer hover:bg-gray-50 transition text-xs sm:text-sm border-b border-gray-50 last:border-0"
                  :class="{ 'bg-blue-50': form.tools.includes(tool.name) }"
                  @click="toggleTool(tool.name)">
                  <input type="checkbox" :checked="form.tools.includes(tool.name)" class="rounded shrink-0" />
                  <span class="text-sm sm:text-base shrink-0">{{ tool.icon }}</span>
                  <div class="min-w-0 flex-1">
                    <span class="font-medium">{{ tool.display_name || tool.name }}</span>
                    <span class="text-[10px] sm:text-xs text-gray-400 ml-1 line-clamp-1 hidden sm:inline">{{ tool.description || '暂无描述' }}</span>
                  </div>
                </div>
              </div>
            </template>
            <div v-if="noToolSearchResult" class="text-gray-400 text-xs sm:text-sm text-center py-4">
              未找到匹配「{{ toolSearch }}」的工具
            </div>
          </div>
        </div>

        <!-- 按钮 -->
        <div class="flex gap-2 sm:gap-3 pt-4 sm:pt-5 border-t mt-4 sm:mt-5">
          <button @click="save" :disabled="!canSave || saving"
            class="bg-blue-500 text-white px-4 sm:px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm flex-1 sm:flex-none">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button @click="safeBack" class="bg-gray-100 text-gray-700 px-4 sm:px-6 py-2 rounded-lg hover:bg-gray-200 transition text-sm flex-1 sm:flex-none">取消</button>
          <div v-if="saveError" class="text-xs sm:text-sm text-red-600 self-center ml-2">{{ saveError }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAgent, createAgent, updateAgent, getModels, getTools, getErrMsg, unwrap } from '../api.js'

const route = useRoute()
const router = useRouter()
const agentId = Number(route.params.id)
const isEdit = computed(() => agentId > 0)

const models = ref([])
const tools = ref([])
const saving = ref(false)
const loading = ref(true)
const error = ref('')
const saveError = ref('')
const toolSearch = ref('')

// ── 模型级联选择状态 ──
const modelStep2 = ref(false)
const step2Provider = ref(null)
const step2Models = ref([])

const providerIconMap = { openai: '🤖', anthropic: '🧠', deepseek: '🔍', ollama: '🦙', aliyun: '☁️', custom: '⚙️' }
function providerIcon(type) { return providerIconMap[type] || '⚙️' }

const providerList = computed(() => {
  const groups = {}
  for (const m of models.value) {
    const pid = m.provider_id
    if (!groups[pid]) groups[pid] = { id: pid, name: m.provider_name || '未知', type: m.provider_type || 'custom', models: [] }
    groups[pid].models.push(m)
  }
  return Object.values(groups)
})

const selectedModelInfo = computed(() => {
  if (!form.value.model_id) return null
  return models.value.find(m => m.id === form.value.model_id) || null
})

function selectProviderForModel(provider) {
  step2Provider.value = provider
  step2Models.value = provider.models
  modelStep2.value = true
}

function selectModel(m) {
  form.value.model_id = m.id
  if (m.temperature != null) form.value.temperature = m.temperature
  if (m.max_tokens) form.value.max_tokens = m.max_tokens
  modelStep2.value = false
}

function resetModelSelection() {
  form.value.model_id = ''
  modelStep2.value = false
}

function toggleTool(name) {
  const idx = form.value.tools.indexOf(name)
  if (idx >= 0) form.value.tools.splice(idx, 1)
  else form.value.tools.push(name)
}

const toolsByCategory = computed(() => {
  const groups = {}
  for (const t of tools.value) {
    const cat = t.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(t)
  }
  return groups
})

const filteredToolsByCategory = computed(() => {
  const q = toolSearch.value.trim().toLowerCase()
  if (!q) return toolsByCategory.value
  const result = {}
  for (const [cat, catTools] of Object.entries(toolsByCategory.value)) {
    const filtered = catTools.filter(t =>
      (t.name || '').toLowerCase().includes(q) ||
      (t.display_name || '').toLowerCase().includes(q) ||
      (t.description || '').toLowerCase().includes(q)
    )
    if (filtered.length) result[cat] = filtered
  }
  return result
})

const noToolSearchResult = computed(() => {
  if (!toolSearch.value.trim()) return false
  return Object.values(filteredToolsByCategory.value).every(arr => arr.length === 0)
})

const canSave = computed(() => {
  return form.value.name && form.value.model_id && models.value.length > 0
})

const form = ref({
  name: '', avatar: '🤖', description: '', model_id: '',
  system_prompt: '你是一个有用的 AI 助手。',
  tools: [], temperature: 70, max_tokens: 4096, max_history: 20,
  search_enabled: true,
})

async function load() {
  loading.value = true
  error.value = ''
  saveError.value = ''
  try {
    const [modelsRes, toolsRes] = await Promise.all([getModels(), getTools()])
    models.value = unwrap(modelsRes)
    tools.value = unwrap(toolsRes)
    if (isEdit.value) {
      const r = await getAgent(agentId)
      if (r.data) Object.assign(form.value, r.data)
    }
  } catch (e) {
    error.value = getErrMsg(e, '网络错误')
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  saveError.value = ''
  try {
    const data = { ...form.value }
    if (isEdit.value) {
      await updateAgent(agentId, data)
    } else {
      await createAgent(data)
    }
    router.push('/agents')
  } catch (e) {
    saveError.value = getErrMsg(e, '保存失败')
  } finally {
    saving.value = false
  }
}

function safeBack() {
  if (window.history.length > 1) router.back()
  else router.push('/agents')
}

onMounted(load)
</script>
