import React, {use, useEffect, useState} from "react";
import { useNetWorkInfo } from "../infolist/InfoCommon";
import './set_nav.css'

const SetLLM = () => { 
    const [activeTab, setActiveTab] = useState('llm');
    const tabs = [
        {id: 'llm', name: 'LLM'},
        {id: 'api', name: 'API'},
    ]
    
    const { apiKeys, apiLoading, apiError, fetchApiKeys, handleApiKeyChange, saveApiKeyChange } = useNetWorkInfo();
    const [editingKey, setEditingKey] = useState({});
    const [showForm, setShowForm] = useState(false);
    const [newApiName, setNewApiName] = useState("");
    const [newApiKey, setNewApiKey] = useState("");
    const [newApiUrl, setNewApiUrl] = useState("");
    const [visiblePasswords, setVisiblePasswords] = useState({});
    const [addFormVisible, setAddFormVisible] = useState(false);
    
    useEffect(() => {
        fetchApiKeys();
    }, []);
    

    const handleInputChange = (apiName, value) => {
        handleApiKeyChange(apiName, value);
        setEditingKey(prev => ({
            ...prev,
            [apiName]: value
        }));
    };

    const handleApiChange = (apiName, key_) => {
        const currentValue = apiKeys[apiName] || {};
        const newValue = {
            ...currentValue, 
            key : key_};
        handleInputChange(apiName, newValue);
        setEditingKey(prev => ({
            ...prev,
            [apiName]: newValue
        }));

    };

    const handleUrlChange = (apiName, url) => {
        const currentValue = apiKeys[apiName] || {};
        const newValue = {
            ...currentValue, 
            url : url};
        handleInputChange(apiName, newValue);
        setEditingKey(prev => ({
            ...prev,
            [apiName]: newValue
        }));
    }
    

    const handleSave = async (apiName) => {
        await saveApiKeyChange(apiName, apiKeys[apiName]);
    };
    

    const handleAddApiKey = async () => {
        if (!newApiName.trim() || !newApiKey.trim()|| !newApiUrl.trim()) {
            alert("请输入API名称、密钥、URL");
            return;
        }
        const newValue = {
            key: newApiKey,
            url: newApiUrl
        };
        try {
            await saveApiKeyChange(newApiName, newValue);
            setNewApiName("");
            setNewApiKey("");
            setNewApiUrl("");
            setShowForm(false);
        } catch (error) {
            console.error("添加API密钥失败:", error);
            alert("添加API密钥失败");
        }
    };
    

    const handleDelete = async (apiName) => {
        if (window.confirm(`确定要删除 ${apiName} 吗？`)) {
            const NullInfo ={
            key: "del",
            url: "del"
            };
            try {
                await saveApiKeyChange(apiName, NullInfo);
            } catch (error) {
                console.error("删除API密钥失败:", error);
                alert("删除API密钥失败");
            }
        }
    };
    

    const togglePasswordVisibility = (apiName) => {
        setVisiblePasswords(prev => ({
            ...prev,
            [apiName]: !prev[apiName]
        }));
    };
    
    const toggleAddFormPasswordVisibility = () => {
        setAddFormVisible(prev => !prev);
    };
    
    return (
        <div className="set-container">
            <div className="button-column">
                <div className="set-title">设置</div>
                {tabs.map(tab => (
                <button
                key={tab.id}
                className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
            >
                {tab.name}
            </button>
            ))}
            </div>
            {activeTab === 'llm' && (
            <div className="llm-setting"> 
                <div className="api-keys-container">
                    <div className="header-section">
                        <h2>大语言模型 API 管理</h2>
                        <button className="add-api-btn" onClick={() => setShowForm(!showForm)}>+ 添加API</button>
                    </div>
                    
                    {showForm && (
                        <div className="add-api-form">
                            <h3>添加新API</h3>
                            <div className="input-group">
                                <label>API名称:</label>
                                <input
                                    type="text"
                                    value={newApiName}
                                    onChange={(e) => setNewApiName(e.target.value)}
                                    placeholder="例如：openai, qwen等"
                                />
                            </div>
                            <div className="input-group">
                                <label>API URL:</label>
                                <input
                                    type="text"
                                    value={newApiUrl}
                                    onChange={(e) => setNewApiUrl(e.target.value)}
                                    placeholder="例如：https://api.openai.com/v1"
                                />
                            </div>
                            <div className="input-group password-input-group">
                                <label>API密钥:</label>
                                <div className="password-input-wrapper">
                                    <input
                                        type={addFormVisible ? "text" : "password"}
                                        value={newApiKey}
                                        onChange={(e) => setNewApiKey(e.target.value)}
                                        placeholder="输入API密钥"
                                        className="password-input"
                                    />
                                    <span
                                        className={`password-toggle-icon ${addFormVisible ? 'visible' : ''}`}
                                        onClick={toggleAddFormPasswordVisibility}
                                    >
                                        {addFormVisible ? '👁️' : '👁️‍🗨️'}
                                        
                                    </span>
                                </div>
                            </div>
                            <div className="form-actions">
                                <button onClick={handleAddApiKey}>添加</button>
                                <button onClick={() => setShowForm(false)}>取消</button>
                            </div>
                        </div>
                    )}
                    
                    {apiLoading && <div className="loading">加载中...</div>}
                    {apiError && <div className="error">错误: {apiError}</div>}
                    
                    <div className="api-keys-list">
                        {apiKeys && Object.keys(apiKeys).length > 0 ? (
                            Object.entries(apiKeys).map(([apiName, apiKey]) => (
                                <div key={apiName} className="api-key-item">
                                    <div className="api-info">
                                        <div className="api-name">{apiName}</div>
                                        <div className="input-group">
                                            <input
                                                type="text"
                                                value={apiKey.url || ""}
                                                onChange={(e) => handleUrlChange(apiName, e.target.value)}
                                                placeholder="API URL"
                                                className="url-input"
                                            />
                                        </div>
                                        <div className="password-input-wrapper">
                                            <input
                                                type={visiblePasswords[apiName] ? "text" : "password"}
                                                value={apiKey.key || ""}
                                                onChange={(e) => handleApiChange(apiName, e.target.value)}
                                                placeholder="API 密钥"
                                                className="password-input"
                                            />
                                            <span
                                                className={`password-toggle-icon ${visiblePasswords[apiName] ? 'visible' : ''}`}
                                                onClick={() => togglePasswordVisibility(apiName)}
                                            >
                                                {visiblePasswords[apiName] ? '👁️' : '👁️‍🗨️'}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="api-actions">
                                        <button onClick={() => handleSave(apiName)}>保存</button>
                                        <button className="delete-btn" onClick={() => handleDelete(apiName)}>删除</button>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="no-data">暂无API密钥数据</div>
                        )}
                    </div>
                </div>
            </div>
            )}
            {activeTab === 'api' && (
            <div className="api-setting"> 
                <h2>通用 API 管理</h2>
                <p>这里是API相关的设置选项。</p>
            </div>
            )}

        </div>
    )

    
}

export default SetLLM;