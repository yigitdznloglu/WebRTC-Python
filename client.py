import argparse
import asyncio
import logging
import cv2
import numpy as np
import multiprocessing
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaBlackhole
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling, BYE

def process_a(frame_queue, x, y):
    """Process frames to detect the ball and update coordinates."""
    while True:
        item = frame_queue.get()
        if item is None:
            break
        
        frame_data, frame_timestamp = item
        img = np.frombuffer(frame_data, dtype=np.uint8).reshape((480, 640, 3))
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (15, 15), 0)
        edges = cv2.Canny(blurred, 30, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                with x.get_lock():
                    x.value = cx
                with y.get_lock():
                    y.value = cy

async def run(pc, signaling, role, frame_queue):
    """Run the client to handle WebRTC connections and media streams."""
    def add_tracks():
        pass

    @pc.on("track")
    async def on_track(track):
        if track.kind == "video":
            while True:
                try:
                    frame = await track.recv()
                    img = frame.to_ndarray(format="bgr24")
                    cv2.imshow("Ball", img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    
                    frame_data = frame.to_ndarray(format="bgr24").tobytes()
                    frame_queue.put((frame_data, frame.time))
                    await asyncio.sleep(0)
                except Exception as e:
                    break

    await signaling.connect()

    @pc.on("datachannel")
    def on_datachannel(channel):
        real_x, real_y = 0, 0

        async def send_coordinates():
            while True:
                with x.get_lock():
                    with y.get_lock():
                        coords = "%d, %d" % (x.value, y.value)
                        channel.send("calculated,%d,%d,%s" % (real_x, real_y, coords))
                await asyncio.sleep(0.033)

        @channel.on("message")
        def on_message(message):
            nonlocal real_x, real_y
            parts = message.split(",")
            if parts[0] == "coords":
                real_x, real_y = int(parts[1]), int(parts[2])

        asyncio.ensure_future(send_coordinates())

    await consume_signaling(pc, signaling)

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
    pc = RTCPeerConnection()
    recorder = MediaBlackhole()

    frame_queue = multiprocessing.Queue()
    x = multiprocessing.Value('i', 0)  # Shared value for x coordinate
    y = multiprocessing.Value('i', 0)  # Shared value for y coordinate
    process = multiprocessing.Process(target=process_a, args=(frame_queue, x, y))
    process.start()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run(pc=pc, signaling=signaling, role=args.role, frame_queue=frame_queue))
    except KeyboardInterrupt:
        pass
    finally:
        frame_queue.put(None)
        process.join()
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())
