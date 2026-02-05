from ...driver_base import DriverBase
import asyncio
import sys
import os
import struct
from loguru import logger as log
from aiortc import MediaStreamTrack
from av import VideoFrame

class RtpHeader:
    """RTP头部解析"""
    def __init__(self, data):

        self.version = (data[0] >> 6) & 0x03
        self.padding = (data[0] >> 5) & 0x01
        self.extension = (data[0] >> 4) & 0x01
        self.cc = data[0] & 0x0F
        self.marker = (data[1] >> 7) & 0x01
        self.payload_type = data[1] & 0x7F
        self.sequence_number = struct.unpack('!H', data[2:4])[0]
        self.timestamp = struct.unpack('!I', data[4:8])[0]
        self.ssrc = struct.unpack('!I', data[8:12])[0]
        
        self.csrc_list = []
        offset = 12
        if self.cc > 0:
            self.csrc_list = struct.unpack(f'!{self.cc}I', data[offset:offset + self.cc * 4])
            offset += self.cc * 4
        
        self.extension_header = None
        if self.extension:
            ext_profile = struct.unpack('!H', data[offset:offset + 2])[0]
            ext_length = struct.unpack('!H', data[offset + 2:offset + 4])[0]
            ext_data = data[offset + 4:offset + 4 + ext_length * 4]
            self.extension_header = (ext_profile, ext_length, ext_data)
            offset += 4 + ext_length * 4
        
        self.payload_offset = offset

class RtpDriver(DriverBase):
    def __init__(self, ip: str, port: int, video_codec: str = "h264"):
        super().__init__(ip=ip,
                         port=port,
                         socket_type="rtp",
                         name="Video RTP Driver",
                         max_thread=5,
                         max_cache_size=50 * 1024 * 1024)
        
        self.video_codec = video_codec
        
        self.supported_codecs = {
            "h264": 96,
            "vp8": 97,
            "vp9": 98,
            "h265": 99
        }
        
        log.info(f"{self.tag} RTP视频驱动初始化: IP={ip}, Port={port}, Codec={video_codec}")
    
    async def data_received(self, data, addr):
        try:
            header = RtpHeader(data)
            
            if header.version != 2:
                log.warning(f"{self.tag} 不支持的RTP版本: {header.version}")
                return
            
            payload = data[header.payload_offset:]
            
            if header.payload_type not in self.supported_codecs.values():
                log.debug(f"{self.tag} 未知的负载类型: {header.payload_type}")
                return
            
            await self._process_video_frame(header, payload, addr)
            
        except Exception as e:
            log.error(f"{self.tag} RTP数据处理错误: {e}")
            log.debug(f"{self.tag} 错误数据: {data[:50]}...")
    
    async def _process_video_frame(self, header, payload, addr):
        ssrc = header.ssrc
        
        seq_key = f"seq_info_{ssrc}"
        seq_info = self._cache.get(seq_key)
        
        if seq_info is None:
            seq_info = {
                "last_seq": -1,
                "expected_seq": -1
            }
            self._cache.put(seq_key, seq_info)
        
        if seq_info["last_seq"] == -1:
            seq_info["last_seq"] = header.sequence_number
            seq_info["expected_seq"] = header.sequence_number + 1
        else:
            if header.sequence_number != seq_info["expected_seq"]:
                lost_packets = (header.sequence_number - seq_info["expected_seq"]) % 65536
                if lost_packets > 0 and lost_packets < 100: 
                    log.warning(f"{self.tag} RTP包丢失: SSRC={ssrc}, 预期={seq_info['expected_seq']}, 实际={header.sequence_number}, 丢失={lost_packets}")
            
            seq_info["last_seq"] = header.sequence_number
            seq_info["expected_seq"] = (header.sequence_number + 1) % 65536
        
        self._cache.put(seq_key, seq_info)
        
        if self.video_codec == "h264":
            await self._process_h264_payload(header, payload, ssrc)
        elif self.video_codec == "vp8":
            await self._process_vp8_payload(header, payload, ssrc)
        elif self.video_codec == "vp9":
            await self._process_vp9_payload(header, payload, ssrc)
        elif self.video_codec == "h265":
            await self._process_h265_payload(header, payload, ssrc)
    
    async def _process_h264_payload(self, header, payload, ssrc):

        frame_key = f"frame_buffer_{ssrc}"
        frame_buffer = self._cache.get(frame_key)
        
        if frame_buffer is None:
            frame_buffer = []
            self._cache.put(frame_key, frame_buffer)

        if len(payload) > 0:
            nal_type = (payload[0] & 0x1F)
            
            if nal_type == 0:
                return
            elif nal_type == 24:
                offset = 1
                while offset < len(payload):
                    nal_length = struct.unpack('!H', payload[offset:offset+2])[0]
                    offset += 2
                    nal_unit = payload[offset:offset+nal_length]
                    frame_buffer.append(nal_unit)
                    offset += nal_length
            elif nal_type == 25:

                log.warning(f"{self.tag} 不支持STAP-B格式")
            elif nal_type == 26:

                log.warning(f"{self.tag} 不支持MTAP16格式")
            elif nal_type == 27:

                log.warning(f"{self.tag} 不支持MTAP24格式")
            elif nal_type == 28:
                if len(payload) < 2:
                    return
                
                fu_header = payload[1]
                start_bit = (fu_header & 0x80) != 0
                end_bit = (fu_header & 0x40) != 0
                nal_type = (fu_header & 0x1F)
                
                nal_header = bytes([(payload[0] & 0xE0) | nal_type])
                nal_unit = nal_header + payload[2:]
                
                if start_bit:
                    frame_buffer = []
                    self._cache.put(frame_key, frame_buffer)
                    
                frame_buffer.append(nal_unit)
                
                if end_bit:
                    await self._assemble_and_decode_frame(ssrc, b''.join(frame_buffer))
            elif nal_type == 29:

                log.warning("不支持FU-B格式")
            else:
                frame_buffer = [payload]
                self._cache.put(frame_key, frame_buffer)
                await self._assemble_and_decode_frame(ssrc, payload)
    
    async def _process_vp8_payload(self, header, payload, ssrc):
        frame_key = f"frame_buffer_{ssrc}"
        frame_buffer = self._cache.get(frame_key)
        
        if frame_buffer is None:
            frame_buffer = []
            self._cache.put(frame_key, frame_buffer)
        
        if len(payload) < 1:
            return
        
        vp8_header = payload[0]
        start_bit = (vp8_header & 0x10) != 0
        partition_id = vp8_header & 0x0F
        
        if start_bit:
            frame_buffer = [payload]
            self._cache.put(frame_key, frame_buffer)
        else:
            frame_buffer.append(payload)
        
        if header.marker:
            await self._assemble_and_decode_frame(ssrc, b''.join(frame_buffer))
    
    async def _process_vp9_payload(self, header, payload, ssrc):
        log.warning(f"{self.tag} VP9解码功能尚未完全实现")
    
    async def _process_h265_payload(self, header, payload, ssrc):
        log.warning(f"{self.tag} H.265解码功能尚未完全实现")
    
    async def _assemble_and_decode_frame(self, ssrc, frame_data):
        try:
            log.debug(f"{self.tag} 处理完整视频帧: SSRC={ssrc}, 大小={len(frame_data)} bytes")
            
            if self.video_codec == "h264":
                try:
                    import av

                    packet = av.Packet(frame_data)
                    packet.stream = None
                    
                    log.info(f"{self.tag} 成功处理H.264帧: 大小={len(frame_data)} bytes")
                    
                    await self._on_video_frame(frame_data, ssrc)
                    
                except Exception as e:
                    log.error(f"{self.tag} H.264帧处理错误: {e}")
            
        except Exception as e:
            log.error(f"{self.tag} 视频帧解码错误: {e}")
    
    async def _on_video_frame(self, frame_data, ssrc):
        log.debug(f"{self.tag} 视频帧就绪: SSRC={ssrc}, 大小={len(frame_data)} bytes")
    
    async def connection_made(self, transport):
        log.info(f"{self.tag} RTP连接建立: {transport}")
    
    async def connection_lost(self, addr, exc):
        log.info(f"{self.tag} RTP连接丢失: {addr}, 错误: {exc}")
        
        log.debug(f"{self.tag} RTP连接资源清理")