from core.core import app, udp_manager
from fastapi import APIRouter
from typing import Dict

router = APIRouter(prefix="/api/data", tags=["data"])

@router.get("/network/udp/cache/all")
async def get_all_data():
    static_cache_all : Dict = udp_manager.static_cache.get_all_data()
    stream_cache_all : Dict = udp_manager.stream_cache.get_all_data()
    merged_cache = {**static_cache_all, **stream_cache_all}

@router.get("/network/udp/cache/{uid}")
async def get_data_uid(uid):
    static_uid_data = udp_manager.static_cache.get_cache(uid)
    stream_uid_data = udp_manager.stream_cache.get_cache(uid)
    



app.include_router(router)