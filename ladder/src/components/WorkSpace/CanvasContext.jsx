import React, { createContext, useState, useContext } from 'react';
import ladderApi from '../../services/api';

// 导出元件类型 (公共导出)
export const ELEMENT_TYPES = {
  NORMAL_OPEN: { id: 'normal_open', icon: '| |', name: '常开触点' },
  NORMAL_CLOSED: { id: 'normal_closed', icon: '|/|', name: '常闭触点' },
  COIL: { id: 'coil', icon: '( )', name: '输出线圈' },
  // 添加新的连接元件类型
  CONNECT_UP: { id: 'connect_up', icon: '↑', name: '向上连接' },
  CONNECT_DOWN: { id: 'connect_down', icon: '↓', name: '向下连接' },
  
};

const CANVAS_GRID_SIZE = 20; // 网格尺寸(px)

// 梯级结构
export const RUNG_HEIGHT = 80;
export const RUNG_LEFT_MARGIN = 60; // 左侧母线间距
export const ELEMENT_SPACING = 60;  // 元件间距
export const ELEMENT_AREA_WIDTH = 60;  // 元件区域宽度
export const ELEMENT_AREA_HEIGHT = 60; // 元件区域高度

// 画布元素数据结构
const createElement = (typeId, position) => {
  const type = ELEMENT_TYPES[typeId.toUpperCase()] || ELEMENT_TYPES[typeId];
  if (!type) {
    throw new Error(`Unknown element type: ${typeId}`);
  }
  
  return {
    id: `${typeId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type: type,
    position: position,
    properties: {},
    comments: ""
  };
};

// 创建梯级
const createRung = (id, index) => ({
  id: id || `rung_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  index: index,
  elements: [],
  rung_bbox: []
});

// 创建上下文
export const CanvasContext = createContext();

// 创建useCanvas hook
export const useCanvas = () => {
  const context = useContext(CanvasContext);
  if (!context) {
    throw new Error('useCanvas must be used within a CanvasProvider');
  }
  return context;
};

export function CanvasProvider({ children }) {
  const [rungs, setRungs] = useState([createRung(null, 0)]); // 初始创建一个梯级
  const [selectedElement, setSelectedElement] = useState(null);
  const [selectedRung, setSelectedRung] = useState(0); // 当前选中的梯级索引
  
  // 对齐到网格
  const snapToGrid = (position) => ({
    x: Math.round(position.x / CANVAS_GRID_SIZE) * CANVAS_GRID_SIZE,
    y: Math.round(position.y / CANVAS_GRID_SIZE) * CANVAS_GRID_SIZE
  });
  
  // 计算元件在梯级中的标准位置
  const calculateElementPosition = (rungIndex, elementIndex) => ({
    x: RUNG_LEFT_MARGIN + elementIndex * ELEMENT_AREA_WIDTH,
    y: RUNG_HEIGHT / 2
  });
  
  // 根据坐标查找区域
  const findElementArea = (position) => {
    const areaX = Math.floor((position.x - RUNG_LEFT_MARGIN) / ELEMENT_AREA_WIDTH);
    let areaY = Math.floor((position.y - RUNG_HEIGHT / 2 + ELEMENT_AREA_HEIGHT / 2) / ELEMENT_AREA_HEIGHT);
    areaY = Math.max(0, areaY);
    return { areaX, areaY };
  };
  
  // 检查区域是否已被占用
  const isAreaOccupied = (rungIndex, areaX, areaY, excludeElementId = null) => {
    const rung = rungs[rungIndex];
    if (!rung) return false;
    
    for (const element of rung.elements) {
      if (element.id === excludeElementId) continue;
      
      const elementArea = findElementArea(element.position);
      if (elementArea.areaX === areaX && elementArea.areaY === areaY) {
        return true;
      }
    }
    return false;
  };
  
  // 添加元件到指定梯级（符合梯形图规范）
  const addElement = async (typeId, position, rungIndex = selectedRung) => {
    try {
      // 确保元件不能放置在母线区域（左侧边缘）
      if (position.x < RUNG_LEFT_MARGIN) {
        console.log("不能在母线区域放置元件");
        return null;
      }
      
      // 找到放置位置对应的区域
      const targetArea = findElementArea(position);
      
      // 检查该区域是否已被占用
      if (isAreaOccupied(rungIndex, targetArea.areaX, targetArea.areaY)) {
        console.log("区域已被占用，无法放置元件");
        return null; // 区域已被占用，不放置新元件
      }
      
      // 计算区域中心位置
      const elementPosition = {
        x: RUNG_LEFT_MARGIN + targetArea.areaX * ELEMENT_AREA_WIDTH + ELEMENT_AREA_WIDTH / 2,
        y: RUNG_HEIGHT / 2 + targetArea.areaY * ELEMENT_AREA_HEIGHT
      };
      
      const newElement = createElement(typeId, elementPosition);
      try{
          await ladderApi.addComponent(
          {
            id: newElement.id,
            bbox: [
              elementPosition.x - ELEMENT_AREA_WIDTH / 2,
              elementPosition.y - ELEMENT_AREA_HEIGHT / 2,
              elementPosition.x + ELEMENT_AREA_WIDTH / 2,
              elementPosition.y + ELEMENT_AREA_HEIGHT / 2
            ],
            type: newElement.type.id,
          });
      }catch (error) {
        console.error("后端添加元件失败:", error);
      }

      setRungs(prev => {
        const newRungs = [...prev];
        const rung = {...newRungs[rungIndex]};
        
        // 直接添加元件，不进行排序
        rung.elements = [...rung.elements, newElement];
        
        newRungs[rungIndex] = rung;
        return newRungs;
      });
      
      setSelectedElement(newElement);
      return newElement;
    } catch (error) {
      console.error("Error adding element:", error);
    }
  };
  
  // 添加新梯级
  const addRung = () => {
    setRungs(prev => [...prev, createRung(null, prev.length)]);
  };
  
  // 更新元件位置（保持梯形图规范，只允许水平移动）
    // 更新元件位置（保持梯形图规范，只允许水平移动）
  const updateElementPosition = (id, newPosition, rungIndex = selectedRung) => {
    // 确保元件不能放置在母线区域（左侧边缘）
    if (newPosition.x < RUNG_LEFT_MARGIN) {
      console.log("不能在母线区域放置元件");
      return;
    }
    
    setRungs(prev => {
      const newRungs = [...prev];
      const elementIndex = newRungs[rungIndex].elements.findIndex(el => el.id === id);
      
      if (elementIndex !== -1) {
        // 找到新位置对应的区域
        const targetArea = findElementArea(newPosition);
        
        // 检查该区域是否已被占用
        if (isAreaOccupied(rungIndex, targetArea.areaX, targetArea.areaY, id)) {
          // 如果被占用，保持原位置不变
          return prev;
        }
        
        // 计算区域中心位置，并确保不放置在第一行上方
        const elementPosition = {
          x: RUNG_LEFT_MARGIN + targetArea.areaX * ELEMENT_AREA_WIDTH + ELEMENT_AREA_WIDTH / 2,
          y: RUNG_HEIGHT / 2 + Math.max(0, targetArea.areaY) * ELEMENT_AREA_HEIGHT
        };
        
        newRungs[rungIndex] = {
          ...newRungs[rungIndex],
          elements: newRungs[rungIndex].elements.map(el => 
            el.id === id ? { ...el, position: elementPosition } : el
          )
        };
      }
      return newRungs;
    });
  };
  
  // 删除元件
  const removeElement = async (id, rungIndex = selectedRung) => {
    try {
      await ladderApi.deleteComponent(id);
    } catch (error) {
      console.error("后端删除元件失败:", error);
    }
    setRungs(prev => {
      const newRungs = [...prev];
      const elementIndex = newRungs[rungIndex].elements.findIndex(el => el.id === id);
      
      if (elementIndex !== -1) {
        newRungs[rungIndex] = {
          ...newRungs[rungIndex],
          elements: newRungs[rungIndex].elements.filter(el => el.id !== id)
        };
      }
      
      return newRungs;
    });
    
    if (selectedElement && selectedElement.id === id) {
      setSelectedElement(null);
    }
  };
  
  // 删除梯级
  const removeRung = (rungIndex) => {
    if (rungs.length <= 1) return; // 至少保留一个梯级
    
    setRungs(prev => {
      const newRungs = [...prev];
      newRungs.splice(rungIndex, 1);
      // 更新索引
      return newRungs.map((rung, index) => ({
        ...rung,
        index: index
      }));
    });
    
    // 如果删除的是当前选中的梯级，选择前一个
    if (rungIndex === selectedRung) {
      setSelectedRung(Math.max(0, rungIndex - 1));
    } else if (rungIndex < selectedRung) {
      setSelectedRung(selectedRung - 1);
    }
  };
  
  // 更新元件属性
  const updateElementProperties = (id, properties, rungIndex = selectedRung) => {
    setRungs(prev => {
      const newRungs = [...prev];
      newRungs[rungIndex] = {
        ...newRungs[rungIndex],
        elements: newRungs[rungIndex].elements.map(el => 
          el.id === id ? { ...el, properties: { ...el.properties, ...properties } } : el
        )
      };
      return newRungs;
    });
  };

  return (
    <CanvasContext.Provider value={{
      rungs,
      selectedElement,
      selectedRung,
      setSelectedElement,
      setSelectedRung,
      addElement,
      removeElement,
      updateElementPosition,
      addRung,
      removeRung,
      updateElementProperties,
      snapToGrid
    }}>
      {children}
    </CanvasContext.Provider>
  );
}