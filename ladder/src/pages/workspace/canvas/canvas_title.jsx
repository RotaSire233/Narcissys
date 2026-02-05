import React, { use, useEffect, useState } from 'react';
import './canvas_title.css';
import SettingWindow from '../../../components/setting_window/SettingWindow';
import {NewProject} from './configs/canvas_title';
import EventBus from '../../../components/event_bus/EventBus';
import NoticeWindow from '../../../components/notice_window/NoticeWindow';
import OsFile, * as OSFile from '../../../components/utils/OsFile';

const GroupTabs = () => {
  const [openGroup, setOpenGroup] = useState(null);
  const [showNewModal, setShowNewModal] = useState(false);
  const [showNotice, setShowNotice] = useState(false);
  const [noticeMessage, setNoticeMessage] = useState('');
  const [noticeType, setNoticeType] = useState('success');
  
  const groups = [
    {
      id: 'file',
      name: '文件',
      subTabs: [
        { id: 'new', name: '新建' },
        { id: 'open', name: '运行' },
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
    
    if (groupId === 'file') {
      switch (subTabId) {
        case 'new':
          setShowNewModal(true);
          break;
        case 'save':
          EventBus.emit('saveFile');
          break;
        default:
          break;
      }
    }
    
    setOpenGroup(null); 
  };

  const handleNewProjectSave = async (formData) => {
    console.log('New Project Form Data:', formData);
    const combinedPath = OSFile.joinPath(formData.projectType, `${formData.projectName}.json`);
    try {
      EventBus.emit('addPage', formData.projectName, combinedPath);  
      setShowNewModal(false); 
    } catch (error) {
      console.error('Failed to create project file:', error);
    }
  };




  const handleNewProjectClose = () => {
    setShowNewModal(false);
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

      <NoticeWindow
        visible={showNotice}
        message={noticeMessage}
        type={noticeType}
        duration={3000}
        onClose={() => setShowNotice(false)}
      />


      <SettingWindow
        title="新建项目"
        settings={NewProject.projectTypes}
        theme="default"
        visible={showNewModal}
        onClose={handleNewProjectClose}
        onSave={handleNewProjectSave}
      />
    </div>
  );
};

export default GroupTabs;