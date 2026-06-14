<div align="center">

# AI Agent Studio

**Desktop AI agent platform — multi-model, tool-calling, MCP support, cluster workflows.**

*FastAPI + Vue 3 + PyWebview*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4%2B-42b883?logo=vue.js)](https://vuejs.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

</div>

---

一个桌面端 AI 智能体平台，支持多模型接入、工具调用、MCP 协议扩展和集群协作。可作为桌面应用运行（PyWebview），也可独立部署为 Web 服务。

---

## Features / 核心功能

| 功能 | 说明 |
|------|------|
| **智能体管理** | 创建、配置、对话，支持自定义系统提示、工具授权和模型绑定 |
| **多模型接入** | OpenAI / Anthropic / DeepSeek / Ollama / 阿里云 / 自定义兼容 API |
| **工具系统** | 内置文件读写、命令执行、HTTP 请求、计算器、搜索等工具，支持自定义插件扩展 |
| **MCP 协议** | 接入 stdio / SSE 类型的 MCP 服务器，自动发现并注册远程工具 |
| **集群协作** | 多智能体组成集群，共享工作空间，支持工作流编排和任务调度 |
| **文件处理** | 支持文本、图片、PDF、Office 文档上传和内容提取，兼容多模态模型视觉识别 |
| **安全机制** | API Key 加密存储、命令白名单、代码沙箱、路径访问控制 |
| **工作空间** | 每个会话独立工作目录，集群模式下支持共享与私有空间隔离 |

## Demo / 演示

| 智能体 / Agent | 工具和 MCP / Tools & MCP | 集群协作 / Cluster |
|:---:|:---:|:---:|
| ![Agent](docs/demo/智能体.gif) | ![Tools & MCP](docs/demo/工具和mcp.gif) | ![Cluster](docs/demo/智能体集群.gif) |

## Tech Stack / 技术栈

| 层级 | 技术 |
|------|------|
| Desktop Shell | PyWebview |
| Backend | Python / FastAPI / Uvicorn / SQLAlchemy |
| Database | SQLite (auto-migration) |
| Frontend | Vue 3 / Vite / Tailwind CSS / Pinia |
| Build | PyInstaller (Windows EXE) |

## Quick Start / 快速开始

### Prerequisites / 环境要求

- Python 3.10+
- Node.js 18+
- npm

### Install / 安装依赖

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Run / 启动

```bash
# 方式一：启动桌面应用（推荐）/ Desktop app (Recommended)
python main.py

# 方式二：仅启动后端 API / Backend API only
python -m uvicorn backend.main:app --reload --port 8000

# 方式三：启动前端开发服务器 / Frontend dev server
cd frontend && npm run dev
```

### Build / 构建可执行文件

```bash
build_exe.bat
# Output: dist/AI Agent.exe
```

## Environment Variables / 环境变量

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///data/app.db` |
| `ENCRYPTION_KEY` | API Key encryption key (Fernet) | Auto-generated from machine ID |
| `FRONTEND_URL` | Frontend dev server URL | Empty (use built-in static) |
| `API_VERSION` | API version prefix | `v1` |

## Project Structure / 项目结构

```
ai-agent-platform/
├── main.py                  # Desktop entry (PyWebview + FastAPI)
├── requirements.txt
├── ai-agent.spec            # PyInstaller config
├── build_exe.bat            # One-click build script
│
├── backend/
│   ├── main.py              # FastAPI app init
│   ├── config.py            # Global config
│   ├── database.py          # SQLAlchemy engine + auto-migration
│   ├── di.py                # Dependency injection
│   ├── security.py          # Encryption / command whitelist / sandbox
│   ├── workspace.py         # Session workspace management
│   ├── file_processor.py    # File validation, text extraction, image encoding
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   └── tools_builtin/       # Built-in tools
│
├── tools_custom/            # Custom tools directory
├── plugins/                 # Plugin directory (reserved)
│
├── frontend/
│   ├── src/
│   │   ├── views/           # Page components
│   │   ├── components/      # Shared components
│   │   ├── store.js         # Pinia state management
│   │   ├── api.js           # Axios API wrapper
│   │   └── router.js        # Vue Router
│   └── vite.config.js
│
└── data/                    # Runtime data (gitignored)
```

## Custom Tools / 自定义工具

Create Python files in `tools_custom/` and register with `@registry.register()`:

```python
from backend.services.tool_registry import registry

@registry.register(
    name="my_tool",
    description="Tool description",
    icon="🔧",
    category="Custom",
)
def my_tool(param1: str, param2: int = 0) -> str:
    """Tool logic"""
    return f"Result: {param1}"
```

Tools are auto-loaded on startup.

## MCP Servers / MCP 服务器

Add MCP servers via the management UI (supports `stdio` and `sse` types). Once enabled, tools are auto-discovered and registered with prefix `mcp_{server_name}_{tool_name}`.

## Data Storage / 数据存储

| Path | Description |
|------|-------------|
| `data/app.db` | SQLite database |
| `data/app.log` | Application logs |
| `data/workspaces/` | Agent workspaces |
| `data/clusters/` | Cluster shared data |

## License

MIT
