from fastapi import APIRouter

from app.api import api_router

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}

# include this router in the versioned api router
api_router.include_router(router)
