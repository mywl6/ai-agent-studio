<template>
  <div class="h-full overflow-y-auto">
    <div class="p-6 max-w-4xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">MCP 服务器</h1>
        <button @click="showCreate = true" class="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-600">+ 添加服务器</button>
      </div>

      <div v-if="loading" class="text-center py-16 text-gray-400">⏳ 加载中...</div>

      <div v-else-if="!servers.length" class="text-center py-16 text-gray-400">
        <div class="text-4xl mb-3">🔌</div>
        <div class="text-lg mb-2">还没有 MCP 服务器</div>
        <p class="text-sm mb-4">MCP（Model Context Protocol）让 AI 工具可以通过标准协议发现和调用</p>
        <button @click="showCreate = true" class="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm">添加第一个 MCP 服务器</button>
      </div>

      <div v-else class="space-y-3">
        <div v-for="s in servers" :key="s.id" class="bg-white rounded-xl p-4 shadow">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-bold">{{ s.name }}</div>
              <div class="text-xs text-gray-400">{{ s.server_type }} · {{ s.enabled ? '已启用' : '已禁用' }}</div>
            </div>
            <div class="flex gap-2">
              <button @click="handleDiscover(s)" :disabled="discovering === s.id"
                class="text-xs text-purple-500 hover:text-purple-700">
                {{ discovering === s.id ? '发现中...' : '发现工具' }}
              </button>
              <button @click="handleToggle(s)" class="text-xs text-gray-500 hover:text-gray-700">
                {{ s.enabled ? '禁用' : '启用' }}
              </button>
              <button @click="handleDelete(s)" class="text-xs text-red-500 hover:text-red-700">删除</button>
            </div>
          </div>
          <div class="text-sm text-gray-500 mt-1">{{ s.description || '暂无描述' }}</div>
          <div v-if="s.command" class="text-xs text-gray-400 mt-1 font-mono">{{ s.command }} {{ (s.args || []).join(' ') }}</div>
          <div v-if="s.url" class="text-xs text-gray-400 mt-1">{{ s.url }}</div>
          <div v-if="s.tools?.length" class="mt-2">
            <div class="text-xs font-medium text-gray-500 mb-1">已发现 {{ s.tools.length }} 个工具：</div>
            <div class="flex flex-wrap gap-1">
              <span v-for="t in s.tools" :key="t.name"
                class="text-xs bg-gray-100 px-2 py-0.5 rounded">{{ t.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 创建弹窗 -->
      <div v-if="showCreate" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="showCreate = false">
        <div class="bg-white rounded-xl p-6 w-[480px] max-h-[80vh] overflow-y-auto">
          <h2 class="text-lg font-bold mb-4">添加 MCP 服务器</h2>
          <div class="space-y-3">
            <input v-model="form.name" class="w-full border rounded-lg px-3 py-2" placeholder="服务器名称" />
            <textarea v-model="form.description" class="w-full border rounded-lg px-3 py-2" rows="2" placeholder="描述"></textarea>
            <select v-model="form.server_type" class="w-full border rounded-lg px-3 py-2">
              <option value="stdio">stdio（本地进程）</option>
              <option value="sse">SSE（HTTP 服务）</option>
            </select>
            <template v-if="form.server_type === 'stdio'">
              <input v-model="form.command" class="w-full border rounded-lg px-3 py-2" placeholder="启动命令（如 npx）" />
              <input v-model="form.argsText" class="w-full border rounded-lg px-3 py-2" placeholder="参数（空格分隔）" />
            </template>
            <template v-else>
              <input v-model="form.url" class="w-full border rounded-lg px-3 py-2" placeholder="SSE URL" />
            </template>
          </div>
          <div class="flex gap-2 mt-4">
            <button @click="handleCreate" :disabled="!form.name" class="bg-blue-500 text-white px-4 py-2 rounded-lg disabled:opacity-50">保存</button>
            <button @click="showCreate = false" class="bg-gray-100 px-4 py-2 rounded-lg">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMCPServers, createMCPServer, updateMCPServer, deleteMCPServer, discoverMCPTools, unwrap } from '../api.js'

const servers = ref([])
const loading = ref(true)
const showCreate = ref(false)
const discovering = ref(null)
const form = ref({ name: '', description: '', server_type: 'stdio', command: '', argsText: '', url: '' })

async function load() {
  loading.value = true
  try { servers.value = unwrap(await getMCPServers()) || [] }
  catch (e) { /* ignore */ }
  finally { loading.value = false }
}

async function handleCreate() {
  try {
    const data = { ...form.value }
    if (data.server_type === 'stdio') {
      data.args = data.argsText ? data.argsText.split(' ').filter(Boolean) : []
      delete data.argsText
    }
    await createMCPServer(data)
    showCreate.value = false
    form.value = { name: '', description: '', server_type: 'stdio', command: '', argsText: '', url: '' }
    await load()
  } catch (e) { /* ignore */ }
}

async function handleDiscover(s) {
  discovering.value = s.id
  try {
    const r = await discoverMCPTools(s.id)
    s.tools = r.data.tools
  } catch (e) { /* ignore */ }
  finally { discovering.value = null }
}

async function handleToggle(s) {
  try { await updateMCPServer(s.id, { enabled: !s.enabled }); s.enabled = !s.enabled }
  catch (e) { /* ignore */ }
}

async function handleDelete(s) {
  if (!confirm(`确定删除 MCP 服务器「${s.name}」？`)) return
  try { await deleteMCPServer(s.id); await load() }
  catch (e) { /* ignore */ }
}

onMounted(load)
</script>