from fastapi import FastAPI, HTTPException

from app.controllers.items import create, read, read_all
from app.models.items import ItemCreate, ItemResponse

app = FastAPI()


@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}


@app.post("/items/", response_model=ItemResponse, tags=["Items"])
async def create_item(item: ItemCreate):
    return create(item)


@app.get("/items/", response_model=list[ItemResponse], tags=["Items"])
async def read_items():
    return read_all()


@app.get(
    "/items/{item_id}",
    responses={
        400: {"description": "Invalid token header"},
        404: {"description": "Item not found"},
    },
    response_model=ItemResponse,
    tags=["Items"],
)
async def read_item(item_id: str):
    try:
        return read(item_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")
