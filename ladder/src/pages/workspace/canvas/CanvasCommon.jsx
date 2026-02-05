import React, {createContext, useState,useContext, useEffect } from 'react';
import {ELEMENT_TYPES} from "./configs/base_element";

// 网格参数
const CANVAS_GRID_SIZE = 20; // 网格尺寸(px)

// 梯级结构
export const RUNG_HEIGHT = 80;
export const RUNG_LEFT_MARGIN = 60; // 左侧母线间距
export const ELEMENT_SPACING = 60;  // 元件间距
export const ELEMENT_AREA_WIDTH = 60;  // 元件区域宽度
export const ELEMENT_AREA_HEIGHT = 60; // 元件区域高度

// 创建组件
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
export const createRung = (id, index) => ({
  id: id || `rung_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  index: index,
  elements: [],
  rung_bbox: []
});



// 连接逻辑判断函数
const getConnectionRules = (elementType, connectionSide, adjacentElementType) => {

    if (elementType === ELEMENT_TYPES.CONNECT_UP.id && connectionSide === "right") {
      // 向上连接组件右侧不生成连接线
      return false;
    }
    
    // CONNECT_DOWN 元件不能与母线连接
    if (elementType === ELEMENT_TYPES.CONNECT_DOWN.id && connectionSide === "left" && adjacentElementType === null) {
      return false;
    }
    
    // CONNECT_RIGHT 元件不能与母线或左侧元件连接
    if (elementType === ELEMENT_TYPES.CONNECT_RIGHT.id) {
      if (connectionSide === "left") {
        // 左侧无论是与母线还是其他元件都不连接
        return false;
      }
    }
    
    // 检查当前元件是否支持该侧连接
    const elementTypeDef = ELEMENT_TYPES[elementType.toUpperCase()] || ELEMENT_TYPES[elementType];
    if (!elementTypeDef) return false;
    
    if (connectionSide === "left" && !elementTypeDef.canConnectLeft) {
      return false;
    }
    
    if (connectionSide === "right" && !elementTypeDef.canConnectRight) {
      return false;
    }
    
    // 检查相邻元件是否支持反向连接
    if (adjacentElementType) {
      const adjacentTypeDef = ELEMENT_TYPES[adjacentElementType.toUpperCase()] || ELEMENT_TYPES[adjacentElementType];
      if (!adjacentTypeDef) return false;
      
      // 如果是左侧连接，检查相邻元件右侧是否可连接
      if (connectionSide === "left" && !adjacentTypeDef.canConnectRight) {
        return false;
      }
      
      // 如果是右侧连接，检查相邻元件左侧是否可连接
      if (connectionSide === "right" && !adjacentTypeDef.canConnectLeft) {
        return false;
      }
    }
    
    return true;
  };

// 创建上下文
export const CanvasContext = createContext();


// 创建Canvas接口 hook
export const useCanvas = () => {
  const context = useContext(CanvasContext);
  if (!context) {
    throw new Error('useCanvas must be used within a CanvasProvider');
  }
  return context;
};
export function CanvasProvider({ children, curRungs, curElement, canvasId }) {
  const [rungs, setRungs] = useState(curRungs || [createRung(null, 0)]);
  const [selectedElement, setSelectedElement] = useState(curElement || null);
  const [selectedRung, setSelectedRung] = useState(0); // 当前选中的梯级索引
  const [invalidElements, setInvalidElements] = useState([]); // 非法元件ID列表

  useEffect(() => {
    setRungs(curRungs || [createRung(null, 0)]);
    setSelectedElement(curElement || null);
  }, [canvasId]);
    
  // 内宽和外宽状态
  const [canvasWidth, setCanvasWidth] = useState(1000); // 外宽
  const [contentWidth, setContentWidth] = useState(880); // 内宽 (1000 - 2*60)
    
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
    
  // 检查指定位置是否可以放置元件（符合梯形图规范）
  const canPlaceElement = (rungIndex, areaX, areaY, elements) => {
    // 限制网格范围
    if (areaX < 0 || areaY < 0 || areaY > 5) return false; // 限制行数为6行
      
    // 如果是第一行第一个位置，总是可以放置
    if (areaX === 0 && areaY === 0) return true;
      
    // 检查同行前一个位置是否有元件
    const hasPreviousInRow = elements.some(el => {
      const elementArea = findElementArea(el.position);
      return elementArea.areaY === areaY && elementArea.areaX === areaX - 1;
    });
      
    // 检查同列上一个位置是否有元件
    const hasAboveInColumn = elements.some(el => {
      const elementArea = findElementArea(el.position);
      return elementArea.areaX === areaX && elementArea.areaY === areaY - 1;
    });
      
    // 只有当前一个位置或上一个位置有元件时才能放置
    return hasPreviousInRow || hasAboveInColumn;
  };
    
  // 计算最大元件X坐标
  const calculateMaxElementX = () => {
    let maxX = 0;
    rungs.forEach(rung => {
      rung.elements.forEach(element => {
        // 元件右边界 = x位置 + 元件宽度/2
        const elementRight = element.position.x + ELEMENT_AREA_WIDTH / 2;
        maxX = Math.max(maxX, elementRight);
      });
    });
    return maxX;
  };
    
  // 更新画布宽度
  const updateCanvasWidth = () => {
    const maxX = calculateMaxElementX();
    // 如果最大元件X坐标超过当前内宽，则更新内宽和外宽
    if (maxX > contentWidth) {
      const newContentWidth = maxX + ELEMENT_AREA_WIDTH; // 添加一个元件宽度的边距
      const newCanvasWidth = newContentWidth + 2 * ELEMENT_AREA_WIDTH; // 外宽 = 内宽 + 2*元件宽度
      setContentWidth(newContentWidth);
      setCanvasWidth(newCanvasWidth);
    } 
    // 如果最大元件X坐标远小于当前内宽（超过2个元件宽度），则缩小内宽和外宽
    else if (maxX < contentWidth - 2 * ELEMENT_AREA_WIDTH && contentWidth > 880) {
      const newContentWidth = Math.max(880, maxX + ELEMENT_AREA_WIDTH);
      const newCanvasWidth = newContentWidth + 2 * ELEMENT_AREA_WIDTH;
      setContentWidth(newContentWidth);
      setCanvasWidth(newCanvasWidth);
    }
  };

  useEffect(() => {
    updateCanvasWidth();
  }, [rungs]);

  const validateComponentConnections = (element, adjacentElements) => {
    const elementType = element.type.id;
    const elementDef = ELEMENT_TYPES[elementType.toUpperCase()] || ELEMENT_TYPES[elementType];
    
    if (adjacentElements.left) {
      const leftElementType = adjacentElements.left.type.id;
      const leftDef = ELEMENT_TYPES[leftElementType.toUpperCase()] || ELEMENT_TYPES[leftElementType];
      
      if (!elementDef.canConnectLeft || !leftDef.canConnectRight) {
        return false;
      }
      
      if (elementType === ELEMENT_TYPES.CONNECT_DOWN.id && !adjacentElements.left) {
        return false;
      }
    }
    
    if (adjacentElements.right) {
      const rightElementType = adjacentElements.right.type.id;
      const rightDef = ELEMENT_TYPES[rightElementType.toUpperCase()] || ELEMENT_TYPES[rightElementType];
      
      if (!elementDef.canConnectRight || !rightDef.canConnectLeft) {
        return false;
      }
      
      if (elementType === ELEMENT_TYPES.CONNECT_UP.id && adjacentElements.right) {
        return false;
      }
      
      if (elementType === ELEMENT_TYPES.CONNECT_RIGHT.id && adjacentElements.left) {
        return false;
      }
    }
    
    if (elementType === ELEMENT_TYPES.COIL.id && adjacentElements.right) {
      return false;
    }
    
    return true;
  };

  const validateLadderStructure = (rungs) => {
    const invalidElements = [];
    
    rungs.forEach(rung => {
      rung.elements.forEach(element => {
        const elementArea = findElementArea(element.position);
        
        const leftElement = rung.elements.find(el => {
          const elArea = findElementArea(el.position);
          return elArea.areaY === elementArea.areaY && elArea.areaX === elementArea.areaX - 1;
        });
        
        const rightElement = rung.elements.find(el => {
          const elArea = findElementArea(el.position);
          return elArea.areaY === elementArea.areaY && elArea.areaX === elementArea.areaX + 1;
        });
        
        const upElement = rung.elements.find(el => {
          const elArea = findElementArea(el.position);
          return elArea.areaX === elementArea.areaX && elArea.areaY === elementArea.areaY - 1;
        });
        
        const downElement = rung.elements.find(el => {
          const elArea = findElementArea(el.position);
          return elArea.areaX === elementArea.areaX && elArea.areaY === elementArea.areaY + 1;
        });

        const isValid = validateComponentConnections(element, {
          left: leftElement,
          right: rightElement,
          up: upElement,
          down: downElement
        });
        
        if (!isValid) {
          invalidElements.push(element.id);
        }

        if (element.type.id === ELEMENT_TYPES.COIL.id) {
          if (rightElement) {
            invalidElements.push(element.id);
          }
          
          if (!leftElement) {
            invalidElements.push(element.id);
          }
        }
      });
    });
    
    return {
      valid: invalidElements.length === 0,
      invalidElements: invalidElements
    };
  };
    
  
    
  // 添加元件到指定梯级（符合梯形图规范）
  const addElement = (typeId, position, rungIndex = selectedRung) => {
    try {
      if (position.x < RUNG_LEFT_MARGIN) {
        console.log("[CanvasCommon]: Cannot place element on the left margin");
        return null;
      }
        
      const targetArea = findElementArea(position);
        
      const rung = rungs[rungIndex];
      if (!canPlaceElement(rungIndex, targetArea.areaX, targetArea.areaY, rung.elements)) {
        console.log("[CanvasCommon]: Element placement does not follow ladder rules");
        return null;
      }
        
      if (isAreaOccupied(rungIndex, targetArea.areaX, targetArea.areaY)) {
        console.log("[CanvasCommon]: Area is already occupied, cannot place element");
        return null;
      }

      const elementPosition = {
        x: RUNG_LEFT_MARGIN + targetArea.areaX * ELEMENT_AREA_WIDTH + ELEMENT_AREA_WIDTH / 2,
        y: RUNG_HEIGHT / 2 + targetArea.areaY * ELEMENT_AREA_HEIGHT
      };
        
      const newElement = createElement(typeId, elementPosition);
      const leftElement = rung.elements.find(el => {
        const elArea = findElementArea(el.position);
        return elArea.areaY === targetArea.areaY && elArea.areaX === targetArea.areaX - 1;
      });
      
      const rightElement = rung.elements.find(el => {
        const elArea = findElementArea(el.position);
        return elArea.areaY === targetArea.areaY && elArea.areaX === targetArea.areaX + 1;
      });
      
      const upElement = rung.elements.find(el => {
        const elArea = findElementArea(el.position);
        return elArea.areaX === targetArea.areaX && elArea.areaY === targetArea.areaY - 1;
      });
      
      const downElement = rung.elements.find(el => {
        const elArea = findElementArea(el.position);
        return elArea.areaX === targetArea.areaX && elArea.areaY === targetArea.areaY + 1;
      });
      
      const isValidConnection = validateComponentConnections(newElement, {
        left: leftElement,
        right: rightElement,
        up: upElement,
        down: downElement
      });
      
      if (!isValidConnection) {
        console.log("[CanvasCommon]: Component connection rules validation failed");
        return null;
      }
      
      setRungs(prev => {
        const newRungs = [...prev];
        newRungs[rungIndex] = {
          ...newRungs[rungIndex],
          elements: [...newRungs[rungIndex].elements, newElement]
        };
        return newRungs;
      });

      const validationResult = validateLadderStructure([...rungs]);
      setInvalidElements(validationResult.invalidElements);
      
      return newElement;
    } catch (error) {
      console.error("[CanvasCommon]: Failed to add element:", error);
      return null;
    }
  };
    
  // 添加新梯级
  const addRung = () => {
    setRungs(prev => [...prev, createRung(null, prev.length)]);
  };
    
  // 更新元件位置（保持梯形图规范，只允许水平移动）
  const updateElementPosition = (id, newPosition, rungIndex = selectedRung) => {
    // 确保元件不能放置在母线区域（左侧边缘）
    if (newPosition.x < RUNG_LEFT_MARGIN) {
      console.log("[CanvasCommon]: Cannot place element on the left margin");
      return;
    }
      
    setRungs(prev => {
      const newRungs = [...prev];
      const elementIndex = newRungs[rungIndex].elements.findIndex(el => el.id === id);
        
      if (elementIndex !== -1) {
        // 找到新位置对应的区域
        const targetArea = findElementArea(newPosition);
          
        // 检查该区域是否符合梯形图放置规则
        if (!canPlaceElement(rungIndex, targetArea.areaX, targetArea.areaY, newRungs[rungIndex].elements)) {
          console.log("[CanvasCommon]: Element placement does not follow ladder rules");
          return prev;
        }
          
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
  const removeElement = (id, rungIndex = selectedRung) => {
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
  
    setRungs(prev => {
      const validationResult = validateLadderStructure(prev);
      setInvalidElements(validationResult.invalidElements);
      return prev;
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
        elements: newRungs[rungIndex].elements.map(el => {
          // 分离name属性和其它属性
          let updatedElement = { ...el };
          if ('name' in properties) {
            updatedElement.name = properties.name;
            // 从properties中移除name，避免重复
            const { name, ...restProperties } = properties;
            updatedElement.properties = { ...updatedElement.properties, ...restProperties };
          } else {
            updatedElement.properties = { ...updatedElement.properties, ...properties };
          }
          return el.id === id ? updatedElement : el;
        })
      };
      return newRungs;
    });
  };
  
    // 获取元件连接信息
  const getElementConnections = (element, elements) => {
    const connections = {
      left: false,
      right: false
    };
      
    // 查找相邻元件
    const elementArea = findElementArea(element.position);
      
    // 查找左侧相邻元件
    const leftElement = elements.find(el => {
      const area = findElementArea(el.position);
      return area.areaX === elementArea.areaX - 1 && area.areaY === elementArea.areaY;
    });
      
    // 查找右侧相邻元件
    const rightElement = elements.find(el => {
      const area = findElementArea(el.position);
      return area.areaX === elementArea.areaX + 1 && area.areaY === elementArea.areaY;
    });
      
    // 判断左侧连接
    if (element.position.x > RUNG_LEFT_MARGIN) { // 不在母线位置
      if (leftElement) {
        // 双向检查：当前元件左侧和相邻元件右侧都必须允许连接
        const currentElementLeftAllowed = getConnectionRules(element.type.id, "left", leftElement.type.id);
        const leftElementRightAllowed = getConnectionRules(leftElement.type.id, "right", element.type.id);
        connections.left = currentElementLeftAllowed && leftElementRightAllowed;
      } else {
        // 与母线连接：只需检查当前元件左侧是否允许连接
        connections.left = getConnectionRules(element.type.id, "left", null);
      }
    }
      
    // 判断右侧连接
    if (rightElement) {
      // 双向检查：当前元件右侧和相邻元件左侧都必须允许连接
      const currentElementRightAllowed = getConnectionRules(element.type.id, "right", rightElement.type.id);
      const rightElementLeftAllowed = getConnectionRules(rightElement.type.id, "left", element.type.id);
      connections.right = currentElementRightAllowed && rightElementLeftAllowed;
    }
      
    return connections;
  };

  const exportCanvasState = () => {
    return {
      rungs,
      selectedElement,
    };
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
      snapToGrid,
      canvasWidth,
      contentWidth,
      setCanvasWidth,
      setContentWidth,
      invalidElements,
      getElementConnections,
      exportCanvasState
    }}>
      {children}
    </CanvasContext.Provider>
  );
}