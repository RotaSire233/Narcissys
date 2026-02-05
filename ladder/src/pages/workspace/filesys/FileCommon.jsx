import { LLMApi, MqttApi, FileApi } from '../../../services/api';
import React, {createContext, useState,useContext, useEffect, use } from 'react';
import AsyncStateUpdate from '../../../components/utils/WaitReturn';
export const FileContext = createContext();

export const useFiles = () => {
  const context = useContext(FileContext);
  if (!context) {
    throw new Error('useInfo must be used within a FileProvider');
  }
  return context;
};

// 将文件路径转换为文件树结构（生成文件树）
const convertPathsToTree = (paths) => {
    const root = { children: [] };
    paths.forEach(pathObj => {
        const fullPath = pathObj.file;
        const type = pathObj.type;
        const parts = fullPath.replace(/^[\\/]/, '').split(/[\\/]/).filter(part => part !== '');
            
        if (parts.length === 0) return;
            
        let current = root;
        let currentPath = ''; 
            
        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            const isLast = i === parts.length - 1;
                
            currentPath = currentPath ? `${currentPath}/${part}` : part;
                
            if (!current.children) {
                current.children = [];
            }
                
            let existingNode = current.children.find(child => {
                return i === parts.length - 1 
                ? child.name === (part.lastIndexOf('.') !== -1 ? part.substring(0, part.lastIndexOf('.')) : part)
                : child.name === part;
            });
                
            if (!existingNode) {
                let displayName = part;
                if (isLast && part.lastIndexOf('.') !== -1) {
                    displayName = part.substring(0, part.lastIndexOf('.'));
                }
                  
                existingNode = {
                    name: displayName,  
                    type: isLast ? type : 'folder',
                    toggled: false,
                    path: currentPath
                  };
                  
                if (!isLast) {
                    existingNode.children = [];
                  }
                  
                current.children.push(existingNode);
                } else if (!existingNode.path) {
                  existingNode.path = currentPath;
                }
                
                if (!isLast) {
                  current = existingNode;
                }
              }
          });
          
          return root.children;
        };
        

export function FileInfo({ children }){ 
    const [fileList, setFileList] = useState([]);
    const [oldFileList, setOldFileList] = useState([]);

    // 文件表单 -> 总表单 包含 文件与文件夹
    const [fileTree, setFileTree] = useState([]);
    const [oldFileTree, setOldFileTree] = useState([]);
    // 文件树 -> 文件树渲染
    const [fileLoading, setFileLoading] = useState(false);
    const [fileError, setFileError] = useState(null);

    // 文件名表单 -> 文件名存储查重 暂时不用
    const [fileNameDict, setFileNameDict] = useState({});

    const [canvasCache, setCanvasCache] = useState({});
    const [oldCanvasCache, setOldCanvasCache] = useState({});
    // 画布缓存管理

    const [activeCache, setActiveCache] = useState({});

    // 白名单文件夹
    const whitelist = ['groups', 'projects'];
    const { wrapWithPromise } = AsyncStateUpdate();

    // 初始化文件
    const initFile = async () => {
        setFileLoading(true);   
        setFileError(null); 
        initFileCache();
      try {
        const data = await FileApi.getList();
        console.log('Received file data:', data);
        setFileList(data);
        setFileTree(convertPathsToTree(data));
        
      } catch (err) {
        setFileError(err.message);
        console.error('Failed to fetch file list:', err);
      } finally {
        setFileLoading(false);
      }
    }

    // 文件列表刷新
    const refreshFile = async () => {
        setFileLoading(true);
        setFileError(null);

        try {
          const data = await FileApi.forceRefresh();
          setFileList(data);
          setFileTree(convertPathsToTree(data));
          
        } catch (err) {
          setFileError(err.message);
          console.error('Failed to refresh file list:', err);
        } finally {
          setFileLoading(false);
        }
      }

    // 修改文件树
    const modifyFileTree = (oldPath, newPath) => {
        const updatedTree = JSON.parse(JSON.stringify(fileTree));
        const operation = fileTreeOperation(oldPath, newPath);

        switch (operation) {
            case 'add':
                fileTreeAdd(updatedTree, newPath);
                break;
            case 'delete':
                fileTreeDel(updatedTree, oldPath);
                break;
            case 'rename':
                fileTreeRename(updatedTree, oldPath, newPath);
                break;
            default:
                console.log('No operation selected');
                return;
        }
        setFileTree(updatedTree);
    }

    // 文件树操作选择
    const fileTreeOperation = (oldPath, newPath) => {
        if (!oldPath && newPath) return 'add';
        if (oldPath && !newPath) return 'delete';
        if (oldPath && newPath) return 'rename';
        return 'none';
    };

    const fileTreeAdd = (tree, filePath) => {
        console.log('fileTreeAdd:', tree, filePath);
        const pathParts = filePath.replace(/^[\/]/, '').split(/[\/]/).filter(part => part !== '');
        if (pathParts.length === 0) return;
        let current = tree;
        let currentPath = '';
        
        for (let i = 0; i < pathParts.length; i++) {
            const part = pathParts[i];
            const isLast = i === pathParts.length - 1;
            currentPath = currentPath ? `${currentPath}/${part}` : part;
            
            const displayName = isLast && part.lastIndexOf('.') !== -1 
                ? part.substring(0, part.lastIndexOf('.')) 
                : part;
            
            let existingNode = current.find(node => {
                if (isLast) {
                    return node.name === displayName && node.type === 'file';
                } else {
                    return node.name === displayName && node.type === 'folder';
                }
            });
            
            if (!existingNode) {
                existingNode = {
                    name: displayName,
                    type: isLast ? 'file' : 'folder',
                    toggled: false,
                    path: currentPath
                };
                
                if (!isLast) {
                    existingNode.children = [];
                }
                
                current.push(existingNode);
            }
            
            if (!isLast) {
                if (!existingNode.children) {
                    existingNode.children = [];
                }
                current = existingNode.children;
            }
        }
    }

    const fileTreeDel = (tree, filePath) => {
        const pathParts = filePath.replace(/^[\/]/, '').split(/[\/]/).filter(part => part !== '');
        if (pathParts.length === 0) return;
        
        const findAndRemove = (nodes, pathIndex) => {
            if (pathIndex === pathParts.length - 1) {
            const fileName = pathParts[pathIndex];
            const displayName = fileName.lastIndexOf('.') !== -1 
                ? fileName.substring(0, fileName.lastIndexOf('.')) 
                : fileName;
            
            const fileIndex = nodes.findIndex(node => node.name === displayName && node.type === 'file');
            if (fileIndex !== -1) {
                nodes.splice(fileIndex, 1);
                return true;
            }
            } else {
            const folderName = pathParts[pathIndex];
            const folderIndex = nodes.findIndex(node => node.name === folderName && node.type === 'folder');
            
            if (folderIndex !== -1) {
                const folder = nodes[folderIndex];
                if (folder.children) {
                const removed = findAndRemove(folder.children, pathIndex + 1);

                return removed;
                }
            }
            }
            return false;
        };
        findAndRemove(tree, 0);
        };
    
    const fileTreeRename = (tree, oldPath, newPath) => {
        fileTreeDel(tree, oldPath);
        fileTreeAdd(tree, newPath);
    }

    const legalCheck = (filePath) => {
        if (!filePath) {
            console.log('Path cannot be empty');
            return false
        }
        
        // 这里可以优化，使用字典或者数据库查找，但是说实话，不是现在该考虑的
        const exists = fileList.some(file => 
            file.file === filePath
        );
        if (exists) {
            console.log('Exist file:', filePath);
            return false
        }
        return true
    }

    // 文件添加
    const addFile = async (filePath, fileInfo, type = 'file') => {
        try {
            setOldFileList(fileList);
            setOldFileTree(fileTree);
            setOldCanvasCache(canvasCache);
            if (!legalCheck(filePath)) {
                return false;
            }
            const newFile = { file: filePath, type: type };
            const updatedFileList = [...fileList, newFile];
            console.log('fileTree:', fileTree);
            setFileList(updatedFileList);
            
            modifyFileTree(null, filePath);

            const fileName = filePath.replace(/^[\\/]/, '').split(/[\\/]/).filter(part => part !== '');
            setCanvasCache(prevCache => ({
                ...prevCache,
                [filePath]: {
                    active: true,
                    loaded: false,
                    canvas: null,
                    name: fileName,
                    operation: 'none',
                    loading: false,
                    error: null,
                }
            }));

            await FileApi.writeFile(filePath, fileInfo);
        } catch (err) {
            console.error('Failed to add file:', err);
            setFileList(oldFileList);
            setFileTree(oldFileTree);
            setCanvasCache(oldCanvasCache);
        }
    }
    
    // 文件删除
    const deleteFile = async (filePath) => {
        try{
        setOldFileList(fileList);
        setOldFileTree(fileTree);
        setOldCanvasCache(canvasCache);
        modifyFileTree(filePath, null);
        setCanvasCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[filePath];
        return newCache;
        });
        setFileList(prevList => prevList.filter(file => file.file !== filePath));
        await FileApi.deleteFile(filePath);
        } catch (err) {
            console.error('Failed to delete file:', err);
            setFileList(oldFileList);
            setFileTree(oldFileTree);
            setCanvasCache(oldCanvasCache);
        }
      }
    
    const renameFile = async (oldPath, newPath) => {
        try{
        setOldFileList(fileList);
        setOldFileTree(fileTree);
        setOldCanvasCache(canvasCache);
        if (!legalCheck(newPath)) {
            return false
        }
        modifyFileTree(oldPath, newPath);
        setCanvasCache(prevCache => {
        const newCache = { ...prevCache };
        if (newCache[oldPath]) {
          newCache[newPath] = newCache[oldPath];
          delete newCache[oldPath];
        }
        return newCache;
        });
        await FileApi.modifyName(oldPath, newPath);
        } catch (err) {
        console.error('Failed to rename file:', err);
        setFileList(oldFileList);
        setFileTree(oldFileTree);
        setCanvasCache(oldCanvasCache);
        }
        
      }
      
    // 从文件树初始化文件缓存区
    const initFileCache = () => {
        if (!fileList || !Array.isArray(fileList)) return;

        const newCache = {};

        fileList.forEach(file => {
            if (file.file && file.type === 'file') {
                const fileName = file.file.replace(/^[\\/]/, '').split(/[\\/]/).filter(part => part !== '');
                newCache[file.file] = {
                        active: false,
                        loaded: false,
                        canvas: null,
                        name: fileName,
                        operation: 'none',
                        loading: false,
                        error: null,
                    };
            }
        });
        setCanvasCache(newCache);
    };

    const loadFileCache = async (filePath) => {
       try {
            if (!canvasCache[filePath]) {
                console.log('File cache not found:', filePath);
                setCanvasCache(prevCache => ({
                    ...prevCache,
                    [filePath]: {
                        ...prevCache[filePath],
                        active: true,
                        loading: true,
                        loaded: false,
                        canvas: null,
                        error: null
                    }
                }));
            } else if (canvasCache[filePath].loaded) {
                console.log('File cache already loaded:', filePath);
            
                setCanvasCache(prevCache => ({
                    ...prevCache,
                    [filePath]: {
                        ...prevCache[filePath],
                        active: true
                    }
                }));
                return false
            } else {
                console.log('File cache exists:', filePath);
                setCanvasCache(prevCache => ({
                    ...prevCache,
                    [filePath]: {
                        ...prevCache[filePath],
                        loading: true,
                        error: null,
                        active: true 
                    }
                }));

            }


        console.log('Loading file cache:', filePath);
        let loadCanvas = await FileApi.getJson(filePath);
        
        if (JSON.stringify(loadCanvas) === '{}') {
            console.log('Empty canvas data, initializing canvas');
            loadCanvas = {
                rungs: undefined,
                selectedElement: null
            };
        }
        setCanvasCache(prevCache => ({
            ...prevCache,
            [filePath]: {
                ...prevCache[filePath],
                loading: false,
                loaded: true,
                canvas: loadCanvas,
                active: true
            }
        })); 
        return loadCanvas;
                  
        } catch (err){
             console.error('Failed to load file cache:', err);
           }
        }

    const releaseFileCache = async (filePath) => {
        try {
            if (!canvasCache[filePath]){
                console.log('File cache not found:', filePath);
                return;
            }

            if (!canvasCache[filePath].loaded) {
                console.log('File cache unload:', filePath);
                return;
            }

            // 释放文件缓存
            setCanvasCache(prevCache => ({
                ...prevCache,
                [filePath]: {
                    ...prevCache[filePath],
                    loading: false,
                    loaded: false,
                    canvas: null,
                }
            }));
                    
           } catch (err){
             console.error('Failed to load file cache:', err);
           }
        }
    
    const addActiveCache = (filePath) => {
        if (!canvasCache[filePath].loaded){
            console.log('File cache not found:', filePath);
            loadFileCache(filePath);
        }
        try {
            setActiveCache(prevCache => ({
            ...prevCache,
            [filePath]: canvasCache[filePath],
            }));
            console.log('Add active cache:', filePath);
        } catch (err) {
            console.error('Failed to add active cache:', err);
        }
    };

    const removeActiveCache = (filePath) => {
        try {
            setActiveCache(prevCache => {
            const newCache = { ...prevCache };
            delete newCache[filePath];
            console.log(`Removed item from active cache: ${filePath}`);   
            return newCache;
            });
        } catch (err) {
            console.error('Failed to remove item from active cache:', err);
        }

    };

    const saveItem = async (filePath, item) => {
        try {
            await FileApi.writeFile(filePath, item);
        } catch (err) {
            console.error('Failed to save file:', err);
        }
    }
    
    useEffect(() => {
    
    console.log('canvasCache has been updated:', canvasCache);
    console.log('fileTree has been updated:', fileTree);
    }, [canvasCache, fileTree]);


    useEffect(() => {

        const handleBeforeUnload = (event) => {
            refreshFile();
        };

        window.addEventListener('beforeunload', handleBeforeUnload);

        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, []); 

    useEffect(() => {
        initFile();
    }, []);
    
    return (
        <FileContext.Provider value={{
          fileTree,
          fileLoading,
          fileError,
          canvasCache,
          whitelist,
          activeCache,
          
          setCanvasCache,
          addActiveCache,
          removeActiveCache,
          initFile,
          refreshFile,
          addFile,
          deleteFile,
          renameFile,
          loadFileCache,
          releaseFileCache,
          saveItem,
        }}>
          {children}
        </FileContext.Provider>
      );
    
}
