"""
Music School Management System - API Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.error_handler import register_exception_handlers
from src.api.router import api_router


def create_app() -> FastAPI:
    """Создаёт и настраивает приложение FastAPI."""
    
    app = FastAPI(
        title="Music School Management System",
        description="API для управления музыкальной школой",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Настроить для прода: ["http://localhost:3000", "https://yourdomain.com"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Обработчики исключений
    register_exception_handlers(app)
    
    # Middleware для установки заголовков (для будущей настройки фронта)
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response
    
    # Подключение роутеров
    app.include_router(api_router)

    # Раздача статических файлов
    app.mount("/static", StaticFiles(directory="src/static"), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_spa():
        return FileResponse("src/static/index.html")

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
