import pytest
import numpy as np
import multiprocessing
import cv2
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiortc.contrib.signaling import BYE
from client import process_a, run, consume_signaling

@pytest.fixture
def frame_queue():
    return multiprocessing.Queue()

@pytest.fixture
def shared_values():
    x = multiprocessing.Value('i', 0)
    y = multiprocessing.Value('i', 0)
    return x, y

def test_process_a(frame_queue, shared_values):
    x, y = shared_values

    img = np.zeros((480, 640, 3), np.uint8)
    cv2.circle(img, (320, 240), 20, (255, 255, 255), -1)
    frame_data = img.tobytes()
    frame_queue.put((frame_data, 0))
    frame_queue.put(None)

    process_a(frame_queue, x, y)

    assert abs(x.value - 320) <= 2
    assert abs(y.value - 240) <= 2

@pytest.mark.asyncio
async def test_run(shared_values):
    pc = MagicMock()
    signaling = AsyncMock()
    frame_queue = multiprocessing.Queue()
    x, y = shared_values

    video_frame = MagicMock()
    video_frame.to_ndarray.return_value = np.zeros((480, 640, 3), np.uint8)
    video_frame.time = 0

    track = MagicMock()
    track.recv = AsyncMock(return_value=video_frame)

    pc.getReceivers = MagicMock(return_value=[MagicMock(track=track)])

    @pc.on("track")
    async def on_track(track):
        if track.kind == "video":
            while True:
                try:
                    frame = await track.recv()
                    img = frame.to_ndarray(format="bgr24")
                    cv2.imshow("Received Video", img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                    frame_data = frame.to_ndarray(format="bgr24").tobytes()
                    frame_queue.put((frame_data, frame.time))
                    await asyncio.sleep(0)
                except Exception as e:
                    break

    async def mock_consume_signaling(pc, signaling):
        await asyncio.sleep(1)
        await signaling.send(BYE)

    with patch('client.consume_signaling', mock_consume_signaling):
        await run(pc=pc, signaling=signaling, role='answer', frame_queue=frame_queue)

    signaling.connect.assert_called()

    frame_queue.put((video_frame.to_ndarray.return_value.tobytes(), video_frame.time))
    frame_queue.put(None)

    process = multiprocessing.Process(target=process_a, args=(frame_queue, x, y))
    process.start()
    process.join()

    assert x.value == 0
    assert y.value == 0

def test_process_a_no_contours(frame_queue, shared_values):
    x, y = shared_values

    img = np.zeros((480, 640, 3), np.uint8)
    frame_data = img.tobytes()
    frame_queue.put((frame_data, 0))
    frame_queue.put(None)

    process_a(frame_queue, x, y)

    assert x.value == 0
    assert y.value == 0
