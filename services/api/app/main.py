import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from services.api.app.api.v1.routes import router
from services.api.app.core.config import get_settings
from services.api.app.core.logging import configure_logging
from services.api.app.core.metrics import install_metrics
from services.api.app.db.session import get_session


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(title="AquaMaroc AI", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {"code": f"http_{exc.status_code}", "message": str(exc.detail)},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Paramètres invalides",
                    "details": [
                        {"location": list(e["loc"]), "message": e["msg"]} for e in exc.errors()
                    ],
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_request: Request, _exc: SQLAlchemyError):
        logging.getLogger("aquamaroc.api").error("database_unavailable")
        return JSONResponse(
            status_code=503,
            content={
                "error": {"code": "database_unavailable", "message": "Base indisponible"},
            },
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": settings.app_mode}

    @app.get("/ready")
    def ready(db: Session = Depends(get_session)):
        try:
            # La version attendue évolue avec les migrations requises par cette API.
            version = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            if version != "0002_capacity_provenance":
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": {
                            "code": "schema_outdated",
                            "message": "Appliquer les migrations de cette version",
                        }
                    },
                )
            db.execute(text("SELECT id FROM reservoirs LIMIT 1"))
        except SQLAlchemyError:
            return JSONResponse(
                status_code=503,
                content={
                    "error": {"code": "not_ready", "message": "Base ou migrations indisponibles"},
                },
            )
        return {"status": "ready"}

    app.include_router(router)
    if settings.metrics_enabled:
        install_metrics(app)
    return app


app = create_app()
