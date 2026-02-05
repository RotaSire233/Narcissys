import asyncio
from loguru import logger as log
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRecorder

class RtpProtocol:
    def __init__(self, driver):
        self.driver = driver
        self.pcs = set()
        self.tracks = {}
        
    async def connection_made(self, transport):
        self.driver._transport = transport
        log.info(f"{self.driver.tag} RTP服务已启动,监听 {self.driver.ip}:{self.driver.port}")
    
    async def datagram_received(self, data, addr):
        asyncio.create_task(self.driver._recv_queue.put((data, addr)))
        asyncio.create_task(self.driver.data_received(data, addr))
    
    async def create_peer_connection(self):
        pc = RTCPeerConnection()
        self.pcs.add(pc)
        
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            if pc.iceConnectionState == "failed":
                await pc.close()
                self.pcs.discard(pc)
        
        return pc
    
    async def add_track(self, pc, track_id, track):
        """Add a media track to the peer connection"""
        self.tracks[track_id] = track
        pc.addTrack(track)
    
    async def offer(self, pc):
        """Create an offer"""
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        return pc.localDescription
    
    async def answer(self, pc, offer):
        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer["sdp"], type=offer["type"]))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        return pc.localDescription
    
    async def set_remote_description(self, pc, description):
        await pc.setRemoteDescription(RTCSessionDescription(sdp=description["sdp"], type=description["type"]))
    
    async def connection_lost(self, exc):
        if exc:
            log.error(f"{self.driver.tag} RTP连接丢失: {exc}")
        else:
            log.info(f"{self.driver.tag} RTP连接已关闭")
        
        # Close all peer connections
        for pc in self.pcs:
            await pc.close()
        self.pcs.clear()
        self.tracks.clear()