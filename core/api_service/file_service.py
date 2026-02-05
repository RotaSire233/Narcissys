import json
from core.core import app
from fastapi import APIRouter
from typing import List
from loguru import logger as _logger
from core.save.file_sys import FileSys
import os

file_sys = FileSys()

router = APIRouter(prefix="/api/file", tags=["file"])

@router.get("/info")
async def get_file_info() -> List:
    return file_sys.get_struct()

@router.get("/refresh")
async def refresh() -> List:
    file_sys.file_struct = {}
    file_sys.init_struct(file_sys.scan_dir)
    return file_sys.get_struct()

@router.post("/write/file")
async def write_file(file: dict):
    file_path = file_sys.path_restruct(file["path"])
    file_sys.file_write(file_path, file["info"])
    _logger .info(f"Add file on {file_path}")
    return {"code": "200"}

@router.post("/write/folder")
async  def write_folder(folder: dict):
    file_path = file_sys.path_restruct(folder["path"])
    file_sys.folder_write(file_path)
    _logger .info(f"Add folder on {file_path}")
    return {"code": "200"}
@router.post("/del")
async def del_file(file: dict):
    file_path = file_sys.path_restruct(file["path"])
    file_sys.file_del(file_path)
    _logger .info(f"Del dile on {file_path}")
    return {"code": "200"}

@router.post("/read")
async def read_file(file: dict):
    file_path = file_sys.path_restruct(file["path"])
    return file_sys.load_json(file_path)

@router.post("/mov")
async def mov_file(file: dict):
    src_path = file_sys.path_restruct(file["src_path"])
    dest_path = file_sys.path_restruct(file["dest_path"])
    file_sys.file_mov(src_path, dest_path)
    return {"code": "200"}

@router.post("/copy")
async def copy_file(file: dict):
    src_path = file_sys.path_restruct(file["src_path"])
    dest_path = file_sys.path_restruct(file["dest_path"])
    file_sys.file_copy(src_path, dest_path)
    return {"code": "200"}

@router.post("/modify")
async def modify_file(file: dict):
    file_path = file_sys.path_restruct(file["path"])
    new_path = file_sys.path_restruct(file["name"])
    file_sys.file_name_modify(file_path, new_path)
    return {"code": "200"}

@router.get("/runtime/read")
async def read_runtime_info():
    return file_sys.run_time_load()

@router.post("/runtime/write")
async def write_runtime_info(runtime_info: dict):
    file_sys.run_time_write(runtime_info)
    return {"code": "200"}

app.include_router(router)