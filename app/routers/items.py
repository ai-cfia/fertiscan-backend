from fastapi import APIRouter, HTTPException

from app.controllers.items import create, read, read_all
from app.models.items import ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("/", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    return create(item)


@router.get("/", response_model=list[ItemResponse])
async def read_items():
    return read_all()


@router.get(
    "/{item_id}",
    responses={
        400: {"description": "Invalid token header"},
        404: {"description": "Item not found"},
    },
    response_model=ItemResponse,
)
async def read_item(item_id: str):
    try:
        return read(item_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")
