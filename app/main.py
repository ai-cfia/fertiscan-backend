from fastapi import FastAPI

from app.routers import items, monitoring

app = FastAPI()

app.include_router(monitoring.router)
app.include_router(items.router)
