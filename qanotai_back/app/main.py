from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import init_db
from .routers import admin, auth, catalog
from .seed import seed_catalog

media = Path(get_settings().media_dir)
media.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await seed_catalog()
    yield


app = FastAPI(title="QANOT.AI API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(catalog.router)
app.mount("/api/media", StaticFiles(directory=media), name="media")


@app.get("/api/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
