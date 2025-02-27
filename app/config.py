from contextlib import asynccontextmanager
from http import HTTPStatus

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request

# from fastapi.logger import logger
# from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# from opentelemetry import trace
# from opentelemetry._logs import set_logger_provider
# from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
# from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
# from opentelemetry.sdk.resources import Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
from minio import Minio
from pipeline import GPT, OCR
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings

from app.exceptions import log_error
from app.services.file_storage import MinIOStorageManager, build_storage_name

load_dotenv(".env.secrets")
load_dotenv(".env.config")


class Settings(BaseSettings):
    api_endpoint: str = Field(alias="azure_api_endpoint")
    api_key: str = Field(alias="azure_api_key")
    base_path: str = Field("", alias="api_base_path")
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str
    fertiscan_schema: str
    azure_storage_account_name: str | None = None
    azure_storage_account_key: str | None = None
    azure_storage_default_endpoint_protocol: str | None = None
    azure_storage_endpoint_suffix: str | None = None
    openai_api_deployment: str = Field(alias="azure_openai_deployment")
    openai_api_endpoint: str = Field(alias="azure_openai_endpoint")
    openai_api_key: str = Field(alias="azure_openai_key")
    phoenix_endpoint: str | None = None
    swagger_path: str = "/docs"
    # upload_folder: str = "uploads"
    allowed_origins: list[str]
    otel_exporter_otlp_endpoint: str = Field(alias="otel_exporter_otlp_endpoint")
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool = True

    @computed_field
    @property
    def azure_storage_connection_string(self) -> str:
        return (
            f"DefaultEndpointsProtocol={self.azure_storage_default_endpoint_protocol};"
            f"AccountName={self.azure_storage_account_name};"
            f"AccountKey={self.azure_storage_account_key};"
            f"EndpointSuffix={self.azure_storage_endpoint_suffix}"
        )

    @computed_field
    @property
    def db_conn_info(self) -> str:
        return make_conninfo(
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # settings: Settings = app.settings
    app.pool.open()
    # resource = Resource.create(
    #     {
    #         "service.name": "fertiscan-backend",
    #     }
    # )

    # # Tracing setup
    # tracer_provider = TracerProvider(resource=resource)
    # trace.set_tracer_provider(tracer_provider)
    # tracer_provider.add_span_processor(
    #     BatchSpanProcessor(
    #         OTLPSpanExporter(
    #             endpoint=settings.otel_exporter_otlp_endpoint, insecure=True
    #         )
    #     )
    # )
    # # Logging setup
    # logger_provider = LoggerProvider(resource=resource)
    # set_logger_provider(logger_provider)
    # logger_provider.add_log_record_processor(
    #     BatchLogRecordProcessor(
    #         OTLPLogExporter(
    #             endpoint=settings.otel_exporter_otlp_endpoint, insecure=True
    #         )
    #     )
    # )
    # handler = LoggingHandler(logger_provider=logger_provider)
    # logger.addHandler(handler)
    yield
    app.pool.close()
    # logger_provider.shutdown()
    # tracer_provider.shutdown()


def create_app(settings: Settings, router: APIRouter, lifespan=None):
    app = FastAPI(
        lifespan=lifespan, docs_url=settings.swagger_path, root_path=settings.base_path
    )
    app.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    pool = ConnectionPool(
        open=False,
        conninfo=settings.db_conn_info,
        kwargs={"options": f"-c search_path={settings.fertiscan_schema},public"},
    )
    app.pool = pool

    ocr = OCR(api_endpoint=settings.api_endpoint, api_key=settings.api_key)
    app.ocr = ocr

    gpt = GPT(
        api_endpoint=settings.openai_api_endpoint,
        api_key=settings.openai_api_key,
        deployment_id=settings.openai_api_deployment,
        # phoenix_endpoint=settings.phoenix_endpoint,
    )
    app.gpt = gpt

    app.include_router(router)

    minio_client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )

    storage = MinIOStorageManager(minio_client, build_storage_name)

    app.storage = storage

    @app.exception_handler(Exception)
    async def global_exception_handler(_: Request, e: Exception):
        log_error(e)
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content={"detail": str(e)}
        )

    return app
