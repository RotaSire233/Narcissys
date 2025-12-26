import { LLMApi, MqttApi } from '../../../services/api';
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
      // 恢复原来的值
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

  return (
    <NetWorkContext.Provider value={{
      apiKeys,
      apiLoading,
      apiError,
      mqttClients,
      mqttLoading,
      mqttError,
      fetchApiKeys,
      handleApiKeyChange,
      saveApiKeyChange,
      fetchMqttClients,
      refreshMqttClients
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
