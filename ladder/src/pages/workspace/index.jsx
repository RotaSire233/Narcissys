import React, {createContext, useContext, use, useState} from "react";
import { CanvasProvider, useCanvas } from "./canvas/CanvasCommon";
import { NetWorkInfo , useNetWorkInfo} from "./infolist/InfoCommon";
import {FileInfo, useFiles} from "./filesys/FileCommon"; 
import FileTree from "./filesys/file_tree";
import ToolBox from "./canvas/tool_box";
import GroupTabs from "./canvas/canvas_title";
import SetLLM from "./setting/set_nav";
import InfoList from "./infolist/info_list";
import CanvasManager from "./canvas/canvas";
import './index.css'


export default function WorkSpace() {
    const [activeTab, setActiveTab] = useState('workspace1');
    const [fileTreeWidth, setFileTreeWidth] = useState(250);
    const [toolBoxHeight, setToolBoxHeight] = useState(250);
  
    const [isResizing, setIsResizing] = useState(false);
    const [resizeMode, setResizeMode] = useState(null); 
    const tabs = [
        { id: 'workspace1', name: '画布' },
        { id: 'workspace2', name: '节点' },
        { id: 'workspace3', name: '设置' },
    ];
     const startResizing = (e, mode) => {
      e.preventDefault();
      setIsResizing(true);
      setResizeMode(mode);
      const dragBar = e.currentTarget;
      dragBar.classList.add('active');
    }

    const stopResizing = () => {
      setIsResizing(false);
      setResizeMode(null);
      const dragBars = document.querySelectorAll('.tc-drag-bar, .tf-drag-bar', 'ct-drag-bar');
      dragBars.forEach(bar => bar.classList.remove('active'));
    }

    const resize = (e) => { 
      if (isResizing && resizeMode === 'tc') {
        const containerRect = document.querySelector('.workspace-container').getBoundingClientRect();
        const newWidth = e.clientX - containerRect.left;
        const adjustedWidth = Math.max(250, Math.min(newWidth, 300));
        setFileTreeWidth(adjustedWidth);
      } else if (isResizing && resizeMode === 'tf') {
        const containerRect = document.querySelector('.workspace-container').getBoundingClientRect();
        const newHeight = e.clientY - containerRect.top;
        const adjustedHeight = Math.max(30, Math.min(newHeight, 300));
        setToolBoxHeight(adjustedHeight);
      } 
    }

    React.useEffect(() => {
        window.addEventListener('mousemove', resize);
        window.addEventListener('mouseup', stopResizing);

        return () => {
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        };
    }, [isResizing, resizeMode]);


    // 组件入口
    // CanvasProvider： 画布作用域
    // InfoProvider： 信息作用域
    // style={{ width: `${fileTreeWidth}px` }} toolbar 的可移动性先固定，没啥用
    //

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
      
      {/* 将FileInfo提升到所有页面共享的位置 */}
      <NetWorkInfo>
        <FileInfo>
          {activeTab === 'workspace1' && (
            <div className="canvas-title">
              <GroupTabs/>
              <div className="workspace-container">
                <div className='tool-bar'>
                  <ToolBox style={{ height: `${toolBoxHeight}px` }}/>
                  <div className="tf-drag-bar" onMouseDown={(e) => startResizing(e, 'tf')}></div>
                  <FileTree/>
                </div>
                <CanvasManager/>
              </div>
            </div>
          )}
          
          {activeTab === 'workspace2' && (
            <div className="workspace-list"> 
              <InfoList/>
            </div>
          )}

          {activeTab === 'workspace3' && (
            <div className="workspace-setting"> 
              <SetLLM/>
            </div>
          )}
        </FileInfo>
      </NetWorkInfo>
    </div>
    
  );
}