import base64
from core.network.udp.cache import ImgStruct
def decode_image_data(img_struct: ImgStruct):
    """
    解码图片数据
    """
    formats = img_struct.formats
    size = img_struct.size
    byte_data = img_struct.datas.get_full_data
    
    # 根据格式解码图片
    if formats == '565':
        # RGB565格式解码
        img_data = bytearray()
        for i in range(0, len(byte_data), 2):
            if i + 1 >= len(byte_data):
                break
            pixel = int.from_bytes(byte_data[i:i+2], byteorder='big')
            r = (pixel >> 11) & 0x1F
            g = (pixel >> 5) & 0x3F
            b = pixel & 0x1F
            # 扩展到8位
            r = (r << 3) | (r >> 2)
            g = (g << 2) | (g >> 4)
            b = (b << 3) | (b >> 2)
            img_data.extend([r, g, b])
        
        # 将数据转换为base64编码的字符串
        encoded_data = base64.b64encode(bytes(img_data)).decode('utf-8')
        return {
            "type": "img",
            "format": "RGB",
            "width": size[0],
            "height": size[1],
            "data": encoded_data,
        }
    elif formats == '888':
        # RGB888格式解码
        encoded_data = base64.b64encode(byte_data).decode('utf-8')
        return {
            "type": "img",
            "format": "RGB888",
            "width": size[0],
            "height": size[1],
            "data": encoded_data,
        }
    elif formats == 'GS8':
        # 灰度图格式解码
        encoded_data = base64.b64encode(byte_data).decode('utf-8')
        return {
            "type": "img",
            "format": "grayscale",
            "width": size[0],
            "height": size[1],
            "data": encoded_data,
        }

