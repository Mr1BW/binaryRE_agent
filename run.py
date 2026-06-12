"""
DecompAI 启动入口 — FastAPI 模式
  python run.py
"""

import uvicorn
from src.api import app
from src.config import settings

print(
    f"Starting FastAPI on {settings.GRADIO_SERVER_NAME}:{settings.GRADIO_SERVER_PORT}"
)
uvicorn.run(
    app,
    host=settings.GRADIO_SERVER_NAME,
    port=settings.GRADIO_SERVER_PORT,
    log_level="info",
)
