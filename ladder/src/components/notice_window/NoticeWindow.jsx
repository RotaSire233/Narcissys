import React, { useState, useEffect } from "react";
import './NoticeWindow.css';

const NoticeWindow = ({ visible, message, onClose }) => {
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    if (visible) {
      setIsClosing(false);
      const timer = setTimeout(() => {
        handleClose();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [visible]);

  const handleClose = () => {
    setIsClosing(true);
    const timer = setTimeout(() => {
      onClose();
    }, 300);
    return () => clearTimeout(timer);
  };

  if (!visible && !isClosing) return null;

  return (
    <div className={`notice-window ${isClosing ? 'notice-window--closing' : ''}`}>
      {message}
    </div>
  );
};

export default NoticeWindow;