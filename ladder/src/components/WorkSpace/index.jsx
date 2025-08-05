// src/components/WorkSpace/index.jsx
import React from 'react';
import { CanvasProvider } from './CanvasContext';
import Toolbar from './ToolBar';
import WorkCanvas from './WorkCanvas';
import PropertyPanel from './PropertyPanel';
import './workspace.css';

export default function WorkSpace() {
  return (
    <CanvasProvider>
      <div className="workspace-container">
        <Toolbar />
        <WorkCanvas />
        <PropertyPanel />
      </div>
    </CanvasProvider>
  );
}
