from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import install_request_id_logging
from app.core.request_id import request_id_middleware


def create_app() -> FastAPI:
    settings = get_settings()
    docs = settings.docs_enabled
    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    install_request_id_logging()
    register_error_handlers(app)
    app.middleware("http")(request_id_middleware)
    app.include_router(api_router)
    return app


app = create_app()
