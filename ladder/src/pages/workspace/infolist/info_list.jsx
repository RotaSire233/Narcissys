import React, {use, useEffect, useState} from "react";
import { useNetWorkInfo } from "./InfoCommon";
import './info_list.css'

const InfoList = () => {
    const { mqttClients, fetchMqttClients, mqttLoading} = useNetWorkInfo();
    const [devices, setDevices] = useState({});
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [selectedSensor, setSelectedSensor] = useState(null);
    const [refreshInterval, setRefreshInterval] = useState(null);
    const [noDeviceCount, setNoDeviceCount] = useState(0);
    const [showNoDevices, setShowNoDevices] = useState(false);
    
    useEffect(() => { 
        fetchMqttClients();
        const interval = setInterval(() => {
            fetchMqttClients();
        }, 5000);
        setRefreshInterval(interval);
        return () => {
            if (interval){
            clearInterval(interval);
            }
        };
    }, [])

    useEffect(() => {
        if (mqttClients && mqttClients.devices) {
            if (Object.keys(mqttClients.devices).length > 0) {
                setDevices(mqttClients.devices);
                setNoDeviceCount(0);
                setShowNoDevices(false);
            } else {
                setNoDeviceCount(prevCount => {
                    const newCount = prevCount + 1;
                    if (newCount >= 3) {
                        setShowNoDevices(true);
                    }
                    return newCount;
                });
            }
        } else {
            setDevices({});
        }
    }, [mqttClients]);


    const handleDeviceClick = (deviceId) => {
        setSelectedDevice(deviceId);
        setSelectedSensor(null);
    }

    const handleSensorClick = (sensorId) => {
        setSelectedSensor(sensorId);
        console.log(`Sensor ${sensorId} chosen`);
    }

    return (
        <div className="info-list-container">
            <div className="device-info">
                <div className="button-column">
                    <div className="column-title">设备</div>
                    {devices && Object.keys(devices).length > 0 ? (
                        Object.keys(devices).map((deviceId, index) => {
                            const deviceName = deviceId;
                            
                            return (
                                <button 
                                    key={deviceId} 
                                    className={`vertical-button ${selectedDevice === deviceId ? 'active' : ''}`}
                                    onClick={() => handleDeviceClick(deviceId)}
                                >
                                    {deviceName}
                                </button>
                            );
                        })
                    ) : showNoDevices ? (
                        <div className="no-devices">暂无设备</div>
                    ) : (
                        <div className="no-devices">暂无设备</div>
                    )}
                </div>
            </div>
            <div className="sensor-info">
                <div className="button-column">
                    <div className="column-title">传感器</div>
                    {selectedDevice && devices[selectedDevice] && devices[selectedDevice].sensor ? (
                        devices[selectedDevice].sensor.map((sensorObj, index) => {
                            const sensorId = Object.keys(sensorObj)[0];
                            const sensorName = sensorId;
                            
                            return (
                                <button 
                                    key={sensorId} 
                                    className={`vertical-button ${selectedSensor === sensorId ? 'active' : ''}`} // 添加选中状态类
                                    onClick={() => handleSensorClick(sensorId)}
                                >
                                    {sensorName}
                                </button>
                            );
                        })
                    ) : (
                        <div className="no-sensors">请选择设备</div>
                    )}
                </div>
            </div>
            <div className="details">
               
                <p>正在努力开发中！！</p>
                <p>将具备功能：</p>
                <p>传感器数据结构显示</p>
                <p>传感器数据自定义可视化</p>
                <p>数据时序预处理算法</p>

            </div>
        </div>
    )
}


export default InfoList;
