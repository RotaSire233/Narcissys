// src/App.js
import React from 'react';
import WorkSpace from './pages/workspace';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Narcissys</h1>
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
