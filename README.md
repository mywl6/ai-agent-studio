# AI Agent Platform

一个功能完整的 AI 智能体平台，支持多模型接入、工具调用、MCP 协议扩展、集群协作和可视化工作流。可作为桌面应用运行（PyWebview），也可独立部署为 Web 服务。

## 核心功能

- **智能体管理** — 创建、配置、对话，支持自定义系统提示、工具授权和模型绑定
- **多模型接入** — OpenAI / Anthropic / DeepSeek / Ollama / 阿里云 / 自定义兼容 API
- **工具系统** — 内置文件读写、命令执行、HTTP 请求、计算器、搜索等工具，支持自定义插件扩展
- **MCP 协议** — 接入 stdio / SSE 类型的 MCP 服务器，自动发现并注册远程工具
- **集群协作** — 多智能体组成集群，共享工作空间，支持工作流编排和任务调度
- **文件处理** — 支持文本、图片、PDF、Office 文档上传和内容提取，兼容多模态模型视觉识别
- **安全机制** — API Key 加密存储、命令白名单、代码沙箱、路径访问控制
- **工作空间** — 每个会话独立工作目录，集群模式下支持共享与私有空间隔离

## 技术栈

| 层级 | 技术 |
|------|------|
| 桌面入口 | PyWebview |
| 后端 | Python / FastAPI / Uvicorn / SQLAlchemy |
| 数据库 | SQLite（自动迁移） |
| 前端 | Vue 3 / Vite / Tailwind CSS / Pinia |
| 打包 | PyInstaller（Windows EXE） |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- npm

### 安装依赖

```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 启动开发服务

```bash
# 方式一：启动桌面应用（推荐）
python main.py

# 方式二：仅启动后端 API（访问 http://127.0.0.1:8000）
python -m uvicorn backend.main:app --reload --port 8000

# 方式三：启动前端开发服务器
cd frontend
npm run dev
```

### 构建可执行文件

```bash
# Windows
build_exe.bat
```

产出文件：`dist/AI Agent.exe`

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite:///data/app.db` |
| `ENCRYPTION_KEY` | API Key 加密密钥（Fernet 格式） | 基于机器特征自动生成 |
| `FRONTEND_URL` | 前端开发服务器地址 | 空（使用内置静态文件） |
| `API_VERSION` | API 版本前缀 | `v1` |

## 项目结构

```
ai-agent-platform/
├── main.py                  # 桌面入口（PyWebview + FastAPI）
├── requirements.txt         # Python 依赖
├── ai-agent.spec            # PyInstaller 打包配置
├── build_exe.bat            # 一键打包脚本
├── backend/
│   ├── main.py              # FastAPI 应用初始化
│   ├── config.py            # 全局配置
│   ├── database.py          # SQLAlchemy 引擎 + 自动迁移
│   ├── di.py                # 依赖注入工厂
│   ├── security.py          # 加密 / 命令白名单 / 代码沙箱
│   ├── workspace.py         # 会话工作空间管理
│   ├── file_processor.py    # 文件校验、文本提取、图片编码
│   ├── models/              # SQLAlchemy 数据模型
│   │   ├── provider.py      # 模型提供商
│   │   ├── model_provider.py# 模型配置
│   │   ├── agent.py         # 智能体
│   │   ├── conversation.py  # 会话
│   │   ├── message.py       # 消息
│   │   ├── cluster.py       # 集群 + 工作流 + 任务
│   │   └── mcp_server.py    # MCP 服务器
│   ├── routers/             # API 路由
│   │   ├── chat.py          # 对话接口（流式）
│   │   ├── agents.py        # 智能体 CRUD
│   │   ├── models.py        # 模型管理
│   │   ├── providers.py     # 提供商管理
│   │   ├── tools.py         # 工具管理
│   │   ├── clusters.py      # 集群管理
│   │   ├── mcp_router.py    # MCP 服务器管理
│   │   └── settings.py      # 系统设置
│   ├── services/            # 业务逻辑层
│   │   ├── agent_engine.py  # 智能体对话引擎（流式 + 工具循环）
│   │   ├── model_pool.py    # 模型连接池
│   │   ├── tool_registry.py # 工具注册中心
│   │   ├── tool_loader.py   # 工具加载（内置 + 自定义）
│   │   ├── mcp_manager.py   # MCP 协议管理
│   │   ├── cluster_service.py # 集群 + 工作流服务
│   │   └── cluster_engine.py  # 集群执行引擎
│   └── tools_builtin/       # 内置工具
│       ├── calculator.py    # 计算器
│       ├── command_runner.py# 命令执行
│       ├── file_reader.py   # 文件读取
│       ├── file_writer.py   # 文件写入
│       ├── dir_lister.py    # 目录浏览
│       ├── http_request.py  # HTTP 请求
│       └── web_search.py    # 联网搜索
├── tools_custom/            # 自定义工具目录
│   └── custom_tool.py       # 示例：云盘上传工具
├── plugins/                 # 插件目录（预留）
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   │   ├── ChatView.vue       # 对话界面
│   │   │   ├── AgentConfig.vue    # 智能体配置
│   │   │   ├── AgentSquare.vue    # 智能体广场
│   │   │   ├── ToolMarket.vue     # 工具市场
│   │   │   ├── ToolGenerator.vue  # 工具生成器
│   │   │   ├── ClusterList.vue    # 集群列表
│   │   │   ├── ClusterDetail.vue  # 集群详情
│   │   │   ├── WorkflowDetail.vue # 工作流详情
│   │   │   ├── MCPServers.vue     # MCP 服务器管理
│   │   │   └── SettingsView.vue   # 系统设置
│   │   ├── components/      # 公共组件
│   │   ├── store.js         # Pinia 状态管理
│   │   ├── api.js           # Axios API 封装
│   │   └── router.js        # Vue Router 路由
│   └── vite.config.js       # Vite 构建配置
└── data/                    # 运行时数据（数据库、日志、工作空间）
    ├── app.db
    ├── workspaces/
    └── clusters/
```

## 自定义工具

在 `tools_custom/` 目录下创建 Python 文件，使用 `@registry.register()` 装饰器注册工具：

```python
from backend.services.tool_registry import registry

@registry.register(
    name="my_tool",
    description="工具描述",
    icon="🔧",
    category="自定义",
)
def my_tool(param1: str, param2: int = 0) -> str:
    """工具逻辑"""
    return f"结果: {param1}"
```

工具会在启动时自动加载并注册到工具注册中心。

## MCP 服务器

通过管理界面添加 MCP 服务器（支持 stdio 和 SSE 两种类型），启用后自动发现并注册远程工具。工具前缀为 `mcp_{服务器名}_{工具名}`。

## 数据存储

- 数据库文件：`data/app.db`
- 日志文件：`data/app.log`
- 工作空间：`data/workspaces/`
- 集群数据：`data/clusters/`
