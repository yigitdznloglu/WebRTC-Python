import argparse
import asyncio
import logging
import fractions
import time
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling, BYE
from av import VideoFrame

class Ball:
    """A class to represent a ball moving within a frame."""
    
    def __init__(self, width, height, radius=20):
        self.width = width
        self.height = height
        self.radius = radius
        self.x = width // 2
        self.y = height // 2
        self.dx = 5
        self.dy = 5

    def move(self):
        """Move the ball within the frame, reversing direction upon hitting edges."""
        if self.x - self.radius < 0 or self.x + self.radius > self.width:
            self.dx = -self.dx
        if self.y - self.radius < 0 or self.y + self.radius > self.height:
            self.dy = -self.dy

        self.x += self.dx
        self.y += self.dy

class BouncingBallVideoStreamTrack(VideoStreamTrack):
    """A class to represent a video stream track of a bouncing ball."""
    
    def __init__(self, server):
        super().__init__()
        self.kind = "video"
        self.ball = Ball(640, 480)
        self.server = server
        self.frame_width = 640
        self.frame_height = 480

    async def next_timestamp(self):
        """Calculate the next timestamp for the video frame."""
        self._timestamp += int(1 / 30 * 90000)
        wait = self._start + (self._timestamp / 90000) - time.time()
        await asyncio.sleep(wait)

    async def recv(self):
        """Generate and return the next video frame with the ball's current position."""
        if not hasattr(self, "_start"):
            self._start = time.time()
            self._timestamp = 0
        else:
            await self.next_timestamp()

        frame = np.zeros((self.frame_height, self.frame_width, 3), np.uint8)
        self.ball.move()
        cv2.circle(frame, (self.ball.x, self.ball.y), self.ball.radius, (0, 255, 0), -1)
        video_frame = VideoFrame.from_ndarray(frame, format='bgr24')
        video_frame.pts = self._timestamp
        video_frame.time_base = fractions.Fraction(1, 90000)

        self.server.send_real_coordinates(self.ball.x, self.ball.y)
        
        return video_frame

class Server:
    """A class to represent the server handling WebRTC connections."""
    
    def __init__(self):
        self.pc = RTCPeerConnection()
        self.recorder = MediaBlackhole()
        self.channel = None

    def send_real_coordinates(self, x, y):
        """Send real coordinates of the ball to the client via the data channel."""
        if self.channel and self.channel.readyState == "open":
            message = "coords,%d,%d" % (x, y)
            self.channel.send(message)

    def calculate_error(self, real_x, real_y, calc_x, calc_y):
        """Calculate and print the error between real and calculated coordinates."""
        error_x = real_x - calc_x
        error_y = real_y - calc_y
        print(f"Error: X = {error_x}, Y = {error_y}")
        return error_x, error_y

    async def run(self, signaling, role):
        """Run the server to handle WebRTC connections and media streams."""
        def add_tracks():
            self.pc.addTrack(BouncingBallVideoStreamTrack(self))

        @self.pc.on("track")
        def on_track(track):
            self.recorder.addTrack(track)

        await signaling.connect()

        self.channel = self.pc.createDataChannel("chat")

        @self.channel.on("message")
        def on_message(message):
            try:
                parts = message.split(",")
                if parts[0] == "calculated":
                    real_x, real_y, calc_x, calc_y = map(int, parts[1:])
                    self.calculate_error(real_x, real_y, calc_x, calc_y)
            except Exception as e:
                pass

        if role == "offer":
            add_tracks()
            await self.pc.setLocalDescription(await self.pc.createOffer())
            await signaling.send(self.pc.localDescription)

        await consume_signaling(self.pc, signaling)

async def consume_signaling(pc, signaling):
    """Consume signaling messages from the signaling server."""
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            if obj.type == "offer":
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--verbose", "-v", action="count")
    add_signaling_arguments(parser)
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    signaling = create_signaling(args)
    server = Server()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(server.run(signaling, args.role))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(server.recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(server.pc.close())
