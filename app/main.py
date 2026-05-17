from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import load_config
from app.core.db import init_db
from app.core.quota_scheduler import scheduler as quota_scheduler
from app.proxy.client import close_shared_clients
from app.api.keys import router as keys_router
from app.api.proxies import router as proxies_router
from app.api.stats import router as stats_router
from app.api.tokens import router as tokens_router
from app.api.auth import router as auth_router
from app.api.platforms import router as platforms_router
from app.platforms import REGISTERED_PLUGINS


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    quota_scheduler.cancel_all()
    await close_shared_clients()


def create_app() -> FastAPI:
    config = load_config()

    app = FastAPI(
        title="KeyPool",
        description="API Key 池代理服务",
        version="0.1.0",
        lifespan=lifespan,
    )

    init_db()

    app.include_router(auth_router)
    app.include_router(keys_router)
    app.include_router(proxies_router)
    app.include_router(stats_router)
    app.include_router(tokens_router)
    app.include_router(platforms_router)

    for plugin in REGISTERED_PLUGINS:
        platform_conf = config.platforms.get(plugin.name)
        if platform_conf and not platform_conf.enabled:
            continue
        app.include_router(plugin.get_router(), prefix=f"/api/{plugin.name}")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    static_dir = Path(__file__).parent.parent / "web" / "dist"
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="static-assets")

        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            file_path = static_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()
