"""API v1 routes."""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .learning import router as learning_router
from .questions import router as questions_router
from .content import router as content_router
from .progress import router as progress_router
from .analytics import router as analytics_router
from .achievements import router as achievements_router

router = APIRouter()

# Include all routers
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(learning_router, prefix="/learning", tags=["Learning"])
router.include_router(questions_router, prefix="/questions", tags=["Questions"])
router.include_router(content_router, prefix="/content", tags=["Content"])
router.include_router(progress_router, prefix="/progress", tags=["Progress"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
router.include_router(achievements_router, prefix="/achievements", tags=["Achievements"])