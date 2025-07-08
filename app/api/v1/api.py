from fastapi import APIRouter

from app.api.v1.endpoints import recommendations, courses, tags

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["recommendations"]
)

api_router.include_router(
    courses.router,
    prefix="/courses",
    tags=["courses"]
)

api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["tags"]
)