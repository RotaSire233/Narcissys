import React from 'react';
import { useCanvas, RUNG_HEIGHT, ELEMENT_AREA_HEIGHT, ELEMENT_AREA_WIDTH } from './CanvasContext';
import CanvasElement from './CanvasElement';
import './workspace.css';

export default function Rung({ rung, index, isSelected, onSelect, totalRungs, yPosition }) {
  const { removeRung } = useCanvas();
  
  // 使用传入的yPosition或计算默认位置
  const rungY = yPosition !== undefined ? yPosition : index * RUNG_HEIGHT;
  
  // 计算该梯级中元件的Y轴范围，以确定电源线的高度
  let minY = RUNG_HEIGHT / 2;
  let maxY = RUNG_HEIGHT / 2;
  
  if (rung.elements.length > 0) {
    minY = Math.min(...rung.elements.map(el => el.position.y));
    maxY = Math.max(...rung.elements.map(el => el.position.y));
  }
  
  // 给电源线增加一些边距
  const powerLineTop = Math.min(RUNG_HEIGHT / 2 - 20, minY - 15);
  const powerLineBottom = Math.max(RUNG_HEIGHT / 2 + 20, maxY + 15);
  
  // 计算梯级实际高度
  const rungActualHeight = Math.max(RUNG_HEIGHT, powerLineBottom - powerLineTop + 30);
  
  // 计算电源轨（母线）的垂直中心位置
  const powerLineCenter = (powerLineTop + powerLineBottom) / 2;

  // 生成连接线
  const generateConnections = () => {
    const connections = [];
    
    // 按照Y坐标分组元件，只在同一行的元件之间建立连接
    const rows = {};
    rung.elements.forEach(element => {
      const rowKey = element.position.y;
      if (!rows[rowKey]) {
        rows[rowKey] = [];
      }
      rows[rowKey].push(element);
    });
    
    // 对每一行的元件按X坐标排序并连接
    Object.values(rows).forEach(rowElements => {
      const sortedElements = [...rowElements].sort((a, b) => a.position.x - b.position.x);
      
      if (sortedElements.length > 0) {
        // 从左母线到第一个元件的连接
        const firstElement = sortedElements[0];
        connections.push({
          from: { x: 40, y: firstElement.position.y },
          to: { x: firstElement.position.x - 20, y: firstElement.position.y }
        });
        
        // 元件之间的连接 - 每个元件的右节点连接到下一个元件的左节点
        for (let i = 0; i < sortedElements.length - 1; i++) {
          const currentElement = sortedElements[i];
          const nextElement = sortedElements[i + 1];
          
          connections.push({
            from: { x: currentElement.position.x + 20, y: currentElement.position.y },
            to: { x: nextElement.position.x - 20, y: nextElement.position.y }
          });
        }
        
        // 检查是否有向上连接的元件
        const lastElement = sortedElements[sortedElements.length - 1];
        if (lastElement.type.id === 'connect_up' && index > 0) {
          // 查找上一行中最接近当前位置的元件
          const upperRungElements = [];
          // 这里需要访问整个梯形图的数据，但目前只能访问当前梯级
          // 实际实现中需要通过context传递所有梯级数据
        }
      }
    });
    
    return connections;
  };

  const connections = generateConnections();

  return (
    <g 
      className={`rung ${isSelected ? 'selected-rung' : ''}`}
      transform={`translate(0, ${rungY})`}
      onClick={(e) => {
        e.stopPropagation();
        onSelect();
      }}
    >
      {/* 左电源轨 - 根据元件垂直范围扩展 */}
      <line 
        x1="40" 
        y1={powerLineTop} 
        x2="40" 
        y2={powerLineBottom} 
        stroke="#000" 
        strokeWidth="2" 
      />
      
      {/* 右电源轨 - 根据元件垂直范围扩展 */}
      <line 
        x1="1000" 
        y1={powerLineTop} 
        x2="1000" 
        y2={powerLineBottom} 
        stroke="#000" 
        strokeWidth="2" 
      />
      
      {/* 梯级背景，用于点击选择 */}
      <rect 
        x="0" 
        y="0" 
        width="100%" 
        height={rungActualHeight} 
        fill="transparent"
        className="rung-background"
      />
      
      {/* 梯级编号 */}
      <text x="10" y={powerLineCenter} dy="5" className="rung-number">
        {index + 1}
      </text>
      
      {/* 渲染元件 - 仅渲染当前行的元件 */}
      {rung.elements.map((element, elementIndex) => (
        <CanvasElement 
          key={element.id} 
          element={element} 
          rungIndex={index}
          elementIndex={elementIndex}
        />
      ))}
      
      {/* 连接线 - 仅连接当前行的元件 */}
      {connections.map((conn, connIndex) => (
        <line
          key={`conn-${index}-${connIndex}`}
          x1={conn.from.x}
          y1={conn.from.y}
          x2={conn.to.x}
          y2={conn.to.y}
          stroke="#000"
          strokeWidth="2"
          className="connection-line"
        />
      ))}
      
      {/* 删除梯级按钮 */}
      {totalRungs > 1 && (
        <g 
          className="remove-rung-button"
          onClick={(e) => {
            e.stopPropagation();
            removeRung(index);
          }}
        >
          <circle cx="1020" cy={powerLineCenter} r="10" fill="#f44336" />
          <text x="1020" y={powerLineCenter} dy="5" textAnchor="middle" fill="white" fontSize="12">
            ×
          </text>
        </g>
      )}
    </g>
  );
}