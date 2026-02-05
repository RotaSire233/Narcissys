// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import {semaphoreManager} from './components/event_bus/EventBus';

semaphoreManager.initSemaphore('fileOperations', 1); // 初始化信号量>>文件树名称

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
