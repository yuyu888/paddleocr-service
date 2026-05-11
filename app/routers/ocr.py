from __future__ import annotations

import base64
from typing import Any

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core import ocr_engine

router = APIRouter()


@router.post("")
async def ocr_upload(
    file: UploadFile = File(..., description="图片文件"),
    lang: str = Form("ch"),
    auto_rotate: bool = Form(True),
    return_text_only: bool = Form(False),
) -> JSONResponse:
    try:
        contents = await file.read()
        img = ocr_engine.decode_image_bytes(contents)
        if img is None:
            raise HTTPException(status_code=400, detail="无法解析图片文件")
        if auto_rotate:
            img = ocr_engine.auto_rotate_image(img)
        ocr = ocr_engine.get_ocr_engine(lang)
        result = ocr.ocr(img, cls=True)
        parsed = ocr_engine.parse_ocr_result(result, return_text_only)
        return JSONResponse(
            content={
                "success": True,
                "language": lang,
                "text_count": len(parsed),
                "results": parsed,
                "full_text": "\n".join([item["text"] for item in parsed]),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {e}") from e


class OcrBase64Body(BaseModel):
    image_base64: str = Field(..., description="Base64 图片")
    lang: str = "ch"
    auto_rotate: bool = True
    return_text_only: bool = False


@router.post("/base64")
async def ocr_base64(body: OcrBase64Body) -> JSONResponse:
    try:
        b64 = body.image_base64
        if "," in b64:
            b64 = b64.split(",", 1)[1]
        data = base64.b64decode(b64, validate=False)
        img = ocr_engine.decode_image_bytes(data)
        if img is None:
            raise HTTPException(status_code=400, detail="无法解析 Base64 图片")
        if body.auto_rotate:
            img = ocr_engine.auto_rotate_image(img)
        ocr = ocr_engine.get_ocr_engine(body.lang)
        result = ocr.ocr(img, cls=True)
        parsed = ocr_engine.parse_ocr_result(result, body.return_text_only)
        return JSONResponse(
            content={
                "success": True,
                "language": body.lang,
                "text_count": len(parsed),
                "results": parsed,
                "full_text": "\n".join([item["text"] for item in parsed]),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {e}") from e


class OcrUrlBody(BaseModel):
    url: str
    lang: str = "ch"
    auto_rotate: bool = True
    return_text_only: bool = False


@router.post("/url")
async def ocr_url(body: OcrUrlBody) -> JSONResponse:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(body.url)
            r.raise_for_status()
            data = r.content
        img = ocr_engine.decode_image_bytes(data)
        if img is None:
            raise HTTPException(status_code=400, detail="URL 内容无法解码为图片")
        if body.auto_rotate:
            img = ocr_engine.auto_rotate_image(img)
        ocr = ocr_engine.get_ocr_engine(body.lang)
        result = ocr.ocr(img, cls=True)
        parsed = ocr_engine.parse_ocr_result(result, body.return_text_only)
        return JSONResponse(
            content={
                "success": True,
                "language": body.lang,
                "text_count": len(parsed),
                "results": parsed,
                "full_text": "\n".join([item["text"] for item in parsed]),
            }
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"拉取 URL 失败: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {e}") from e


@router.post("/batch")
async def ocr_batch(
    files: list[UploadFile] = File(..., description="批量图片"),
    lang: str = Form("ch"),
    return_text_only: bool = Form(False),
) -> JSONResponse:
    results: list[dict[str, Any]] = []
    for file in files:
        try:
            contents = await file.read()
            img = ocr_engine.decode_image_bytes(contents)
            if img is None:
                results.append({"filename": file.filename, "success": False, "error": "无法解析图片"})
                continue
            ocr = ocr_engine.get_ocr_engine(lang)
            result = ocr.ocr(img, cls=True)
            parsed = ocr_engine.parse_ocr_result(result, return_text_only)
            results.append(
                {
                    "filename": file.filename,
                    "success": True,
                    "text_count": len(parsed),
                    "full_text": "\n".join([item["text"] for item in parsed]),
                }
            )
        except Exception as e:
            results.append({"filename": file.filename, "success": False, "error": str(e)})

    return JSONResponse(content={"success": True, "total": len(files), "results": results})
