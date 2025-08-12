import React from 'react';
import { ELEMENT_TYPES } from './CanvasContext'; 
import './workspace.css';
 
export default function Toolbar() {
  return (
    <div className="toolbar">
      <h3>梯形图元件库</h3>
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
  );
}