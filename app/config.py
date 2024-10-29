from contextlib import asynccontextmanager

from fastapi import FastAPI
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool

import app.constants as c
from app.connection_manager import ConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize a connection manager
    pool = ConnectionPool(
        conninfo=c.FERTISCAN_DB_URL,
        open=True,
        kwargs={"options": f"-c search_path={c.FERTISCAN_SCHEMA},public"},
    )
    connection_manager = ConnectionManager(pool)
    app.connection_manager = connection_manager

    # Initialize OCR
    ocr = OCR(api_endpoint=c.API_ENDPOINT, api_key=c.API_KEY)
    app.ocr = ocr

    # Initialize GPT
    gpt = GPT(
        api_endpoint=c.OPENAI_API_ENDPOINT,
        api_key=c.OPENAI_API_KEY,
        deployment_id=c.OPENAI_API_DEPLOYMENT,
    )
    app.gpt = gpt

    # Yield control back to FastAPI, indicating setup completion
    yield

    # Close the connection pool when the application is shutting down
    pool.close()
