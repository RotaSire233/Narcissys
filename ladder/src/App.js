// src/App.js
import React from 'react';
import WorkSpace from './components/WorkSpace';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Narcissys 网关工作台</h1>
        <p>梯形图&物联网&AI 探索现代网关工作台</p>
      </header>
      <main>
        <WorkSpace />
      </main>
      <footer className="app-footer">
        <span>© 2025 Narcissys | 版本 0.0.1b</span>
      </footer>
    </div>
  );
}

export default App;
