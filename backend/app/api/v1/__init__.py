from fastapi import APIRouter

from app.api.v1 import (
    auth,
    designers,
    designs,
    favorites,
    follows,
    health,
    notifications,
    owner_reservations,
    owners,
    reports,
    reservations,
    reviews,
    search,
    shops,
    snails,
    users,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(users.router, tags=["users"])
api_v1_router.include_router(owners.router, tags=["owners"])
api_v1_router.include_router(shops.router, tags=["shops"])
api_v1_router.include_router(designers.router, tags=["designers"])
api_v1_router.include_router(designs.router, tags=["designs"])
api_v1_router.include_router(snails.router, tags=["snails"])
api_v1_router.include_router(follows.router, tags=["follows"])
api_v1_router.include_router(reviews.router, tags=["reviews"])
api_v1_router.include_router(reports.router, tags=["reports"])
api_v1_router.include_router(favorites.router, tags=["favorites"])
api_v1_router.include_router(search.router, tags=["search"])
api_v1_router.include_router(reservations.router, tags=["reservations"])
api_v1_router.include_router(owner_reservations.router, tags=["reservations"])
api_v1_router.include_router(notifications.router, tags=["notifications"])
