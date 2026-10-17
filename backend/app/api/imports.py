from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from app.services.document_parser import DocumentParser
from app.api.auth import get_current_user, User

import logging

logger = logging.getLogger(__name__)
router = APIRouter()
parser = DocumentParser()

@router.post("/text")
def import_text(payload: dict, user: User = Depends(get_current_user)):
    text = payload.get("text", "")
    try:
        res = parser.extract_from_text(text)
        return res.model_dump()
    except Exception as e:
        logger.error(f"Text import failed: {e}")
        raise HTTPException(status_code=400, detail="We couldn't structure that itinerary.")

@router.post("/pdf")
async def import_pdf(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    try:
        res = parser.extract_from_pdf(content)
        return res.model_dump()
    except Exception as e:
        logger.error(f"PDF import failed: {e}")
        raise HTTPException(status_code=400, detail="We couldn't structure that itinerary.")

@router.post("/image")
async def import_image(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    try:
        res = parser.extract_from_image(content, file.content_type)
        return res.model_dump()
    except Exception as e:
        logger.error(f"Image import failed: {e}")
        raise HTTPException(status_code=400, detail="We couldn't structure that itinerary.")
