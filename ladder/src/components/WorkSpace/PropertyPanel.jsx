import React, { useState, useEffect } from 'react';
import { useCanvas } from './CanvasContext';
import { MqttApi } from '../../services/api';
import './workspace.css';

export default function PropertyPanel() {
  const canvas = useCanvas();
  const { selectedElement, removeElement } = canvas;
  const [comment, setComment] = useState('');
  // 为选项栏添加状态
  const [selectedOption, setSelectedOption] = useState('');
  // 添加设备和传感器数据状态
  const [deviceSensorData, setDeviceSensorData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 获取设备和传感器数据
  const fetchDeviceSensorData = async (forceRefresh = false) => {
    // 检查是否为触点或线圈元件
    const isContactElement = selectedElement && (selectedElement.type.id === 'normal_open' || selectedElement.type.id === 'normal_closed');
    const isCoilElement = selectedElement && selectedElement.type.id === 'coil';
    
    if (!selectedElement || (!isContactElement && !isCoilElement)) {
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      // 使用缓存数据或强制刷新数据
      const data = forceRefresh ? await MqttApi.refresh() : await MqttApi.getList();
      const formattedData = [];
      
      if (data && data.devices) {
        // 对于线圈元件，只添加设备ID
        if (isCoilElement) {
          Object.keys(data.devices).forEach(deviceId => {
            formattedData.push({
              value: deviceId,
              label: deviceId,
              isDevice: true
            });
          });
        } 
        // 对于触点元件，添加设备ID和传感器
        else if (isContactElement) {
          // 按设备分组添加选项，参考ResizablePanels组件中的处理方式
          Object.entries(data.devices).forEach(([deviceId, deviceInfo]) => {
            // 添加设备ID作为选项
            formattedData.push({
              value: deviceId,
              label: deviceId,
              isDevice: true
            });
            
            // 添加设备下的传感器作为选项
            if (deviceInfo.sensor && Array.isArray(deviceInfo.sensor)) {
              deviceInfo.sensor.forEach((sensorObj, index) => {
                // 从传感器对象中提取键作为传感器名称，参考ResizablePanels组件中的处理方式
                const sensorKeys = Object.keys(sensorObj);
                if (sensorKeys.length > 0) {
                  const sensorName = sensorKeys[0];
                  formattedData.push({
                    value: `${deviceId}:${sensorName}`,
                    label: `${deviceId}：${sensorName}`,
                    isDevice: false
                  });
                }
              });
            }
          });
        }
      }
      
      setDeviceSensorData(formattedData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // 获取设备和传感器数据
  useEffect(() => {
    fetchDeviceSensorData();
  }, [selectedElement]);
  
  useEffect(() => {
    if (selectedElement) {
      setComment(selectedElement.comments || '');
      // 初始化选项值
      setSelectedOption(selectedElement.properties.option || '');
    } else {
      setComment('');
      setSelectedOption('');
    }
  }, [selectedElement]);
  
  const handleSaveComment = () => {
    if (selectedElement) {
      selectedElement.comments = comment;
      // 在实际应用中，这里应该更新状态管理器中的元素数据
    }
  };
  
  const handleDelete = () => {
    if (selectedElement) {
      removeElement(selectedElement.id);
    }
  };
  
  // 处理选项更改但暂不发送到后端
  const handleOptionChange = (e) => {
    const value = e.target.value;
    setSelectedOption(value);
    // 暂存到元素属性中但不发送到后端
    if (selectedElement) {
      selectedElement.properties.option = value;
    }
  };
  
  // 手动刷新设备传感器数据
  const handleRefresh = () => {
    fetchDeviceSensorData(true); // 强制刷新数据
  };
  
  if (!selectedElement) {
    return (
      <div className="property-panel">
        <div className="empty-state">
          <p>请选择画布上的元件以编辑属性</p>
        </div>
      </div>
    );
  }
  
  // 检查是否为触点或闭路触点
  const isContactElement = selectedElement.type.id === 'normal_open' || selectedElement.type.id === 'normal_closed';
  // 检查是否为线圈元件
  const isCoilElement = selectedElement.type.id === 'coil';
  
  return (
    <div className="property-panel">
      <h3>{selectedElement.type.name} 属性</h3>
      
      {(isContactElement || isCoilElement) ? (
        <div className="panel-section">
          <label>{isCoilElement ? '设备ID' : '设备/传感器'}</label>
          {loading ? (
            <div>加载中...</div>
          ) : error ? (
            <div className="error">加载失败: {error}</div>
          ) : deviceSensorData.length > 0 ? (
            <>
              <select value={selectedOption} onChange={handleOptionChange}>
                {deviceSensorData.map((item, index) => (
                  <option 
                    key={index} 
                    value={item.value}
                    style={item.isDevice ? { fontWeight: 'bold' } : {}}
                  >
                    {item.label}
                  </option>
                ))}
              </select>
              <button onClick={handleRefresh} style={{ marginTop: '5px' }}>刷新</button>
            </>
          ) : (
            <>
              <div>暂无设备数据</div>
              <button onClick={handleRefresh} style={{ marginTop: '5px' }}>刷新</button>
            </>
          )}
        </div>
      ) : (
        <div className="panel-section">
          <label>位置</label>
          <div className="position-info">
            X: {selectedElement.position.x}px, 
            Y: {selectedElement.position.y}px
          </div>
        </div>
      )}
      
      <div className="panel-section">
        <label>注释</label>
        <textarea 
          value={comment}
          onChange={e => setComment(e.target.value)}
          placeholder="添加元件描述..."
        />
        <button onClick={handleSaveComment}>保存</button>
      </div>
      
      <div className="panel-section">
        <button className="delete-btn" onClick={handleDelete}>
          删除元件
        </button>
      </div>
    </div>
  );
}