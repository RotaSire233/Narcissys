// src/components/WorkSpace/WorkCanvas.jsx
import React, { useRef } from 'react';
import { useCanvas, RUNG_HEIGHT } from './CanvasContext';
import CanvasElement from './CanvasElement';
import Rung from './Rung';
import './workspace.css';

export default function WorkCanvas() {
  const { rungs, addElement, snapToGrid, addRung, selectedRung, setSelectedRung } = useCanvas();
  const canvasRef = useRef(null);
  
  // 计算每个梯级的实际高度（基于其中的元件）
  const calculateRungActualHeight = React.useCallback((rung) => {
    
    // 修改为始终基于基础梯级高度，避免因元件影响梯级高度计算
    if (rung.elements.length === 0) {
      return RUNG_HEIGHT;
    }
    
    
    let minY = Infinity;
    let maxY = -Infinity;
    
    rung.elements.forEach(el => {
      minY = Math.min(minY, el.position.y);
      maxY = Math.max(maxY, el.position.y);
    });
    
    // 基于元件位置计算梯级高度，但保持最小高度
    const elementHeight = maxY - minY;
    return Math.max(RUNG_HEIGHT, elementHeight + 40); // 40为上下边距
  }, []);
  
  // 计算每个梯级的累积Y位置
  const calculateRungYPosition = React.useCallback((rungIndex) => {
    let yPosition = 0;
    for (let i = 0; i < rungIndex; i++) {
      yPosition += calculateRungActualHeight(rungs[i]);
    }
    return yPosition;
  }, [rungs, calculateRungActualHeight]);
  
  // 根据Y坐标查找梯级索引
  const findRungIndexByY = React.useCallback((y) => {
    let accumulatedHeight = 0;
    for (let i = 0; i < rungs.length; i++) {
      const rungHeight = calculateRungActualHeight(rungs[i]);
      if (y >= accumulatedHeight && y < accumulatedHeight + rungHeight) {
        return i;
      }
      accumulatedHeight += rungHeight;
    }
    return rungs.length - 1; // 默认返回最后一个梯级
  }, [rungs, calculateRungActualHeight]);

  const handleDrop = (e) => {
    e.preventDefault();
    
    if (!canvasRef.current) return;
    
    const fromToolbar = e.dataTransfer.getData('from-toolbar');
    const typeId = e.dataTransfer.getData('element-type');
    
    if (fromToolbar && typeId) {
      const rect = canvasRef.current.getBoundingClientRect();
      const rawPos = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };
      
      // 只允许在选中的梯级上添加元件
      const rungIndex = selectedRung;
      
      // 对放置位置进行网格对齐，确保元件放置在合适的位置
      const snappedPos = snapToGrid(rawPos);
      
      // 调整Y坐标，使其相对于当前梯级而不是整个画布
      const rungYPosition = calculateRungYPosition(rungIndex);
      const adjustedPos = {
        x: snappedPos.x,
        y: snappedPos.y - rungYPosition
      };
      
      // 直接添加元件到指定梯级
      addElement(typeId, adjustedPos, rungIndex);
    }
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  };

  // 计算SVG总高度
  const calculateSvgHeight = React.useCallback(() => {
    const totalHeight = rungs.reduce((acc, rung) => acc + calculateRungActualHeight(rung), 0);
    return Math.max(600, totalHeight + 100);
  }, [rungs, calculateRungActualHeight]);

  return (
    <div 
      className="work-canvas-container"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <div className="canvas-grid-background" ref={canvasRef}>
        <svg className="work-canvas" width="100%" height={calculateSvgHeight()}>
          {/* 渲染梯级 */}
          {rungs.map((rung, index) => (
            <Rung 
              key={rung.id} 
              rung={rung} 
              index={index}
              isSelected={index === selectedRung}
              onSelect={() => setSelectedRung(index)}
              totalRungs={rungs.length}
              yPosition={calculateRungYPosition(index)}
            />
          ))}
        </svg>
        
        {/* 添加梯级按钮 */}
        <div className="add-rung-button" onClick={addRung}>
          + 添加梯级
        </div>
      </div>
    </div>
  );
}
