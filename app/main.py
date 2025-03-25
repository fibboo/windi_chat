import logging

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.api import api_router
from app.configs.logging_settings import get_logger
from app.configs.settings import EnvironmentType, settings
from app.exceptions.base import AppBaseException
from app.schemas.error_response import Error, ErrorResponse

logger = get_logger(__name__)
app = FastAPI(title=settings.app_title)

log_level = logging.INFO if settings.environment == EnvironmentType.PROD else logging.DEBUG
logging.getLogger('uvicorn.access').setLevel(log_level)

app.include_router(api_router)


@app.exception_handler(AppBaseException)
async def entity_exception(_: Request, exc: AppBaseException):
    exc.logger.log(level=exc.log_level, msg=exc.log_message)
    content = ErrorResponse(error=Error(title=exc.title, message=exc.message),
                            error_code=exc.error_code)

    return JSONResponse(status_code=exc.status_code.value,
                        content=content.model_dump())


# Root routes

@app.get('/')
async def main():
    return f'{settings.app_name} entry point.'
