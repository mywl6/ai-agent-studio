"""桌面入口：启动 PyWebview + FastAPI 服务"""
import sys
import os
import threading
import logging
import webview
import uvicorn
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(os.path.dirname(sys.executable)) / "data"
else:
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"

sys.path.insert(0, str(BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)

log_file = DATA_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler() if not getattr(sys, 'frozen', False) else logging.NullHandler(),
    ],
)
logger = logging.getLogger(__name__)

API_PORT = 8000


def start_api_server():
    """在后台线程启动 FastAPI"""
    try:
        uvicorn.run(
            "backend.main:app",
            host="127.0.0.1",
            port=API_PORT,
            log_level="info",
        )
    except Exception as e:
        logger.error(f"API 服务启动失败: {e}", exc_info=True)


def main():
    try:
        # 启动 API 服务线程
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()

        import time
        time.sleep(1.5)  # 等待服务就绪

        # 使用 API URL（FastAPI 也挂载了前端静态文件）
        url = f"http://127.0.0.1:{API_PORT}"

        webview.create_window(
            title="AI Agent 平台",
            url=url,
            width=1280,
            height=800,
            min_size=(900, 600),
            text_select=True,
        )
        webview.start()
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        input("按 Enter 退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()