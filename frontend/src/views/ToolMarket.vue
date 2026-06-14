<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">工具市场</h1>
      <div class="flex gap-2">
        <button @click="$router.push('/tools/generate')" class="bg-blue-500 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-600">从 API 创建</button>
        <button @click="openManualCreate" class="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-200">手动创建</button>
        <button @click="showCategoryManager = true" class="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-sm hover:bg-gray-200">管理分类</button>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-4 mb-2 border-b">
      <button v-for="tab in tabs" :key="tab.key" @click="switchTab(tab.key)"
        class="pb-2 text-sm font-medium border-b-2 transition"
        :class="tabKey === tab.key ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500'">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-400">加载中...</div>

    <template v-else>
      <!-- 分类筛选 -->
      <div class="flex gap-2 mb-4 flex-wrap">
        <button v-for="cat in categories" :key="cat" @click="catFilter = cat"
          class="px-2 py-0.5 rounded text-xs border transition"
          :class="catFilter === cat ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-100'">
          {{ cat }}
        </button>
      </div>

      <!-- 工具列表 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="tool in filteredTools" :key="tool.name" class="bg-white rounded-xl p-4 shadow">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-2xl">{{ tool.icon }}</span>
            <div>
              <div class="font-bold">{{ tool.display_name || tool.name }}</div>
              <div class="text-xs text-gray-400">{{ tool.source }} · {{ tool.category || '未分类' }}</div>
            </div>
          </div>
          <div class="text-sm text-gray-600 mb-3 line-clamp-3 min-h-[3rem]">{{ tool.description || '暂无描述，AI 无法理解此工具的用途' }}</div>
          <div class="flex gap-2">
            <label class="flex items-center gap-1 text-sm cursor-pointer">
              <input type="checkbox" :checked="tool.enabled" @change="handleToggle(tool)" :disabled="tool.id === 0" class="rounded" />
              <span :class="tool.id === 0 ? 'text-gray-400' : ''">{{ tool.enabled ? '启用' : '禁用' }}</span>
            </label>
            <div class="flex-1"></div>
            <button v-if="tool.source === 'custom' && tool.id !== 0" @click="handleEdit(tool)" class="text-sm text-blue-500 hover:text-blue-700">编辑</button>
            <button v-if="tool.source !== 'builtin' && tool.id !== 0" @click="handleDelete(tool)" class="text-sm text-red-500 hover:text-red-700">删除</button>
          </div>
        </div>
        <div v-if="!filteredTools.length" class="col-span-full text-center text-gray-400 py-12">
          该分类下暂无工具
        </div>
      </div>
    </template>

    <!-- 手动创建弹窗 -->
    <div v-if="showManualCreate" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showManualCreate = false">
      <div class="bg-white rounded-xl p-6 w-[640px] max-h-[85vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">手动创建工具</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium">工具名称（英文）*</label>
            <input v-model="manualForm.name" class="w-full border rounded-lg px-3 py-2 mt-1" placeholder="如 weather_api" />
          </div>
          <div>
            <label class="text-sm font-medium">显示名称</label>
            <input v-model="manualForm.display_name" class="w-full border rounded-lg px-3 py-2 mt-1" placeholder="如 天气查询" />
          </div>
          <div>
            <label class="text-sm font-medium">工具描述 *</label>
            <textarea v-model="manualForm.description" class="w-full border rounded-lg px-3 py-2 mt-1" rows="2"
              placeholder="描述工具的用途，AI 通过此描述决定何时调用此工具，如「查询指定城市的实时天气信息」"></textarea>
            <div v-if="manualSaveError" class="text-xs text-red-500 mt-1">{{ manualSaveError }}</div>
          </div>
          <div class="flex gap-3">
            <div class="flex-1">
              <label class="text-sm font-medium">图标（Emoji）</label>
              <input v-model="manualForm.icon" class="w-full border rounded-lg px-3 py-2 mt-1 text-center text-xl" placeholder="🔧" />
            </div>
            <div class="flex-1">
              <label class="text-sm font-medium">分类</label>
              <select v-model="manualForm.category" class="w-full border rounded-lg px-3 py-2 mt-1">
                <option v-for="c in allCategories" :key="c.name" :value="c.name">{{ c.icon }} {{ c.name }}</option>
                <option value="通用">📦 通用</option>
              </select>
            </div>
          </div>
          <div>
            <label class="text-sm font-medium">Python 代码 *</label>
            <textarea v-model="manualForm.code" class="w-full border rounded-lg px-3 py-2 font-mono text-sm mt-1" rows="12"
              placeholder="@registry.register(name=&quot;my_tool&quot;, description=&quot;...&quot;, icon=&quot;🔧&quot;, category=&quot;通用&quot;)
def my_tool(param: str) -> str:
    &#34;&#34;&#34;工具描述&#34;&#34;&#34;
    return f&#34;Hello {param}&#34;"></textarea>
          </div>
        </div>
        <div class="flex gap-2 mt-4">
          <button @click="handleManualSave" :disabled="manualSaving" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50">
            {{ manualSaving ? '保存中...' : '保存' }}
          </button>
          <button @click="showManualCreate = false" class="bg-gray-100 px-4 py-2 rounded-lg">取消</button>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="editingTool" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="editingTool = null">
      <div class="bg-white rounded-xl p-6 w-[640px] max-h-[85vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">编辑工具：{{ editingTool.name }}</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium">显示名称</label>
            <input v-model="editForm.display_name" class="w-full border rounded-lg px-3 py-2 mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium">工具描述 *</label>
            <textarea v-model="editForm.description" class="w-full border rounded-lg px-3 py-2 mt-1" rows="2"
              placeholder="描述工具的用途，AI 通过此描述决定何时调用"></textarea>
            <div v-if="editError" class="text-xs text-red-500 mt-1">{{ editError }}</div>
          </div>
          <div class="flex gap-3">
            <div class="flex-1">
              <label class="text-sm font-medium">图标</label>
              <input v-model="editForm.icon" class="w-full border rounded-lg px-3 py-2 mt-1 text-center text-xl" />
            </div>
            <div class="flex-1">
              <label class="text-sm font-medium">分类</label>
              <select v-model="editForm.category" class="w-full border rounded-lg px-3 py-2 mt-1">
                <option v-for="c in allCategories" :key="c.name" :value="c.name">{{ c.icon }} {{ c.name }}</option>
              </select>
            </div>
          </div>
          <div>
            <label class="text-sm font-medium">Python 代码</label>
            <textarea v-model="editForm.code" class="w-full border rounded-lg px-3 py-2 font-mono text-sm mt-1" rows="12"></textarea>
          </div>
        </div>
        <div class="flex gap-2 mt-4">
          <button @click="handleEditSave" :disabled="editSaving" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50">
            {{ editSaving ? '保存中...' : '保存' }}
          </button>
          <button @click="editingTool = null" class="bg-gray-100 px-4 py-2 rounded-lg">取消</button>
        </div>
      </div>
    </div>

    <!-- 分类管理弹窗 -->
    <div v-if="showCategoryManager" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showCategoryManager = false">
      <div class="bg-white rounded-xl p-6 w-[480px] max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold">分类管理</h2>
          <button @click="startAddCategory" class="bg-blue-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-blue-600">+ 添加分类</button>
        </div>
        <div class="space-y-2">
          <div v-for="cat in allCategories" :key="cat.id || cat.name"
            class="flex items-center gap-2 p-2 border rounded-lg">
            <span class="text-xl">{{ cat.icon }}</span>
            <div class="flex-1">
              <div class="font-medium">{{ cat.name }}</div>
              <div class="text-xs text-gray-400">{{ cat.description || '无描述' }}</div>
            </div>
            <button @click="startEditCategory(cat)" class="text-blue-500 hover:text-blue-700 text-sm">编辑</button>
            <button @click="handleDeleteCategory(cat)" class="text-red-500 hover:text-red-700 text-sm">删除</button>
          </div>
          <div v-if="!allCategories.length" class="text-gray-400 text-sm text-center py-4">暂无分类</div>
        </div>

        <!-- 添加/编辑分类 -->
        <div v-if="categoryForm.show" class="mt-4 pt-4 border-t space-y-2">
          <input v-model="categoryForm.name" class="w-full border rounded-lg px-3 py-2" placeholder="分类名称" />
          <input v-model="categoryForm.description" class="w-full border rounded-lg px-3 py-2" placeholder="分类描述" />
          <input v-model="categoryForm.icon" class="w-20 border rounded-lg px-3 py-2 text-center text-xl" placeholder="📂" />
          <div class="flex gap-2">
            <button @click="handleSaveCategory" :disabled="!categoryForm.name" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50">
              保存
            </button>
            <button @click="categoryForm.show = false" class="bg-gray-100 px-4 py-2 rounded-lg">取消</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 通知 -->
    <div v-if="notification.show" class="fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg text-white text-sm z-50"
      :class="notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'">
      {{ notification.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTools, toggleTool, deleteTool, saveTool, updateTool, getErrMsg, unwrap } from '../api.js'
import { getCategories, createCategory, updateCategory, deleteCategory } from '../api.js'

const tabKey = ref('builtin')
const catFilter = ref('全部')
const loading = ref(false)
const tabs = [
  { key: 'builtin', label: '内置工具' },
  { key: 'custom', label: '自定义工具' },
  { key: 'plugin', label: '插件' },
]

const allTools = ref([])
const allCategories = ref([])

const notification = ref({ show: false, message: '', type: 'success' })

function notify(message, type = 'success') {
  notification.value = { show: true, message, type }
  setTimeout(() => { notification.value.show = false }, 3000)
}

const categories = computed(() => {
  const cats = new Set(['全部'])
  for (const t of allTools.value) {
    const match = tabKey.value === 'all' || t.source === tabKey.value ||
      (tabKey.value === 'builtin' && t.source === 'builtin')
    if (match) {
      cats.add(t.category || '未分类')
    }
  }
  return [...cats]
})

const filteredTools = computed(() => {
  return allTools.value.filter(t => {
    const sourceMatch = tabKey.value === 'all' || t.source === tabKey.value ||
      (tabKey.value === 'builtin' && t.source === 'builtin')
    if (!sourceMatch) return false
    if (catFilter.value !== '全部' && (t.category || '未分类') !== catFilter.value) return false
    return true
  })
})

function switchTab(key) {
  tabKey.value = key
  catFilter.value = '全部'
}

async function load() {
  loading.value = true
  try {
    const [toolsRes, catsRes] = await Promise.all([getTools(), getCategories()])
    allTools.value = unwrap(toolsRes)
    allCategories.value = unwrap(catsRes) || []
  } catch (e) {
    notify(getErrMsg(e, '加载失败'), 'error')
  } finally {
    loading.value = false
  }
}

async function handleToggle(tool) {
  if (tool.id === 0) return
  try {
    await toggleTool(tool.id)
    await load()
  } catch (e) {
    notify('操作失败', 'error')
  }
}

async function handleDelete(tool) {
  if (!confirm(`确定删除工具「${tool.name}」？`)) return
  try {
    await deleteTool(tool.id)
    notify('删除成功')
    await load()
  } catch (e) {
    notify('删除失败', 'error')
  }
}

// --- Manual Create ---
const showManualCreate = ref(false)
const manualSaving = ref(false)
const manualSaveError = ref('')
const manualForm = ref({ name: '', display_name: '', description: '', icon: '🔧', category: '通用', code: '' })

function openManualCreate() {
  manualForm.value = { name: '', display_name: '', description: '', icon: '🔧', category: allCategories.value[0]?.name || '通用', code: '' }
  manualSaveError.value = ''
  showManualCreate.value = true
}

async function handleManualSave() {
  if (!manualForm.value.name || !manualForm.value.code) return
  if (!manualForm.value.description) {
    manualSaveError.value = '请填写工具描述，AI 通过描述理解工具的用途'
    return
  }
  manualSaving.value = true
  manualSaveError.value = ''
  try {
    await saveTool(manualForm.value)
    showManualCreate.value = false
    notify('工具创建成功')
    await load()
  } catch (e) {
    manualSaveError.value = getErrMsg(e, '保存失败')
  } finally {
    manualSaving.value = false
  }
}

// --- Edit ---
const editingTool = ref(null)
const editSaving = ref(false)
const editError = ref('')
const editForm = ref({ display_name: '', description: '', icon: '🔧', category: '通用', code: '' })

function handleEdit(tool) {
  editingTool.value = tool
  editForm.value = {
    display_name: tool.display_name || tool.name,
    description: tool.description || '',
    icon: tool.icon || '🔧',
    category: tool.category || '通用',
    code: tool.code || '',
  }
  editError.value = ''
}

async function handleEditSave() {
  if (!editForm.value.description) {
    editError.value = '请填写工具描述，AI 通过描述理解工具的用途'
    return
  }
  editSaving.value = true
  editError.value = ''
  try {
    await updateTool(editingTool.value.id, editForm.value)
    editingTool.value = null
    notify('工具更新成功')
    await load()
  } catch (e) {
    editError.value = getErrMsg(e, '保存失败')
  } finally {
    editSaving.value = false
  }
}

// --- Category Management ---
const showCategoryManager = ref(false)
const categoryForm = ref({ show: false, editId: null, name: '', description: '', icon: '📂' })

function startAddCategory() {
  categoryForm.value = { show: true, editId: null, name: '', description: '', icon: '📂' }
}

function startEditCategory(cat) {
  categoryForm.value = { show: true, editId: cat.id || null, name: cat.name, description: cat.description || '', icon: cat.icon || '📂' }
}

async function handleSaveCategory() {
  if (!categoryForm.value.name) return
  try {
    if (categoryForm.value.editId) {
      await updateCategory(categoryForm.value.editId, {
        name: categoryForm.value.name,
        description: categoryForm.value.description,
        icon: categoryForm.value.icon,
      })
      notify('分类更新成功')
    } else {
      await createCategory({
        name: categoryForm.value.name,
        description: categoryForm.value.description,
        icon: categoryForm.value.icon,
      })
      notify('分类创建成功')
    }
    categoryForm.value.show = false
    const r = await getCategories()
    allCategories.value = r.data || []
  } catch (e) {
    notify(getErrMsg(e, '操作失败'), 'error')
  }
}

async function handleDeleteCategory(cat) {
  if (!cat.id) return
  if (!confirm(`确定删除分类「${cat.name}」？工具不会自动删除，但会失去分类关联`)) return
  try {
    await deleteCategory(cat.id)
    notify('分类已删除')
    const r = await getCategories()
    allCategories.value = r.data || []
  } catch (e) {
    notify('删除失败', 'error')
  }
}

onMounted(load)
</script>