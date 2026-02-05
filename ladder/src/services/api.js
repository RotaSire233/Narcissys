// ladder/src/services/api.js
// ladder/src/services/api.js
const API_BASE_URL = 'http://localhost:5000/api';

// 为MQTT设备数据添加缓存
let mqttDeviceCache = null;
let mqttDeviceCacheTimestamp = null;
const CACHE_DURATION = 5 * 60 * 1000; // 缓存5分钟


// LLM Api
export const LLMApi = {

  getList: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/model/api_keys/info`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Fail to get model list:', error);
      throw error;
    }
  },
  
  modifyList: async (apiName, value) => {
    try {
      const response = await fetch(`${API_BASE_URL}/model/api_keys/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_name: apiName, api_key: value.key, api_url: value.url})
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Fail to modify model list:', error);
      throw error;
    }
  }
};

// MQTT API服务
export const MqttApi = {

  getList: async () => {
    // 检查缓存是否有效
    const now = Date.now();
    if (mqttDeviceCache && mqttDeviceCacheTimestamp && 
        (now - mqttDeviceCacheTimestamp) < CACHE_DURATION) {
      console.log('Return cached MQTT device list');
      return mqttDeviceCache;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/mqtt/devices`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // 更新缓存
      mqttDeviceCache = data;
      mqttDeviceCacheTimestamp = now;
      
      return data;
    } catch (error) {
      console.error('Fail to get MQTT device list:', error);
      throw error;
    }
  },

  // 提供清除缓存的方法
  clearCache: () => {
    mqttDeviceCache = null;
    mqttDeviceCacheTimestamp = null;
  },

  // 提供强制刷新的方法
  refresh: async () => {
    mqttDeviceCache = null;
    mqttDeviceCacheTimestamp = null;
    return await MqttApi.getList();
  }
}

export const FileApi = {
  forceRefresh: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/refresh`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Fail to get file list:', error);
      throw error;
    }
  }, 
  getList: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/info`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Fail to get file list:', error);
      throw error;
    }
  },
  getJson: async (filePath) => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/read`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;

  } catch (error) {
      console.error('Fail to get file content:', error);
      throw error;
    }
  },
  
  modifyName: async (path, newName) => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/modify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: path, name: newName })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Fail to modify file name:', error);
      throw error;
    }
  },
  movPath: async (srcPath, destPath) => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/mov`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ srcpath: srcPath, destpath: destPath })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Fail to move file:', error);
      throw error;
    }
  },
  copyPath: async (srcPath, destPath) => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/copy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ srcpath: srcPath, destpath: destPath })
      });
    } catch (error) {
      console.error('Fail to copy file:', error);
      throw error;
    }
  },
  deleteFile: async (filePath) => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/del`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      } 

    }catch (error) {
      console.error('Fail to delete file:', error);
      throw error;
    }
  },

  writeFile: async (filePath, fileInfo) => { 
    try {
      console.log('writeFile:', filePath, fileInfo);
      const response = await fetch(`${API_BASE_URL}/file/write/file`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({path: filePath, info: fileInfo })
      });

      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      } 

    }catch (error) {
      console.error('Fail to write file:', error);
      throw error;
    }
  },
  writeFolder: async (folderPath) => { 
    try {
      const response = await fetch(`${API_BASE_URL}/file/write/folder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({path: folderPath })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    }catch (error) {
      console.error('Fail to write folder:', error);
      throw error;
    }
  },

  refresh: async () => {
    return await FileApi.getList();
  },
}
export const runTimeApi = {
  getCurrent: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/runtime/read`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Fail to get current run time info:', error);
      throw error;
    }
  },

  saveCurrent: async (runTimeInfo) => {
    try {
      const response = await fetch(`${API_BASE_URL}/file/runtime/write`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(runTimeInfo)
      });
      
      if (!response.ok) { 
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Fail to save current run time info:', error);
      throw error;
    }
  }
}