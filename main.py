import time
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from routers.memo  import router as memo_api_router
from routers.pages import router as pages_router
from config import APP_NAME, DEBUG

BASE_DIR = Path(__file__).parent

# -------------------------------------------------------
# ロガー設定
# -------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------
# アプリ初期化
# -------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    description="FastAPI + Jinja2 メモ管理アプリ",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 静的ファイル
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# -------------------------------------------------------
# ミドルウェア: リクエスト/レスポンスログ
# -------------------------------------------------------
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

# -------------------------------------------------------
# バリデーションエラーハンドラ
# -------------------------------------------------------
@app.exception_handler(ValidationError)
async def validation_exception_handler(_request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.model},
    )

# -------------------------------------------------------
# ルーター登録
# -------------------------------------------------------
app.include_router(pages_router)       # Jinja2 ページ (/)
app.include_router(memo_api_router)    # REST API (/api/memos)
