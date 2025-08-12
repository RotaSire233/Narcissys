import React, { useState, useRef, useEffect } from 'react';
import './workspace.css';
import { LLMApi } from '../../services/api';

const ResizablePanels = () => {
  const [panelSizes, setPanelSizes] = useState([33.33, 33.33, 33.33]);
  const [isDragging, setIsDragging] = useState(false);
  const [dragIndex, setDragIndex] = useState(null);
  const [apiKeys, setApiKeys] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);

  // 获取API密钥信息
  const fetchApiKeys = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await LLMApi.getList();
      setApiKeys(data);
    } catch (err) {
      setError(err.message);
      console.error('获取API密钥信息失败:', err);
    } finally {
      setLoading(false);
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
      const totalPercent = 100;
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

  // 页面加载时获取API密钥信息
  useEffect(() => {
    fetchApiKeys();
  }, []);

  // 渲染API密钥表格行
  const renderApiKeysRows = () => {
    if (loading) {
      return (
        <tr>
          <td colSpan="3">加载中...</td>
        </tr>
      );
    }

    if (error) {
      return (
        <tr>
          <td colSpan="3">错误: {error}</td>
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
            readOnly
            style={{ width: '100%', boxSizing: 'border-box' }}
          />
        </td>
        <td></td>
      </tr>
    ));
  };

  return (
    <div className="resizable-container" ref={containerRef}>
      <div className="panel" style={{ height: `${panelSizes[0]}%` }}>
        <div className="panel-header">区域 1 - 模型信息表单
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
        <div className="panel-header">区域 2</div>
        <div className="table-container">
          <table className="expandable-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>类型</th>
                <th>值</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>项目 1</td>
                <td>输入</td>
                <td>True</td>
              </tr>
              <tr>
                <td>项目 2</td>
                <td>输出</td>
                <td>False</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div 
        className={`resizer ${isDragging && dragIndex === 1 ? 'active' : ''}`}
        onMouseDown={(e) => handleMouseDown(1, e)}
      />
      
      <div className="panel" style={{ height: `${panelSizes[2]}%` }}>
        <div className="panel-header">区域 3</div>
        <div className="table-container">
          <table className="expandable-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>描述</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>001</td>
                <td>传感器1</td>
                <td>正常</td>
              </tr>
              <tr>
                <td>002</td>
                <td>执行器1</td>
                <td>故障</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ResizablePanels;