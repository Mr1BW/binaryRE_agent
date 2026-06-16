# binaryRE

## 项目简介

binaryRE 是一款基于大语言模型的二进制逆向分析智能助手。前端采用 React + TypeScript（Vite 构建），后端采用 Python FastAPI 暴露 REST API，通过 SSE 实现流式对话通信。核心分析引擎基于 LangGraph 构建 Agent 工作流，调用 LLM 自主编排二进制分析工具链，所有逆向工具运行在 Kali Linux Docker 沙箱中，确保执行环境隔离。

## 环境与依赖

### 运行环境

| 项目     | 版本         | 说明                            |
| -------- | ------------ | ------------------------------- |
| 操作系统 | Ubuntu 20.04 | 开发与测试所用系统              |
| Python   | 3.11         | 核心语言版本                    |
| Node.js  | 18+          | 前端构建                        |
| Docker   | 20.10+       | 运行 Kali Runner 沙箱与分析工具 |

### 开源程序与第三方依赖

| 依赖名称         | 使用版本 | 下载链接                                          | 安装方式    | 说明                                       |
| ---------------- | -------- | ------------------------------------------------- | ----------- | ------------------------------------------ |
| Kali Runner 镜像 | 1.0.0    | `docker pull louisgauthier/decompai-runner:1.0.0` | Docker 拉取 | Kali 工具链（Ghidra / r2 / gdb / objdump） |
| Node.js          | 18.20.0  | https://nodejs.org/en/download/                   | 官方安装包  | 前端构建                                   |

> **注意**：Kali Runner 镜像约 8GB+，首次拉取耗时较长，建议提前准备。

### Python / npm 依赖

依赖清单文件：

- Python → `requirements.txt`
- Node.js → `frontend/package.json`

安装命令：

```bash
# Python
pip install -r requirements.txt

# Node.js（前端）
cd frontend && npm install && cd ..
```

## 配置说明

### LLM 配置

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入 API Key 和模型选择：

```env
# ── 通用（OpenAI 兼容 API）──
OPENAI_API_KEY=sk-your-key
LLM_MODEL=deepseek-v4-pro
OPENAI_BASE_URL=https://api.deepseek.com

```

> **安全提示**：`.env` 已加入 `.gitignore`，API Key 仅用于本地 Python 进程，不传入 Runner 容器。

### 其他关键配置

| 配置项                     | 默认值                                | 说明                                        | 配置文件        |
| -------------------------- | ------------------------------------- | ------------------------------------------- | --------------- |
| `LLM_MODEL`                | `gpt-4o-mini`                         | 对话模型（支持 DeepSeek / OpenAI / Gemini） | `.env`          |
| `ANALYSIS_SESSIONS_ROOT`   | `/tmp/decompai_analysis_sessions`     | 会话持久化存储路径                          | `.env`          |
| `DECOMPAI_RUNNER_IMAGE`    | `louisgauthier/decompai-runner:1.0.0` | Kali Runner 镜像                            | `.env`          |
| `DECOMPAI_SHELL_TIMEOUT`   | 120                                   | Shell 命令超时（秒）                        | `.env`          |
| `DECOMPAI_COMMAND_TIMEOUT` | 60                                    | Docker 命令超时（秒）                       | `.env`          |
| `GRADIO_SERVER_PORT`       | 7860                                  | 后端服务端口                                | `src/config.py` |

## 数据集

### 数据集说明

| 数据集名称                   | 来源                                                    | 大小     | 格式             | 说明                         |
| ---------------------------- | ------------------------------------------------------- | -------- | ---------------- | ---------------------------- |
| CGC（Cyber Grand Challenge） | [cb-multios](https://github.com/trailofbits/cb-multios) | 约 200MB | DECREE 格式      | DARPA 漏洞挖掘竞赛二进制合集 |
| CrackMe                      | [crackmes.one](https://crackmes.one)                    | 按需下载 | x86 / x86-64 ELF | 逆向挑战题目合集             |

> **体积较大的数据集不纳入 Git 仓库**，请通过外部链接下载后放置到指定目录。
>
> **CGC 特殊说明**：CGC 二进制为非标准 ELF（DECREE 格式），`objdump` 无法直接读取。本项目已内置 CGC 兼容处理（`-b binary -m i386` 模式），上传后自动识别格式并选用合适的分析策略。

### 数据集下载与放置

```bash
# 1. 创建数据目录
mkdir -p data/cgc data/crackme

# 2. 下载 CGC 数据集
git clone https://github.com/trailofbits/cb-multios.git
# 提取二进制文件放入 data/cgc/

# 3. 从 crackmes.one 下载挑战题目
# 放入 data/crackme/ 目录
```

数据集目录结构：

```
data/
├── cgc/                         # CGC 二进制（DECREE 格式）
│   ├── CADET_00001/
│   │   ├── CADET_00001          # 二进制文件
│   │   └── 1.txt                # 来源链接
│   └── ...
├── crackme/                     # CrackMe 题目（ELF 格式）
│   └── ...
└── README.md                    # 数据集说明
```

> `data/` 目录已加入 `.gitignore`，但 `data/samples/` 通过 `!data/samples/` 规则**强制纳入版本控制**。

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Mr1BW/binaryRE_agent.git
cd binaryRE_agent

# 2. 安装 Python 依赖
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend && npm install && cd ..

# 4. 拉取 Kali Runner 镜像
docker pull louisgauthier/decompai-runner:1.0.0
docker tag louisgauthier/decompai-runner:1.0.0 decompai-runner:dev

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 6. 启动后端（终端 1）
source venv/bin/activate && python run.py

# 7. 启动前端（终端 2）
cd frontend && npm run dev
```

浏览器打开 **http://localhost:5173**。

## 使用方法

1. 点击左侧 **「上传二进制文件」**，选择文件进行上传
2. Agent 自动进行反汇编分析（小文件直接嵌入上下文，大文件生成摘要）
3. 在聊天框中输入自然语言分析指令

| 你想做什么      | 可以这样说                          |
| --------------- | ----------------------------------- |
| 理解程序逻辑    | "总结这个程序的功能"                |
| 反编译函数      | "反编译 main 函数"                  |
| 查看字符串      | "列出所有可读字符串"                |
| 反汇编指定段    | "反汇编 .text 段"                   |
| 查找漏洞        | "检查是否存在缓冲区溢出"            |
| 动态调试        | "用 gdb 在 main 设断点并运行"       |
| 修补二进制      | "把地址 0x1050 处的指令 NOP 掉"     |
| 内存分析        | "dump 地址 0x401000 开始的 64 字节" |
| Ghidra 深度分析 | "用 Ghidra 反编译 sub_401080 函数"  |

## 可用分析工具

| 工具             | 功能                                      |
| ---------------- | ----------------------------------------- |
| **objdump**      | 反汇编、查看段和符号表                    |
| **Ghidra**       | headless 反编译、深度静态分析             |
| **radare2 (r2)** | 反汇编、字符串搜索、内存 dump、二进制修补 |
| **gdb**          | 动态调试（断点、单步、寄存器查看）        |
| **Kali Shell**   | 沙箱内任意命令执行（持久 + 一次性模式）   |
| **Python 脚本**  | Runner 容器内 Python 脚本执行             |
| **文件工具**     | 读写搜索工作目录文件                      |

## 项目结构

```
binaryRE_agent/
├── src/                          # Python 后端
│   ├── main.py                   # LangGraph Agent 核心（模型 / 工具 / Graph）
│   ├── api.py                    # FastAPI 路由（SSE 流式 chat、上传、session CRUD）
│   ├── config.py                 # 环境变量配置（pydantic-settings）
│   ├── state.py                  # 会话 State 定义
│   ├── tools/                    # Agent 工具定义
│   │   ├── __init__.py
│   │   ├── tools.py              # 反汇编 / 反编译 / 修补等工具实现
│   │   └── sandboxed_shell/      # Docker 沙箱 Shell 工具
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── docker_env.py         # Docker 环境管理与镜像构建
│       ├── llm.py                # LLM 上下文长度等辅助
│       ├── utils.py              # 通用工具函数
│       └── ghidra_scripts/       # Ghidra headless 分析脚本
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── App.tsx               # 主布局 + 状态管理
│   │   └── components/           # Sidebar / ChatArea / Welcome / MessageBubble
│   ├── styles/                   # 样式表
│   ├── vite.config.ts
│   └── package.json
├── tests/                        # 测试
├── Dockerfile.runner             # Kali 工具镜像 Dockerfile
├── compose.yaml                  # Docker Compose 多服务编排
├── run.py                        # 后端启动入口
├── requirements.txt              # Python 依赖清单
├── .env.example                  # 环境变量示例
├── .gitignore
└── README.md                     # 本文件
```

## 架构

```
React (Vite :5173)  ──SSE──>  FastAPI (:7860)  ──>  DeepSeek / OpenAI / Gemini LLM
                                    │
                                    └──>  Docker Kali Runner
                                          ├── objdump（反汇编）
                                          ├── Ghidra（headless 反编译）
                                          ├── radare2（交互分析 / 修补）
                                          └── gdb（动态调试）
```

前后端分离架构：React 前端通过 SSE（Server-Sent Events）流式接收后端响应，Python FastAPI 暴露 REST API。LangGraph 驱动的 Agent 根据用户意图自主选择合适的分析工具，所有工具在 Docker Kali 沙箱容器中安全执行。
