import React, { useState } from 'react';
import './canvas_title.css';

const GroupTabs = () => {
  const [openGroup, setOpenGroup] = useState(null);
  
  const groups = [
    {
      id: 'file',
      name: '文件',
      subTabs: [
        { id: 'new', name: '新建' },
        { id: 'open', name: '打开' },
        { id: 'save', name: '保存' },
        { id: 'save-as', name: '另存为' }
      ]
    },
    {
      id: 'edit',
      name: '编辑',
      subTabs: [
        { id: 'undo', name: '撤销' },
        { id: 'redo', name: '重做' },
        { id: 'copy', name: '复制' },
        { id: 'paste', name: '粘贴' }
      ]
    },
    {
      id: 'view',
      name: '视图',
      subTabs: [
        { id: 'zoom-in', name: '放大' },
        { id: 'zoom-out', name: '缩小' },
        { id: 'reset-zoom', name: '重置缩放' }
      ]
    },
    {
      id: 'tools',
      name: '工具',
      subTabs: [
        { id: 'select', name: '选择工具' }
      ]
    }
  ];

  const toggleGroup = (groupId) => {
    if (openGroup === groupId) {
      setOpenGroup(null);
    } else {
      setOpenGroup(groupId);
    }
  };

  const handleSubTabClick = (groupId, subTabId) => {
    console.log(`Selected: ${groupId} -> ${subTabId}`);
    setOpenGroup(null); 
  };

  return (
    <div className="group-tabs-container">
      <div className="group-tabs-header">
        {groups.map((group) => (
          <div 
            key={group.id} 
            className={`group-tab ${openGroup === group.id ? 'expanded' : ''}`}
            onClick={() => toggleGroup(group.id)}
          >
            <span className="group-tab-label">{group.name}</span>
            <span className="dropdown-arrow"></span>
            
            {openGroup === group.id && group.subTabs && group.subTabs.length > 0 && (
              <div className="sub-tabs-dropdown">
                {group.subTabs.map((subTab) => (
                  <div
                    key={subTab.id}
                    className="sub-tab"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSubTabClick(group.id, subTab.id);
                    }}
                  >
                    {subTab.name}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default GroupTabs;