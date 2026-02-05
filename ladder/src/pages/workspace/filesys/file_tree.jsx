import React, { useState, useEffect} from "react";
import { useFiles } from "./FileCommon";
import './file_tree.css'
import useAsyncStateUpdate from '../../../components/utils/WaitReturn';
import EventBus from '../../../components/event_bus/EventBus';
import DeleteButton from '../../../components/close_button/DeleteButton';
import SettingWindow from '../../../components/setting_window/SettingWindow';

const FileTree = ({style}) => {
    const {fileTree,fileLoading,fileError,
           whitelist,refreshFile,
          } = useFiles();
    const { wrapWithPromise } = useAsyncStateUpdate();
    const [activateNode, setActivateNode] = useState(null);
  


    // 强制刷新文件树
    const handleRefresh = async () => {
      try {
        refreshFile();
      } catch (error) {
        console.error('Fail to refresh file tree:', error);
      }
    }

    // 处理展开（仅文件夹）
    const onToggle = (node, toggled) =>{
      if (activateNode) {
        activateNode.active = false;
      }
      node.active = true;
      if (node.children) {
        node.toggled = toggled;
      }
      setActivateNode(node);
    }
    // 处理选择文件
    const onSelect = async (node) => {
      if (activateNode) {
        activateNode.active = false;
      }
      node.active = true;
          setActivateNode(node);
          if (node.children) {
        return;
      }
  
      if (whitelist.includes(node.name)) {
        return;
      }
      
      const fileName = node.name.replace(/\.[^/.]+$/, '');
      const filePath = node.path;
      
      EventBus.emit('openFile', fileName, filePath);
          
    };

    const onDelete = async (path) => {
      try{
        EventBus.emit('deleteFile', path);
        console.log('Delete file:', path);
      } catch (err) {
        console.error('Failed to delete file:', err);
      }
    };

    const onRename = (newName, oldName) => {
      try {
        EventBus.emit('renameFile', newName, oldName)
      } catch (err) {
        console.error('Fail to rename file:', err)

      }
    };


    if (fileLoading) {
    return (
      <div className="file-tree-container" style={style}>
        <h3>文件管理</h3>
        <div className="tree-root" style={{ height: 'calc(100% - 40px)', overflow: 'hidden' }}>
          <div>加载中...</div>
        </div>
      </div>
    );
  }

  if (fileError) {
    return (
      <div className="file-tree-container" style={style}>
        <h3>文件管理</h3>
        <div className="tree-root" style={{ height: 'calc(100% - 40px)', overflow: 'hidden' }}>
          <div>错误: {fileError}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="file-tree-container" style={style}>
      <h3>文件管理</h3>
      <div className="tree-root" style={{ height: 'calc(100% - 40px)', overflow: 'hidden' }}>
        {fileTree.map((node, index) => (
          <TreeNode
            key={index}
            node={node}
            onToggle={onToggle}
            onSelect={onSelect}
            onDelete={onDelete}
            onRename={onRename}
            whitelist={whitelist} 
          />
        ))}
      </div>
    </div>
  );

    
};

const TreeNode = ({ node, onToggle, onSelect,
   onDelete, onRename, level = 0, whitelist = [] }) => {
  const [isExpanded, setIsExpanded] = useState(node.toggled || false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(node.name);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const hasChildren = node.children && node.children.length > 0;

  const handleToggle = () => {
    if (hasChildren) {
      const newExpanded = !isExpanded;
      setIsExpanded(newExpanded);
      onToggle && onToggle(node, newExpanded);
    }
  };

  const handleSelect = () => {
    onSelect && onSelect(node);
    if (node.type === 'folder') {
      return;
    }
  };

  const handleRename = async () => {
    if (newName !== node.name) {
      const lastSlashIndex = node.path.lastIndexOf('/');
      const directory = lastSlashIndex !== -1 ? node.path.substring(0, lastSlashIndex) : '';
      const newFileName = `${newName}.json`;
      const newPath = directory ? `${directory}/${newFileName}` : newFileName;
      
      await onRename(node.path, newPath);
    }
    setIsRenaming(false);
  };

  const handleDoubleClick = async() => {
    if (whitelist.includes(node.name)) {
      return;
    }
    setIsRenaming(true);
  };

  const cancelRename = () => {
    setIsRenaming(false);
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };


  const confirmDelete = async (formData) => {
    const deleteInput = formData.deleteConfirm;
    if (deleteInput === node.name) {
      await onDelete(node.path);
    } else {
      console.error('Delete confirmation failed: input does not match filename');
    }
    setShowDeleteConfirm(false);
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
  };


  return (
    <div className="tree-node">
      <div 
        className={`tree-node-item level-${level} ${node.active ? 'active' : ''}`}
        onClick={handleSelect}
      >
        {hasChildren && (
          <span 
            className={`toggle-icon ${isExpanded ? 'expanded' : 'collapsed'}`}
            onClick={(e) => {
              e.stopPropagation();
              handleToggle();
            }}
          >
            {isExpanded ? '▼' : '▶'}
          </span>
        )}
        {!hasChildren && <span className="toggle-placeholder"></span>}
        {isRenaming ? (
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onBlur={handleRename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRename();
              if (e.key === 'Escape') cancelRename();
            }}
            autoFocus
          />
        ) : (
          <span
            className="node-label"
            onDoubleClick={handleDoubleClick}
          >
            {node.name}
          </span>
        )}
        {!isRenaming && !whitelist.includes(node.name) && !hasChildren && (
          <DeleteButton 
            onClick={handleDelete} 
            size={16}
          />
        )}
      </div>
      {hasChildren && isExpanded && (
        <div className="tree-node-children">
          {node.children.map((child, index) => (
            <TreeNode
              key={index}
              node={child}
              onToggle={onToggle}
              onSelect={onSelect}
              onRename={onRename}
              onDelete={onDelete}
              level={level + 1}
              whitelist={whitelist} 
            />
          ))}
        </div>
      )}
      <SettingWindow
                title="确认删除"
                visible={showDeleteConfirm}
                onClose={cancelDelete}
                onSave={confirmDelete}
                settings={[
                    {
                        id: 'deleteConfirm',
                        name: `确定要删除文件 "${node.name}" 吗？`,
                        type: 'text',
                        placeholder: '输入文件名',
                        description: '删除后文件将无法恢复，请谨慎操作。'
                    }
                ]}
      />
    </div>
  );
};


export default FileTree;