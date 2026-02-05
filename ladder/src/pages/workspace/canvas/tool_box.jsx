import React, { useState, useEffect } from "react";
import { ELEMENT_TYPES } from './configs/base_element';
import './tool_box.css';

export function ToolBox({style}) { 
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipContent, setTooltipContent] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);

  const handleMouseEnter = (type, event) => {
    if (!isDragging) {
      setTooltipContent(type);
      setTooltipVisible(true);
      setTooltipPosition({ x: event.clientX, y: event.clientY });
    }
  };

  const handleMouseLeave = () => {
    if (!isDragging) {
      setTooltipVisible(false);
    }
  };

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const handleDragStart = (type, e) => {
    e.dataTransfer.setData('element-type', type.id);
    e.dataTransfer.setData('from-toolbar', 'true');
    
    setTooltipVisible(false);
  };

  const handleDragEnd = () => {
    setTimeout(() => {
      setIsDragging(false);
    }, 100);
  };

  useEffect(() => {
    if (!tooltipVisible) return;

    const handleGlobalMouseMove = (event) => {
      setTooltipPosition({ x: event.clientX, y: event.clientY });
    };

    document.addEventListener('mousemove', handleGlobalMouseMove);

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
    };
  }, [tooltipVisible]);

  return(
    <div className="toolbar" style={style}>
          <h3>基础元件库</h3>
          <div className="toolbar-container" style={{ height: 'calc(100% - 40px)', overflow: 'hidden' }}>
            <div className="elements-list">
              {Object.values(ELEMENT_TYPES).map((type) => (
                <div 
                  key={type.id}
                  className="element-item"
                  draggable
                  onMouseEnter={(e) => handleMouseEnter(type, e)}
                  onMouseLeave={handleMouseLeave}
                  onMouseDown={handleMouseDown}
                  onDragStart={(e) => handleDragStart(type, e)}
                  onDragEnd={handleDragEnd}
                >
                  <div className="element-icon">{type.icon}</div>
                </div>
              ))}
            </div>
          </div>
          
          {tooltipVisible && tooltipContent && (
            <div 
              style={{
                position: 'fixed',
                top: `${tooltipPosition.y}px`,
                left: `${tooltipPosition.x}px`,
                backgroundColor: '#fff',
                border: '1px solid #ccc',
                borderRadius: '4px',
                padding: '12px',
                zIndex: 9999,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                minWidth: '200px',
                maxWidth: '300px',
                fontSize: '14px',
                lineHeight: '1.5',
                backgroundColor: '#f8f9fa',
                border: '1px solid #e0e0e0',
                pointerEvents: 'none'
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '6px', color: '#333' }}>
                {tooltipContent.name}
              </div>
              <div style={{ color: '#666', fontSize: '13px' }}>
                {tooltipContent.tooltip}
              </div>
            </div>
          )}
        </div>

  );
}

export default ToolBox;