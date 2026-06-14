<template>
  <div class="h-full overflow-y-auto">
  <div class="p-6 max-w-3xl mx-auto">
    <div class="flex items-center gap-3 mb-6">
      <button @click="$router.back()" class="text-gray-400 hover:text-gray-600">← 返回</button>
      <h1 class="text-xl font-bold">工具生成器</h1>
    </div>

    <!-- 步骤指示 -->
    <div class="flex gap-4 mb-6">
      <div v-for="(step, i) in steps" :key="i" class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
          :class="currentStep >= i ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'">{{ i + 1 }}</div>
        <span class="text-sm" :class="currentStep >= i ? 'text-blue-600' : 'text-gray-400'">{{ step }}</span>
        <span v-if="i < steps.length - 1" class="text-gray-300 mx-2">→</span>
      </div>
    </div>

    <!-- 步骤 1: 选择类型 -->
    <div v-if="currentStep === 0" class="bg-white rounded-xl p-6 shadow space-y-3">
      <div v-for="opt in typeOptions" :key="opt.value"
        @click="inputType = opt.value; currentStep = 1"
        class="border rounded-lg p-4 cursor-pointer hover:border-blue-400 transition">
        <div class="font-bold">{{ opt.label }}</div>
        <div class="text-sm text-gray-500">{{ opt.desc }}</div>
      </div>
    </div>

    <!-- 步骤 2: 输入内容 -->
    <div v-if="currentStep === 1" class="bg-white rounded-xl p-6 shadow">
      <div v-if="genError" class="mb-3 text-sm text-red-600 bg-red-50 rounded-lg p-3">{{ genError }}</div>
      <textarea v-model="inputContent" class="w-full border rounded-lg px-3 py-2 font-mono text-sm" rows="15"
        :placeholder="inputPlaceholder"></textarea>
      <div class="flex gap-2 mt-4">
        <button @click="currentStep = 0" class="bg-gray-100 px-4 py-2 rounded-lg">上一步</button>
        <button @click="handleGenerate" :disabled="!inputContent.trim() || generating"
          class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50">
          {{ generating ? '生成中...' : '生成代码' }}
        </button>
      </div>
    </div>

    <!-- 步骤 3: 预览和保存 -->
    <div v-if="currentStep === 2" class="bg-white rounded-xl p-6 shadow">
      <div v-if="genError" class="mb-3 text-sm text-red-600 bg-red-50 rounded-lg p-3">{{ genError }}</div>

      <div class="mb-3">
        <label class="text-sm font-medium">工具名称（英文）</label>
        <input v-model="toolName" class="w-full border rounded-lg px-3 py-2 mt-1" placeholder="如 weather_api" />
      </div>
      <div class="mb-3">
        <label class="text-sm font-medium">显示名称</label>
        <input v-model="displayName" class="w-full border rounded-lg px-3 py-2 mt-1" placeholder="如 天气查询" />
      </div>
      <div class="mb-3">
        <label class="text-sm font-medium">工具描述 *</label>
        <textarea v-model="toolDescription" class="w-full border rounded-lg px-3 py-2 mt-1" rows="2"
          placeholder="详细描述工具的用途和功能，AI 通过此描述决定何时调用此工具"></textarea>
        <div v-if="saveError" class="text-xs text-red-500 mt-1">{{ saveError }}</div>
      </div>
      <div class="flex gap-3 mb-3">
        <div class="flex-1">
          <label class="text-sm font-medium">图标</label>
          <input v-model="toolIcon" class="w-full border rounded-lg px-3 py-2 mt-1 text-center text-xl" placeholder="🔧" />
        </div>
        <div class="flex-1">
          <label class="text-sm font-medium">分类</label>
          <select v-model="toolCategory" class="w-full border rounded-lg px-3 py-2 mt-1">
            <option v-for="c in categories" :key="c.name" :value="c.name">{{ c.icon }} {{ c.name }}</option>
            <option value="通用">📦 通用</option>
          </select>
        </div>
      </div>
      <div class="mb-3">
        <label class="text-sm font-medium">代码预览</label>
        <textarea v-model="generatedCode" class="w-full border rounded-lg px-3 py-2 font-mono text-sm mt-1" rows="12"></textarea>
      </div>
      <div class="flex gap-2">
        <button @click="currentStep = 1" class="bg-gray-100 px-4 py-2 rounded-lg">重新生成</button>
        <button @click="handleSave" :disabled="saving" class="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50">
          {{ saving ? '保存中...' : '保存工具' }}
        </button>
      </div>
    </div>

    <!-- 保存成功 -->
    <div v-if="saved" class="bg-green-50 border border-green-200 rounded-xl p-4 mt-4 text-green-700">
      工具已保存！AI 现在可以通过描述理解并使用此工具。
      <router-link to="/tools" class="underline ml-2">前往工具市场</router-link>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { generateTool, saveTool, getCategories, getErrMsg, unwrap } from '../api.js'

const steps = ['选择类型', '输入内容', '预览保存']
const currentStep = ref(0)
const inputType = ref('openapi')
const inputContent = ref('')
const generating = ref(false)
const generatedCode = ref('')
const toolName = ref('')
const displayName = ref('')
const toolDescription = ref('')
const toolIcon = ref('🔧')
const toolCategory = ref('通用')
const saving = ref(false)
const saved = ref(false)
const genError = ref('')
const saveError = ref('')
const categories = ref([])

const typeOptions = [
  { value: 'openapi', label: 'OpenAPI / Swagger JSON', desc: '粘贴 OpenAPI 3.0 格式的 JSON 文档' },
  { value: 'curl', label: 'curl 命令', desc: '粘贴 curl 命令，自动生成对应工具' },
  { value: 'desc', label: '文字描述', desc: '用自然语言描述 API 接口的功能' },
]

const inputPlaceholder = computed(() => {
  const map = {
    openapi: '粘贴 OpenAPI/Swagger JSON...',
    curl: '粘贴 curl 命令...',
    desc: '描述 API 接口：如「调用 XX 系统的订单查询接口，传入订单号返回订单信息」',
  }
  return map[inputType.value] || ''
})

async function loadCategories() {
  try {
    categories.value = unwrap(await getCategories()) || []
  } catch (e) { /* ignore */ }
}

async function handleGenerate() {
  generating.value = true
  genError.value = ''
  try {
    const r = await generateTool({ type: inputType.value, content: inputContent.value })
    if (r.data.error) {
      genError.value = r.data.error
      return
    }
    generatedCode.value = r.data.code
    toolName.value = r.data.suggested_name
    displayName.value = ''
    toolDescription.value = ''
    toolIcon.value = '🔧'
    toolCategory.value = categories.value[0]?.name || '通用'
    currentStep.value = 2
  } catch (e) {
    genError.value = getErrMsg(e, '生成失败')
  } finally {
    generating.value = false
  }
}

async function handleSave() {
  if (!toolDescription.value) {
    saveError.value = '请填写工具描述，AI 需要通过描述来理解工具的用途'
    return
  }
  saving.value = true
  saveError.value = ''
  try {
    await saveTool({
      name: toolName.value,
      code: generatedCode.value,
      display_name: displayName.value || toolName.value,
      description: toolDescription.value,
      icon: toolIcon.value,
      category: toolCategory.value,
    })
    saved.value = true
  } catch (e) {
    saveError.value = getErrMsg(e, '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadCategories)
</script>