import uuid
import os
import shutil
import logging
from pathlib import Path
from fastapi import UploadFile, status

from app.core.exceptions import AppException


logger = logging.getLogger(__name__)


UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE_MB = 4
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024



# validation
def _get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no extension",
            code="INVALID_FILE_TYPE",
        )
    
    return filename.rsplit(".", 1)[-1].lower()


def _validate_image(filename: str, content: bytes) -> str:
    extension = _get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{extension}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            code="INVALID_FILE_TYPE",
        )
        
    if len(content) == 0:
        raise AppException(
            status_code=status.HTTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
            code="EMPTY_FILE"
        )
    
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB",
            code="FILE_TOO_LARGE",
        )
        
    
    return extension



# uploading files
async def upload_image(file: UploadFile, folder: str = "products") -> str:
    pass
        
        