from fastapi import APIRouter

from reelshelf.api.v1.auth import router as auth_router
from reelshelf.api.v1.entries import router as entries_router
from reelshelf.api.v1.users import router as users_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(entries_router)
