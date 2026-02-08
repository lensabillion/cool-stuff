from pathlib import Path

from bson import ObjectId
from fastapi import HTTPException, UploadFile

from app.core.config import settings


def save_pdf_upload(pdf: UploadFile) -> tuple[str, str]:
    if not pdf or (pdf.content_type != "application/pdf" and not (pdf.filename or "").lower().endswith(".pdf")):
        raise HTTPException(status_code=400, detail="PDF file required")

    filename = f"{ObjectId()}_{pdf.filename}"
    full_path = Path(settings.upload_dir) / filename
    return filename, str(full_path)
