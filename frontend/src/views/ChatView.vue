<template>
  <div class="flex h-screen overflow-hidden">
    <div class="w-48 lg:w-60 bg-white border-r flex flex-col shrink-0">
      <div class="p-3 border-b font-bold text-gray-700">智能体</div>
      <div class="flex-1 overflow-y-auto">
        <div v-for="agent in agents" :key="agent.id"
          @click="selectAgent(agent)"
          class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-gray-100"
          :class="{ 'bg-blue-50 border-r-2 border-blue-500': currentAgent?.id === agent.id }">
          <span class="text-xl">{{ agent.avatar }}</span>
          <span class="text-sm truncate">{{ agent.name }}</span>
        </div>
        <div v-if="loadingAgents" class="text-gray-400 text-sm text-center mt-4">加载中...</div>
        <div v-if="!agents.length && !loadingAgents" class="text-gray-400 text-sm text-center mt-4">暂无智能体</div>
      </div>
      <div class="p-2 border-t">
        <button @click="$router.push('/agents')" class="w-full text-sm text-blue-500 hover:text-blue-700 py-1">+ 新建智能体</button>
      </div>
    </div>

    <div class="w-44 lg:w-52 bg-gray-50 border-r flex flex-col shrink-0" v-if="currentAgent">
      <div class="p-3 border-b font-bold text-gray-700 text-sm flex justify-between items-center">
        <span>对话历史</span>
        <button @click="newConversation" class="text-blue-500 text-xs hover:text-blue-700">+ 新对话</button>
      </div>
      <div class="overflow-y-auto flex-1">
        <div v-for="conv in conversations" :key="conv.id"
          @click="loadConversation(conv)"
          class="px-3 py-2 cursor-pointer hover:bg-gray-200 text-sm"
          :class="{ 'bg-white border-l-2 border-blue-500': currentConversationId === conv.id }">
          <div class="truncate">{{ conv.title }}</div>
          <div class="text-xs text-gray-400">{{ conv.created_at?.slice(0, 16) }}</div>
        </div>
        <div v-if="!conversations.length" class="text-gray-400 text-xs text-center mt-4">暂无对话</div>
      </div>

      <div v-if="currentConversationId && files.length" class="border-t">
        <div class="p-2 text-xs font-bold text-gray-500 flex items-center justify-between">
          <span>📎 文件 ({{ files.length }})</span>
          <button @click="showFiles = !showFiles" class="text-gray-400 hover:text-gray-600">{{ showFiles ? '收起' : '展开' }}</button>
        </div>
        <div v-if="showFiles" class="max-h-40 overflow-y-auto">
          <div v-for="f in files" :key="f.filename"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs hover:bg-gray-200 cursor-pointer"
            @click="openSidebarFile(f)">
            <span>{{ fileIcon(f.mime_type) }}</span>
            <span class="truncate flex-1">{{ f.filename }}</span>
            <span class="text-gray-400 shrink-0">{{ formatSize(f.size) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex flex-col">
      <template v-if="currentAgent || currentCluster">
        <div class="h-14 border-b bg-white flex items-center px-4 gap-3 shrink-0">
          <template v-if="currentCluster">
            <span class="text-xl">{{ currentCluster.icon || '🌐' }}</span>
            <span class="font-bold">{{ currentCluster.name }}</span>
            <span class="text-xs bg-purple-100 text-purple-600 px-2 py-0.5 rounded">集群</span>
          </template>
          <template v-else-if="currentAgent">
            <span class="text-xl">{{ currentAgent.avatar }}</span>
            <span class="font-bold">{{ currentAgent.name }}</span>
            <span class="text-xs text-gray-400">{{ currentAgent.model_id }}</span>
            <span class="text-xs bg-gray-100 px-2 py-0.5 rounded">{{ currentAgent.tool_count || 0 }} 工具</span>
          </template>
          <div class="flex-1"></div>
          <div class="relative">
            <button @click="showClusterSelect = !showClusterSelect" class="text-xs text-purple-500 hover:text-purple-700 border border-purple-200 rounded px-2 py-0.5">
              {{ currentCluster ? '切换' : '集群模式' }}
            </button>
            <div v-if="showClusterSelect && clusters.length" class="absolute right-0 top-8 bg-white border rounded-lg shadow-lg z-50 w-48">
              <div v-for="c in clusters" :key="c.id"
                @click="selectCluster(c)"
                class="px-3 py-2 text-sm cursor-pointer hover:bg-purple-50"
                :class="{ 'bg-purple-50 font-medium': currentCluster?.id === c.id }">
                {{ c.icon }} {{ c.name }}
              </div>
            </div>
          </div>
          <router-link v-if="currentAgent" :to="`/agents/${currentAgent.id}/config`" class="text-gray-400 hover:text-gray-600">⚙️</router-link>
        </div>

        <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
          <div v-for="msg in messages" :key="msg.id || msg._key" class="flex flex-col"
            :class="msg.role === 'user' ? 'items-end' : 'items-start'">

            <div v-if="msg.role === 'user' && msg.files?.length" class="flex flex-wrap gap-1.5 mb-1 max-w-[70%]">
              <div v-for="f in msg.files" :key="f.filename"
                class="bg-blue-100 text-blue-700 text-xs rounded-lg px-2 py-1 flex items-center gap-1 cursor-pointer hover:bg-blue-200 transition"
                @click="openPreview(f, currentConversationId)">
                <span>{{ fileIcon(f.mime_type) }}</span>
                <span class="truncate max-w-[120px]">{{ f.filename }}</span>
              </div>
            </div>

            <div :class="msg.role === 'user'
              ? 'max-w-[70%] bg-blue-500 text-white rounded-2xl px-4 py-2 whitespace-pre-wrap'
              : msg.role === 'assistant'
                ? 'max-w-[70%] bg-gray-100 rounded-2xl px-4 py-2 markdown-body'
                : 'max-w-[80%] bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-2 text-sm'">
              <div v-if="msg.role === 'tool'" class="text-yellow-600 font-bold mb-1">🛠️ {{ msg.tool_name || '工具调用' }}</div>

              <template v-if="msg.role === 'assistant'">
                <div v-if="msg.files?.length" class="flex flex-wrap gap-2 mb-2">
                  <div v-for="f in msg.files" :key="f.filename" class="relative">
                    <img v-if="f.mime_type?.startsWith('image/') && f.data_url"
                      :src="f.data_url" class="max-w-[200px] max-h-[200px] rounded-lg cursor-pointer"
                      @click="openPreview(f)" />
                    <div v-else class="flex items-center gap-1 text-xs bg-gray-200 rounded px-2 py-1">
                      <span>{{ fileIcon(f.mime_type) }}</span>
                      <span>{{ f.filename }}</span>
                    </div>
                  </div>
                </div>
                <div v-html="renderMarkdown(msg.content)"></div>
              </template>

              <template v-else-if="msg.role === 'user'">
                <div v-if="msg._files_preview?.length" class="flex flex-wrap gap-1 mb-1">
                  <div v-for="f in msg._files_preview" :key="f.name" class="overflow-hidden"
                    :class="isImageType(f.type) ? 'rounded' : 'bg-blue-400 rounded px-1.5 py-0.5'">
                    <img v-if="isImageType(f.type) && f._dataUrl"
                      :src="f._dataUrl"
                      class="max-w-[100px] max-h-[100px] rounded cursor-pointer object-cover"
                      @click="openPreview({filename: f.name, mime_type: f.type, _dataUrl: f._dataUrl})" />
                    <span v-else class="text-xs flex items-center gap-1">
                      <span>{{ fileIcon(f.type) }}</span>
                      <span>{{ f.name }}</span>
                    </span>
                  </div>
                </div>
                {{ msg.content }}
              </template>

              <div v-else class="text-gray-600">{{ msg.content }}</div>
            </div>
          </div>

          <div v-if="isLoading" class="flex justify-start">
            <div v-if="streamingContent" class="max-w-[70%] bg-gray-100 rounded-2xl px-4 py-2 markdown-body"
              v-html="renderMarkdown(streamingContent)">
            </div>
            <div v-else class="bg-gray-100 rounded-2xl px-4 py-2 text-gray-400">
              <span class="animate-pulse">思考中...</span>
            </div>
          </div>
        </div>

        <div class="border-t bg-white shrink-0">
          <div v-if="attachedFiles.length" class="px-4 pt-3 flex flex-wrap gap-2">
            <div v-for="(f, i) in attachedFiles" :key="i"
              class="bg-blue-50 border border-blue-200 rounded-lg overflow-hidden flex items-stretch">
              <img v-if="isImageType(f.mime_type) && f._dataUrl"
                :src="f._dataUrl" class="w-10 h-10 object-cover shrink-0" />
              <div class="flex items-center gap-1.5 px-2 py-1.5 text-sm">
                <span>{{ fileIcon(f.mime_type) }}</span>
                <span class="truncate max-w-[120px]">{{ f.filename }}</span>
                <span class="text-xs text-gray-400">{{ formatSize(f.size) }}</span>
                <button @click="removeFile(i)" class="text-red-400 hover:text-red-600 ml-1">&times;</button>
              </div>
            </div>
          </div>

          <div class="p-4 flex gap-2 items-end">
            <button @click="fileInput.click()"
              class="text-gray-400 hover:text-blue-500 text-xl shrink-0 mb-1" title="上传附件">📎</button>
            <input ref="fileInput" type="file" multiple @change="handleFileSelect" class="hidden"
              accept=".txt,.md,.py,.js,.ts,.html,.css,.json,.xml,.yaml,.yml,.csv,.log,.sh,.bat,.ps1,.env,.java,.cpp,.c,.h,.go,.rs,.rb,.php,.swift,.kt,.pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.jpg,.jpeg,.png,.gif,.webp,.bmp,.svg" />

            <textarea ref="inputBox" v-model="inputText" @keydown.enter.exact.prevent="sendMessage"
              placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
              class="flex-1 border rounded-xl px-4 py-2 resize-none focus:outline-none focus:border-blue-400"
              rows="1" :disabled="isLoading"></textarea>

            <button @click="toggleSearch"
              class="text-sm border rounded-lg px-3 py-2 shrink-0 transition"
              :class="searchEnabled ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-500 border-gray-200 hover:border-blue-300'"
              :title="searchEnabled ? '联网搜索已开启' : '点击开启联网搜索'">
              🌐 {{ searchEnabled ? '已联网' : '联网' }}
            </button>

            <button @click="sendMessage" :disabled="isLoading || (!inputText.trim() && !attachedFiles.length)"
              class="bg-blue-500 text-white rounded-xl px-4 py-2 hover:bg-blue-600 disabled:opacity-50 shrink-0">▶</button>
          </div>
        </div>
      </template>
      <template v-else>
        <div class="flex-1 flex items-center justify-center text-gray-400">
          <div class="text-center">
            <div class="text-4xl mb-2">🤖</div>
            <div>选择一个智能体或启用集群模式开始对话</div>
          </div>
        </div>
      </template>
    </div>

    <!-- Preview Modal -->
    <Teleport to="body">
      <div v-if="preview.show" class="fixed inset-0 z-[999] bg-black/60 flex items-center justify-center p-4"
        @click.self="closePreview">
        <div class="bg-white rounded-xl max-w-[90vw] max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
          <div class="flex items-center justify-between px-4 py-3 border-b shrink-0">
            <div class="flex items-center gap-2 text-sm font-medium truncate">
              <span>{{ fileIcon(preview.mime_type) }}</span>
              <span class="truncate max-w-[400px]">{{ preview.filename }}</span>
            </div>
            <div class="flex items-center gap-2">
              <a v-if="preview.downloadUrl" :href="preview.downloadUrl" target="_blank"
                class="text-xs text-blue-500 hover:text-blue-700" title="下载">⬇️</a>
              <button @click="closePreview" class="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
            </div>
          </div>
          <div class="flex-1 overflow-auto p-4 min-w-[300px] min-h-[200px] flex items-center justify-center">
            <div v-if="preview.loading" class="text-gray-400">加载中...</div>
            <img v-else-if="preview.type === 'image'"
              :src="preview.src" class="max-w-full max-h-[75vh] rounded object-contain" />
            <pre v-else-if="preview.type === 'text'"
              class="w-full text-sm font-mono whitespace-pre-wrap overflow-auto max-h-[70vh] bg-gray-50 rounded p-4">{{ preview.content }}</pre>
            <iframe v-else-if="preview.type === 'pdf'"
              :src="preview.src" class="w-full h-[75vh] rounded" />
            <div v-else class="text-gray-400 text-center">
              <div class="text-3xl mb-2">{{ fileIcon(preview.mime_type) }}</div>
              <div>{{ preview.filename }}</div>
              <a :href="preview.downloadUrl" target="_blank" class="text-blue-500 underline mt-2 inline-block">下载查看</a>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import { useAgentStore, useChatStore } from '../store.js'
import { getAgents, streamChat, getConversations, getMessages, getConversationFiles, getConversationFileUrl, getClusters, uploadChatFile, createConversation, getFileContent, unwrap } from '../api.js'

const agentStore = useAgentStore()
const chatStore = useChatStore()

const agents = ref([])
const clusters = ref([])
const currentAgent = ref(null)
const currentCluster = ref(null)
const messages = ref([])
const conversations = ref([])
const currentConversationId = ref(null)
const inputText = ref('')
const isLoading = ref(false)
const loadingAgents = ref(false)
const streamingContent = ref('')
const messagesContainer = ref(null)
const inputBox = ref(null)
const files = ref([])
const showFiles = ref(true)
const showClusterSelect = ref(false)
const fileInput = ref(null)
const attachedFiles = ref([])
const searchEnabled = ref(false)

const preview = ref({
  show: false, type: '', filename: '', mime_type: '',
  src: '', content: '', loading: false, downloadUrl: '',
})

function isImageType(mime) { return mime?.startsWith('image/') }
function isPreviewableText(mime) {
  if (!mime) return false
  return mime.startsWith('text/') || ['json', 'xml', 'yaml', 'javascript', 'typescript'].some(t => mime.includes(t))
}

function fileIcon(mime) {
  if (!mime) return '📄'
  if (mime.startsWith('image/')) return '🖼️'
  if (mime.startsWith('text/') || mime.includes('json') || mime.includes('yaml') || mime.includes('xml')) return '📝'
  if (mime.includes('pdf')) return '📕'
  if (mime.includes('zip') || mime.includes('tar') || mime.includes('rar')) return '📦'
  if (mime.includes('video')) return '🎬'
  if (mime.includes('audio')) return '🎵'
  if (mime.includes('word') || mime.includes('document')) return '📄'
  if (mime.includes('sheet') || mime.includes('excel') || mime.includes('spreadsheet')) return '📊'
  if (mime.includes('presentation') || mime.includes('powerpoint')) return '📽️'
  return '📄'
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

function makeFileUrl(filename) {
  if (!currentConversationId.value || !currentAgent.value) return null
  return getConversationFileUrl(currentConversationId.value, filename, currentAgent.value.id)
}

function closePreview() {
  preview.value = { show: false, type: '', filename: '', mime_type: '', src: '', content: '', loading: false, downloadUrl: '' }
}

async function openPreview(file, convId) {
  const filename = file.filename || file.name
  const mime = file.mime_type || file.type || ''
  const cid = convId || currentConversationId.value
  preview.value = { show: true, type: '', filename, mime_type: mime, src: '', content: '', loading: true, downloadUrl: '' }

  if (isImageType(mime)) {
    const src = file.data_url || file._dataUrl || makeFileUrl(filename)
    preview.value.type = 'image'
    preview.value.src = src
    preview.value.loading = false
    preview.value.downloadUrl = makeFileUrl(filename)
    return
  }

  if (mime.includes('pdf')) {
    preview.value.type = 'pdf'
    preview.value.src = makeFileUrl(filename)
    preview.value.loading = false
    preview.value.downloadUrl = makeFileUrl(filename)
    return
  }

  if (isPreviewableText(mime)) {
    try {
      const r = await getFileContent(cid, currentAgent.value?.id, filename)
      preview.value.type = 'text'
      preview.value.content = r.data || ''
    } catch (e) {
      preview.value.content = '加载失败: ' + (e.message || '')
    }
    preview.value.loading = false
    preview.value.downloadUrl = makeFileUrl(filename)
    return
  }

  preview.value.loading = false
  preview.value.downloadUrl = makeFileUrl(filename)
}

function openSidebarFile(f) {
  openPreview(f, currentConversationId.value)
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

async function uploadFile(file) {
  if (!currentConversationId.value) return null
  const form = new FormData()
  form.append('file', file)
  form.append('agent_id', String(currentAgent.value?.id || 0))
  form.append('conversation_id', String(currentConversationId.value))
  try { return (await uploadChatFile(form)).data }
  catch (e) { return null }
}

function guessMimeFromExt(name) {
  const map = {
    '.txt': 'text/plain', '.md': 'text/markdown', '.py': 'text/x-python',
    '.js': 'text/javascript', '.ts': 'text/typescript', '.json': 'application/json',
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.gif': 'image/gif', '.webp': 'image/webp', '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  }
  const ext = '.' + name.split('.').pop().toLowerCase()
  return map[ext] || 'application/octet-stream'
}

async function handleFileSelect(e) {
  const selFiles = Array.from(e.target.files || [])
  for (const f of selFiles) {
    const info = {
      file: f, filename: f.name, size: f.size,
      mime_type: f.type || guessMimeFromExt(f.name), uploaded: false,
    }
    if (f.type?.startsWith('image/')) {
      info._dataUrl = await fileToDataUrl(f)
    }
    attachedFiles.value.push(info)
  }
  e.target.value = ''
}

function fileToDataUrl(file) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => resolve(null)
    reader.readAsDataURL(file)
  })
}

function removeFile(idx) { attachedFiles.value.splice(idx, 1) }

function toggleSearch() { searchEnabled.value = !searchEnabled.value }

async function loadAgents() {
  loadingAgents.value = true
  try {
    agents.value = unwrap(await getAgents()) || []
    clusters.value = unwrap(await getClusters()) || []
    if (agents.value.length && !currentAgent.value) selectAgent(agents.value[0])
  } catch (e) { /* ignore */ }
  finally { loadingAgents.value = false }
}

function selectCluster(c) {
  currentCluster.value = c; currentAgent.value = null
  showClusterSelect.value = false; messages.value = []
  conversations.value = []; currentConversationId.value = null
  attachedFiles.value = []; searchEnabled.value = false
  newConversation()
}

async function selectAgent(agent) {
  if (!agent || !agent.id) return
  currentAgent.value = agent; currentCluster.value = null
  messages.value = []; conversations.value = []
  currentConversationId.value = null; attachedFiles.value = []
  searchEnabled.value = false
  try { conversations.value = unwrap(await getConversations(agent.id)) }
  catch (e) { /* ignore */ }
}

function newConversation() {
  messages.value = []; currentConversationId.value = null
  streamingContent.value = ''; files.value = []; attachedFiles.value = []
}

async function loadConversation(conv) {
  try {
    messages.value = unwrap(await getMessages(conv.id))
    currentConversationId.value = conv.id; attachedFiles.value = []
    await loadFiles()
  } catch (e) { /* ignore */ }
}

async function loadConversationsForAgent() {
  if (!currentAgent.value) return
  try { conversations.value = unwrap(await getConversations(currentAgent.value.id)) }
  catch (e) { /* ignore */ }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if ((!text && !attachedFiles.value.length) || !currentAgent.value || isLoading.value) return

  const filesToSend = [...attachedFiles.value]
  attachedFiles.value = []
  inputText.value = ''
  isLoading.value = true
  streamingContent.value = ''

  if (!currentConversationId.value && filesToSend.length) {
    try {
      const form = new FormData()
      form.append('agent_id', String(currentAgent.value.id))
      if (currentCluster.value) form.append('cluster_id', String(currentCluster.value.id))
      form.append('title', text ? text.slice(0, 100) : '(上传文件)')
      const r = await createConversation(form)
      currentConversationId.value = r.data.id
    } catch (e) { /* ignore */ }
  }

  const fileInfos = []
  const filePreviews = []
  for (const f of filesToSend) {
    const fp = { name: f.filename, type: f.mime_type }
    if (f._dataUrl) fp._dataUrl = f._dataUrl
    filePreviews.push(fp)

    const info = { filename: f.filename, size: f.size, mime_type: f.mime_type }
    if (currentConversationId.value) {
      const uploaded = await uploadFile(f.file)
      if (uploaded) info.text_content = uploaded.text_content || ''
    }
    fileInfos.push(info)
  }

  messages.value.push({
    role: 'user', content: text || '(上传文件)', _key: Date.now(),
    _files_preview: filePreviews, files: fileInfos,
  })
  await nextTick(); scrollToBottom()

  try {
    const agentId = currentAgent.value?.id || 0
    const clusterId = currentCluster.value?.id || null
    const filesJson = fileInfos.length ? JSON.stringify(fileInfos) : null
    const resp = await streamChat(agentId, text || '(上传文件)', currentConversationId.value, clusterId, searchEnabled.value, filesJson)
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'text') { streamingContent.value += event.content; await nextTick(); scrollToBottom() }
          else if (event.type === 'cluster_start') { messages.value.push({ role: 'system', content: '🌐 集群「' + event.cluster + '」开始协作', _key: Date.now() + Math.random() }) }
          else if (event.type === 'agent_turn') { messages.value.push({ role: 'system', content: '🤖 轮到 ' + event.agent_name + (event.role ? ' (' + event.role + ')' : ''), _key: Date.now() + Math.random() }) }
          else if (event.type === 'step_start') { messages.value.push({ role: 'system', content: '📋 步骤 ' + event.step + ': ' + event.name, _key: Date.now() + Math.random() }) }
          else if (event.type === 'tool_start') { messages.value.push({ role: 'tool', tool_name: event.tool, content: '⚙️ 正在使用工具「' + event.tool + '」...', _key: Date.now() + Math.random() }) }
          else if (event.type === 'tool_result') {
            const last = messages.value[messages.value.length - 1]
            if (last && last.role === 'tool') { last.content = '✅ 工具「' + event.tool + '」返回：' + (event.result ? event.result.slice(0, 300) : '无返回结果') }
            await nextTick(); scrollToBottom()
          } else if (event.type === 'conversation_id') { currentConversationId.value = event.conversation_id; loadConversationsForAgent(); loadFiles() }
          else if (event.type === 'error') { streamingContent.value = '❌ 错误：' + event.message }
          else if (event.type === 'done') { if (streamingContent.value) { messages.value.push({ role: 'assistant', content: streamingContent.value, _key: Date.now() + Math.random() }); streamingContent.value = '' }; loadFiles() }
        } catch (e) { /* ignore */ }
      }
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '❌ 连接错误：' + e.message, _key: Date.now() + Math.random() })
  } finally {
    if (streamingContent.value) { messages.value.push({ role: 'assistant', content: streamingContent.value, _key: Date.now() + Math.random() }) }
    isLoading.value = false; streamingContent.value = ''
    await nextTick(); scrollToBottom()
  }
}

async function loadFiles() {
  if (!currentConversationId.value || !currentAgent.value) { files.value = []; return }
  try { files.value = (await getConversationFiles(currentConversationId.value, currentAgent.value.id)).data || [] }
  catch (e) { files.value = [] }
}

function scrollToBottom() {
  requestAnimationFrame(() => { if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight })
}

onMounted(loadAgents)
</script>