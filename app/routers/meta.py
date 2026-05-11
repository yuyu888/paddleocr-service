from fastapi import APIRouter

from app.config import get_settings
from app.core import ocr_engine

router = APIRouter(tags=["meta"])


@router.get("/")
async def root() -> dict:
    s = get_settings()
    return {
        "service": s.service_name,
        "version": s.service_version,
        "status": "running",
        "endpoints": {
            "POST /ocr": "OCR 上传图片",
            "POST /ocr/base64": "OCR Base64",
            "POST /ocr/batch": "批量 OCR",
            "POST /ocr/url": "OCR 远程图片 URL",
            "POST /invoice/v1/parse": "发票解析（数电/影像，local|remote）",
            "GET /health": "健康检查",
            "GET /languages": "OCR 语言列表",
        },
    }


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "engines_loaded": ocr_engine.loaded_engine_langs()}


@router.get("/languages")
async def languages() -> dict:
    return {
        "languages": {
            "ch": "中文（简体）",
            "en": "英文",
            "korean": "韩文",
            "japan": "日文",
            "german": "德文",
            "french": "法文",
        }
    }
