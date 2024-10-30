from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool

import app.constants as c
from app.connection_manager import ConnectionManager
from app.controllers.users import sign_in, sign_up
from app.dependencies import authenticate_user, get_connection_manager
from app.exceptions import UserConflictError, UserNotFoundError, log_error
from app.models.monitoring import HealthStatus
from app.models.users import User


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


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, e: Exception):
    log_error(e)
    return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=str(e))


@app.get("/health", tags=["Monitoring"], response_model=HealthStatus)
async def health_check():
    return HealthStatus()


@app.post(
    "/signup",
    tags=["Users"],
    status_code=201,
    response_model=User,
    responses={
        HTTPStatus.CONFLICT: {"description": "User exists"},
    },
)
async def signup(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: User = Depends(authenticate_user),
):
    try:
        return await sign_up(cm, user)
    except UserConflictError:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="User exists!")


@app.post(
    "/login",
    tags=["Users"],
    status_code=200,
    response_model=User,
    responses={
        HTTPStatus.NOT_FOUND: {"description": "User not found"},
    },
)
async def login(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: User = Depends(authenticate_user),
):
    try:
        return await sign_in(cm, user)
    except UserNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found!")
