"""
DecompAI 启动入口
  python run.py              # 带 Gradio UI + API（默认）
  python run.py --api-only   # FastAPI 模式，供前端调用
"""

import sys
import gradio as gr
import src.main as main
from src.config import settings

mode = "ui"
if "--api-only" in sys.argv:
    mode = "api"

if mode == "api":
    import uvicorn
    from src.api import app

    print(f"Starting FastAPI on port {settings.GRADIO_SERVER_PORT}")
    uvicorn.run(
        app,
        host=settings.GRADIO_SERVER_NAME,
        port=settings.GRADIO_SERVER_PORT,
        log_level="info",
    )
else:
    with gr.Blocks(css=main.CSS, title="Binary Analysis Console") as demo:
        main.demo_block()

    main.setup_api_routes(demo)
    demo.queue(default_concurrency_limit=5)
    demo.launch(
        server_name=settings.GRADIO_SERVER_NAME,
        server_port=settings.GRADIO_SERVER_PORT,
        share=settings.GRADIO_SHARE,
    )
