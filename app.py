import os
from contextlib import asynccontextmanager
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from psycopg_pool import ConnectionPool
from pydantic import UUID4

from backend.connection_manager import ConnectionManager

load_dotenv()

FERTISCAN_SCHEMA = os.getenv("FERTISCAN_SCHEMA")
FERTISCAN_DB_URL = os.getenv("FERTISCAN_DB_URL")
# FERTISCAN_STORAGE_URL = os.getenv("FERTISCAN_STORAGE_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = ConnectionPool(
        conninfo=FERTISCAN_DB_URL,
        open=True,
        kwargs={"options": f"-c search_path={FERTISCAN_SCHEMA},public"},
    )
    connection_manager = ConnectionManager(pool)
    app.connection_manager = connection_manager
    yield
    if connection_manager.testing:
        connection_manager.rollback()
    pool.close()


app = FastAPI(lifespan=lifespan)


# Dependency to provide a connection
def get_db_connection(request: Request):
    with app.pool.connection() as conn:
        yield conn


def get_connection_manager(request: Request):
    yield app.connection_manager


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
