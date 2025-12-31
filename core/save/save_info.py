from core.core import CorePath
import os 
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional
import shutil
from loguru import logger

class FileManager:
    def __init__(self):

        self.root_path = os.path.join(CorePath.root_dir, "save")
        self.hash_path = os.path.join(CorePath.root_dir, "save", "hash_idex.json")
        self.compile_path = os.path.join(CorePath.root_dir, "save", "compile")
        self.file_struct = []
        self.hash_index = {}
        self.white_list = {"save_info.cpython-310.pyc", "save_info.py", "hash_idex.json","__pycache__"}
        # 白名单
        scan_dir = os.path.join(CorePath.root_dir, "save")
        self.init_hash(scan_dir, include_dirs=True)

        logger.info(f"[FILE SYS]: 文件系统初始化 {self.hash_index}")
        
    # 保存哈希引索 
    def save_hash(self):
        try:
            with open(self.hash_path, 'w', encoding='utf-8') as f:
                json.dump(self.hash_index, f, indent=4)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error saving hash index: {e}")

    #添加文件到哈希引索中
    def add_to_hash(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"[FILE SYS]: Path '{path}' does not exist.")
        
        name = os.path.basename(path)
        if name in self.white_list:
            return
        
        if os.path.isfile(path):
            item_hash = self.get_hash(path)
            item_type = self.get_type(path)
            size = os.path.getsize(path)
        elif os.path.isdir(path):
            item_hash = self.get_folder_hash(path)
            item_type = "folder"
            size = self.get_folder_size(path)
        else:
            return  
        
        item_info = {
            "ab_path": path,
            "name": name,
            "size": size,
            "type": item_type,
            "create_time": datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
            "modified_time": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(), 
        }
        if item_type == "folder":
            info_struct = {"file": path.replace(self.root_path, ""), "type": "folder"}
        else:
            info_struct = {"file": os.path.splitext(path.replace(self.root_path, ""))[0], "type": "file"}
        self.file_struct.append(info_struct)
        if item_hash in self.hash_index:
            existing_paths = [f["ab_path"] for f in self.hash_index[item_hash]]
            if path not in existing_paths:
                self.hash_index[item_hash].append(item_info)
        else:
            self.hash_index[item_hash] = [item_info]
    # 移除哈希引索中文件记录
    def remove_from_hash(self, path: str):
        if os.path.isdir(path):
            item_hash = self.get_folder_hash(path)
        else:
            item_hash = self.get_hash(path)
        
        if item_hash in self.hash_index:
            self.hash_index[item_hash] = [
                f for f in self.hash_index[item_hash] 
                if f["ab_path"] != path
            ]
            
            if not self.hash_index[item_hash]:
                del self.hash_index[item_hash]
        
        self.save_hash()
    # 查找重复文件/文件夹
    def find_same(self) -> List[Dict]:
        same = []
        for hash_value, items in self.hash_index.items():
            if len(items) > 1:
                same.append({
                    "hash": hash_value,
                    "items": items
                })
        return same
    # 验证完整性
    def verify_file(self, filepath: str) -> Dict:
        if not os.path.exists(filepath):
            return {"valid": False, "error": "File does not exist"}
        
        if os.path.isdir(filepath):
            current_hash = self.get_folder_hash(filepath)
        else:
            current_hash = self.get_hash(filepath)
            
        for indexed_hash, items in self.hash_index.items():
            for item_info in items:
                if item_info["ab_path"] == filepath:
                    expected_hash = indexed_hash
                    return {
                        "valid": current_hash == expected_hash,
                        "current_hash": current_hash,
                        "expected_hash": expected_hash,
                        "message": "File/folder integrity verified" if current_hash == expected_hash else "File/folder has been modified"
                    }
        
        return {
            "valid": None,
            "current_hash": current_hash,
            "expected_hash": None,
            "message": "File/folder not in hash index"
        }
    def get_file(self, hash_value: str) -> List[Dict]:
        return self.hash_index.get(hash_value, [])
    def scan_directory(self, directory_path: str, recursive: bool = True, include_dirs: bool = True):
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory does not exist: {directory_path}")
        
        for root, dirs, files in os.walk(directory_path) if recursive else (next(os.walk(directory_path)),):

            for file in files:
                filepath = os.path.join(root, file)
                try:
                    self.add_to_hash(filepath)
                    self.save_hash()
                except Exception as e:
                    print(f"Error adding file {filepath}: {e}")
            
            if include_dirs:
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        self.add_to_hash(dir_path)
                        self.save_hash()
                    except Exception as e:
                        print(f"Error adding directory {dir_path}: {e}")
            
            if not recursive:
                break
   
    #获取存储统计信息
    def get_storage_stats(self) -> Dict:
        total_items = 0
        total_size = 0
        unique_items = len(self.hash_index)
        
        for item_list in self.hash_index.values():
            for item_info in item_list:
                total_items += 1
                total_size += item_info["size"]
        
        file_count = sum(1 for item_list in self.hash_index.values() for item in item_list if item['type'] != 'folder')
        folder_count = sum(1 for item_list in self.hash_index.values() for item in item_list if item['type'] == 'folder')
        
        return {
            "total_items": total_items,
            "file_count": file_count,
            "folder_count": folder_count,
            "unique_items": unique_items,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "duplicate_count": total_items - unique_items
        }
    # 初始化哈希索引
    def init_hash(self, dir_path: str, depth: bool = True, include_dirs: bool = True):
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"[FILE SYS]: Directory '{dir_path}' does not exist.")
        for root, dirs, files in os.walk(dir_path) if depth else (next(os.walk(dir_path))):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    self.add_to_hash(file_path)
                except Exception as e:
                    logger.warning(f"[FILE SYS]: {str(e)}")
            
            if include_dirs:
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        self.add_to_hash(dir_path)
                    except Exception as e:
                        logger.warning(f"[FILE SYS]: {str(e)}")
                        
            if not depth:
                break

            self.save_hash()
        logger.info("[FILE SYS]: Hash index initialized.")

    def file_add(self, path: str, info: Dict):
        file_path = os.path.join(self.root_path, path)
        try:
            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=4)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error add compile: {e}")

    def file_read(self, path: str) -> Dict:
        file_path = os.path.join(self.root_path, path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error read compile: {e}")
            return {}
    def file_del(self, path: str):
        file_path = os.path.join(self.root_path, path)
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error del compile: {e}")

        scan_dir = os.path.join(CorePath.root_dir, "save")
        self.init_hash(scan_dir, include_dirs=True)

    def file_mov(self, src_path: str, dest_path: str, update_hash: bool = True):
        try:
            if not os.path.exists(src_path):
                raise FileNotFoundError(f"Source path does not exist: {src_path}")
            
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
            
            if update_hash:
                self.remove_from_hash(src_path)
                self.add_to_hash(dest_path)
                self.save_hash()
            
            logger.info(f"[FILE SYS]: Successfully moved '{src_path}' to '{dest_path}'")
            return True
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error moving file/folder: {e}")
            return False
        
    def file_copy(self, src_path: str, dest_path: str, update_hash: bool = True):
        try:
            if not os.path.exists(src_path):
                raise FileNotFoundError(f"Source path does not exist: {src_path}")

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
            
            if update_hash:
                self.add_to_hash(dest_path)
                self.save_hash()
            
            logger.info(f"[FILE SYS]: Successfully copied '{src_path}' to '{dest_path}'")
            return True
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error copying file/folder: {e}")
            return False
    
    # 哈希函数
    @staticmethod
    def get_hash(file_path: str, 
                 algorithm: str = 'sha256')->str:
        hash_obj = hashlib.new(algorithm)
        try: 
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.warning(f"[FILE SYS]: {str(e)}")
            return False
    
    # 计算文件夹哈希值
    @staticmethod
    def get_folder_hash(folder_path: str,
                        algorithm: str = 'sha256') -> str:
        hash_obj = hashlib.new(algorithm)
        try:
            all_paths = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    all_paths.append(os.path.relpath(os.path.join(root, file), folder_path))
                for dir in dirs:
                    all_paths.append(os.path.relpath(os.path.join(root, dir), folder_path))
            
            all_paths.sort()
            
            for path in all_paths:
                hash_obj.update(path.encode('utf-8'))
            
            return hash_obj.hexdigest()
        except Exception as e:
            logger.warning(f"[FILE SYS]: {str(e)}")
            return False
    
    # 获取文件夹大小
    @staticmethod
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
    @staticmethod
    def get_type(file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        return ext.lower() if ext else "unknown"
    
   

    

    