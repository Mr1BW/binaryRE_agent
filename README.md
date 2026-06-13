# binaryRE

LangGraph + FastAPI 驱动的 LLM 二进制逆向分析助手。React 前端 + Python 后端，Kali Linux Docker 沙箱执行工具链。

## 架构

```
React (Vite :5173)  ──SSE──>  FastAPI (:7860)  ──>  DeepSeek LLM
                                    │
                                    └──>  Docker Kali Runner
                                          (objdump / Ghidra / r2 / gdb)
```

前后端分离：React SSE 流式通信，Python FastAPI 暴露 REST API。二进制分析工具在 Docker Kali 容器中执行。

---

## 数据集

| 数据集 | 说明 | 链接 |
|---|---|---|
| **CGC** | DARPA Cyber Grand Challenge 漏洞挖掘竞赛二进制（DECREE 格式） | [cb-multios](https://github.com/trailofbits/cb-multios) |
| **CrackMe** | crackmes.one 逆向挑战题目合集（x86 / x86-64 ELF） | [crackmes.one](https://crackmes.one) |

数据存放在 `data/cgc/` 和 `data/crackme/`，每个二进制子目录内含来源链接 `1.txt`。

> CGC 二进制为非标准 ELF（DECREE），`objdump` 无法直接读取。本项目已内置 CGC 兼容处理（`-b binary -m i386` 模式），上传后自动识别。

---

## 环境准备

### 系统要求

- Python 3.11+
- Node.js 18+
- Docker

### 安装依赖

```bash
# Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..
```

### 拉取 Kali Runner 镜像

```bash
docker pull louisgauthier/decompai-runner:1.0.0
docker tag louisgauthier/decompai-runner:1.0.0 decompai-runner:dev
```

### 配置

```bash
cp .env.example .env
```

编辑 `.env`：

```env
OPENAI_API_KEY=sk-你的Key
LLM_MODEL=deepseek-v4-pro          # 普通对话；换 deepseek-reasoner 可看思考过程
OPENAI_BASE_URL=https://api.deepseek.com
DECOMPAI_RUNNER_IMAGE=decompai-runner:dev

# 可选
ANALYSIS_SESSIONS_ROOT=./decompai_analysis_sessions   # 会话存储路径（默认 /tmp）
DECOMPAI_SHELL_TIMEOUT=120        # Shell 命令超时秒数（默认 120）
DECOMPAI_COMMAND_TIMEOUT=60       # Docker 命令超时秒数（默认 60）
```

支持所有 OpenAI 兼容 API（DeepSeek、OpenAI、OpenRouter 等）。Gemini 模型也支持，设 `LLM_MODEL=gemini-2.5-pro` 并在 `.env` 加 `GEMINI_API_KEY`。

---

## 启动

```bash
# 终端 1：后端
source venv/bin/activate
python run.py

# 终端 2：前端
cd frontend
npx vite --port 5173
```

浏览器打开 **http://localhost:5173**。

---

## 使用方法

1. 点击左侧 **「上传二进制文件」**，选择 ELF / CGC 二进制
2. Agent 自动反汇编（小文件直接嵌入，大文件生成摘要）
3. 在聊天框输入分析指令

| 你想做什么 | 可以这样说 |
|---|---|
| 理解程序逻辑 | "总结这个程序的功能" |
| 反编译函数 | "反编译 main 函数" |
| 查看字符串 | "列出所有可读字符串" |
| 反汇编段 | "反汇编 .text 段" |
| 查找漏洞 | "检查是否存在缓冲区溢出" |
| 动态调试 | "用 gdb 在 main 设断点并运行" |
| 修补二进制 | "把地址 0x1050 的指令 NOP 掉" |

---

## 可用工具

| 工具 | 功能 |
|---|---|
| **objdump** | 反汇编、查看段和符号表 |
| **Ghidra** | headless 反编译 |
| **radare2** | 反汇编、字符串搜索、内存 dump、二进制修补 |
| **gdb** | 动态调试 |
| **Shell** | Kali 沙箱任意命令（持久 + 一次性模式） |
| **文件工具** | 读写搜索工作目录 |

---

## 项目结构

```
src/
  main.py                 # LangGraph Agent 核心（模型 / 工具 / Graph）
  api.py                  # FastAPI 路由（SSE 流式 chat、上传、session CRUD）
  config.py               # 环境变量配置（pydantic-settings）
  state.py                # 会话 State 定义
  tools/                  # 工具定义 + Sandbox Shell
  utils/                  # Docker 调用、反汇编、Ghidra 脚本
frontend/
  src/
    App.tsx               # 主布局 + 状态管理
    components/           # Sidebar / ChatArea / Welcome / MessageBubble
    hooks/                # useApi（fetch + SSE）
  App.css                 # 全局样式（含 Markdown 渲染）
Dockerfile.runner         # Kali 工具镜像
```

---

## 注意事项

- Runner 容器需要 Docker socket 挂载
- 会话按文件 SHA-256 哈希持久化，保存在 `ANALYSIS_SESSIONS_ROOT` 目录
- `.env` 中的 API key 仅用于本地 Python 进程，不传入 runner 容器
- 仅限合法的逆向工程、安全研究和教育用途
