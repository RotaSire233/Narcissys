import React, { useState, useEffect } from 'react';
import { useCanvas } from './CanvasContext';
import { MqttApi, LLMApi } from '../../services/api';
import './workspace.css';

export default function PropertyPanel() {
  const canvas = useCanvas();
  const { selectedElement, removeElement, updateElementProperties } = canvas;
  const [comment, setComment] = useState('');
  const [name, setName] = useState('');
  // 为选项栏添加状态
  const [selectedOption, setSelectedOption] = useState('');
  // 添加设备和传感器数据状态
  const [deviceSensorData, setDeviceSensorData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // 添加模型模式状态
  const [modelMode, setModelMode] = useState('llm');
  // 添加模型列表状态
  const [modelList, setModelList] = useState([]);
  const [modelListLoading, setModelListLoading] = useState(false);
  // 添加模型名称状态
  const [selectedModelName, setSelectedModelName] = useState('');
  // 添加流式传输状态
  const [streamValue, setStreamValue] = useState('false');
  // 添加参数选取状态
  const [modelParams, setModelParams] = useState('');
  
  // 获取设备和传感器数据
  const fetchDeviceSensorData = async (forceRefresh = false) => {
    // 检查是否为触点或线圈元件
    const isContactElement = selectedElement && (selectedElement.type.id === 'normal_open' || selectedElement.type.id === 'normal_closed');
    const isCoilElement = selectedElement && selectedElement.type.id === 'coil';
    // 检查是否为模型元件
    const isModelElement = selectedElement && selectedElement.type.id === 'model';
    
    if (!selectedElement || (!isContactElement && !isCoilElement && !isModelElement)) {
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
        else if (isContactElement || isModelElement) {
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
                    value: `${deviceId}/${sensorName}`,
                    label: `${deviceId}/${sensorName}`,
                    deviceId: deviceId,
                    sensorName: sensorName,
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
  
  // 获取模型列表数据
  const fetchModelList = async () => {
    const isModelElement = selectedElement && selectedElement.type.id === 'model';
    const isLLMMode = modelMode === 'llm';
    
    if (!isModelElement || !isLLMMode) {
      return;
    }
    
    setModelListLoading(true);
    try {
      const data = await LLMApi.getList();
      const formattedModels = [];
      
      if (data) {
        // 解析模型数据，将其格式化为选项列表
        Object.entries(data).forEach(([apiName, apiInfo]) => {
          // 添加API名称作为选项
          formattedModels.push({
            value: apiName,
            label: apiName
          });
        });
      }
      
      setModelList(formattedModels);
    } catch (err) {
      console.error('获取模型列表失败:', err);
      setError(err.message);
    } finally {
      setModelListLoading(false);
    }
  };
  
  // 获取设备和传感器数据
  useEffect(() => {
    if (selectedElement) {
      setComment(selectedElement.comments || '');
      setName(selectedElement.name || '');
      // 初始化选项值
      setSelectedOption(selectedElement.properties.option || '');
      // 初始化模型模式
      setModelMode(selectedElement.properties.modelMode || 'llm');
      // 初始化模型名称
      setSelectedModelName(selectedElement.properties.modelName || '');
      // 初始化流式传输值
      setStreamValue(selectedElement.properties.stream || 'false');
      // 初始化模型参数
      setModelParams(selectedElement.properties.modelParams || '');
    } else {
      setComment('');
      setName('');
      setSelectedOption('');
      setModelMode('llm');
      setSelectedModelName('');
      setStreamValue('false');
      setModelParams('');
    }
  }, [selectedElement]);
  
  // 当选中模型元件且为LLM模式时获取模型列表
  useEffect(() => {
    const isModelElement = selectedElement && selectedElement.type.id === 'model';
    if (isModelElement && modelMode === 'llm') {
      fetchModelList();
    }
  }, [selectedElement, modelMode]);
  
  const handleSaveComment = () => {
    if (selectedElement) {
      // 更新元件的注释和名称
      updateElementProperties(selectedElement.id, { 
        comments: comment,
        name: name
      });
      
      // 如果有选中的选项，也更新到属性中
      if (selectedOption) {
        updateElementProperties(selectedElement.id, {
          option: selectedOption
        });
      }
      
      // 更新模型模式和其他模型属性
      if (selectedElement.type.id === 'model') {
        // 构建模型的option字符串，包含所有模型相关信息
        const modelOption = `${modelMode}|${selectedModelName}|${streamValue}|${modelParams}`;
        updateElementProperties(selectedElement.id, {
          modelMode: modelMode,
          modelName: selectedModelName,
          stream: streamValue,
          modelParams: modelParams,
          option: modelOption  // 将所有模型信息组合成option字段
        });
      }
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
      updateElementProperties(selectedElement.id, {
        option: value
      });
    }
  };
  
  // 处理模型名称更改
  const handleModelNameChange = (e) => {
    const value = e.target.value;
    setSelectedModelName(value);
    // 更新元素属性
    if (selectedElement) {
      updateElementProperties(selectedElement.id, {
        modelName: value
      });
    }
  };
  
  // 处理流式传输更改
  const handleStreamChange = (e) => {
    const value = e.target.value;
    setStreamValue(value);
    // 更新元素属性
    if (selectedElement) {
      updateElementProperties(selectedElement.id, {
        stream: value
      });
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
  // 检查是否为连接元件
  const isConnectionElement = selectedElement.type.id === 'connect_up' || selectedElement.type.id === 'connect_down' || selectedElement.type.id === 'connect_right';
  // 检查是否为模型元件
  const isModelElement = selectedElement.type.id === 'model';
  
  return (
    <div className="property-panel">
      <h3>{selectedElement.type.name} 属性</h3>
      
      <div className="panel-section">
        <label>元件名称</label>
        <input 
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="输入元件名称..."
        />
      </div>
      
      {isModelElement ? (
        <div className="panel-section">
          <label>模型属性</label>
          <div className="model-properties-placeholder">
            {/* 模型组件的专用属性区域 */}
            <div className="model-mode-selector">
              <select 
                value={modelMode} 
                onChange={(e) => {
                  const value = e.target.value;
                  setModelMode(value);
                  // 更新元素属性
                  if (selectedElement) {
                    updateElementProperties(selectedElement.id, {
                      modelMode: value
                    });
                  }
                }}
              >
                <option value="llm">大模型API模式</option>
                <option value="common">通用API模式</option>
              </select>
            </div>
            <div className="model-mode-content">

              {modelMode === 'llm' ? (
                <div className="llm-mode-properties">
                  <div className="panel-section">
                    <label>模型平台</label>
                    {modelListLoading ? (
                      <div>加载模型列表中...</div>
                    ) : modelList.length > 0 ? (
                      <select
                        value={selectedModelName}
                        onChange={handleModelNameChange}
                      >
                        <option value="">请选择平台</option>
                        {modelList.map((model, index) => (
                          <option key={index} value={model.value}>
                            {model.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={selectedModelName}
                        onChange={handleModelNameChange}
                        placeholder="输入模型名称..."
                      />
                    )}
                  </div>
                  {selectedModelName && (
                <>
                  <div className="panel-section">
                    <label>模型选择</label>
                    <input
                      type="text"
                      placeholder="请输入模型名称..."
                    />
                  </div>
                  <div className="panel-section">
                    <label>参数选取</label>
                    <div className="param-selector">
                      <input
                        type="text"
                        value={modelParams}
                        onChange={(e) => setModelParams(e.target.value)}
                        placeholder="输入参数，多个参数用分号分隔..."
                        style={{ width: '100%', marginBottom: '5px' }}
                      />
                      {loading ? (
                        <div>加载中...</div>
                      ) : error ? (
                        <div className="error">加载失败: {error}</div>
                      ) : deviceSensorData.length > 0 ? (
                        <select 
                          onChange={(e) => {
                            if (e.target.value) {
                              const newValue = modelParams 
                                ? `${modelParams};${e.target.value}`
                                : e.target.value;
                              setModelParams(newValue);
                            }
                          }}
                          value=""
                        >
                          <option value="">选择参数添加到列表</option>
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
                      ) : (
                        <div>暂无设备数据</div>
                      )}
                      <button 
                        onClick={handleRefresh} 
                        style={{ marginTop: '5px' }}
                      >
                        刷新
                      </button>
                    </div>
                  </div>
                      <div className="panel-section">
                        <label>流式传输</label>
                        <select
                          value={streamValue}
                          onChange={handleStreamChange}
                        >
                          <option value="true">True</option>
                          <option value="false">False</option>
                        </select>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="common-mode-properties">
                  <p>通用 API 模式配置区域</p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
      
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
                <option value="">请选择</option>
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
      ) : null}
      
      {!isConnectionElement && !isModelElement && (
        <div className="panel-section">
          <label>描述</label>
          <textarea 
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="添加元件描述..."
            style={{ height: '40px' }}
          />
        </div>
      )}
      
      <div className="panel-section">
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