// ladder/src/services/api.js
const API_BASE_URL = 'http://localhost:5000/api';

// 梯形图API服务
export const ladderApi = {
  // 添加元件到后端
  addComponent: async (component) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ladder/components/ladder/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(component)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('添加元件失败:', error);
      throw error;
    }
  },
  

  deleteComponent: async (componentId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ladder/components/ladder/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: componentId })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('删除元件失败:', error);
      throw error;
    }
  }
};

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
      console.error('获取模型表单失败:', error);
      throw error;
    }
  },
  
  modifyList: async (apiName, apiKey) => {
    try {
      const response = await fetch(`${API_BASE_URL}/model/api_keys/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_name: apiName, api_key: apiKey })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('修改密钥表单失败', error);
      throw error;
    }
  }
};