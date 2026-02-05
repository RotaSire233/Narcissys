import os
import json
from datetime import datetime   
from typing import List, Dict, Optional
import shutil
from loguru import logger as log
from core.global_infos import ROOT_DIR


def get_folder_size(folder_path: str) -> int:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except FileNotFoundError:
                   
                continue
    return total_size 

def get_type(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    return ext.lower() if ext else "unknown"

class FileSys:
    def __init__(self):
        self.root_path = os.path.join(ROOT_DIR, "save")
        self.run_time_path = os.path.join(ROOT_DIR, "save", "run_time.json")   
        self.file_struct = {}
        # 文件系统页表
        self.white_list = {"file_sys.cpython-310.pyc", 
                           "file_sys.py", 
                           "hash_idex.json",
                           "run_time.json",
                           "__pycache__"}
        self.scan_dir = os.path.join(ROOT_DIR, "save")
        self.init_struct(self.scan_dir)

    def path_restruct(self, path: str):
        combined_path = os.path.join(self.root_path, path)
        return combined_path
    
    def get_struct(self):
        file_struct = []
        for key, value in self.file_struct.items():
            standardized_path = key.replace("\\", "/")
            temp = {"file": standardized_path, "type": value}
            file_struct.append(temp)
        return file_struct
    
    def add_to_struct(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"[FILE SYS]: 路径 '{path}' 不存在.")
        name = os.path.basename(path)
        if name in self.white_list:
            return
    
        if os.path.isfile(path):
            item_type = get_type(path)
        elif os.path.isdir(path):
            item_type = "folder"
        else:
            return
        key = path.replace(self.root_path, "")
        if item_type == "folder":
            self.file_struct[key] = "folder"
        else:
           self.file_struct[key] = "file"

    def init_struct(self,
                    dir_path: str,
                    depth: bool = True,
                    include_dirs: bool = True):
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"[FILE SYS]: 目录 '{dir_path}' 不存在.")
        for root, dirs, files in os.walk(dir_path) if depth else (next(os.walk(dir_path))):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    self.add_to_struct(file_path)
                except Exception as e:
                    log.warning(f"[FILE SYS]: {str(e)}")
            
            if include_dirs:
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        self.add_to_struct(dir_path)
                    except Exception as e:
                        log.warning(f"[FILE SYS]: {str(e)}")
                        
            if not depth:
                break
        log.info("[FILE SYS]: 文件系统索引初始化完成.")

    
    def load_json(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                load_info = json.load(f)
        except Exception as e:
            log.warning(f"[FILE SYS]: 文件加载失败: {e}")
        return load_info
    
    def folder_write(self, path: str):
        file_path = os.path.join(self.root_path, path)
        try:
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
        except Exception as e:
            log.warning(f"[FILE SYS]: 文件夹创建失败: {e}")
    
    def file_write(self, path: str, info: Dict):
        file_path = os.path.join(self.root_path, path)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=4)
        except Exception as e:
            log.warning(f"[FILE SYS]: 文件写入失败: {e}")

    def file_del(self, path: str):
        file_path = os.path.join(self.root_path, path)
        try:
            os.remove(file_path)
        except Exception as e:
            log.warning(f"[FILE SYS]: 文件删除失败: {e}")
    
    def file_mov(self, src_path: str, dest_path: str, update_hash: bool = True):
        try:
            if not os.path.exists(src_path):
                raise FileNotFoundError(f"[FILE SYS]: 源路径不存在: {src_path}")
            
            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)

            if os.path.exists(dest_path):
                if os.path.isdir(dest_path):
                    shutil.rmtree(dest_path)
                else:
                    os.remove(dest_path)

            if os.path.isdir(src_path):
                shutil.move(src_path, dest_path)
            else:
                shutil.move(src_path, dest_path)
            
            
            log.info(f"[FILE SYS]: 将 '{src_path}' 移动到 '{dest_path}'")
            return True
        except Exception as e:
            log.warning(f"[FILE SYS]: 移动文件/文件夹时出错: {e}")
            return False
        
    
    def file_copy(self, src_path: str, dest_path: str, update_hash: bool = True):
        try:
            if not os.path.exists(src_path):
                raise FileNotFoundError(f"[FILE SYS]: 源路径不存在: {src_path}")

            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            if os.path.exists(dest_path):
                if os.path.isdir(dest_path):
                    shutil.rmtree(dest_path)
                else:
                    os.remove(dest_path)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)
            
            
            log.info(f"[FILE SYS]: 将 '{src_path}' 复制到 '{dest_path}'")
            return True
        except Exception as e:
            log.warning(f"[FILE SYS]: 复制文件/文件夹时出错: {e}")
            return False
    
    def file_name_modify(self, path: str, new_name: str):
        dir_path = os.path.dirname(path)
        new_path = os.path.join(dir_path, new_name)
        try:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for name in files + dirs:
                        old_item_path = os.path.join(root, name)
                        new_item_path = old_item_path.replace(path, new_path)
            
            os.rename(path, new_path)
            log.info(f"[FILE SYS]: 将 '{path}' 重命名为 '{new_path}'")
            return True
        except Exception as e:
            log.warning(f"[FILE SYS]: 文件/文件夹重命名失败: {e}")
            return False
    
    def run_time_load(self) -> Optional[Dict]:
        try:
            with open(self.run_time_path, 'r', encoding='utf-8') as f:
                run_time_info = json.load(f)
            return run_time_info
        except Exception as e:
            log.warning(f"[FILE SYS]: 加载运行时信息失败: {e}")
            return None
        
    def run_time_write(self, info: Dict):
        try:
            with open(self.run_time_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=4)
        except Exception as e:
            log.warning(f"[FILE SYS]: 保存运行时信息失败: {e}")