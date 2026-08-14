from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, auth, chat, documents, feedback, health, search
from app.config.settings import get_settings
from app.monitoring.logging_config import configure_logging
from app.monitoring.request_context import RequestContextMiddleware
from app.utils.errors import unhandled_exception_handler

settings = get_settings()
configure_logging(settings.app_env)

app = FastAPI(title="AI Knowledge Intelligence Platform", version="0.1.0")

# CORS: strictly environment-driven, never "*" in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestContextMiddleware)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(feedback.router)
