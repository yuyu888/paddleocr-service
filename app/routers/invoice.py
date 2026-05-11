import base64

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.models.invoice import ComputeMode, DocType, InvoiceParseRequest, InvoiceParseResponse
from app.services.invoice_facade import parse_invoice

router = APIRouter()


@router.post("/invoice/v1/parse", response_model=InvoiceParseResponse)
async def invoice_parse(
    body: InvoiceParseRequest,
    settings: Settings = Depends(get_settings),
) -> InvoiceParseResponse:
    try:
        return await parse_invoice(body, settings)
    except ValueError as e:
        code = str(e)
        status = 400
        if code in ("invoice_remote_base_url_not_set", "remote_unreachable"):
            status = 503
        if code.startswith("remote_http_"):
            status = 502
        raise HTTPException(status_code=status, detail=code) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"invoice_parse_failed: {e}") from e


@router.post("/invoice/v1/parse/file", response_model=InvoiceParseResponse)
async def invoice_parse_file(
    file: UploadFile = File(..., description="票据图片文件"),
    compute_mode: ComputeMode | None = Form(default=None),
    doc_type: DocType = Form(default=DocType.cn_vat),
    lang: str = Form(default="ch"),
    auto_rotate: bool = Form(default=True),
    settings: Settings = Depends(get_settings),
) -> InvoiceParseResponse:
    payload = await file.read()
    body = InvoiceParseRequest(
        compute_mode=compute_mode,
        input_kind="image_base64",
        doc_type=doc_type,
        payload=base64.b64encode(payload).decode("ascii"),
        lang=lang,
        auto_rotate=auto_rotate,
    )
    try:
        return await parse_invoice(body, settings)
    except ValueError as e:
        code = str(e)
        status = 400
        if code in ("invoice_remote_base_url_not_set", "remote_unreachable"):
            status = 503
        if code.startswith("remote_http_"):
            status = 502
        raise HTTPException(status_code=status, detail=code) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"invoice_parse_failed: {e}") from e
