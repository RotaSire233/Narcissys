from ...driver_base import DriverBase
import asyncio
import sys
import os
import struct
from loguru import logger as log

class RtpHeader:
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

class RtpAudioDriver(DriverBase):
    def __init__(self, ip: str, port: int, audio_codec: str = "pcmu"):
        super().__init__(ip=ip,
                         port=port,
                         socket_type="rtp",
                         name="Audio RTP Driver",
                         max_thread=5,
                         max_cache_size=10 * 1024 * 1024)  # 音频缓存可以小一些
        
        self.audio_codec = audio_codec
        
        self.supported_codecs = {
            "pcmu": 0,     # G.711 μ-law
            "pcma": 8,     # G.711 A-law
            "opus": 111,   # OPUS
            "g722": 9,     # G.722
            "g729": 18     # G.729
        }
        
        log.info(f"{self.tag} RTP音频驱动初始化: IP={ip}, Port={port}, Codec={audio_codec}")
    
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
            
            await self._process_audio_frame(header, payload, addr)
            
        except Exception as e:
            log.error(f"{self.tag} RTP数据处理错误: {e}")
            log.debug(f"{self.tag} 错误数据: {data[:50]}...")
    
    async def _process_audio_frame(self, header, payload, addr):
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
        
        codec_type = None
        for codec, pt in self.supported_codecs.items():
            if pt == header.payload_type:
                codec_type = codec
                break
        
        await self._process_audio_payload(codec_type, header, payload, ssrc)
    
    async def _process_audio_payload(self, codec_type, header, payload, ssrc):
        if codec_type in ["pcmu", "pcma", "g722", "g729"]:
            await self._assemble_and_decode_frame(ssrc, payload, codec_type)
        
        elif codec_type == "opus":
            await self._process_opus_payload(header, payload, ssrc)
    
    async def _process_opus_payload(self, header, payload, ssrc):
        frame_key = f"frame_buffer_{ssrc}"
        frame_buffer = self._cache.get(frame_key)
        
        if frame_buffer is None:
            frame_buffer = []
            self._cache.put(frame_key, frame_buffer)
        
        await self._assemble_and_decode_frame(ssrc, payload, "opus")
    
    async def _assemble_and_decode_frame(self, ssrc, frame_data, codec_type):
        try:
            log.debug(f"{self.tag} 处理完整音频帧: SSRC={ssrc}, 大小={len(frame_data)} bytes, 编解码器={codec_type}")
        
            if codec_type in ["pcmu", "pcma", "g722", "g729", "opus"]:
                log.info(f"{self.tag} 成功处理{codec_type.upper()}音频帧: 大小={len(frame_data)} bytes")
                await self._on_audio_frame(frame_data, ssrc, codec_type)
            
        except Exception as e:
            log.error(f"{self.tag} 音频帧处理错误: {e}")
    
    async def _on_audio_frame(self, frame_data, ssrc, codec_type):
        """音频帧就绪回调"""
        log.debug(f"{self.tag} 音频帧就绪: SSRC={ssrc}, 大小={len(frame_data)} bytes, 编解码器={codec_type}")
    
    async def connection_made(self, transport):
        log.info(f"{self.tag} RTP连接建立: {transport}")
    
    async def connection_lost(self, addr, exc):
        log.info(f"{self.tag} RTP连接丢失: {addr}, 错误: {exc}")
        log.debug(f"{self.tag} RTP连接资源清理")