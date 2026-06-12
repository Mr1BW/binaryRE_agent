"""
Gradio UI 模板 — 侧边栏 / 欢迎屏 HTML 片段。
供 src/main.py 的 demo_block() 使用。
"""

from __future__ import annotations

SIDEBAR_HEADER = """
<div id="sidebar-header">
    <div class="sidebar-logo">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
        </svg>
        <span>DecompAI</span>
    </div>
    <p class="sidebar-subtitle">Binary Analysis Console</p>
</div>
"""

SESSION_LIST_EMPTY = """
<div id="session-list-empty">
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#94a3b8"
         stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
    </svg>
    <p>暂无分析会话</p>
    <p class="hint">上传一个二进制文件开始</p>
</div>
"""

SIDEBAR_FOOTER = """
<div id="sidebar-footer">
    <div class="footer-row">
        <span>DecompAI v0.1</span>
        <span class="dot">·</span>
        <a href="https://github.com" target="_blank" class="footer-link">GitHub</a>
    </div>
</div>
"""


def build_session_list_html(
    sessions: list[dict], current_hash: str | None = None
) -> str:
    """根据会话列表生成侧边栏 HTML。

    每个会话显示：二进制文件名、短哈希、最后修改时间。
    """
    if not sessions:
        return SESSION_LIST_EMPTY

    items = []
    for s in sessions:
        active_class = "active" if s.get("full_hash") == current_hash else ""
        binary_name = s.get("binary", "未知")
        truncated_name = (
            binary_name if len(binary_name) <= 28 else binary_name[:25] + "..."
        )
        time_str = s.get("time", "")
        short_hash = s.get("hash", "")

        items.append(f"""
        <div class="session-item {active_class}" data-hash="{s.get("full_hash", "")}">
            <div class="session-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
            </div>
            <div class="session-info">
                <span class="session-name" title="{binary_name}">{truncated_name}</span>
                <span class="session-meta">#{short_hash} · {time_str}</span>
            </div>
        </div>
        """)

    return f"""
    <div id="session-list">
        {"".join(items)}
    </div>
    """


WELCOME_SCREEN = """
<div id="welcome-screen">
    <div class="welcome-inner">
        <div class="welcome-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
            </svg>
        </div>
        <h1 class="welcome-title">Binary Analysis Console</h1>
        <p class="welcome-desc">
            上传一个 x86 Linux ELF 二进制文件，开始逆向分析与反编译。
        </p>
        <div class="welcome-features">
            <div class="feature-item">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="16 18 22 12 16 6"/>
                    <polyline points="8 6 2 12 8 18"/>
                </svg>
                <span>反汇编 & 反编译</span>
            </div>
            <div class="feature-item">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                <span>漏洞扫描 & 二进制补丁</span>
            </div>
            <div class="feature-item">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                    <line x1="8" y1="21" x2="16" y2="21"/>
                    <line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
                <span>GDB 动态调试</span>
            </div>
            <div class="feature-item">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                <span>Ghidra / radare2 工具链</span>
            </div>
        </div>
    </div>
</div>
"""
