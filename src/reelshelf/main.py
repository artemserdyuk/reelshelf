from fastapi import FastAPI

from reelshelf.api.error_handlers import register_exception_handlers
from reelshelf.api.health import router as health_router
from reelshelf.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings: Settings = settings if settings is not None else Settings()

    app = FastAPI(
        title="ReelShelf API",
        version="0.1.0",
        description="A REST API for personal movie watchlists.",
    )

    app.state.settings = resolved_settings

    register_exception_handlers(app)

    app.include_router(health_router)
    return app
