from app.config import Settings, create_app
from app.routes import router

test_settings = Settings(
    azure_api_key="test_api_key",
    fertiscan_db_url="postgresql://user:password@localhost:5432/test_fertiscan",
    azure_storage_account_name="test_account_name",
    azure_storage_account_key="test_account_key",
    azure_openai_key="test_openai_key",
)


app = create_app(test_settings, router)
