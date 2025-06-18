"""API v1 router aggregator."""

from fastapi import APIRouter
from app.api.v1 import sightings, users

api_router = APIRouter()

# Include route modules
api_router.include_router(
    sightings.router,
    prefix="/sightings",
    tags=["sightings"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)
