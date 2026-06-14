<template>
  <div class="p-3 sm:p-6 max-w-4xl mx-auto">
    <h1 class="text-xl sm:text-2xl font-bold mb-4 sm:mb-6">设置</h1>

    <!-- ═══════════ 模型提供商管理 ═══════════ -->
    <div class="bg-white rounded-xl p-3 sm:p-6 shadow mb-4 sm:mb-6">
      <div class="flex items-center justify-between mb-3 sm:mb-4">
        <h2 class="text-base sm:text-lg font-bold">模型提供商</h2>
        <button @click="openAddProviderModal" class="bg-blue-500 text-white px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg text-xs sm:text-sm hover:bg-blue-600">添加提供商</button>
      </div>

      <div v-if="!providers.length" class="text-center py-8 sm:py-10 text-gray-400 text-sm">
        暂无提供商，请先添加一个模型提供商
      </div>

      <!-- 提供商手风琴 -->
      <div class="space-y-2">
        <div v-for="p in providers" :key="p.id" class="border rounded-lg overflow-hidden">
          <!-- 提供商头部 - 点击展开/收起 -->
          <div class="flex items-center justify-between px-3 sm:px-4 py-2.5 sm:py-3 cursor-pointer hover:bg-gray-50 transition select-none"
               @click="toggleProvider(p.id)">
            <div class="flex items-center gap-2 sm:gap-3 min-w-0">
              <span class="text-base sm:text-lg shrink-0">{{ providerIcon(p.type) }}</span>
              <div class="min-w-0">
                <div class="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                  <span class="font-medium text-xs sm:text-sm">{{ p.name }}</span>
                  <span class="text-[10px] sm:text-xs bg-gray-200 text-gray-600 px-1 sm:px-1.5 py-0.5 rounded">{{ p.model_count }} 模型</span>
                  <span v-if="!p.enabled" class="text-[10px] sm:text-xs bg-red-100 text-red-500 px-1 sm:px-1.5 py-0.5 rounded">禁用</span>
                </div>
                <div class="text-[10px] sm:text-xs text-gray-400 mt-0.5 font-mono truncate max-w-[200px] sm:max-w-none">{{ p.api_key_masked }}</div>
              </div>
            </div>
            <div class="flex items-center gap-1 sm:gap-2 shrink-0 ml-2">
              <button @click.stop="handleFetchModels(p)" class="text-blue-500 hover:text-blue-700 text-[10px] sm:text-xs">
                {{ fetchingId === p.id ? '...' : '获取模型' }}
              </button>
              <button @click.stop="openAddModelModal(p)" class="text-green-500 hover:text-green-700 text-[10px] sm:text-xs hidden sm:inline">添加</button>
              <button @click.stop="handleEditProvider(p)" class="text-gray-500 hover:text-gray-700 text-[10px] sm:text-xs hidden sm:inline">编辑</button>
              <button @click.stop="handleDeleteProvider(p)" class="text-red-500 hover:text-red-700 text-[10px] sm:text-xs hidden sm:inline">删除</button>
              <span class="text-gray-400 text-xs ml-1 transition-transform" :class="{ 'rotate-180': expandedProviders.has(p.id) }">▼</span>
            </div>
          </div>

          <!-- 小屏幕操作按钮（展开时显示） -->
          <div v-if="expandedProviders.has(p.id)" class="flex gap-2 px-3 sm:hidden pb-2 border-b bg-gray-50">
            <button @click="openAddModelModal(p)" class="text-green-500 hover:text-green-700 text-xs flex-1 text-center py-1">添加模型</button>
            <button @click="handleEditProvider(p)" class="text-gray-500 hover:text-gray-700 text-xs flex-1 text-center py-1">编辑</button>
            <button @click="handleDeleteProvider(p)" class="text-red-500 hover:text-red-700 text-xs flex-1 text-center py-1">删除</button>
          </div>

          <!-- 模型列表（展开时显示） -->
          <div v-if="expandedProviders.has(p.id)">
            <div v-if="getProviderModels(p.id).length" class="divide-y">
              <div v-for="m in getProviderModels(p.id)" :key="m.id"
                class="flex items-center justify-between px-3 sm:px-4 py-2 sm:py-2.5 hover:bg-gray-50 transition">
                <div class="flex items-center gap-2 sm:gap-3 min-w-0">
                  <span :class="m.enabled ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'" class="w-1.5 sm:w-2 h-1.5 sm:h-2 rounded-full shrink-0"></span>
                  <div class="min-w-0">
                    <div class="flex items-center gap-1.5">
                      <span class="text-xs sm:text-sm font-medium truncate max-w-[120px] sm:max-w-none">{{ m.name }}</span>
                      <span v-if="m.is_default" class="text-[10px] sm:text-xs bg-blue-100 text-blue-600 px-1 rounded">默认</span>
                    </div>
                    <div class="text-[10px] sm:text-xs text-gray-400 font-mono mt-0.5 truncate max-w-[150px] sm:max-w-none">{{ m.model_id }}</div>
                  </div>
                </div>
                <div class="flex items-center gap-1.5 sm:gap-3 shrink-0 ml-2">
                  <button @click="handleTest(m)" class="text-blue-500 hover:text-blue-700 text-[10px] sm:text-xs">
                    {{ testingId === m.id ? '...' : '测试' }}
                  </button>
                  <button @click="handleEditModel(m)" class="text-green-500 hover:text-green-700 text-[10px] sm:text-xs hidden sm:inline">编辑</button>
                  <button @click="setDefault(m)" v-if="!m.is_default" class="text-gray-400 hover:text-blue-500 text-[10px] sm:text-xs hidden sm:inline">默认</button>
                  <button @click="handleDeleteModel(m)" class="text-red-500 hover:text-red-700 text-[10px] sm:text-xs hidden sm:inline">删除</button>
                  <!-- 小屏幕：长按或点击展开操作 -->
                  <div class="relative sm:hidden" v-if="expandedModel === m.id">
                    <div class="absolute right-0 top-full mt-1 bg-white border rounded-lg shadow-lg z-10 py-1 min-w-[80px]">
                      <button @click="handleEditModel(m)" class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50">编辑</button>
                      <button @click="setDefault(m)" v-if="!m.is_default" class="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50">设为默认</button>
                      <button @click="handleDeleteModel(m)" class="w-full text-left px-3 py-1.5 text-xs text-red-500 hover:bg-gray-50">删除</button>
                    </div>
                  </div>
                  <button @click.stop="expandedModel = expandedModel === m.id ? null : m.id" class="text-gray-400 text-xs sm:hidden">⋯</button>
                </div>
              </div>
            </div>
            <div v-else class="px-3 sm:px-4 py-3 text-[10px] sm:text-xs text-gray-400 text-center">
              暂无模型，点击「获取模型」或「添加」
            </div>
          </div>
        </div>
      </div>

      <div v-if="testResult" class="mt-3 text-xs sm:text-sm" :class="testResult.ok ? 'text-green-600' : 'text-red-600'">
        {{ testResult.ok ? `✅ 连通！延迟 ${testResult.latency}s` : `❌ ${testResult.error}` }}
        <div v-if="testResult.detail" class="text-[10px] sm:text-xs text-gray-500 mt-1">{{ testResult.detail }}</div>
      </div>
    </div>

    <!-- 数据备份 -->
    <div class="bg-white rounded-xl p-3 sm:p-6 shadow mb-4 sm:mb-6">
      <h2 class="text-base sm:text-lg font-bold mb-3 sm:mb-4">数据备份</h2>
      <button @click="handleExport" class="bg-gray-100 text-gray-700 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg hover:bg-gray-200 text-xs sm:text-sm">导出数据库</button>
    </div>

    <!-- 关于 -->
    <div class="bg-white rounded-xl p-3 sm:p-6 shadow">
      <h2 class="text-base sm:text-lg font-bold mb-2">关于</h2>
      <div class="text-xs sm:text-sm text-gray-600 space-y-1">
        <div>应用名称：AI Agent 平台</div>
        <div>版本：1.0.0</div>
        <div>协议：MIT</div>
      </div>
    </div>

    <!-- ═══════════ 添加/编辑提供商弹窗 ═══════════ -->
    <div v-if="showProviderModal" class="fixed inset-0 bg-black/30 flex items-end sm:items-center justify-center z-50" @click.self="closeProviderModal">
      <div class="bg-white rounded-t-xl sm:rounded-xl p-4 sm:p-6 w-full sm:w-[480px] max-h-[85vh] overflow-y-auto">
        <h2 class="text-base sm:text-lg font-bold mb-3 sm:mb-4">{{ editingProvider ? '编辑提供商' : '添加提供商' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">提供商类型</label>
            <select v-model="providerForm.type" :disabled="!!editingProvider" class="w-full border rounded-lg px-3 py-2 text-sm disabled:bg-gray-50">
              <option value="">请选择</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="deepseek">DeepSeek</option>
              <option value="ollama">Ollama (本地)</option>
              <option value="aliyun">阿里云 (通义)</option>
              <option value="custom">自定义 (OpenAI 兼容)</option>
            </select>
          </div>
          <div>
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">名称</label>
            <input v-model="providerForm.name" class="w-full border rounded-lg px-3 py-2 text-sm" placeholder="给提供商起个名字" />
          </div>
          <div>
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input v-model="providerForm.api_key" type="password" class="w-full border rounded-lg px-3 py-2 text-sm" :placeholder="editingProvider ? '留空则不修改' : '输入 API Key'" />
          </div>
          <div>
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">Base URL</label>
            <input v-model="providerForm.base_url" :disabled="providerForm.type !== 'custom' && providerForm.type !== 'ollama'" class="w-full border rounded-lg px-3 py-2 text-sm disabled:bg-gray-50" placeholder="API 端点地址" />
          </div>
        </div>
        <div class="flex gap-2 mt-4 sm:mt-5">
          <button @click="handleSaveProvider" :disabled="!providerForm.type || !providerForm.name" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 text-sm flex-1 sm:flex-none">保存</button>
          <button @click="closeProviderModal" class="bg-gray-100 px-4 py-2 rounded-lg text-sm flex-1 sm:flex-none">取消</button>
        </div>
      </div>
    </div>

    <!-- ═══════════ 添加/编辑模型弹窗 ═══════════ -->
    <div v-if="showModelModal" class="fixed inset-0 bg-black/30 flex items-end sm:items-center justify-center z-50" @click.self="closeModelModal">
      <div class="bg-white rounded-t-xl sm:rounded-xl p-4 sm:p-6 w-full sm:w-[520px] max-h-[85vh] overflow-y-auto">
        <h2 class="text-base sm:text-lg font-bold mb-3 sm:mb-4">{{ editingModel ? '编辑模型' : '添加模型' }}</h2>

        <div v-if="!editingModel" class="space-y-3">
          <div class="flex items-center gap-2 text-xs sm:text-sm text-gray-500">
            <span>提供商：</span>
            <span class="font-medium text-gray-700">{{ currentProviderName }}</span>
          </div>
          <div>
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">选择模型</label>
            <select v-model="modelForm.preset_id" @change="onPresetSelect" class="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">请选择模型</option>
              <option v-for="preset in providerPresets" :key="preset.id" :value="preset.id">
                {{ preset.name }}{{ preset.max_tokens ? ` (${preset.max_tokens > 1000 ? (preset.max_tokens / 1000) + 'K' : preset.max_tokens})` : '' }}
              </option>
              <option value="__custom__">自定义模型...</option>
            </select>
          </div>
          <div v-if="modelForm.preset_id === '__custom__'">
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">模型 ID</label>
            <input v-model="modelForm.custom_model_id" class="w-full border rounded-lg px-3 py-2 text-sm" placeholder="输入模型 ID（如 gpt-4o）" />
          </div>
        </div>

        <div class="space-y-3 mt-3" :class="{ 'mt-0': editingModel }">
          <div v-if="editingModel">
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">模型 ID</label>
            <input :value="editingModel.model_id" disabled class="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50" />
          </div>
          <div>
            <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">显示名称</label>
            <input v-model="modelForm.name" class="w-full border rounded-lg px-3 py-2 text-sm" placeholder="给模型起个名字" />
          </div>
          <div class="flex gap-3">
            <div class="flex-1">
              <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">最大 Token</label>
              <input v-model.number="modelForm.max_tokens" type="number" min="100" class="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div class="flex-1">
              <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1">Temp ({{ (modelForm.temperature / 100).toFixed(2) }})</label>
              <input type="range" v-model.number="modelForm.temperature" min="0" max="200" class="w-full mt-1" />
            </div>
          </div>
        </div>

        <div class="flex gap-2 mt-4 sm:mt-5 pt-3 border-t">
          <button @click="handleSaveModel" :disabled="!canSaveModel" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 text-sm flex-1 sm:flex-none">保存</button>
          <button @click="closeModelModal" class="bg-gray-100 px-4 py-2 rounded-lg text-sm flex-1 sm:flex-none">取消</button>
        </div>
      </div>
    </div>

    <!-- ═══════════ 获取模型弹窗 ═══════════ -->
    <div v-if="showFetchModal" class="fixed inset-0 bg-black/30 flex items-end sm:items-center justify-center z-50" @click.self="closeFetchModal">
      <div class="bg-white rounded-t-xl sm:rounded-xl p-4 sm:p-6 w-full sm:w-[560px] max-h-[85vh] overflow-y-auto">
        <h2 class="text-base sm:text-lg font-bold mb-2 sm:mb-4">选择要添加的模型</h2>
        <p class="text-xs sm:text-sm text-gray-500 mb-2 sm:mb-3">从「{{ fetchProviderName }}」获取到以下模型：</p>

        <div v-if="!fetchedModels.length" class="text-center py-6 text-gray-400 text-sm">未获取到模型</div>

        <div v-else class="space-y-0.5 border rounded-lg divide-y max-h-64 sm:max-h-80 overflow-y-auto">
          <label v-for="m in fetchedModels" :key="m.id"
            class="flex items-center gap-2 sm:gap-3 px-2.5 sm:px-3 py-2 sm:py-2.5 cursor-pointer hover:bg-gray-50 transition"
            :class="{ 'bg-blue-50': fetchedSelected.has(m.id) }">
            <input type="checkbox" :checked="fetchedSelected.has(m.id)" @change="toggleFetched(m.id)" class="rounded shrink-0" />
            <div class="min-w-0 flex-1">
              <div class="text-xs sm:text-sm font-medium truncate">{{ m.name || m.id }}</div>
              <div class="text-[10px] sm:text-xs text-gray-400 font-mono truncate">{{ m.id }}</div>
            </div>
            <span v-if="m.context_window" class="text-[10px] sm:text-xs text-gray-400 shrink-0">{{ Math.round(m.context_window / 1000) }}K</span>
            <span v-if="fetchProviderId && existingModelIdsByProvider[fetchProviderId]?.has(m.id)" class="text-[10px] sm:text-xs text-green-500 shrink-0">已有</span>
          </label>
        </div>

        <div class="flex gap-2 mt-3 sm:mt-4">
          <button @click="handleBatchAddModels" :disabled="fetchedSelected.size === 0" class="bg-blue-500 text-white px-3 sm:px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 text-xs sm:text-sm flex-1 sm:flex-none">
            添加 {{ fetchedSelected.size }} 个模型
          </button>
          <button @click="closeFetchModal" class="bg-gray-100 px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm flex-1 sm:flex-none">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  getProviders, addProvider, updateProvider, deleteProvider, fetchProviderModels,
  getModels, addModel, updateModel, testModel, deleteModel, setDefaultModel,
  exportDb, getErrMsg, unwrap,
} from '../api.js'

const providers = ref([])
const models = ref([])
const showProviderModal = ref(false)
const showModelModal = ref(false)
const showFetchModal = ref(false)
const editingProvider = ref(null)
const editingModel = ref(null)
const testingId = ref(null)
const fetchingId = ref(null)
const testResult = ref(null)
const fetchedModels = ref([])
const fetchedSelected = ref(new Set())
const fetchProviderName = ref('')
const fetchProviderId = ref(null)
const expandedProviders = ref(new Set())
const expandedModel = ref(null)

const providerForm = ref({ name: '', type: '', api_key: '', base_url: '' })
const modelForm = ref({ preset_id: '', custom_model_id: '', name: '', max_tokens: 4096, temperature: 70 })

const providerIconMap = { openai: '🤖', anthropic: '🧠', deepseek: '🔍', ollama: '🦙', aliyun: '☁️', custom: '⚙️' }

const providerDefaults = {
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com/v1',
  anthropic: 'https://api.anthropic.com/v1',
  ollama: 'http://localhost:11434/v1',
  aliyun: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  custom: '',
}

const providerModelPresets = {
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o', max_tokens: 128000 },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', max_tokens: 128000 },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', max_tokens: 128000 },
    { id: 'o1', name: 'o1', max_tokens: 200000 },
    { id: 'o1-mini', name: 'o1-mini', max_tokens: 128000 },
    { id: 'o3-mini', name: 'o3-mini', max_tokens: 200000 },
  ],
  anthropic: [
    { id: 'claude-opus-4-20250514', name: 'Claude Opus 4', max_tokens: 200000 },
    { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', max_tokens: 200000 },
    { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', max_tokens: 200000 },
    { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', max_tokens: 200000 },
  ],
  deepseek: [
    { id: 'deepseek-chat', name: 'DeepSeek Chat (V3)', max_tokens: 65536 },
    { id: 'deepseek-reasoner', name: 'DeepSeek Reasoner (R1)', max_tokens: 65536 },
  ],
  aliyun: [
    { id: 'qwen-max', name: 'Qwen Max', max_tokens: 32000 },
    { id: 'qwen-plus', name: 'Qwen Plus', max_tokens: 131072 },
    { id: 'qwen-turbo', name: 'Qwen Turbo', max_tokens: 131072 },
    { id: 'qwen-coder-plus', name: 'Qwen Coder Plus', max_tokens: 131072 },
  ],
  ollama: [
    { id: 'llama3.1', name: 'Llama 3.1', max_tokens: 8192 },
    { id: 'qwen2.5', name: 'Qwen 2.5', max_tokens: 8192 },
    { id: 'deepseek-r1', name: 'DeepSeek R1', max_tokens: 8192 },
  ],
  custom: [],
}

function providerIcon(type) { return providerIconMap[type] || '⚙️' }

function toggleProvider(pid) {
  const s = new Set(expandedProviders.value)
  if (s.has(pid)) s.delete(pid)
  else s.add(pid)
  expandedProviders.value = s
  expandedModel.value = null
}

function getProviderModels(providerId) {
  return models.value.filter(m => m.provider_id === providerId)
}

const currentProviderName = computed(() => {
  const p = providers.value.find(p => p.id === modelForm.value._provider_id)
  return p ? p.name : ''
})

const providerPresets = computed(() => {
  const p = providers.value.find(p => p.id === modelForm.value._provider_id)
  return p ? (providerModelPresets[p.type] || []) : []
})

const existingModelIdsByProvider = computed(() => {
  const map = {}
  for (const m of models.value) {
    const pid = m.provider_id
    if (!map[pid]) map[pid] = new Set()
    map[pid].add(m.model_id)
  }
  return map
})

const canSaveModel = computed(() => {
  return modelForm.value.name && (modelForm.value.model_id || modelForm.value.custom_model_id)
})

async function loadAll() {
  const [pRes, mRes] = await Promise.all([getProviders(), getModels()])
  providers.value = unwrap(pRes)
  models.value = unwrap(mRes)
}

function openAddProviderModal() {
  editingProvider.value = null
  providerForm.value = { name: '', type: '', api_key: '', base_url: '' }
  showProviderModal.value = true
}

function handleEditProvider(p) {
  editingProvider.value = p
  providerForm.value = { name: p.name, type: p.type, api_key: '', base_url: p.base_url }
  showProviderModal.value = true
}

function closeProviderModal() {
  showProviderModal.value = false
  editingProvider.value = null
}

async function handleSaveProvider() {
  const form = providerForm.value
  if (!form.type || !form.name) return
  if (!editingProvider.value && !form.api_key) {
    alert('请输入 API Key')
    return
  }
  const base_url = form.base_url || providerDefaults[form.type] || ''
  try {
    if (editingProvider.value) {
      await updateProvider(editingProvider.value.id, { ...form, base_url })
    } else {
      await addProvider({ ...form, base_url })
    }
    closeProviderModal()
    await loadAll()
  } catch (e) {
    alert(getErrMsg(e, '保存失败'))
  }
}

async function handleDeleteProvider(p) {
  if (!confirm(`确定删除提供商「${p.name}」及其所有模型？`)) return
  await deleteProvider(p.id)
  await loadAll()
}

function openAddModelModal(provider) {
  editingModel.value = null
  modelForm.value = { preset_id: '', custom_model_id: '', name: '', max_tokens: 4096, temperature: 70, _provider_id: provider.id }
  showModelModal.value = true
}

function handleEditModel(m) {
  editingModel.value = m
  modelForm.value = { name: m.name, max_tokens: m.max_tokens, temperature: m.temperature, _provider_id: m.provider_id, preset_id: '', custom_model_id: '' }
  showModelModal.value = true
  expandedModel.value = null
}

function closeModelModal() {
  showModelModal.value = false
  editingModel.value = null
}

function onPresetSelect() {
  const pid = modelForm.value.preset_id
  if (pid === '__custom__' || !pid) {
    modelForm.value.name = ''
    return
  }
  const preset = providerPresets.value.find(p => p.id === pid)
  if (preset) {
    modelForm.value.name = preset.name
    modelForm.value.max_tokens = preset.max_tokens || 4096
  }
}

async function handleSaveModel() {
  const form = modelForm.value
  const modelId = editingModel.value ? editingModel.value.model_id : (form.preset_id === '__custom__' ? form.custom_model_id : form.preset_id)
  if (!modelId || !form.name) return

  const payload = {
    provider_id: form._provider_id,
    model_id: modelId,
    name: form.name,
    max_tokens: form.max_tokens,
    temperature: form.temperature,
  }

  try {
    if (editingModel.value) {
      await updateModel(editingModel.value.id, payload)
    } else {
      await addModel(payload)
    }
    closeModelModal()
    await loadAll()
  } catch (e) {
    alert(getErrMsg(e, '保存失败'))
  }
}

async function handleTest(m) {
  testingId.value = m.id
  testResult.value = null
  try {
    testResult.value = (await testModel(m.id)).data
  } catch (e) {
    testResult.value = { ok: false, error: e.message }
  }
  testingId.value = null
}

async function handleDeleteModel(m) {
  if (!confirm(`确定删除模型「${m.name}」？`)) return
  await deleteModel(m.id)
  expandedModel.value = null
  await loadAll()
}

async function setDefault(m) {
  try {
    await setDefaultModel(m.id)
    expandedModel.value = null
    await loadAll()
  } catch (e) {
    alert(getErrMsg(e, '设置失败'))
  }
}

async function handleFetchModels(p) {
  fetchingId.value = p.id
  fetchProviderName.value = p.name
  fetchProviderId.value = p.id
  fetchedSelected.value = new Set()
  try {
    const res = await fetchProviderModels(p.id)
    fetchedModels.value = res.data.models || []
    showFetchModal.value = true
  } catch (e) {
    alert(getErrMsg(e, '获取模型列表失败'))
  }
  fetchingId.value = null
}

function toggleFetched(id) {
  const s = new Set(fetchedSelected.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  fetchedSelected.value = s
}

function closeFetchModal() {
  showFetchModal.value = false
  fetchedModels.value = []
  fetchedSelected.value = new Set()
}

async function handleBatchAddModels() {
  const pid = fetchProviderId.value
  const existing = existingModelIdsByProvider.value[pid] || new Set()
  let count = 0
  for (const mid of fetchedSelected.value) {
    if (existing.has(mid)) continue
    const m = fetchedModels.value.find(x => x.id === mid)
    try {
      await addModel({
        provider_id: pid,
        model_id: mid,
        name: m?.name || mid,
        max_tokens: m?.context_window || 4096,
        temperature: 70,
      })
      count++
    } catch (e) {
      // 跳过已存在的
    }
  }
  closeFetchModal()
  await loadAll()
  if (count > 0) alert(`成功添加 ${count} 个模型`)
}

async function handleExport() {
  const r = await exportDb()
  const url = URL.createObjectURL(new Blob([r.data]))
  const a = document.createElement('a')
  a.href = url; a.download = 'app.db'; a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadAll)
</script>
