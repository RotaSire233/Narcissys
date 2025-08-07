
from fastapi import APIRouter
from typing import Dict, Any

from dataclasses import dataclass
from core.network.udp.packet import AUDFORMAT, IMGFORMAT
from core.core import app, udp_manager
from core.network.udp.cache import (StaticCache, StreamCache, 
                                    FltStruct, ImgStruct, AudStruct,
                                    StaticBufferStruct,
                                    StreamBufferStruct)
from core.utils.image.image_byte_decode import decode_image_data

current_online = {}
router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/network/udp/cache/all")
async def get_all_data():
    global current_online

    static_cache_all : Dict = udp_manager.static_cache.get_all_data()
    stream_cache_all : Dict = udp_manager.stream_cache.get_all_data()
    merged_cache = {**static_cache_all, **stream_cache_all}
    update_online = {}
    for uid, cache in merged_cache.items():
        cache : StaticBufferStruct | FltStruct | ImgStruct | AudStruct
        dtype = cache.dtype
        if dtype == 'static':
            cache : StaticBufferStruct
            online = cache.rout
        elif dtype == 'flt':
            cache : FltStruct
            online = cache.rout

        elif dtype == 'img':
            cache : ImgStruct
            if cache.datas.done:
                online =cache.rout
        elif dtype == 'aud':
            cache : AudStruct
            online = cache.rout
        update_online[uid] = online
    current_online = update_online

    return current_online
    
@router.get("/network/udp/cache/{uid}")
async def get_data_uid(uid):
    static_uid_data = udp_manager.static_cache.get_cache(uid)
    stream_uid_data = udp_manager.stream_cache.get_cache(uid)
    if static_uid_data is not None:
        cache : StaticBufferStruct = static_uid_data
    else:
        cache : FltStruct | ImgStruct | AudStruct = stream_uid_data
        dtype = cache.dtype
            
        if dtype == 'flt':
            cache : FltStruct
            current_data = cache.datas.get_next_chunk()
            if current_data is not None:
                data = current_data.decode("utf-8")
                return {
                    "uid": cache.uid,
                    "type": "flt",
                    'data': data,
                }
            
            else:
                return {
                    "uid": cache.uid,
                    "type": "flt",
                    'data': 'wait',
                }
            
        elif dtype == 'img':
            cache : ImgStruct
            if cache.datas.done:
                img = decode_image_data(cache)

                return {
                    "uid": cache.uid,
                    "type": "img",
                    'data': img,
                }
                
            else:
                return {
                    "uid": cache.uid,
                    "type": "img",
                    'data': 'wait',
                }

        elif dtype == 'aud':
            cache : AudStruct
            
            
    

app.include_router(router)