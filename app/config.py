from dotenv import load_dotenv
from fastapi import FastAPI
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    api_endpoint: str = Field(alias="azure_api_endpoint")
    api_key: str = Field(alias="azure_api_key")
    base_path: str = ""
    fertiscan_db_url: PostgresDsn
    fertiscan_schema: str
    fertiscan_storage_url: str
    frontend_url: str = "*"
    openai_api_deployment: str = Field(alias="azure_openai_deployment")
    openai_api_endpoint: str = Field(alias="azure_openai_endpoint")
    openai_api_key: str = Field(alias="azure_openai_key")
    otel_exporter_otlp_endpoint: str | None = None
    swagger_base_path: str = ""
    swagger_path: str = "/docs"
    upload_folder: str = "uploads"
    testing: str = "false"


def configure(app: FastAPI, settings: Settings):
    pool = ConnectionPool(
        open=False,
        conninfo=settings.fertiscan_db_url.unicode_string(),
        kwargs={"options": f"-c search_path={settings.fertiscan_schema},public"},
    )
    app.pool = pool

    # Initialize OCR
    ocr = OCR(api_endpoint=settings.api_endpoint, api_key=settings.api_key)
    app.ocr = ocr

    # Initialize GPT
    gpt = GPT(
        api_endpoint=settings.openai_api_endpoint,
        api_key=settings.openai_api_key,
        deployment_id=settings.openai_api_deployment,
        phoenix_endpoint=settings.otel_exporter_otlp_endpoint,
    )
    app.gpt = gpt
    return app
