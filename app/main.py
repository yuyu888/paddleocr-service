from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from app.config import get_settings
from app.routers import invoice, meta, ocr


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.service_name,
        description="PaddleOCR HTTP API；发票支持数电 XML/JSON 与影像 OCR+规则，local/remote 计算模式",
        version=settings.service_version,
    )
    application.include_router(meta.router)
    application.include_router(ocr.router, prefix="/ocr")
    application.include_router(invoice.router)
    return application


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8088,
        workers=1,
        log_level="info",
    )
