import React, { useState, useRef } from 'react';
import { useCanvas } from './CanvasContext';
import './workspace.css';

// 定义SVG组件
const NormalOpenSvg = () => (
  <g>
    <line stroke-width="3" y2="80" x2="25" y1="20" x1="25" stroke="#000000" fill="none"/>
    <line stroke-width="3" y2="80" x2="75" y1="20" x1="75" stroke="#000000" fill="none"/>
    <line y2="49" y1="49" x1="25" stroke-width="3" stroke="#000000" fill="none"/>
    <line y2="48.66387" x2="75" y1="48.66387" x1="100" stroke-width="3" stroke="#000000" fill="none"/>
  </g>
);

const NormalClosedSvg = () => (
  <g>
    <line stroke-width="3" y2="80" x2="25" y1="20" x1="25" stroke="#000000" fill="none"/>
    <line stroke-width="3" y2="80" x2="75" y1="20" x1="75" stroke="#000000" fill="none"/>
    <line y2="49" y1="49" x1="25" stroke-width="3" stroke="#000000" fill="none"/>
    <line y2="48.66387" x2="75" y1="48.66387" x1="100" stroke-width="3" stroke="#000000" fill="none"/>
    <line stroke-width="3" y2="30" x2="65.17394" y1="70.36014" x1="35" stroke="#000000" fill="none"/>
  </g>
);

// 更新线圈SVG - 使用用户提供的Moto.svg文件
const CoilSvg = () => (
  <g>
    <line y2="49" y1="49" x1="25" stroke-width="3" stroke="#000000" fill="none"/>
    <text style={{cursor: 'move'}} xmlSpace="preserve" textAnchor="start" fontFamily="Noto Sans JP" fontSize="50" y="67.59988" x="-10.32629" strokeWidth="0" stroke="#000000" fill="#000000">（    ）</text>
  </g>
);

// 向上连接元件SVG - 使用用户提供的up.svg文件
const ConnectUpSvg = () => (
  <g>
    <line stroke="#000000" x2="0" y2="49" y1="49" x1="50.56338" stroke-width="3" fill="none"/>
    <path d="m42.20423,14.71432l6.5996,-11.5493l6.5996,11.5493l-13.1992,0z" stroke-width="3" stroke="#000000" fill="#000000"/>
    <line y2="4.0578" x2="49" y1="49" x1="49" stroke-width="3" stroke="#000000" fill="none"/>
  </g>
);

// 向下连接元件SVG - 使用用户提供的down.svg文件
const ConnectDownSvg = () => (
  <g>
    <line stroke="#000000" x2="100" y2="49" y1="49" x1="49.43662" stroke-width="3" fill="none"/>
    <path d="m57.79577,83.28568l-6.5996,11.5493l-6.5996,-11.5493l13.1992,0z" stroke-width="3" stroke="#000000" fill="#000000"/>
    <line y2="94.9422" x2="51" y1="49" x1="51" stroke-width="3" stroke="#000000" fill="none"/>
  </g>
);

export default function CanvasElement({ element, rungIndex, elementIndex }) {
  const { removeElement, updateElementPosition, setSelectedElement, selectedElement, snapToGrid, rungs } = useCanvas();
  const [dragging, setDragging] = useState(false);
  const elementRef = useRef(null);
  
  const isSelected = selectedElement?.id === element.id;
  
  // 计算每个梯级的实际高度（基于其中的元件）
  const calculateRungActualHeight = (rung) => {
    const RUNG_HEIGHT = 80;
    if (rung.elements.length === 0) {
      return RUNG_HEIGHT;
    }
    
    let minY = RUNG_HEIGHT / 2;
    let maxY = RUNG_HEIGHT / 2;
    
    minY = Math.min(...rung.elements.map(el => el.position.y));
    maxY = Math.max(...rung.elements.map(el => el.position.y));
    
    // 给电源线增加一些边距
    const powerLineTop = Math.min(RUNG_HEIGHT / 2 - 20, minY - 15);
    const powerLineBottom = Math.max(RUNG_HEIGHT / 2 + 20, maxY + 15);
    
    // 计算梯级实际高度
    return Math.max(RUNG_HEIGHT, powerLineBottom - powerLineTop + 30);
  };
  
  // 根据Y坐标查找梯级索引
  const findRungIndexByY = (y) => {
    let accumulatedHeight = 0;
    for (let i = 0; i < rungs.length; i++) {
      const rungHeight = calculateRungActualHeight(rungs[i]);
      if (y >= accumulatedHeight && y < accumulatedHeight + rungHeight) {
        return i;
      }
      accumulatedHeight += rungHeight;
    }
    return rungs.length - 1; // 默认返回最后一个梯级
  };
  
  const handleMouseDown = (e) => {
    if (e.button !== 0) return; // 只处理左键
    
    const rect = elementRef.current.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;
    
    const startPos = { x: offsetX, y: offsetY };
    setDragging(true);
    setSelectedElement(element);
    
    const handleMouseMove = (moveEvent) => {
      if (!dragging) return;
      
      const canvas = document.querySelector('.canvas-grid-background');
      const canvasRect = canvas.getBoundingClientRect();
      
      const rawPos = {
        x: moveEvent.clientX - canvasRect.left - startPos.x,
        y: moveEvent.clientY - canvasRect.top - startPos.y
      };
      
      // 根据实际位置计算应该放在哪个梯级
      const targetRungIndex = findRungIndexByY(rawPos.y);
      
      // 对元件位置进行网格对齐，使拖拽更平滑
      const snappedPos = snapToGrid(rawPos);
      updateElementPosition(element.id, snappedPos, targetRungIndex);
    };
    
    const handleMouseUp = () => {
      setDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };
  
  const handleContextMenu = (e) => {
    e.preventDefault();
    removeElement(element.id, rungIndex);
  };
  
  // 根据元件类型渲染不同的图形
  const renderElementShape = () => {
    const typeId = element.type.id?.toLowerCase();
    switch(typeId) {
      case 'normal_open':
      case 'normal open':
        // 常开触点 - 使用SVG文件中的设计
        return (
          <g transform="scale(0.3) translate(-50, -50)">
            <NormalOpenSvg />
          </g>
        );
      case 'normal_closed':
      case 'normal closed':
        // 常闭触点 - 使用SVG文件中的设计
        return (
          <g transform="scale(0.3) translate(-50, -50)">
            <NormalClosedSvg />
          </g>
        );
      case 'coil':
        // 输出线圈 - 使用用户提供的SVG文件
        return (
          <g transform="scale(0.3) translate(-50, -50)">
            <CoilSvg />
          </g>
        );
      case 'connect_up':
        // 向上连接元件 - 使用用户提供的SVG文件
        return (
          <g transform="scale(0.3) translate(-50, -50)">
            <ConnectUpSvg />
          </g>
        );
      case 'connect_down':
        // 向下连接元件 - 使用用户提供的SVG文件
        return (
          <g transform="scale(0.3) translate(-50, -50)">
            <ConnectDownSvg />
          </g>
        );
      default:
        console.log('Unknown element type:', element.type);
        return (
          <g>
            <rect x="-15" y="-10" width="30" height="20" stroke="#000" strokeWidth="2" fill="none" />
            <text x="0" y="5" textAnchor="middle" className="element-symbol">
              ?
            </text>
          </g>
        );
    }
  };

  return (
    <g
      ref={elementRef}
      className={`element-group ${isSelected ? 'selected-element' : ''}`}
      transform={`translate(${element.position.x}, ${element.position.y})`}
      onMouseDown={handleMouseDown}
      onContextMenu={handleContextMenu}
    >
      {renderElementShape()}
      <rect 
        className="element-bounding-box" 
        x="-20" 
        y="-15" 
        width="40" 
        height="30"
      />
      {element.comments && (
        <text 
          className="element-comment" 
          x="0" 
          y="25"
        >
          {element.comments}
        </text>
      )}
    </g>
  );
}