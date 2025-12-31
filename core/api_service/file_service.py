import json
from core.core import app
from fastapi import APIRouter
from typing import List
from loguru import logger as _logger
from  core.save.save_info import FileManager
import os

FILE = FileManager()
FILE_INFO = FILE.hash_index
FILE_STRUCT = FILE.file_struct

router = APIRouter(prefix="/api/file", tags=["file"])

@router.get("/info")
async def get_file_info() -> List:
     return FILE_STRUCT

@router.post("/add")
async def add_file(file: dict):
    FILE.file_add(file["path"], file["info"])
    _logger .info(f"Add file on {file['path']}")
    return {"code": "200"}

@router.post("/del")
async def del_file(file: dict):
    FILE.file_del(file["path"])
    return {"code": "200"}

@router.get("/read")
async def read_file(file: str):
    return FILE.file_read(file)

@router.post("/mov")
async def mov_file(file: dict):
    FILE.file_mov(file["src_path"], file["dest_path"])
    return {"code": "200"}

@router.post("/copy")
async def copy_file(file: dict):
    FILE.file_copy(file["src_path"], file["dest_path"])
    return {"code": "200"}
app.include_router(router)