from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings

load_dotenv("secrets.env")
load_dotenv("config.env")


class Settings(BaseSettings):
    api_endpoint: str = Field(alias="azure_api_endpoint")
    api_key: str = Field(alias="azure_api_key")
    base_path: str = Field("", alias="api_base_path")
    fertiscan_db_url: PostgresDsn
    fertiscan_schema: str
    fertiscan_storage_url: str
    openai_api_deployment: str = Field(alias="azure_openai_deployment")
    openai_api_endpoint: str = Field(alias="azure_openai_endpoint")
    openai_api_key: str = Field(alias="azure_openai_key")
    phoenix_endpoint: str | None = None
    swagger_path: str = "/docs"
    upload_folder: str = "uploads"
    allowed_origins: list[str]
    otel_exporter_otlp_endpoint: str = Field(alias="otel_exporter_otlp_endpoint")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    app.pool.open()
    resource = Resource.create(
        {
            "service.name": "fertiscan-backend",
        }
    )

    # Tracing setup
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint, insecure=True
            )
        )
    )
    # Logging setup
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=settings.otel_exporter_otlp_endpoint, insecure=True
            )
        )
    )
    handler = LoggingHandler(logger_provider=logger_provider)
    logger.addHandler(handler)
    yield
    app.pool.close()
    logger_provider.shutdown()
    tracer_provider.shutdown()


def create_app(settings: Settings):
    app = FastAPI(
        lifespan=lifespan, docs_url=settings.swagger_path, root_path=settings.base_path
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    pool = ConnectionPool(
        open=False,
        conninfo=settings.fertiscan_db_url.unicode_string(),
        kwargs={"options": f"-c search_path={settings.fertiscan_schema},public"},
    )
    app.pool = pool

    ocr = OCR(api_endpoint=settings.api_endpoint, api_key=settings.api_key)
    app.ocr = ocr

    gpt = GPT(
        api_endpoint=settings.openai_api_endpoint,
        api_key=settings.openai_api_key,
        deployment_id=settings.openai_api_deployment,
        phoenix_endpoint=settings.phoenix_endpoint,
    )
    app.gpt = gpt

    return app
