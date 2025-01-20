from app.config import Settings, create_app, lifespan
from app.routes import router

app = create_app(Settings(), router, lifespan)
