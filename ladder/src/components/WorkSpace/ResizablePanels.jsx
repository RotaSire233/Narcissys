import React, { useState, useRef, useEffect } from 'react';
import './workspace.css';
import { LLMApi, MqttApi } from '../../services/api';

const ResizablePanels = () => {
  const [panelSizes, setPanelSizes] = useState([33.33, 33.33, 33.33]);
  const [isDragging, setIsDragging] = useState(false);
  const [dragIndex, setDragIndex] = useState(null);
  const [apiKeys, setApiKeys] = useState({});
  const [mqttClients, setMqttClients] = useState({});
  const [apiLoading, setApiLoading] = useState(false);
  const [mqttLoading, setMqttLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [mqttError, setMqttError] = useState(null);
  const containerRef = useRef(null);

  // 获取API密钥信息
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

  // 获取MQTT客户端信息
  const fetchMqttClients = async () => {
    setMqttLoading(true);
    setMqttError(null);
    try {
      const data = await MqttApi.getList(); // 现在这会使用缓存机制
      setMqttClients(data);
    } catch (err) {
      setMqttError(err.message);
      console.error('获取MQTT客户端信息失败:', err);
    } finally {
      setMqttLoading(false);
    }
  };

  // 添加强制刷新MQTT客户端信息的函数
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

  const handleMouseDown = (index, e) => {
    setIsDragging(true);
    setDragIndex(index);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isDragging || dragIndex === null) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const containerHeight = containerRect.height;
    const posY = e.clientY - containerRect.top;

    setPanelSizes(prev => {
      const newSizes = [...prev];
      
      // 计算当前位置对应的百分比
      const percent = (posY / containerHeight) * 100;
      
      // 确保面板不会变得太小
      const minPercent = 10;
      
      if (dragIndex === 0) {
        // 调整第一个面板和第二个面板的大小
        const secondPanelSize = newSizes[1] + newSizes[0] - percent;
        if (percent >= minPercent && secondPanelSize >= minPercent) {
          newSizes[0] = percent;
          newSizes[1] = secondPanelSize;
        }
      } else if (dragIndex === 1) {
        // 调整第二个面板和第三个面板的大小
        const thirdPanelSize = newSizes[2] + newSizes[1] - percent + newSizes[0];
        if (percent - newSizes[0] >= minPercent && thirdPanelSize >= minPercent) {
          newSizes[1] = percent - newSizes[0];
          newSizes[2] = thirdPanelSize;
        }
      }
      
      return newSizes;
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragIndex(null);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragIndex]);

  // 页面加载时获取API密钥信息和MQTT客户端信息
  useEffect(() => {
    fetchApiKeys();
    fetchMqttClients();
  }, []);

  // 处理API密钥更改
  const handleApiKeyChange = (modelName, value) => {
    setApiKeys(prev => ({
      ...prev,
      [modelName]: value
    }));
  };

  // 保存API密钥更改
  const saveApiKeyChange = async (modelName, value) => {
    try {
      await LLMApi.modifyList(modelName, value);
      // 可以添加一个提示，表示保存成功
    } catch (err) {
      console.error('保存API密钥失败:', err);
      // 恢复原来的值
      fetchApiKeys();
    }
  };

  // 渲染API密钥表格行
  const renderApiKeysRows = () => {
    if (apiLoading) {
      return (
        <tr>
          <td colSpan="3">加载中...</td>
        </tr>
      );
    }

    if (apiError) {
      return (
        <tr>
          <td colSpan="3">错误: {apiError}</td>
        </tr>
      );
    }

    if (Object.keys(apiKeys).length === 0) {
      return (
        <tr>
          <td colSpan="3">暂无数据</td>
        </tr>
      );
    }

    return Object.entries(apiKeys).map(([key, value]) => (
      <tr key={key}>
        <td className="model-name-cell">{key}</td>
        <td className="api-key-cell">
          <input 
            type="text" 
            value={value} 
            onChange={(e) => handleApiKeyChange(key, e.target.value)}
            onBlur={(e) => saveApiKeyChange(key, e.target.value)}
            style={{ width: '100%', boxSizing: 'border-box' }}
          />
        </td>
        <td></td>
      </tr>
    ));
  };

    // 渲染MQTT客户端表格行
  const renderMqttClientRows = () => {
    if (mqttLoading) {
      return (
        <tr>
          <td colSpan="3">加载中...</td>
        </tr>
      );
    }

    if (mqttError) {
      return (
        <tr>
          <td colSpan="3">错误: {mqttError}</td>
        </tr>
      );
    }

    // 检查数据结构
    if (!mqttClients || !mqttClients.devices || Object.keys(mqttClients.devices).length === 0) {
      return (
        <tr>
          <td colSpan="3">暂无数据</td>
        </tr>
      );
    }

    // 将对象转换为数组进行渲染
    return Object.entries(mqttClients.devices).map(([deviceId, deviceInfo]) => (
      <tr key={deviceId}>
        <td>{deviceId}</td>
        <td>{deviceInfo.ip || '未知IP'}</td>
        <td>
          {deviceInfo.sensor && Array.isArray(deviceInfo.sensor) && deviceInfo.sensor.length > 0 
            ? `${deviceInfo.sensor.length}个传感器` 
            : '无传感器'}
        </td>
      </tr>
    ));
  };

  // 渲染区域2的设备传感器信息
  const renderDeviceSensorRows = () => {
    if (mqttLoading) {
      return (
        <tr>
          <td colSpan="3">加载中...</td>
        </tr>
      );
    }

    if (mqttError) {
      return (
        <tr>
          <td colSpan="3">错误: {mqttError}</td>
        </tr>
      );
    }

    // 从mqttClients中提取设备和传感器信息
    const deviceSensorData = [];
    
    if (mqttClients && mqttClients.devices) {
      Object.entries(mqttClients.devices).forEach(([deviceId, deviceInfo]) => {
        // 检查是否有传感器数据
        if (deviceInfo && deviceInfo.sensor && Array.isArray(deviceInfo.sensor) && deviceInfo.sensor.length > 0) {
          deviceInfo.sensor.forEach((sensorObj, index) => {
            // 获取传感器名称（从对象的键获取）
            const sensorName = Object.keys(sensorObj)[0] || `传感器${index + 1}`;
            deviceSensorData.push({
              deviceId,
              sensorName
            });
          });
        } else {
          // 如果没有传感器信息，显示设备ID
          deviceSensorData.push({
            deviceId,
            sensorName: '无传感器'
          });
        }
      });
    }

    if (deviceSensorData.length === 0) {
      return (
        <tr>
          <td colSpan="3">暂无数据</td>
        </tr>
      );
    }

    return deviceSensorData.map((item, index) => (
      <tr key={`${item.deviceId}-${index}`}>
        <td>{item.deviceId}</td>
        <td>{item.sensorName}</td>
        <td></td>
      </tr>
    ));
  };

    return (
    <div className="resizable-container" ref={containerRef}>
      <div className="panel" style={{ height: `${panelSizes[0]}%` }}>
        <div className="panel-header">模型信息表单
          <button onClick={fetchApiKeys} style={{ float: 'right', marginRight: '10px' }}>
            刷新
          </button>
        </div>
        <div className="table-container">
          <table className="expandable-table">
            <thead>
              <tr>
                <th className="model-name-header">模型名称</th>
                <th className="api-key-header">API密钥</th>
              </tr>
            </thead>
            <tbody>
              {renderApiKeysRows()}
            </tbody>
          </table>
        </div>
      </div>
      
      <div 
        className={`resizer ${isDragging && dragIndex === 0 ? 'active' : ''}`}
        onMouseDown={(e) => handleMouseDown(0, e)}
      />
      
      <div className="panel" style={{ height: `${panelSizes[1]}%` }}>
        <div className="panel-header">MQTT客户端信息
          <button onClick={refreshMqttClients} style={{ float: 'right', marginRight: '10px' }}>
            刷新
          </button>
        </div>
        <div className="table-container">
          <table className="expandable-table">
            <thead>
              <tr>
                <th className="model-name-header">设备ID</th>
                <th className="api-key-header">设备IP</th>
                <th className="api-key-header">传感器数量</th>
              </tr>
            </thead>
            <tbody>
              {renderMqttClientRows()}
            </tbody>
          </table>
        </div>
      </div>
      
      <div 
        className={`resizer ${isDragging && dragIndex === 1 ? 'active' : ''}`}
        onMouseDown={(e) => handleMouseDown(1, e)}
      />
      
      <div className="panel" style={{ height: `${panelSizes[2]}%` }}>
        <div className="panel-header">设备传感器列表</div>
        <div className="table-container">
          <table className="expandable-table">
            <thead>
              <tr>
                <th>设备</th>
                <th>传感器</th>
                <th>哈希值</th>
              </tr>
            </thead>
            <tbody>
              {renderDeviceSensorRows()}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ResizablePanels;