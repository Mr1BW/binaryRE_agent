# DecompAI: Binary Analysis and Decompilation Agent

DecompAI 是一个基于 LangGraph + Gradio 的 LLM Agent，通过对话式界面自动化二进制分析和反编译流程。支持 objdump、gdb、Ghidra、radare2 等工具链，在 Kali Linux 沙箱中安全执行。

---

## 架构

```
浏览器 (localhost:5173)
       │
       ▼
┌──────────────────┐      ┌──────────────────┐      LLM API (DeepSeek)
│  React 前端      │ ───► │  Gradio API       │ ──────────────────►
│  (Vite + npm)    │      │  Python 3.11      │
│  :5173           │      │  :7860            │
└──────────────────┘      └──────┬───────────┘
                                 │  docker run --rm (临时创建)
                                 ▼
                          ┌──────────────────┐
                          │  Kali Runner     │
                          │  objdump / gdb   │
                          │  Ghidra / r2     │
                          └──────────────────┘
```

前后端分离：React (Vite) 负责 UI，Python Gradio 提供 REST + WebSocket API。二进制工具在 Docker Kali 容器中执行。

---

## 快速开始

### 1. 启动后端（Python API）

```bash
source venv/bin/activate
python run.py --api-only
```

后端运行在 **http://localhost:7860**（API 模式，不显示 Gradio UI）。

### 2. 启动前端（React）

```bash
cd frontend
npm install
npm run dev
```

前端运行在 **http://localhost:5173**，打开浏览器即可使用。

### 一步启动

```bash
# 终端 1：后端
source venv/bin/activate && python run.py --api-only

# 终端 2：前端
cd frontend && npm run dev
```

> 11.6GB，已配置国内镜像源，取决于网速。

### 2. 创建虚拟环境并安装依赖

```bash
cd /path/to/decompai
uv venv --python 3.11 venv
source venv/bin/activate
uv pip install -r requirements.txt
```

> 必须用 Python 3.11，与 Docker 镜像保持一致。

### 3. 配置 API Key

创建 `.env` 文件：

```env
OPENAI_API_KEY=sk-你的DeepSeek-API-Key
LLM_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com
DECOMPAI_RUNNER_IMAGE=decompai-runner:dev
```

| 变量 | 说明 |
|---|---|
| `OPENAI_API_KEY` | DeepSeek API key |
| `LLM_MODEL` | 模型名：`deepseek-chat`（V3）或 `deepseek-reasoner`（R1） |
| `OPENAI_BASE_URL` | DeepSeek API 端点（已配置好） |
| `DECOMPAI_RUNNER_IMAGE` | Kali 工具镜像名 |
| `DECOMPAI_SHELL_TIMEOUT` | Shell 命令超时秒数（默认 120），防止交互式程序卡死 |

其他支持的 LLM：OpenAI（`gpt-4o`）、Gemini（`gemini-2.5-pro`）等。如果换模型，在 `.env` 中改 `LLM_MODEL` 和对应的 `API_KEY` 即可。

### 4. 创建必要目录

```bash
mkdir -p decompai_analysis_sessions binaries source_code
```

### 5. 启动

```bash
./start.sh
```

或直接：

```bash
source venv/bin/activate
python run.py
```

浏览器打开 **http://localhost:7860**。

后台运行：

```bash
./start.sh -b
tail -f app.log        # 查看日志
pkill -f "python run.py"  # 停止
```

---

## 使用方法

### 基本流程

1. **上传二进制** — 拖拽或点击上传 x86 Linux ELF 文件
2. **自动分析** — Agent 自动反汇编，小文件直接嵌入对话，大文件生成摘要
3. **对话交互** — 在聊天框与 Agent 交流

### 支持的二进制格式

- x86 Linux ELF（当前）
- 规划中：ARM、MIPS、Windows PE（QEMU 支持）

### 对话示例

| 你想做的事 | 可以这样问 |
|---|---|
| 理解程序功能 | "这个程序在做什么？总结一下" |
| 反编译某个函数 | "反编译 main 函数" |
| 查看字符串 | "列出所有字符串" |
| 反汇编某个段 | "反汇编 .text 段" |
| 调试 | "用 gdb 在 main 下断点然后运行" |
| 搜索漏洞 | "检查是否有缓冲区溢出" |
| 写反编译结果 | "把反编译结果写到 decompiled_main.c" |

### 可用工具

Agent 自动选择工具，你也可以明确要求：

- **objdump** — 反汇编、查看段/Symbol Table
- **gdb** — 动态调试
- **Ghidra** — 反编译（headless 模式）
- **radare2** — 十六进制查看、字符串提取、内存 dump
- **Shell** — Kali 环境下的任意命令（有状态/无状态两种模式）
- **File tools** — 读/写/搜索/列出工作目录中的文件

### 会话持久化

上传同一个二进制文件会自动恢复之前的会话。会话按文件 SHA-256 哈希存储，路径在 `decompai_analysis_sessions/` 下。

---

## LLM 兼容性

| 能力 | 项目使用 | DeepSeek |
|---|---|---|
| Function Calling | ✅ 核心（工具绑定） | ✅ |
| Streaming | ✅ 流式输出 | ✅ |
| 多模态 | ❌ | — |

DeepSeek 完全兼容。其他 OpenAI 兼容的 API（如 OpenRouter、Together AI）只需改 `OPENAI_BASE_URL` 和 `LLM_MODEL`。

---

## 项目结构

```
src/
  main.py         # LangGraph Agent + Gradio API
  state.py        # 会话状态定义
  config.py       # 配置（环境变量读取）
  tools/          # 工具定义
  utils/          # Docker 调用、Ghidra 脚本等
run.py            # 后端入口
frontend/         # React 前端（独立 npm 项目）
  src/
    App.tsx       # 主布局
    components/   # Sidebar / ChatArea / Welcome / Message
    hooks/        # useGradioClient（API 通信）
    styles.css    # ChatGPT 风格样式
Dockerfile.runner # Kali 工具镜像
```

---

## 注意事项

- Runner 容器需要 Docker 特权模式（`--privileged`），用于 gdb 等底层工具
- 会话数据存储在 `decompai_analysis_sessions/`，重启后保留
- `.env` 中的 API key 仅用于本地 Python 进程调用 LLM，不会传到 runner 容器
- 仅用于合法的逆向工程、安全研究和教育目的
