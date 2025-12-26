from core.core import CorePath
import os 
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

class FileManager:
    def __init__(self):

        self.root_path = os.path.join(CorePath.root_dir, "save")
        self.hash_path = os.path.join(CorePath.root_dir, "save", "hash_idex.json")
        self.compile_path = os.path.join(CorePath.root_dir, "save", "compile")
        
        self.hash_index = {"root": self.root_path}
        self.white_list = {"save_info.cpython-310.pyc", "save_info.py"}
        # 白名单

        if os.path.exists(self.hash_path):
            self.hash_index = self.load_hash()
        else:
            scan_dir = os.path.join(CorePath.root_dir, "save")
            self.init_hash(scan_dir)
    
    # 加载哈希引索
    def load_hash(self):
        try:
            with open(self.hash_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error loading hash index: {e}")
            return {}
        
    # 保存哈希引索 
    def save_hash(self):
        try:
            with open(self.hash_path, 'w', encoding='utf-8') as f:
                json.dump(self.hash_index, f, indent=4)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error saving hash index: {e}")

    #添加文件到哈希引索中
    def add_to_hash(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"[FILE SYS]: File '{file_path}' does not exist.")
        file_hash = self.get_hash(file_path)
        name = os.path.basename(file_path)
        if name in self.white_list:
            return
        
        file_info = {
            "path": file_path,
            "name": name,
            "size": os.path.getsize(file_path),
            "type": self.get_type(file_path),
            "hash": file_hash,
            "create_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modified_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
        }

        if file_hash in self.hash_index:
            existing_paths = [f["path"] for f in self.hash_index[file_hash]]
            if file_path not in existing_paths:
                self.hash_index[file_hash].append(file_info)
        else:
            self.hash_index[file_hash] = [file_info]
    # 移除哈希引索中文件记录
    def remove_from_hash(self, file_path: str):
        file_hash = self.get_hash(file_path)
        
        if file_hash in self.hash_index:
            self.hash_index[file_hash] = [
                f for f in self.hash_index[file_hash] 
                if f["path"] != file_path
            ]
            
            if not self.hash_index[file_hash]:
                del self.hash_index[file_hash]
        
        self.save_hash()
    # 查找重复文件
    def find_same(self) -> List[Dict]:
        same = []
        for hash_value, files in self.hash_index.items():
            if len(files) > 1:
                same.append({
                    "hash": hash_value,
                    "files": files
                })
        return same
    # 验证完整性
    def verify_file(self, filepath: str) -> Dict:
        if not os.path.exists(filepath):
            return {"valid": False, "error": "File does not exist"}
        
        current_hash = self.get_hash(filepath)
        
        for indexed_hash, files in self.hash_index.items():
            for file_info in files:
                if file_info["path"] == filepath:
                    expected_hash = file_info["hash"]
                    return {
                        "valid": current_hash == expected_hash,
                        "current_hash": current_hash,
                        "expected_hash": expected_hash,
                        "message": "File integrity verified" if current_hash == expected_hash else "File has been modified"
                    }
        
        return {
            "valid": None,
            "current_hash": current_hash,
            "expected_hash": None,
            "message": "File not in hash index"
        }
    # 哈希值获取文件
    def get_file(self, hash_value: str) -> List[Dict]:
        return self.hash_index.get(hash_value, [])
    # 扫描文件（只有有效文件有哈希值）
    def scan_directory(self, directory_path: str, recursive: bool = True):
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
            
            if not recursive:
                break
    #获取存储结构信息
    def get_structure_info(self, base_path: str = None):
        if base_path is None:
            base_path = self.root_path
            
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"[FILE SYS]: Directory '{base_path}' does not exist.")
        
        result = []
        
        for root, dirs, files in os.walk(base_path):
            rel_dir_path = os.path.relpath(root, base_path)
            if rel_dir_path != '.':
                parent_path = os.path.dirname(rel_dir_path)
                if parent_path == '':
                    parent_path = '.'
                result.append({
                    "path": rel_dir_path,
                    "type": "directory",
                    "parent": parent_path
                })
            else:
                result.append({
                    "path": ".",
                    "type": "directory",
                    "parent": None
                })
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_file_path = os.path.relpath(file_path, base_path)
                parent_path = os.path.dirname(rel_file_path)
                if parent_path == '':
                    parent_path = '.'
                
                result.append({
                    "path": rel_file_path,
                    "type": self.get_type(file_path),
                    "parent": parent_path
                })
        
        return result
    #获取存储统计信息
    def get_storage_stats(self) -> Dict:
        total_files = 0
        total_size = 0
        unique_files = len(self.hash_index)
        
        for file_list in self.hash_index.values():
            for file_info in file_list:
                total_files += 1
                total_size += file_info["size"]
        
        return {
            "total_files": total_files,
            "unique_files": unique_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "duplicate_count": total_files - unique_files
        }
    # 初始化哈希索引
    def init_hash(self, dir_path: str, depth: bool = True):
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"[FILE SYS]: Directory '{dir_path}' does not exist.")
        for root, dirs, files in os.walk(dir_path) if depth else (next(os.walk(dir_path))):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    self.add_to_hash(file_path)
                except Exception as e:
                    logger.warning(f"[FILE SYS]: {str(e)}")
            if not depth:
                break

            self.save_hash()
        logger.info("[FILE SYS]: Hash index initialized.")

    def compile_add(self, name: str, info: Dict):
        compile_path = os.path.join(self.compile_path, name + ".json")
        try:
            with open(compile_path, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=4)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error add compile: {e}")
    
    def compile_del(self, name: str):
        compile_path = os.path.join(self.compile_path, name + ".json")
        try:
            os.remove(compile_path)
        except Exception as e:
            logger.warning(f"[FILE SYS]: Error del compile: {e}")
    
    
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
    # 文件类型
    @staticmethod
    def get_type(file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        return ext.lower() if ext else "unknown"
    
   

    

    