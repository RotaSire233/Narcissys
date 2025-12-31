import { LLMApi, MqttApi, FileApi } from '../../../services/api';
import React, {createContext, useState,useContext, useEffect, use } from 'react';

// 创建网络数据上下文
export const NetWorkContext = createContext();
// 创建文件数据上下文
export const FileContext = createContext();

// 创建网关信息接口 hook
export const useNetWorkInfo = () => {
  const context = useContext(NetWorkContext);
  if (!context) {
    throw new Error('useInfo must be used within a CanvasProvider');
  }
  return context;
};

export function NetWorkInfo({ children }){ 
  const [apiKeys, setApiKeys] = useState({});
  const [mqttClients, setMqttClients] = useState({});
  const [apiLoading, setApiLoading] = useState(false);
  const [mqttLoading, setMqttLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [mqttError, setMqttError] = useState(null);

  const [fileList, setFileList] = useState([]);
  const [fileTree, setFileTree] = useState([]);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState(null);
  // 获取API密钥
  const fetchApiKeys = async () => {
      setApiLoading(true);
      setApiError(null);
      try {
        const data = await LLMApi.getList();
        setApiKeys(data);
      } catch (err) {
        setApiError(err.message);
        console.error('获取API密钥信息失败:', err);
      } finally {
        setApiLoading(false);
      }
    };
  // 处理API密钥更改
  const handleApiKeyChange = (modelName, value) => {
    setApiKeys(prev => ({...prev, [modelName]: value}));
  };
  
  // 保存API密钥更改
  const saveApiKeyChange = async (modelName, value) => {
    try {
      await LLMApi.modifyList(modelName, value);

    } catch (err) {
      console.error('保存API密钥失败:', err);
      fetchApiKeys();
    }
  };
  
  // 获取MQTT客户端信息
  const fetchMqttClients = async () => {
    setMqttLoading(true);
    setMqttError(null);
    try {
      const data = await MqttApi.getList();
      setMqttClients(data);
    } catch (err) {
      setMqttError(err.message);
      console.error('获取MQTT客户端信息失败:', err);
    } finally {
      setMqttLoading(false);
    }
  };
  
  // 强制刷新MQTT客户端信息
  const refreshMqttClients = async () => {
    setMqttLoading(true);
    setMqttError(null);
    try {
      const data = await MqttApi.refresh(); // 强制获取最新数据
      setMqttClients(data);
    } catch (err) {
      setMqttError(err.message);
      console.error('刷新MQTT客户端信息失败:', err);
    } finally {
      setMqttLoading(false);
    }
  };
  
  const fetchFile= async () => {
    setApiLoading(true);
    setApiError(null);
    try {
      const data = await FileApi.getList();
      console.log('Received file data:', data);
      setFileList(data);
      setFileTree(convertPathsToTree(data));
    } catch (err) {
      setFileError(err.message);
      console.error('获取文件列表失败:', err);
    } finally {
      setFileLoading(false);

    }
  }

  const refreshFile = async () => {
    setFileLoading(true);
    setFileError(null);
    try {
      const data = await FileApi.refresh();
      setFileList(data);
      setFileTree(convertPathsToTree(data));
    } catch (err) {
      setFileError(err.message);
      console.error('刷新文件列表失败:', err);
    } finally {
      setFileLoading(false);
    }
  }

  const add_file = async (filePath, fileInfo) => {
     try{
      await FileApi.addFile(filePath, fileInfo);
     } catch (err) {
       console.error('添加文件失败:', err);
     }
     fetchFile();
  }

  const delete_file = async (filePath) => {
     try{
      await FileApi.deleteFile(filePath);
     } catch (err) {
       console.error('删除文件失败:', err);
     }
     fetchFile();
  }

   const convertPathsToTree = (paths) => {
        const root = { children: [] };
        
        paths.forEach(pathObj => {
          const path = pathObj.file;
          const type = pathObj.type;
          const parts = path.replace(/^\\/, '').split('\\').filter(part => part !== '');
          
          if (parts.length === 0) return;
          
          let current = root;
          
          for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            const isLast = i === parts.length - 1;
            
            if (!current.children) {
              current.children = [];
            }
            
            let existingNode = current.children.find(child => child.name === part);
            
            if (!existingNode) {
              existingNode = {
                name: part,
                type: isLast ? type : 'folder',
                toggled: false,
              };
              
              if (!isLast) {
                existingNode.children = [];
              }
              
              current.children.push(existingNode);
            }
            
            if (!isLast) {
              current = existingNode;
            }
          }
        });
        
        return root.children;
      };

  return (
    <NetWorkContext.Provider value={{
      apiKeys,
      apiLoading,
      apiError,
      mqttClients,
      mqttLoading,
      mqttError,
      fileTree,
      fileLoading,
      fileError,
      
      fetchApiKeys,
      handleApiKeyChange,
      saveApiKeyChange,
      fetchMqttClients,
      refreshMqttClients,
      fetchFile,
      refreshFile,
      add_file,
      delete_file
    }}>
      {children}
    </NetWorkContext.Provider>
  );

};

// 创建文件信息接口 hook
export const useFileInfo = () => {
  const context = useContext(NetWorkContext);
  if (!context) {
    throw new Error('useInfo must be used within a CanvasProvider');
  }
  return context;
};
