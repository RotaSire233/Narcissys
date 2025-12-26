import React, { useState, useEffect, useRef } from 'react';
import './terminal.css';

const Terminal = ({ title = "Terminal", initialLogs = [], style}) => {
  const [logs, setLogs] = useState(initialLogs);
  const terminalRef = useRef(null);


  const addLog = (logMessage, logType = 'info') => {
    const newLog = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      message: logMessage,
      type: logType
    };
    setLogs(prevLogs => [...prevLogs, newLog]);
  };


  const clearLogs = () => {
    setLogs([]);
  };

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);


  useEffect(() => {
    if (logs.length === 0) {
      setLogs([
        { id: 1, timestamp: new Date().toLocaleTimeString(), message: "编译器初始化完成", type: "info" },
        { id: 2, timestamp: new Date().toLocaleTimeString(), message: "开始编译程序", type: "info" },
        { id: 3, timestamp: new Date().toLocaleTimeString(), message: "检测到程序逻辑", type: "info" },
        { id: 4, timestamp: new Date().toLocaleTimeString(), message: "编译成功", type: "success" },
        { id: 5, timestamp: new Date().toLocaleTimeString(), message: "编译成功", type: "success" },
        { id: 6, timestamp: new Date().toLocaleTimeString(), message: "编译成功", type: "success" },
        { id: 7, timestamp: new Date().toLocaleTimeString(), message: "编译成功", type: "success" },
        { id: 8, timestamp: new Date().toLocaleTimeString(), message: "编译成功", type: "success" }
      ]);
    }
  }, []);

  return (
    <div className="terminal-container" style={style}>
      <div className="terminal-header">
        <div className="terminal-title">{title}</div>
      </div>
      <div className="terminal-body" ref={terminalRef}>
        <div className="terminal-logs">
          {logs.map((log) => (
            <div key={log.id} className={`terminal-log ${log.type}`}>
              <span className="timestamp">[{log.timestamp}]</span>
              <span className="log-content">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

Terminal.addLog = (logMessage, logType = 'info') => {
};

export default Terminal;