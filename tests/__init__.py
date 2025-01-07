from app.config import Settings, create_app
from app.routes import router

test_settings = Settings(
    azure_api_key="test_api_key",
    db_user="test_user",
    db_password="test_password",
    db_host="test_host",
    db_port=5432,
    db_name="test_db",
    azure_storage_account_name="test_account_name",
    azure_storage_account_key="test_account_key",
    azure_openai_key="test_openai_key",
)


app = create_app(test_settings, router)
