import React, { useState, useEffect, useCallback, useRef, act } from "react";
import './canvas.css';
import {runTimeApi, FileApi} from '../../../services/api';
import WorkCanvas from "./work_canvas";
import PropertyPanel from "../setting/setting";
import Terminal from '../terminal/terminal';
import CloseButton from '../../../components/close_button/CloseButton';
import EventBus from '../../../components/event_bus/EventBus';
import { CanvasProvider, useCanvas} from "./CanvasCommon";
import { useFiles } from "../filesys/FileCommon";
import FileTree from "../filesys/file_tree";

// 管理画布数据组件
const CanvasDataManager = ({ onDataChange }) => {
  const canvasContext = useCanvas();
  const previousDataRef = useRef(null);

  useEffect(() => {
    const currentData = { rungs: canvasContext.rungs, selectedElement: canvasContext.selectedElement };
    if (JSON.stringify(currentData) !== JSON.stringify(previousDataRef.current)) {
      onDataChange(currentData);
      previousDataRef.current = currentData;
    }
  }, [canvasContext.rungs, canvasContext.selectedElement, onDataChange]);

  return null; 
};


const CanvasManager = () => {
  const [pages, setPages] = useState({});
  const [activePage, setActivePage] = useState(null);
  const [runTimePages, setRunTimePages] = useState([]);
  const [runTimeCanvas, setRunTimeCanvas] = useState({});
    
  const [canvasHeight, setCanvasHeight] = useState(500);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeMode, setResizeMode] = useState(null); 
  const { canvasCache,loadFileCache,setCanvasCache,
    saveItem, addFile, deleteFile, renameFile, fileTree} = useFiles();
  
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
    const dragBars = document.querySelectorAll('.ct-drag-bar');
    dragBars.forEach(bar => bar.classList.remove('active'));
  }
  
  const resize = (e) => { 
    if (isResizing && resizeMode === 'ct') {
      const containerRect = document.querySelector('.workspace-canvas-terminal').getBoundingClientRect();
      const newHeight =  e.clientY - containerRect.top;
      const adjustedHeight = Math.max(200, Math.min(newHeight, 500));
      setCanvasHeight(adjustedHeight);
      }
  }
  
  const inRunTimeStack = (filePath) => {
    setRunTimePages(prevPages => {
      if (!prevPages.includes(filePath)) {
        return [...prevPages, filePath];
      }
      return prevPages;
    });
  };

  React.useEffect(() => {
    window.addEventListener('mousemove', resize);
    window.addEventListener('mouseup', stopResizing);
        
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
      };
    }, [isResizing, resizeMode]);
           
  const saveCurrentPages = () => {
    const runtimeInfo = {
      last_open: pages,
      run_time_canvas: runTimeCanvas
    };
    runTimeApi.saveCurrent(runtimeInfo).then(() => {
      console.log("Pages and canvas data saved successfully: ", runtimeInfo);
    }).catch((error) => {
      console.error("Failed to save pages and canvas data:", error);
    });
  };

  const getCurrentCanvasData = useCallback(() => {
    if (!activePage) {
      return { rungs: null, selectedElement: null };
    }
    return runTimeCanvas[activePage] || { rungs: null, selectedElement: null };;
  }, []);

  // 新建页面
  const handleAddPage = useCallback(async (pageName, filePath) => {
    try{
      if (activePage){
      const oldPage = activePage;
      setPages(prevPages => ({
        ...prevPages,
        [oldPage]: {
          ...prevPages[oldPage],
          isActive: false,
          }
      }));
    }
    setActivePage(filePath);

    inRunTimeStack(filePath);

    const newPage = {[filePath]: {
      id: Date.now(),
      title: pageName,
      isActive: true
    }}

    const newCanva = {
          [filePath]: {
            rungs: null,
            selectedElement: null
          }
        };

    setPages(prevPages => ({
      ...prevPages,
      ...newPage
    }));

    setRunTimeCanvas(prevCanvas => ({
          ...prevCanvas,
          ...newCanva
        }));
    console.log('fileTree_before_in:', fileTree);
    await addFile(filePath, newCanva[filePath]);
    

    } catch (error) {
        console.error("Failed to add page:", error);
    }
    

    }, [setRunTimePages, fileTree]);

  const handleOpenFile = useCallback(async (pageName, filePath) => {
    try {
      if (activePage && activePage !== filePath) {
        setPages(prevPages => ({
          ...prevPages,
          [activePage]: {
            ...prevPages[activePage],
            isActive: false,
          }
        }));
      }
      
      const isPageExists = pages[filePath] !== undefined;
      
      if (isPageExists) {
        setPages(prevPages => ({
          ...prevPages,
          [filePath]: {
            ...prevPages[filePath],
            isActive: true,
          }
        }));
      } else {
        const newPage = {[filePath]: {
          id: Date.now(),
          title: pageName,
          isActive: true
        }};
        
        setPages(prevPages => ({
          ...prevPages,
          ...newPage
        }));
      }
      
      setActivePage(filePath);
      inRunTimeStack(filePath);
      
      const loaded = await loadFileCache(filePath);
      if (loaded) {
        setRunTimeCanvas(prevCanvas => ({
          ...prevCanvas,
          [filePath]: loaded
        }));
      }
    
    } catch (error) {
      console.error("Failed to open file:", error);
    }
  }, [setRunTimePages, pages, activePage]);

  const handleSaveFile = useCallback(async () => {
    try{
      if (!activePage) {
        console.error('No active page to save');
        return;
      }
      const currentCanvasData = getCurrentCanvasData();
      setCanvasCache(prevCache => ({
        ...prevCache, 
        [activePage]: {
          ...prevCache[activePage],
          canvas: currentCanvasData
        }
      }));
      await saveItem(activePage, currentCanvasData);
      console.log('canvasCache has been saved:', currentCanvasData);
  

    } catch (error) {
      console.error("Failed to save file:", error);
    }  
  }, [activePage, getCurrentCanvasData]);

  useEffect(() => {
    if (activePage && canvasCache[activePage]?.canvas) {
      saveItem(activePage, canvasCache[activePage].canvas);
    }
  }, [canvasCache, activePage]);
  
  // 重命名通知
  const handleNameChange = useCallback(async (oldPath, newPath) => {
    try{
      setPages(prevPages => {
        const updatedPages = {...prevPages};
        if (updatedPages[oldPath]){
          const newFileName = newPath.replace(/^[\\/]/, '').split(/[\\/]/).pop().replace(/\.[^/.]+$/, '');
          updatedPages[newPath] = {
            ...updatedPages[oldPath],
            title: newFileName,
          };

          delete updatedPages[oldPath];
        }
        return updatedPages;
      });
      
      if (activePage === oldPath){
        setActivePage(newPath);
      }
      
      setRunTimeCanvas(prevCanvas => { 
        const updatedCanvas = {...prevCanvas};
        if (updatedCanvas[oldPath]){
          updatedCanvas[newPath] = updatedCanvas[oldPath];
          delete updatedCanvas[oldPath];
        }
        return updatedCanvas;
      });

      setRunTimePages(prevPages => {
        const index = prevPages.indexOf(oldPath);
        if (index !== -1) {
          const updatedPages = [...prevPages];
          updatedPages[index] = newPath;
          return updatedPages;
        }
        return prevPages;
      });
      await renameFile(oldPath, newPath)
      

    } catch (error) {
      console.error("Failed to rename file:", error);
    }

  }, [activePage, fileTree]);

  const handleDeleteFile = useCallback(async (filePath) => {
    try {
      await deleteFile(filePath);
      if (pages[filePath]) {
        const pageIndex = runTimePages.indexOf(filePath);
        const updatedRunTimePages = [...runTimePages];
        if (pageIndex !== -1) {
          updatedRunTimePages.splice(pageIndex, 1);
          setRunTimePages(updatedRunTimePages);
        }

        setPages(prevPages => {
          const updatedPages = {...prevPages};
          delete updatedPages[filePath];
          return updatedPages;
        });

        setRunTimeCanvas(prevCanvas => {
          const updatedCanvas = {...prevCanvas};
          delete updatedCanvas[filePath];
          return updatedCanvas;
        });

        let newActivePage = activePage;
        if (activePage === filePath) {
          if (pageIndex > 0 && updatedRunTimePages.length > 0) {
            newActivePage = updatedRunTimePages[pageIndex - 1];
            setActivePage(newActivePage);
          } else if (updatedRunTimePages.length > 0) {
            newActivePage = updatedRunTimePages[0];
            setActivePage(newActivePage);
          } else {
            newActivePage = null;
            setActivePage(null);
          }
        }

        const updatedPages = {...pages};
        delete updatedPages[filePath];
        
      }
    } catch (error) {
      console.error("Failed to delete file page:", error);
    }
  }, [pages, runTimePages, activePage, fileTree]);

  useEffect(() => {
    EventBus.on('addPage', handleAddPage);
    EventBus.on('openFile', handleOpenFile);
    EventBus.on('saveFile', handleSaveFile);
    EventBus.on('renameFile', handleNameChange);
    EventBus.on('deleteFile', handleDeleteFile);
    return () => {
      EventBus.off('addPage', handleAddPage);
      EventBus.off('openFile', handleOpenFile);
      EventBus.off('saveFile', handleSaveFile);
      EventBus.off('renameFile', handleNameChange); 
      EventBus.off('deleteFile', handleDeleteFile);
      };
    }, [handleAddPage, handleOpenFile, handleSaveFile, handleNameChange, handleDeleteFile]);

  const handlePageClick = (pagekey) => {
     
    if (activePage){
      const oldKey = activePage;
      
      setPages(prevPages => ({
        ...prevPages,
        [oldKey]: {
          ...prevPages[oldKey],
          isActive: false,
        }
      }));
    }
    setActivePage(pagekey);
    setPages(prevPages=>({
      ...prevPages,
      [pagekey]: {
        ...prevPages[pagekey],
        isActive: true,
      }
    }))
    return pagekey;
  }
  
  const handelPageClose = async (pagekey) => {
    const canvasData = runTimeCanvas[pagekey] || { rungs: null, selectedElement: null };
  
    await saveItem(pagekey, canvasData);
    console.log(`Canvas data for page ${pagekey} saved successfully`);

    const pageIndex = runTimePages.indexOf(pagekey);
    const updatedRunTimePages = [...runTimePages];
    if (pageIndex !== -1) {
      updatedRunTimePages.splice(pageIndex, 1);
      setRunTimePages(updatedRunTimePages);
    }

    setPages(prevPages => {
      const updatedPages = {...prevPages};
      delete updatedPages[pagekey];
      return updatedPages;
    });

    if (activePage === pagekey) {
      if (pageIndex > 0 && updatedRunTimePages.length > 0) {
        const previousPageKey = updatedRunTimePages[pageIndex - 1];
        setActivePage(previousPageKey);
        setPages(prevPages => ({
          ...prevPages,
          [previousPageKey]: {
            ...prevPages[previousPageKey],
            isActive: true,
          }
        }));
      } else if (updatedRunTimePages.length > 0) {
        setActivePage(updatedRunTimePages[0]);
        setPages(prevPages => ({
          ...prevPages,
          [updatedRunTimePages[0]]: {
            ...prevPages[updatedRunTimePages[0]],
            isActive: true,
          }
        }));
      } else {
        setActivePage(null);
      }
    }
  };


  useEffect(() => {
    console.log('pages has been updated:', pages);
  }, [pages]);

  useEffect(() => {
    console.log('runTimeCanvas has been updated:', runTimeCanvas);
    saveCurrentPages();
  }, [runTimeCanvas]);

  return (
    <div className="workspace-canvas-terminal">
      <div className="page-bar">
        {Object.entries(pages).map(([pageKey, page]) => (
          <div
            key={pageKey}
            className={`page-tab ${page.isActive ? 'active' : ''}`}
            onClick={() => handlePageClick(pageKey)}
          >
            <span>{page.title}</span>
            <CloseButton onClick={(e) => {
              e.stopPropagation(); 
              handelPageClose(pageKey);
            }} />
          </div>
        ))}
      </div>
      <div className="canvas-container">
        {Object.keys(pages).length === 0 ? (
          <div className="canvas-item-null" style={{ height: `${canvasHeight}px` }}>
            <div style={{ 
              width: '100%', 
              height: '100%', 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              backgroundColor: '#f9f9f9',
              border: '1px solid #e0e0e0',
              fontSize: '18px',
              color: '#666'
            }}>
              新建/打开文件
            </div>
          </div>
          ) : (
          <div className="canvas-item">
            {(() => {
              const canvasData = runTimeCanvas[activePage] || { rungs: null, selectedElement: null };
              return (
                <CanvasProvider 
                  curRungs={canvasData.rungs} 
                  curElement={canvasData.selectedElement}
                  canvasId={activePage}
                >
                  <WorkCanvas style={{ height: `${canvasHeight}px` }} />
                  <PropertyPanel />
                  <CanvasDataManager 
                    onDataChange={(data) => {
                      if (activePage) {
                      setRunTimeCanvas(prev => ({
                        ...prev,
                        [activePage]: data
                      }));
                    }}} 
                  />
                </CanvasProvider>
              );
            })()}
          </div>
        )}
      </div>
      <div className="ct-drag-bar" onMouseDown={(e) => startResizing(e, 'ct')}></div>
      <Terminal title="Terminal"/>
    </div>
  );
}

export default CanvasManager;
