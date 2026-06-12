import os
import uuid
import json
from datetime import datetime
from typing_extensions import Literal, Annotated
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    BaseMessage,
    AIMessage,
    ToolMessage,
    AIMessageChunk,
    ToolMessageChunk,
    ToolCall,
)
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain.load.dump import dumps
from langchain.load.load import loads
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import openai
from langgraph.prebuilt import InjectedState, InjectedStore
from langchain_community.agent_toolkits import FileManagementToolkit
import langchain_community.agent_toolkits.file_management.toolkit as file_management_toolkit
from langchain_community.tools import (
    CopyFileTool,
    DeleteFileTool,
    FileSearchTool,
    MoveFileTool,
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
)
from langchain_community.tools import ShellTool
from langgraph.prebuilt import create_react_agent
from langgraph.managed import IsLastStep, RemainingSteps
import tiktoken
import asyncio
import shutil
import dotenv
import logging

from src.config import settings
import src.utils as utils
import src.tools as tools
from src.tools.sandboxed_shell import SandboxedShellTool
from src.state import State

dotenv.load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)

# ── Tools ────────────────────────────────────────────────────────────────────

custom_tools = [
    tools.disassemble_binary,
    tools.summarize_assembly,
    tools.disassemble_section,
    tools.disassemble_function,
    tools.dump_memory,
    tools.get_string_at_address,
    tools.kali_stateful_shell,
    tools.run_ghidra_post_script,
    tools.decompile_function_with_ghidra,
    tools.r2_stateless_shell,
    tools.r2_stateful_shell,
    tools.run_python_script,
    tools.r2_write_patch,
    tools.patch_bytes,
]

excluded_tools = {FileSearchTool}
file_management_tools = [
    tools.create_tool_function(t)
    for t in file_management_toolkit._FILE_TOOLS
    if t not in excluded_tools
]

all_tools = custom_tools + file_management_tools
tool_node = ToolNode(all_tools)

# ── Model ────────────────────────────────────────────────────────────────────

model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
logging.info(f"Model name: {model_name}")

model_context_length = utils.get_context_length(model_name)

openai_base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

if "gemini" in model_name:
    api_key = os.getenv("GEMINI_API_KEY")
    openai_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    content_null_value = " "
    if "2.5" in model_name:
        model = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            streaming=True,
            base_url=openai_base_url,
            max_retries=10,
        )
    else:
        model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            streaming=True,
            base_url=openai_base_url,
            content_null_value=content_null_value,
            max_retries=10,
        )
else:
    is_deepseek = "deepseek" in model_name.lower()
    model = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        streaming=True,
        base_url=openai_base_url,
        max_retries=10,
        reasoning_effort="low"
        if (
            not is_deepseek
            and ("o1" in model_name or "o3" in model_name or "o4" in model_name)
        )
        else None,
    )

model = model.bind_tools(all_tools)

# ── Graph Nodes ──────────────────────────────────────────────────────────────


async def call_model(state: State, config: RunnableConfig):
    messages = state["messages"]
    retries = 0
    while retries < 3:
        try:
            response = await model.ainvoke(messages, config)
            if response.content == "":
                response.content = " "
            state["messages"] = response
            return state
        except openai.RateLimitError as e:
            retries += 1
            print(
                f"RateLimitError encountered: {e}. Waiting for 30s before retrying (Attempt {retries}/3)"
            )
            await asyncio.sleep(30)
    raise Exception("Model call failed after 3 retries due to rate limit errors.")


def request_feedback(state: State):
    print("Requesting user feedback...")
    feedback = input("Please provide your feedback (or press Enter to skip): ")
    if feedback:
        state["messages"].append(HumanMessage(content=f"User Feedback: {feedback}"))
    return {"messages": state["messages"]}


def should_continue_or_feedback(state: State) -> Literal["tools", "feedback", END]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    elif "critical_step" in last_message.content.lower():
        return "feedback"
    return END


# ── Graph ────────────────────────────────────────────────────────────────────

workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("feedback", request_feedback)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue_or_feedback)
workflow.add_edge("tools", "agent")
workflow.add_edge("feedback", "agent")

checkpointer = MemorySaver()


def prepare_messages(state: State):
    if "gemini" in model_name:
        for m in state["messages"]:
            if isinstance(m, AIMessage):
                m.content = m.content or " "
    return state["messages"]


graph = create_react_agent(
    model,
    all_tools,
    state_schema=State,
    checkpointer=checkpointer,
    prompt=prepare_messages,
)

# ── Session Persistence ──────────────────────────────────────────────────────


def save_state(state: State):
    session_path = state.get("session_path")
    if not session_path:
        print("No session path found. Cannot save conversation history.")
        return
    history_file = os.path.join(session_path, "state.json")
    with open(history_file, "w") as hf:
        hf.write(dumps(state))
    print(f"Conversation history saved to {history_file}")


def load_state(session_path: str) -> dict | None:
    state_file = os.path.join(session_path, "state.json")
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return loads(f.read())
    return None


def erase_session(session_path: str):
    if not os.path.exists(session_path):
        print(f"Session not found at {session_path}")
        return
    if not session_path.startswith(f"{settings.ANALYSIS_SESSIONS_ROOT}/"):
        raise ValueError(f"Invalid session path: {session_path}")
    shutil.rmtree(session_path)


def list_sessions() -> list[dict]:
    sessions = []
    root = settings.ANALYSIS_SESSIONS_ROOT
    if not os.path.isdir(root):
        return sessions
    for session_hash in sorted(os.listdir(root), reverse=True):
        session_path = os.path.join(root, session_hash)
        if not os.path.isdir(session_path):
            continue
        binary_name = "unknown"
        binary_path = ""
        for f in os.listdir(session_path):
            if (
                f != "state.json"
                and f != settings.AGENT_WORKSPACE_NAME
                and os.path.isfile(os.path.join(session_path, f))
            ):
                binary_name = f
                binary_path = os.path.join(session_path, f)
                break
        mtime = os.path.getmtime(session_path)
        mtime_str = datetime.fromtimestamp(mtime).strftime("%m-%d %H:%M")
        sessions.append(
            {
                "hash": session_hash[:12],
                "full_hash": session_hash,
                "binary": binary_name,
                "binary_path": binary_path,
                "time": mtime_str,
                "has_state": os.path.exists(os.path.join(session_path, "state.json")),
            }
        )
    return sessions
