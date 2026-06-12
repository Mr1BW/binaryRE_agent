# BinaryRE Agent

基于 LangGraph + Gradio API 的 LLM 二进制逆向分析助手。React 前端 + Python 后端，Kali Linux Docker 沙箱执行工具链。

## 架构

```
React (Vite :5173)  →  Gradio API (:7860)  →  DeepSeek LLM
                                        →  Docker Kali Runner (objdump/gdb/Ghidra/r2)
```

前后端分离：React 负责 UI，Python Gradio 暴露 API。二进制分析工具在 Docker Kali 容器中临时创建执行。

---

## 环境准备

### 系统要求
- Python 3.11+
- Node.js 18+
- Docker

### 安装依赖

```bash
# Python 虚拟环境
uv venv --python 3.11 venv
source venv/bin/activate
uv pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..
```

### 拉取 Kali Runner 镜像

```bash
docker pull louisgauthier/decompai-runner:1.0.0
docker tag louisgauthier/decompai-runner:1.0.0 decompai-runner:dev
```

### 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`：

```env
OPENAI_API_KEY=sk-你的DeepSeek-API-Key
LLM_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com
DECOMPAI_RUNNER_IMAGE=decompai-runner:dev
```

支持所有 OpenAI 兼容的 API（DeepSeek、OpenAI、OpenRouter 等）。

---

## 启动

```bash
# 终端 1：后端
source venv/bin/activate
python run.py --api-only

# 终端 2：前端
cd frontend
npx vite --port 5173
```

浏览器打开 **http://localhost:5173**。

---

## 使用方法

1. 点击左侧 **「上传二进制文件」**，选择 x86 Linux ELF
2. Agent 自动反汇编，小文件直接嵌入对话，大文件生成摘要
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

- **objdump** — 反汇编、查看段和符号表
- **Ghidra** — headless 反编译
- **radare2** — 十六进制、字符串、内存 dump、二进制修补
- **gdb** — 动态调试
- **Shell** — Kali 环境任意命令（持久 + 一次性模式）
- **文件工具** — 读写搜索工作目录

---

## 项目结构

```
src/
  main.py              # LangGraph Agent + Gradio API
  config.py             # 环境变量配置
  state.py              # 会话状态
  tools/                # 工具定义和 Shell 沙箱
  utils/                # Docker 调用、Ghidra 脚本
frontend/
  src/
    App.tsx             # 主布局
    components/         # Sidebar / ChatArea / Welcome / Message
    hooks/              # useGradioClient
    styles.css          # 全局样式
Dockerfile.runner       # Kali 工具镜像
```

## 注意事项

- Runner 容器需要 `--privileged` 特权模式
- 会话按文件 SHA-256 哈希持久化在 `decompai_analysis_sessions/`
- `.env` 中的 API key 仅用于本地 Python 进程，不传入 runner 容器
- 仅限合法的逆向工程、安全研究和教育用途
