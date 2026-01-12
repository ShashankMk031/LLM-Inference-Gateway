from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, DatabaseError
from typing import Optional
import logging
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from datetime import datetime

logger = logging.getLogger(__name__)

class APIError(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code:str = "ERROR"):
        super().__init__(status_code = status_code, detail = { 
            "error":error_code,
            "message": detail,
            "timestamp": datetime.now().isoformat()
        })

# Standard error response model
class ErrorResponse(BaseModel):
    error:str
    message:str
    timestamp: str
    path: Optional[str] = None
    method: Optional[str] = None

async def api_error_handler(request: Request, exc : Exception)-> JSONResponse:
    # Catch-all for unhandled exceptions
    logger.error(f"Unhandled error: {exc}", exc_info = True)

    status_code = getattr(exc, "status_code", 500)
    detail = str(exc)

    if status_code == 500:
        error_code = "INTERNAL_ERROR"
        message = "Internal server error"
    elif status_code >= 500:
        error_code = "SERVER_ERROR"
        message = "Server error"
    elif status_code >= 400:
        error_code = "CLIENT_ERROR"
        message = detail
    else:
        error_code = "ERROR"
        message = detail

    return JSONResponse(
        status_code=status_code,
        content ={
            "error": error_code,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
            "method": request.method
        }
    )

# Specific handlers
async def http_exception_handler(request: Request, exc:StarletteHTTPException):
    return JSONResponse(
        status_code = exc.status_code,
        content={
            "error":"HTTP_ERROR",
            "message":exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path":request.url.path,
            "method":request.method
        }
    )

async def validation_exception_handler(request:Request, exc:ValidationError):
    return JSONResponse(
        status_code = 422,
        content = {
            "error":"VALIDATION_ERROR",
            "message":"Invalid input data",
            "details":exc.errors(),
            "timestamp": datetime.now().isoformat(),
            "path":request.url.path,
            "method":request.method
        }
    )

async def db_integrity_handler(request:Request, exc:IntegrityError):
    logger.warning(f"DB integrity violation: {exc}")
    return JSONResponse(
        status_code = 409,
        content={
            "error":"DATABASE_CONFLICT",
            "message":"Data conflict (duplicate entry)",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
            "method": request.method
        }
    )

async def db_connection_handler(request:Request, exc:DatabaseError):
    logger.error(f"DB connection error: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "error":"DATABASE_ERROR",
            "message":"Database unavailable",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path,
            "method": request.method
        }
    )