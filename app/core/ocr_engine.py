from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from paddleocr import PaddleOCR
from app.config import get_settings

_ocr_engines: dict[str, PaddleOCR] = {}

_LANG_MAP = {
    "ch": "ch",
    "en": "en",
    "korean": "korean",
    "japan": "japan",
    "german": "german",
    "french": "french",
}


def get_ocr_engine(lang: str = "ch") -> PaddleOCR:
    lang_key = _LANG_MAP.get(lang.lower(), "ch")
    if lang_key not in _ocr_engines:
        settings = get_settings()
        _ocr_engines[lang_key] = PaddleOCR(
            use_angle_cls=True,
            lang=lang_key,
            show_log=False,
            use_gpu=settings.ocr_use_gpu,
            enable_mkldnn=not settings.ocr_use_gpu,
            det_db_thresh=0.3,
            det_db_box_thresh=0.5,
            det_db_unclip_ratio=1.6,
        )
    return _ocr_engines[lang_key]


def loaded_engine_langs() -> list[str]:
    return list(_ocr_engines.keys())


def decode_image_bytes(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def auto_rotate_image(img: np.ndarray) -> np.ndarray:
    return img


def parse_ocr_result(result: Any, return_text_only: bool = False) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    if not result or not result[0]:
        return parsed
    for line in result[0]:
        box = line[0]
        text_info = line[1]
        text = text_info[0]
        confidence = float(text_info[1])
        if return_text_only:
            parsed.append({"text": text, "confidence": confidence})
        else:
            coordinates = [{"x": int(p[0]), "y": int(p[1])} for p in box]
            parsed.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "coordinates": coordinates,
                    "bbox": {
                        "xmin": int(min(p[0] for p in box)),
                        "ymin": int(min(p[1] for p in box)),
                        "xmax": int(max(p[0] for p in box)),
                        "ymax": int(max(p[1] for p in box)),
                    },
                }
            )
    return parsed


def run_ocr_on_bgr(img: np.ndarray, lang: str, return_text_only: bool, auto_rotate: bool) -> list[dict[str, Any]]:
    if auto_rotate:
        img = auto_rotate_image(img)
    ocr = get_ocr_engine(lang)
    result = ocr.ocr(img, cls=True)
    return parse_ocr_result(result, return_text_only)
