from fastapi import APIRouter

from app.api.routes.admin.categories import router as admin_categories_router
from app.api.routes.admin.listings import router as admin_listings_router
from app.api.routes.auth import router as auth_router
from app.api.routes.categories import router as categories_router
from app.api.routes.health import router as health_router
from app.api.routes.listings import router as listings_router
from app.api.routes.profile import router as profile_router
from app.api.routes.public_users import router as public_users_router
from app.api.routes.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(listings_router)
api_router.include_router(profile_router)
api_router.include_router(users_router)
api_router.include_router(public_users_router)
api_router.include_router(admin_categories_router)
api_router.include_router(admin_listings_router)
