from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from auth.auth import auth_middleware

settings = get_settings()

def setup_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.middleware("http")
    async def auth_middleware_handler(request: Request, call_next):
        if request.url.path in settings.PUBLIC_PATHS:
            return await call_next(request)
        return await auth_middleware(request, call_next)
