from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, commerce, restaurant_delivery

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(commerce.router, tags=["commerce"])
api_router.include_router(restaurant_delivery.router, tags=["restaurant-delivery"])