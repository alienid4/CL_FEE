from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.db.schema import init_db
from app.db.session import db_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    with db_session() as conn:
        init_db(conn)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    web_dir = Path(__file__).resolve().parent / "web"
    app = FastAPI(
        title="Fee Contract Control API",
        version="0.1.0",
        description="Development API for fee contract control and signing workflow tracking.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_base_url, "http://localhost:8888", "http://127.0.0.1:8888"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=web_dir), name="static")
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    def web_app() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    return app


app = create_app()
