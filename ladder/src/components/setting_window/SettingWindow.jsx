import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import './SettingWindow.css';
import CloseButton from '../close_button/CloseButton';

const SettingWindow = ({ 
  title = '设置', 
  settings = [], 
  theme = 'default', 
  visible = false,
  onClose, 
  onSave 
}) => {

  const initialFormData = {};
  settings.forEach(setting => {
    initialFormData[setting.id] = setting.default || '';
  });
  
  const [formData, setFormData] = useState(initialFormData);
  const modalRef = useRef(null);
  

  const handleInputChange = (id, value) => {
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };
  

  const handleSave = () => {
    if (onSave) {
      onSave(formData);
    }
  };
  

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };
  

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && visible) {
      onClose();
    }
  };
  
  useEffect(() => {
    if (visible) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [visible]);
  

  const renderInputComponent = (setting) => {
    const { type, id, options, placeholder, min, max, step } = setting;
    const value = formData[id];
    
    switch (type) {
      case 'text':
      case 'number':
      case 'password':
        return (
          <input
            type={type}
            value={value}
            onChange={(e) => handleInputChange(id, e.target.value)}
            placeholder={placeholder || ''}
            min={min}
            max={max}
            step={step}
            className="setting-input"
          />
        );
        
      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleInputChange(id, e.target.value)}
            placeholder={placeholder || ''}
            rows={4}
            className="setting-textarea"
          />
        );
        
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleInputChange(id, e.target.value)}
            className="setting-select"
          >
            {options && options.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
        
      case 'checkbox':
        return (
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => handleInputChange(id, e.target.checked)}
            className="setting-checkbox"
          />
        );
        
      case 'radio':
        return (
          <div className="setting-radio-group">
            {options && options.map(option => (
              <label key={option.value} className="radio-label">
                <input
                  type="radio"
                  name={id}
                  value={option.value}
                  checked={value === option.value}
                  onChange={(e) => handleInputChange(id, e.target.value)}
                  className="setting-radio"
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        );
        
      default:
        return null;
    }
  };
  

  if (!visible) {
    return null;
  }
  
  return (
    <div className="setting-overlay" onClick={handleOverlayClick}>
      <div 
        ref={modalRef}
        className={`setting-window ${theme}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="setting-header">
          <h2 className="setting-title">{title}</h2>
          <CloseButton onClick={onClose} />
        </div>
        
        <div className="setting-content">
          {settings.map(setting => (
            <div key={setting.id} className="setting-item">
              <label className="setting-label">
                {setting.name}
                {setting.required && <span className="required">*</span>}
              </label>
              <div className="setting-control">
                {renderInputComponent(setting)}
                {setting.description && (
                  <p className="setting-description">{setting.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>
        
        <div className="setting-footer">
          <button className="cancel-button" onClick={onClose}>
            取消
          </button>
          <button className="save-button" onClick={handleSave}>
            保存
          </button>
        </div>
      </div>
    </div>
  );
};

SettingWindow.propTypes = {
  title: PropTypes.string,
  settings: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      type: PropTypes.string.isRequired,
      default: PropTypes.any,
      placeholder: PropTypes.string,
      description: PropTypes.string,
      required: PropTypes.bool,
      options: PropTypes.arrayOf(
        PropTypes.shape({
          value: PropTypes.any.isRequired,
          label: PropTypes.string.isRequired
        })
      ),
      min: PropTypes.number,
      max: PropTypes.number,
      step: PropTypes.number
    })
  ),
  theme: PropTypes.oneOf(['default', 'dark', 'light']),
  visible: PropTypes.bool, 
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired
};

export default SettingWindow;