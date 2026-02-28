from fastapi import APIRouter

from .venues import router as venues_router
from .events import router as events_router
from .seats import router as seats_router
from .reviews import router as reviews_router

router = APIRouter()
router.include_router(venues_router)
router.include_router(events_router)
router.include_router(seats_router)
router.include_router(reviews_router)
