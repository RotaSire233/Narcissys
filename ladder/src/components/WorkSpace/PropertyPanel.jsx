import React, { useState, useEffect } from 'react';
import { useCanvas } from './CanvasContext';
import './workspace.css';

export default function PropertyPanel() {
  const canvas = useCanvas();
  const { selectedElement, removeElement } = canvas;
  const [comment, setComment] = useState('');
  
  useEffect(() => {
    if (selectedElement) {
      setComment(selectedElement.comments || '');
    } else {
      setComment('');
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
  
  if (!selectedElement) {
    return (
      <div className="property-panel">
        <div className="empty-state">
          <p>请选择画布上的元件以编辑属性</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="property-panel">
      <h3>{selectedElement.type.name} 属性</h3>
      
      <div className="panel-section">
        <label>位置</label>
        <div className="position-info">
          X: {selectedElement.position.x}px, 
          Y: {selectedElement.position.y}px
        </div>
      </div>
      
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