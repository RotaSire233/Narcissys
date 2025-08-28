// src/components/WorkSpace/index.jsx
import React, { useState } from 'react';
import { CanvasProvider } from './CanvasContext';
import Toolbar from './ToolBar';
import WorkCanvas from './WorkCanvas';
import PropertyPanel from './PropertyPanel';
import ResizablePanels from './ResizablePanels';
import './workspace.css';

export default function WorkSpace() {
  const [activeTab, setActiveTab] = useState('workspace1');

  const tabs = [
    { id: 'workspace1', name: '梯形图画布' },
    { id: 'workspace2', name: '信息表单' }
  ];

  return (
    <div className="workspace-with-tabs">
      <div className="tab-navigation">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.name}
          </button>
        ))}
      </div>
      
      <CanvasProvider>
        {activeTab === 'workspace1' && (
          <div className="workspace-container">
            <Toolbar />
            <WorkCanvas />
            <PropertyPanel />
          </div>
        )}
        
        {activeTab === 'workspace2' && (
          <ResizablePanels />
        )}
      </CanvasProvider>
    </div>
  );
}
