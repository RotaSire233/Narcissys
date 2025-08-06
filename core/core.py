from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import signal
from network.mqtt.mqtt_broker import start_mosquitto
from network.udp.udp_driver import UdpDriver, UdpManager
import gradio as gr
from loguru import logger as _logger
import asyncio
import redis


ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PID_LIST = []
udp_manager = UdpManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _start_compenents()
    # 应用启动时执行
    _logger.info("正在初始化网络...")
    mosquitto_exe = os.path.join(ROOT_PATH, "network", "mosquitto", "mosquitto.exe")
    config_file = os.path.join(ROOT_PATH, "configs", "mosquitto.conf")
    broker_status, broker_pid = start_mosquitto(mosquitto_exe, config_file)
    PID_LIST.append(broker_pid)
    _logger.info(f"网络初始化完成，Broker状态: {broker_status}")
    await create_udp_driver()
    yield
    
    _logger.info("正在关闭应用，清理资源...")

    
    for pid in PID_LIST:
        try:
            if pid and pid > 0:
                os.kill(pid, signal.SIGTERM)
                _logger.info(f"已发送终止信号到进程 {pid}")
        except ProcessLookupError:
            _logger.error(f"进程 {pid} 已经不存在")
        except Exception as e:
            _logger.error(f"终止进程 {pid} 时出错: {e}")
    
    # 清空 PID 列表
    PID_LIST.clear()
    _logger.info("资源清理完成")

app = FastAPI(title="Narcissys System", lifespan=lifespan)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Narcissys System 正常运行", 
    }

@app.post("/network/udp/drivers")
async def create_udp_driver():
    """
    创建并启动一个新的UDP驱动器
    
    Args:
        driver_id: 可选的驱动器ID，如果不提供则自动生成
        
    Returns:
        dict: 包含驱动器信息的响应
    """
    try:
        driver_id, driver = await udp_manager.create_driver()
        
        return {
            "message": f"UDP驱动器 {driver_id} 创建成功",
            "driver_id": driver_id,
            "port": driver.port,
            "ip": driver.ip
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _logger.error(f"创建UDP驱动器时出错: {e}")
        raise HTTPException(status_code=500, detail=f"创建驱动器失败: {str(e)}")

@app.get("/network/udp/drivers/choose/{driver_id}")
async def choose_driver_cache(driver_id: str):
    try:
        udp_manager.choose_driver_cache(driver_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _logger.error(f"选取udp对象出错: {e}")
        raise HTTPException(status_code=500, detail=f"选取udp对象失败: {str(e)}")


@app.delete("/network/udp/drivers/delete/{driver_id}")
async def stop_udp_driver(driver_id: str):
    """
    停止指定的UDP驱动器
    
    Args:
        driver_id: 要停止的驱动器ID
        
    Returns:
        dict: 操作结果
    """
    try:
        await udp_manager.stop_driver(driver_id)
        return {
            "message": f"UDP驱动器 {driver_id} 已停止"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _logger.error(f"停止UDP驱动器 {driver_id} 时出错: {e}")
        raise HTTPException(status_code=500, detail=f"停止驱动器失败: {str(e)}")

@app.get("/network/udp/drivers/list")
async def list_udp_drivers():
    """
    列出所有运行中的UDP驱动器
    Returns:
        dict: 包含所有驱动器信息的列表
    """
    try:
        drivers_info = udp_manager.list_drivers()
        return {
            "drivers": drivers_info,
            "total": len(drivers_info)
        }
    except Exception as e:
        _logger.error(f"获取UDP驱动器列表时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取驱动器列表失败: {str(e)}")

@app.delete("/network/udp/drivers")
async def stop_all_udp_drivers():
    """
    停止所有UDP驱动器
    
    Returns:
        dict: 操作结果
    """
    try:
        await udp_manager.stop_all_drivers()
        return {
            "message": "所有UDP驱动器已停止"
        }
    except Exception as e:
        _logger.error(f"停止所有UDP驱动器时出错: {e}")
        raise HTTPException(status_code=500, detail=f"停止所有驱动器失败: {str(e)}")

@app.get("/network/udp/drivers/{driver_id}")
async def get_udp_driver(driver_id: str):
    """
    获取指定UDP驱动器的详细信息
    
    Args:
        driver_id: 驱动器ID
        
    Returns:
        dict: 驱动器详细信息
    """
    try:
        driver_info = udp_manager.get_driver_info(driver_id)
        if driver_info is None:
            raise HTTPException(status_code=404, detail=f"UDP驱动器 {driver_id} 不存在")
        return driver_info
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"获取UDP驱动器 {driver_id} 信息时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取驱动器信息失败: {str(e)}")
    
def _start_compenents():
    from .api_service import data_service, ladder_service


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("core:app", host="127.0.0.1", port=5000, reload=True)
