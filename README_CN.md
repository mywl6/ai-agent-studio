<div align="center">

# AI Agent Studio

**桌面端 AI 智能体平台 — 多模型接入、工具调用、MCP 协议扩展、集群协作。**

*FastAPI + Vue 3 + PyWebview*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4%2B-42b883?logo=vue.js)](https://vuejs.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

[English](README.md)

</div>

---

一个桌面端 AI 智能体平台，支持多模型接入、工具调用、MCP 协议扩展和集群协作。可作为桌面应用运行（PyWebview），也可独立部署为 Web 服务。

---

## ⚠️ 项目状态

这是一个 **快速原型（MVP）**，在 2 天内构建，用于验证桌面端 AI 智能体平台的产品概念。  
架构和交互流程为独立设计；代码实现由 AI 辅助完成，关键路径（安全、权限边界、API Key 加密）经过人工审查。  

**已知限制**：边界情况处理、生产环境加固和全面测试仍在进行中。  
**适用场景**：架构参考、技术栈评估和原型演示。  
**暂不适合**：未经进一步开发直接用于生产环境。

---

## 核心功能

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

## 演示

| 智能体 | 工具和 MCP | 集群协作 |
|:---:|:---:|:---:|
| ![Agent](docs/demo/智能体.gif) | ![Tools & MCP](docs/demo/工具和mcp.gif) | ![Cluster](docs/demo/智能体集群.gif) |

## 技术栈

| 层级 | 技术 |
|------|------|
| 桌面壳 | PyWebview |
| 后端 | Python / FastAPI / Uvicorn / SQLAlchemy |
| 数据库 | SQLite（自动迁移） |
| 前端 | Vue 3 / Vite / Tailwind CSS / Pinia |
| 构建 | PyInstaller（Windows EXE） |

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
cd frontend && npm install
```

### 启动

```bash
# 方式一：启动桌面应用（推荐）
python main.py

# 方式二：仅启动后端 API
python -m uvicorn backend.main:app --reload --port 8000

# 方式三：启动前端开发服务器
cd frontend && npm run dev
```

### 构建可执行文件

```bash
build_exe.bat
# 输出：dist/AI Agent.exe
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///data/app.db` |
| `ENCRYPTION_KEY` | API Key 加密密钥（Fernet） | 基于机器 ID 自动生成 |
| `FRONTEND_URL` | 前端开发服务器 URL | 空（使用内置静态文件） |
| `API_VERSION` | API 版本前缀 | `v1` |

## 项目结构

```
ai-agent-platform/
├── main.py                  # 桌面入口（PyWebview + FastAPI）
├── requirements.txt
├── ai-agent.spec            # PyInstaller 配置
├── build_exe.bat            # 一键构建脚本
│
├── backend/
│   ├── main.py              # FastAPI 应用初始化
│   ├── config.py            # 全局配置
│   ├── database.py          # SQLAlchemy 引擎 + 自动迁移
│   ├── di.py                # 依赖注入
│   ├── security.py          # 加密 / 命令白名单 / 沙箱
│   ├── workspace.py         # 会话工作空间管理
│   ├── file_processor.py    # 文件校验、文本提取、图片编码
│   ├── models/              # SQLAlchemy 数据模型
│   ├── routers/             # API 路由
│   ├── services/            # 业务逻辑
│   └── tools_builtin/       # 内置工具
│
├── tools_custom/            # 自定义工具目录
├── plugins/                 # 插件目录（预留）
│
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 公共组件
│   │   ├── store.js         # Pinia 状态管理
│   │   ├── api.js           # Axios API 封装
│   │   └── router.js        # Vue Router
│   └── vite.config.js
│
└── data/                    # 运行时数据（已 gitignore）
```

## 自定义工具

在 `tools_custom/` 目录下创建 Python 文件，使用 `@registry.register()` 注册：

```python
from backend.services.tool_registry import registry

@registry.register(
    name="my_tool",
    description="工具描述",
    icon="🔧",
    category="Custom",
)
def my_tool(param1: str, param2: int = 0) -> str:
    """工具逻辑"""
    return f"Result: {param1}"
```

工具在启动时自动加载。

## MCP 服务器

通过管理界面添加 MCP 服务器（支持 `stdio` 和 `sse` 类型）。启用后工具自动发现并注册，前缀为 `mcp_{server_name}_{tool_name}`。

## 数据存储

| 路径 | 说明 |
|------|------|
| `data/app.db` | SQLite 数据库 |
| `data/app.log` | 应用日志 |
| `data/workspaces/` | 智能体工作空间 |
| `data/clusters/` | 集群共享数据 |

## 许可证

MIT
