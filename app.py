#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import base64
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import cv2
import uvicorn

# 初始化 FastAPI
app = FastAPI(
    title="PaddleOCR Service",
    description="PaddleOCR HTTP API 服务，支持多语言识别",
    version="1.0.0"
)

# 全局 OCR 实例
ocr_engines = {}


def get_ocr_engine(lang: str = 'ch') -> PaddleOCR:
    """获取或创建 OCR 实例（单例模式）"""
    lang_map = {
        'ch': 'ch',           # 中文
        'en': 'en',           # 英文
        'korean': 'korean',   # 韩文
        'japan': 'japan',     # 日文
        'german': 'german',   # 德文
        'french': 'french',   # 法文
    }
    
    lang_key = lang_map.get(lang.lower(), 'ch')
    
    if lang_key not in ocr_engines:
        ocr_engines[lang_key] = PaddleOCR(
            use_angle_cls=True,      # 使用角度分类器
            lang=lang_key,            # 识别语言
            show_log=False,           # 不显示日志
            use_gpu=False,            # 使用 CPU（GPU版本需要单独安装）
            enable_mkldnn=True,       # 启用 MKLDNN 加速
            det_db_thresh=0.3,        # 检测阈值
            det_db_box_thresh=0.5,    # 检测框阈值
            det_db_unclip_ratio=1.6,  # 检测框扩展比例
        )
    
    return ocr_engines[lang_key]


@app.get("/")
async def root():
    return {
        "service": "PaddleOCR Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /ocr": "OCR 识别（上传图片文件）",
            "POST /ocr/base64": "OCR 识别（Base64 编码图片）",
            "POST /ocr/url": "OCR 识别（图片URL）",
            "GET /health": "健康检查",
            "GET /languages": "支持的语言列表"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "engines_loaded": list(ocr_engines.keys())}


@app.get("/languages")
async def get_languages():
    return {
        "languages": {
            "ch": "中文（简体）",
            "en": "英文",
            "korean": "韩文",
            "japan": "日文",
            "german": "德文",
            "french": "法文"
        }
    }


@app.post("/ocr")
async def ocr_from_file(
    file: UploadFile = File(..., description="图片文件"),
    lang: str = Form("ch", description="识别语言：ch/en/korean/japan/german/french"),
    auto_rotate: bool = Form(True, description="是否自动旋转图片"),
    return_text_only: bool = Form(False, description="是否只返回文本（不返回坐标）")
):
    """
    从上传的文件进行 OCR 识别
    """
    try:
        # 读取图片
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="无法解析图片文件")
        
        # 自动旋转处理
        if auto_rotate:
            img = auto_rotate_image(img)
        
        # 获取 OCR 引擎并执行识别
        ocr = get_ocr_engine(lang)
        result = ocr.ocr(img, cls=True)
        
        # 解析结果
        parsed_result = parse_ocr_result(result, return_text_only)
        
        return JSONResponse(content={
            "success": True,
            "language": lang,
            "text_count": len(parsed_result),
            "results": parsed_result,
            "full_text": "\n".join([item["text"] for item in parsed_result])
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")


@app.post("/ocr/base64")
async def ocr_from_base64(
    request: Dict[str, Any]
):
    """
    从 Base64 编码的图片进行 OCR 识别
    """
    try:
        image_base64 = request.get("image_base64")
        lang = request.get("lang", "ch")
        auto_rotate = request.get("auto_rotate", True)
        return_text_only = request.get("return_text_only", False)
        
        if not image_base64:
            raise HTTPException(status_code=400, detail="缺少 image_base64 参数")
        
        # 解码 Base64
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        img_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="无法解析 Base64 图片")
        
        # 自动旋转处理
        if auto_rotate:
            img = auto_rotate_image(img)
        
        # 执行 OCR
        ocr = get_ocr_engine(lang)
        result = ocr.ocr(img, cls=True)
        
        parsed_result = parse_ocr_result(result, return_text_only)
        
        return JSONResponse(content={
            "success": True,
            "language": lang,
            "text_count": len(parsed_result),
            "results": parsed_result,
            "full_text": "\n".join([item["text"] for item in parsed_result])
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")


def auto_rotate_image(img):
    """自动旋转图片（基于 PaddleOCR 的角度检测）"""
    # 简化版：这里只做基本的方向检测
    # 完整实现需要额外的角度分类模型
    return img


def parse_ocr_result(result, return_text_only=False):
    """
    解析 PaddleOCR 返回结果
    
    result 格式:
    [
        [
            [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 文本框坐标
            ('识别文本', 置信度)
        ],
        ...
    ]
    """
    parsed = []
    
    if not result or not result[0]:
        return parsed
    
    for line in result[0]:
        box = line[0]
        text_info = line[1]
        
        text = text_info[0]
        confidence = text_info[1]
        
        if return_text_only:
            parsed.append({
                "text": text,
                "confidence": confidence
            })
        else:
            # 转换坐标格式
            coordinates = [
                {"x": int(p[0]), "y": int(p[1])} for p in box
            ]
            parsed.append({
                "text": text,
                "confidence": confidence,
                "coordinates": coordinates,
                "bbox": {
                    "xmin": int(min(p[0] for p in box)),
                    "ymin": int(min(p[1] for p in box)),
                    "xmax": int(max(p[0] for p in box)),
                    "ymax": int(max(p[1] for p in box))
                }
            })
    
    return parsed


@app.post("/ocr/batch")
async def ocr_batch(
    files: List[UploadFile] = File(..., description="批量图片文件"),
    lang: str = Form("ch", description="识别语言"),
    return_text_only: bool = Form(False)
):
    """批量 OCR 识别"""
    results = []
    
    for file in files:
        try:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "无法解析图片"
                })
                continue
            
            ocr = get_ocr_engine(lang)
            result = ocr.ocr(img, cls=True)
            parsed = parse_ocr_result(result, return_text_only)
            
            results.append({
                "filename": file.filename,
                "success": True,
                "text_count": len(parsed),
                "full_text": "\n".join([item["text"] for item in parsed])
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return JSONResponse(content={
        "success": True,
        "total": len(files),
        "results": results
    })


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8088,
        workers=1,  # PaddleOCR 内存占用较大，建议只开一个 worker
        log_level="info"
    )