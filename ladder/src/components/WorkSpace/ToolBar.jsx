import React from 'react';
import { ELEMENT_TYPES } from './CanvasContext'; 
import { useCanvas } from './CanvasContext';
import { ladderApi } from '../../services/api';
import './workspace.css';

export default function Toolbar() {
  const canvas = useCanvas();

  const handleCompile = async () => {
    try {
      // 按照要求格式化数据：以rung index为键，值为该rung中的元件列表
      const ladderData = {};
      
      canvas.rungs.forEach(rung => {
        // 为每个rung创建元件列表，只包含必要信息
        const elements = rung.elements.map(element => ({
          id: element.id,
          name: element.name || '',
          properties: {
            option: element.properties.option || ''
          }
        }));
        
        // 以rung的index作为键
        ladderData[rung.index] = elements;
      });

      // 发送到后端进行编译
      const response = await ladderApi.compileLadder(ladderData);
      console.log('编译响应:', response);
      alert('编译成功!');
    } catch (error) {
      console.error('编译失败:', error);
      alert('编译失败: ' + error.message);
    }
  };

  return (
    <div className="toolbar">
      <h3>梯形图元件库</h3>
      <div className="elements-scroll-container">
        <div className="elements-list">
          {Object.values(ELEMENT_TYPES).map((type) => (
            <div 
              key={type.id}
              className="element-item"
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('element-type', type.id);
                e.dataTransfer.setData('from-toolbar', 'true');
              }}
            >
              <div className="element-icon">{type.icon}</div>
              <div className="element-name">{type.name}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="toolbar-actions">
        <button className="compile-button" onClick={handleCompile}>编译</button>
      </div>
    </div>
  );
}