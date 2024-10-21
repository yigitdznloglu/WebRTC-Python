import pytest
from server import Ball, BouncingBallVideoStreamTrack, Server

@pytest.fixture
def ball():
    return Ball(640, 480)

@pytest.fixture
def server():
    return Server()

@pytest.fixture
def video_stream_track(server):
    return BouncingBallVideoStreamTrack(server)

def test_ball_initial_position(ball):
    assert ball.x == 320
    assert ball.y == 240

def test_ball_move(ball):
    ball.move()
    assert ball.x == 325
    assert ball.y == 245

def test_ball_move_reverse_direction(ball):
    ball.x = ball.radius - 1
    ball.move()
    assert ball.dx == -5

@pytest.mark.asyncio
async def test_video_stream_track_recv(video_stream_track):
    frame = await video_stream_track.recv()
    assert frame.width == 640
    assert frame.height == 480
    assert frame.format.name == 'bgr24'

def test_server_send_real_coordinates(server):
    class MockChannel:
        def __init__(self):
            self.readyState = "open"
        def send(self, message):
            pass
    
    server.channel = MockChannel()
    server.send_real_coordinates(100, 150)
    assert True

def test_server_calculate_error(server):
    error_x, error_y = server.calculate_error(100, 150, 90, 140)
    assert error_x == 10
    assert error_y == 10
