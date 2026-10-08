from fastapi import FastAPI

from reelshelf.api.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ReelShelf API",
        version="0.1.0",
        description="A REST API for personal movie watchlists.",
    )
    app.include_router(health_router)
    return app
