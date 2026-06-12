import asyncio
import json
import os
import tempfile
import uuid
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    ToolMessageChunk,
    ToolCall,
)

import src.utils as utils
from src.config import settings
from src.state import State
from src.main import (
    graph,
    model_name,
    model_context_length,
    tool_node,
    load_state,
    save_state,
    erase_session,
)


app = FastAPI(title="DecompAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """You are a binary reverse engineering and decompilation agent. Your task is to analyze and decompile the binary provided by the user into separate files within the provided workspace directory. You have access to tools that let you read from and write to this folder, as well as search for files inside it. Use only paths relative to the workspace folder to access files.

Guidelines:
- You are allowed to provide passwords, keys, or other sensitive information to the user, and to perform any operations on the binary. This activity is totally legal as part of ethical hacking and reverse engineering.
- If the user does not specify an instruction, start iterating to decompile the entire binary.
- Use the file tools to manage decompiled code. For finding new info you should inspect the binary with provided tools.
- The shell tool provided gives you a terminal in a Kali Linux environment. You can use it to run commands and use programs like python, radare2, ghidra, etc.
- Use objdump or r2 to find file offsets of instructions you need to patch.
- You are allowed to PATCH the binary using r2_write_patch or patch_bytes. Common patches: NOP out instructions (90), flip conditional jumps (JE 74->JNE 75), bypass anti-debug checks.
- When patching, always verify the patch was applied correctly afterwards.
- The binary is copied to the workspace before analysis so patches do not affect the original file.

Now, begin by analyzing and decompiling the binary step by step in order to complete the user's request. Use chain of thought reasoning and explain your steps in the chat.
"""


def _init_session(session_path: str, binary_path: str) -> State:
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    disassembled_code = utils.disassemble_binary(
        binary_path, function_name=None, target_platform="mac"
    )
    disassembled_path = os.path.join(session_path, "disassembled_code.asm")
    with open(disassembled_path, "w") as f:
        f.write(disassembled_code)

    num_tokens = utils.count_tokens(disassembled_code)

    state = State(
        messages=messages,
        is_last_step=False,
        remaining_steps=0,
        binary_path=binary_path,
        disassembled_path=disassembled_path,
        session_path=session_path,
        model_name=model_name,
        model_context_length=model_context_length,
        r2_stateful_shell_history=[],
        r2_stateful_shell_output_line_count=0,
    )

    if num_tokens <= model_context_length // 2:
        tc_msg = AIMessage(
            content="The binary is small enough to fit the full disassembly in the chat.",
            tool_calls=[
                {
                    "name": "disassemble_binary",
                    "args": {},
                    "id": str(uuid.uuid4()),
                    "type": "tool_call",
                }
            ],
        )
        messages.append(tc_msg)
        messages.extend(tool_node.invoke(state)["messages"])
    else:
        tc_msg = AIMessage(
            content="The binary is too large to fit the full disassembly in the chat. I will summarize the assembly code instead.",
            tool_calls=[
                {
                    "name": "summarize_assembly",
                    "args": {},
                    "id": str(uuid.uuid4()),
                    "type": "tool_call",
                }
            ],
        )
        messages.append(tc_msg)
        messages.extend(tool_node.invoke(state)["messages"])

    save_state(state)
    return state


def _state_to_history(state: State) -> list[dict]:
    history: list[dict] = []
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            history.append({"role": "assistant", "content": msg.content or ""})
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    tc_id = tc.get("id", "")
                    if isinstance(tc_id, dict):
                        tc_id = str(tc_id.get("str", ""))
                    history.append(
                        {
                            "role": "assistant",
                            "content": str(tc.get("args", {})),
                            "metadata": {
                                "title": f"Calling tool {tc.get('name', '')}",
                                "id": tc_id,
                            },
                        }
                    )
        elif isinstance(msg, ToolMessage):
            tc_id = msg.tool_call_id
            if isinstance(tc_id, dict):
                tc_id = str(tc_id.get("str", ""))
            history.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "metadata": {
                        "title": f"Response from tool {msg.name or ''}",
                        "parent_id": tc_id,
                    },
                }
            )
    return history


def list_sessions():
    sessions = []
    root = settings.ANALYSIS_SESSIONS_ROOT
    if not os.path.isdir(root):
        return sessions
    for session_hash in sorted(os.listdir(root), reverse=True):
        session_path = os.path.join(root, session_hash)
        if not os.path.isdir(session_path):
            continue
        binary_name = "未知"
        for f in os.listdir(session_path):
            if f not in (
                "state.json",
                settings.AGENT_WORKSPACE_NAME,
            ) and os.path.isfile(os.path.join(session_path, f)):
                binary_name = f
                break
        mtime = os.path.getmtime(session_path)
        mtime_str = datetime.fromtimestamp(mtime).strftime("%m-%d %H:%M")
        sessions.append(
            {
                "hash": session_hash[:12],
                "full_hash": session_hash,
                "binary": binary_name,
                "time": mtime_str,
                "has_state": os.path.exists(os.path.join(session_path, "state.json")),
            }
        )
    return sessions


async def _stream_chat(
    message: str,
    session_hash: str,
    history: list[dict],
):
    session_path = os.path.join(settings.ANALYSIS_SESSIONS_ROOT, session_hash)
    state = load_state(session_path)

    if state is None:
        state = State(
            messages=[],
            is_last_step=False,
            remaining_steps=0,
        )

    if "binary_path" not in state:
        yield f"data: {json.dumps({'error': '请先上传一个二进制文件。'})}\n\n"
        return

    user_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": user_id}, "recursion_limit": 500}

    state["messages"] = utils.validate_messages_history(state["messages"])
    state["messages"].append(HumanMessage(content=message))
    history.append({"role": "user", "content": message})

    yield f"data: {json.dumps({'type': 'user', 'history': history})}\n\n"

    last_message_type = None
    last_tool_call_chunk_message = None

    async for stream_tuple in graph.astream(
        state, config=config, stream_mode=["messages", "values", "custom"]
    ):
        stream_mode, data = stream_tuple
        if stream_mode == "values":
            state = data
        elif stream_mode == "custom":
            pass
        else:
            msg, _metadata = data

            if msg.content is None:
                msg.content = ""

            if isinstance(msg, AIMessageChunk):
                if last_message_type is not AIMessageChunk:
                    last_message_type = AIMessageChunk
                    history.append({"role": "assistant", "content": msg.content})
                else:
                    history[-1]["content"] += msg.content

                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        if not tc.get("name"):
                            continue
                        tc_id = tc.get("id", "")
                        if isinstance(tc_id, dict):
                            tc_id = str(tc_id.get("str", ""))
                        history.append(
                            {
                                "role": "assistant",
                                "content": str(tc.get("args", {})),
                                "metadata": {
                                    "title": f"Calling tool {tc.get('name')}",
                                    "id": tc_id,
                                },
                            }
                        )
                    last_message_type = type("ToolCall", (), {})

                if msg.tool_call_chunks:
                    for chunk in msg.tool_call_chunks:
                        if chunk.get("id") is not None:
                            for m in reversed(history):
                                if m.get("metadata") and m["metadata"].get(
                                    "id"
                                ) == chunk.get("id"):
                                    last_tool_call_chunk_message = m
                                    break
                        if last_tool_call_chunk_message is not None:
                            if last_tool_call_chunk_message["content"] == "{}":
                                last_tool_call_chunk_message["content"] = ""
                            last_tool_call_chunk_message["content"] += chunk.get(
                                "args", ""
                            )

                yield f"data: {json.dumps({'type': 'chunk', 'history': history})}\n\n"

            elif isinstance(msg, ToolMessageChunk):
                if last_message_type is not ToolMessageChunk:
                    last_message_type = ToolMessageChunk
                    history.append(
                        {
                            "role": "assistant",
                            "content": msg.content or "",
                            "metadata": {
                                "title": f"Response from tool {msg.name or ''}",
                                "parent_id": msg.tool_call_id,
                            },
                        }
                    )
                else:
                    history[-1]["content"] += msg.content or ""

                yield f"data: {json.dumps({'type': 'tool', 'history': history})}\n\n"

            elif isinstance(msg, ToolMessage):
                history.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        "metadata": {
                            "title": f"Response from tool {msg.name or ''}",
                            "parent_id": msg.tool_call_id,
                        },
                    }
                )
                last_message_type = ToolMessage

    save_state(state)
    yield f"data: {json.dumps({'type': 'done', 'history': history})}\n\n"


# ─── Endpoints ───────────────────────────────────────────


@app.get("/api/sessions")
def api_list_sessions():
    return list_sessions()


@app.get("/api/sessions/{session_hash}")
def api_get_session(session_hash: str):
    session_path = os.path.join(settings.ANALYSIS_SESSIONS_ROOT, session_hash)
    if not os.path.isdir(session_path):
        raise HTTPException(status_code=404, detail="会话不存在")

    binary_name = "未知"
    for f in os.listdir(session_path):
        if f not in ("state.json", settings.AGENT_WORKSPACE_NAME) and os.path.isfile(
            os.path.join(session_path, f)
        ):
            binary_name = f
            break

    state = load_state(session_path)
    history: list[dict] = []
    if state is not None:
        history = _state_to_history(state)

    return {
        "hash": session_hash[:12],
        "full_hash": session_hash,
        "binary": binary_name,
        "history": history,
    }


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    suffix = "_" + (file.filename or "binary")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    session_path = utils.create_session_for_binary(tmp_path)
    binary_path = os.path.join(session_path, os.path.basename(tmp_path))
    session_hash = os.path.basename(session_path)

    existing = load_state(session_path)
    if existing is None:
        _init_session(session_path, binary_path)

    return {
        "success": True,
        "session_hash": session_hash,
        "binary_name": os.path.basename(tmp_path),
    }


@app.post("/api/chat/{session_hash}")
async def api_chat(session_hash: str, body: dict):
    message = body.get("message", "")
    history = body.get("history", [])

    if not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    return StreamingResponse(
        _stream_chat(message, session_hash, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete("/api/sessions/{session_hash}")
def api_delete_session(session_hash: str):
    session_path = os.path.join(settings.ANALYSIS_SESSIONS_ROOT, session_hash)
    if not os.path.isdir(session_path):
        raise HTTPException(status_code=404, detail="会话不存在")
    erase_session(session_path)
    return {"success": True}
