from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from psycopg_pool import ConnectionPool
from pydantic import UUID4

import app.constants as c
from app.connection_manager import ConnectionManager
from app.controllers.items import create, read, read_all
from app.dependencies import get_connection_manager
from app.models.items import ItemCreate, ItemResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = ConnectionPool(
        conninfo=c.FERTISCAN_DB_URL,
        open=True,
        kwargs={"options": f"-c search_path={c.FERTISCAN_SCHEMA},public"},
    )
    connection_manager = ConnectionManager(pool)
    app.connection_manager = connection_manager
    yield
    pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}


# Just for demonstration
@app.post("/items/", response_model=ItemResponse, tags=["Items"])
async def create_item(item: ItemCreate):
    return create(item)


# Just for demonstration
@app.get("/items/", response_model=list[ItemResponse], tags=["Items"])
async def read_items():
    return read_all()


# Just for demonstration
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


# Just for demonstration
@app.post("/subtypes")
async def insert(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    id: UUID4 | str,
    type_fr: str,
    type_en: str,
):
    with cm as connection_manager:
        with connection_manager.get_cursor() as cur:
            cur.execute(
                "INSERT INTO sub_type VALUES (%s, %s, %s) returning *",
                (id, type_fr, type_en),
            )
            result = cur.fetchone()

    return {"message": result}


# Just for demonstration
@app.get("/subtypes/{id}")
async def get_subtype(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    id: UUID4 | str,
):
    with cm as connection_manager:
        with connection_manager.get_cursor() as cur:
            cur.execute("SELECT * FROM sub_type WHERE id = %s", (id,))
            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Subtype not found")

    return {"message": result}
