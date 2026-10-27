from fastapi import FastAPI

from reelshelf.api.error_handlers import register_exception_handlers
from reelshelf.api.health import router as health_router
from reelshelf.bootstrap import build_container
from reelshelf.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings: Settings = settings if settings is not None else Settings()

    app = FastAPI(
        title="ReelShelf API",
        version="0.1.0",
        description="A REST API for personal movie watchlists.",
    )

    app.state.settings = resolved_settings

    # One container per app instance, shared by that app's requests.
    app.state.container = build_container()

    register_exception_handlers(app)

    app.include_router(health_router)
    return app
