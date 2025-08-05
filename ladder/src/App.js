// src/App.js
import React from 'react';
import WorkSpace from './components/WorkSpace';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>React 工作区组件演示</h1>
        <p>一个独立的工作区界面，包含工具栏和工作区域</p>
      </header>
      <main>
        <WorkSpace />
      </main>
      <footer className="app-footer">
        <span>© 2023 React 工作区组件 | 版本 1.0</span>
      </footer>
    </div>
  );
}

export default App;
