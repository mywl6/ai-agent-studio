import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Chat', component: () => import('./views/ChatView.vue') },
  { path: '/agents', name: 'AgentSquare', component: () => import('./views/AgentSquare.vue') },
  { path: '/agents/:id/config', name: 'AgentConfig', component: () => import('./views/AgentConfig.vue') },
  { path: '/tools', name: 'ToolMarket', component: () => import('./views/ToolMarket.vue') },
  { path: '/tools/generate', name: 'ToolGenerator', component: () => import('./views/ToolGenerator.vue') },
  // 集群
  { path: '/clusters', name: 'Clusters', component: () => import('./views/ClusterList.vue') },
  { path: '/clusters/:id', name: 'ClusterDetail', component: () => import('./views/ClusterDetail.vue') },
  { path: '/clusters/:cid/workflows/:wid', name: 'WorkflowDetail', component: () => import('./views/WorkflowDetail.vue') },
  // MCP
  { path: '/mcp', name: 'MCPServers', component: () => import('./views/MCPServers.vue') },
  // 设置
  { path: '/settings', name: 'Settings', component: () => import('./views/SettingsView.vue') },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})