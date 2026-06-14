<template>
  <div class="w-16 bg-gray-900 flex flex-col items-center py-4 gap-3">
    <div class="text-white text-lg font-bold mb-4">AI</div>
    <router-link to="/" class="w-10 h-10 rounded-lg flex items-center justify-center text-xl hover:bg-gray-700" :class="{ 'bg-gray-700': $route.path === '/' }" title="对话">💬</router-link>
    <router-link to="/agents" class="w-10 h-10 rounded-lg flex items-center justify-center text-xl hover:bg-gray-700" :class="{ 'bg-gray-700': $route.path === '/agents' || $route.path.startsWith('/agents/') }" title="智能体广场">🤖</router-link>
    <router-link to="/tools" class="w-10 h-10 rounded-lg flex items-center justify-center text-xl hover:bg-gray-700" :class="{ 'bg-gray-700': $route.path.startsWith('/tools') }" title="工具市场">🔧</router-link>
    <router-link to="/clusters" class="w-10 h-10 rounded-lg flex items-center justify-center text-xl hover:bg-gray-700" :class="{ 'bg-gray-700': $route.path.startsWith('/clusters') }" title="智能体集群">🌐</router-link>
    <router-link to="/mcp" class="w-10 h-10 rounded-lg flex items-center justify-center text-xl hover:bg-gray-700" :class="{ 'bg-gray-700': $route.path === '/mcp' }" title="MCP 服务器">🔌</router-link>
    <div class="flex-1"></div>
    <router-link to="/settings" class="w-10 h-10 rounded-lg flex items-center justify-center text-xl hover:bg-gray-700" :class="{ 'bg-gray-700': $route.path === '/settings' }" title="设置">⚙️</router-link>
  </div>
</template>