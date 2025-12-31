import React, { useState, useEffect } from "react";
import { useFileInfo } from '../infolist/InfoCommon';
import './file-tree.css';

// 树形组件
const TreeNode = ({ node, onToggle, onSelect, level = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(node.toggled || false);

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
        <span className="node-label">{node.name}</span>
      </div>
      {hasChildren && isExpanded && (
        <div className="tree-node-children">
          {node.children.map((child, index) => (
            <TreeNode
              key={index}
              node={child}
              onToggle={onToggle}
              onSelect={onSelect}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const FileTree = ({ onSelectFile, style}) => {
  const { fileTree, fetchFile, fileLoading, fileError } = useFileInfo();
  const [treeData, setTreeData] = useState([]);
  const [cursor, setCursor] = useState(null);

  useEffect(() => {
    fetchFile();
  }, []);

  useEffect(() => {
    setTreeData(fileTree);
  }, [fileTree]);

  const onToggle = (node, toggled) => {
    if (cursor) {
      cursor.active = false;
    }

    node.active = true;
    if (node.children) {
      node.toggled = toggled;
    }
    setCursor(node);

    if (node.children && onSelectFile) {
      onSelectFile(node.name);
    }
  };

  const handleNodeSelect = (node) => {
    if (cursor) {
      cursor.active = false;
    }

    node.active = true;
    setCursor(node);

    if (onSelectFile) {
      onSelectFile(node.name);
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
        {treeData.map((node, index) => (
          <TreeNode
            key={index}
            node={node}
            onToggle={onToggle}
            onSelect={handleNodeSelect}
          />
        ))}
      </div>
    </div>
  );
};

export default FileTree;