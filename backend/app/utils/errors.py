"""Centralized exception handling — never leak stack traces in prod."""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("errors")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Unable to process document." if "document" in request.url.path else "An unexpected error occurred."}},
    )
