import pytest
from unittest.mock import Mock
import base64
from core.utils.image.image_byte_decode import decode_image_data

def test_decode_image_data_rgb565():
    """测试RGB565格式图像解码"""
    mock_img_struct = Mock()
    mock_img_struct.formats = '565'
    mock_img_struct.size = (10, 10)
    
    mock_datas = Mock()
    mock_data = bytearray()
    for i in range(10*10):
        mock_data.extend(b'\x00\x00')
    mock_datas.get_full_data = bytes(mock_data)
    mock_img_struct.datas = mock_datas
    
    result = decode_image_data(mock_img_struct)
    
    assert result["type"] == "img"
    assert result["format"] == "RGB"
    assert result["width"] == 10
    assert result["height"] == 10
    assert "data" in result
    decoded_data = base64.b64decode(result["data"])
    assert len(decoded_data) == 10 * 10 * 3


def test_decode_image_data_rgb888():
    """测试RGB888格式图像解码"""

    mock_img_struct = Mock()
    mock_img_struct.formats = '888'
    mock_img_struct.size = (5, 5) 
    mock_datas = Mock()
    mock_data = bytearray()
    for i in range(5 * 5):
        mock_data.extend(b'\xFF\x00\x00')
    mock_datas.get_full_data = bytes(mock_data)
    mock_img_struct.datas = mock_datas
    
    result = decode_image_data(mock_img_struct)
    
    assert result["type"] == "img"
    assert result["format"] == "RGB888"
    assert result["width"] == 5
    assert result["height"] == 5
    assert "data" in result
    decoded_data = base64.b64decode(result["data"])
    assert len(decoded_data) == 5 * 5 * 3
    assert decoded_data == mock_data


def test_decode_image_data_grayscale():
    """测试灰度图格式图像解码"""
    mock_img_struct = Mock()
    mock_img_struct.formats = 'GS8'
    mock_img_struct.size = (8, 8)
    
    mock_datas = Mock()
    mock_data = bytearray()
    for i in range(8 * 8):
        mock_data.extend(b'\x80')
    mock_datas.get_full_data = bytes(mock_data)
    mock_img_struct.datas = mock_datas
    
    result = decode_image_data(mock_img_struct)
    
    assert result["type"] == "img"
    assert result["format"] == "grayscale"
    assert result["width"] == 8
    assert result["height"] == 8
    assert "data" in result
    decoded_data = base64.b64decode(result["data"])
    assert len(decoded_data) == 8 * 8


def test_decode_image_data_rgb565_conversion():
    """测试RGB565到RGB888的转换正确性"""
    mock_img_struct = Mock()
    mock_img_struct.formats = '565'
    mock_img_struct.size = (1, 1) 
    
    mock_datas = Mock()
    mock_data = b'\xF8\x00'
    mock_datas.get_full_data = mock_data
    mock_img_struct.datas = mock_datas
    
    result = decode_image_data(mock_img_struct)
    
    decoded_data = base64.b64decode(result["data"])
    assert len(decoded_data) == 3 
    
    assert decoded_data[0] > 200  # 红色分量
    assert decoded_data[1] < 50   # 绿色分量
    assert decoded_data[2] < 50   # 蓝色分量

