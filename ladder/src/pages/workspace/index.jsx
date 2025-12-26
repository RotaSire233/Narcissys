import React, {createContext, useContext, use, useState} from "react";
import { CanvasProvider, useCanvas } from "./canvas/CanvasCommon";
import { NetWorkInfo , useNetWorkInfo} from "./infolist/InfoCommon";
import FileTree from "./filesys/file-tree";
import ToolBox from "./canvas/tool_box";
import WorkCanvas from "./canvas/work_canvas";
import GroupTabs from "./canvas/canvas_title";
import Terminal from "./terminal/terminal";
import PropertyPanel from "./setting/setting";
import './index.css'


const CombinedContext = createContext();


const CombineProvider = ({ children }) => {
  return (
    <CanvasProvider>
      <NetWorkInfo>
        <CombineProviderContent>{children}</CombineProviderContent>
      </NetWorkInfo>
    </CanvasProvider>
  );
};


const CombineProviderContent = ({ children }) => {
  const canvasContext = useCanvas();
  const networkContext = useNetWorkInfo();

  const combinedData = {
    canvs: canvasContext,
    network: networkContext
  };

  return (
    <CombinedContext.Provider value={combinedData}>
      {children}
    </CombinedContext.Provider>
  );
};

export const useCombinedData = () => {
  const context = useContext(CombinedContext);
  if (!context) {
    throw new Error('useCombinedData must be used within a CombineProvider');
  }
  return context;
};

export default function WorkSpace() {
    const [activeTab, setActiveTab] = useState('workspace1');
    const [fileTreeWidth, setFileTreeWidth] = useState(250);
    const [toolBoxHeight, setToolBoxHeight] = useState(250);
    const [canvasHeight, setCanvasHeight] = useState(500);
  
    const [isResizing, setIsResizing] = useState(false);
    const [resizeMode, setResizeMode] = useState(null); 
    const tabs = [
        { id: 'workspace1', name: '画布' },
        { id: 'workspace2', name: '节点' }
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
      } else if (isResizing && resizeMode === 'ct') {
        const containerRect = document.querySelector('.workspace-container').getBoundingClientRect();
        const newHeight =  e.clientY - containerRect.top;
        const adjustedHeight = Math.max(200, Math.min(newHeight, 500));
        setCanvasHeight(adjustedHeight);
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
      
      {activeTab === 'workspace1' && (
        <div className="canvas-title">
          <GroupTabs/>
        <div className="workspace-container">
          <CombineProvider>
            <div className='tool-bar'>
                <ToolBox style={{ height: `${toolBoxHeight}px` }}/>
                <div className="tf-drag-bar" onMouseDown={(e) => startResizing(e, 'tf')}></div>
                <FileTree onSelectFile={(fileName) => console.log('Selected file:', fileName)} />
            </div>
            <div className="workspace-canvas-terminal">
              <div className="canvas-container">
                <WorkCanvas style={{ height: `${canvasHeight}px` }}/>
                <PropertyPanel />
              </div>
              <div className="ct-drag-bar" onMouseDown={(e) => startResizing(e, 'ct')}></div>
               <Terminal title="Terminal"/>
            </div>
          </CombineProvider>
        </div>
        </div>
      )}
      
      {activeTab === 'workspace2' && (
        
        <div className="workspace-list"> 
        <NetWorkInfo>

        </NetWorkInfo>
        </div>
      )}
    </div>
    
  );
}