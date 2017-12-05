from colouredballtracker import ColouredBallTracker
import time
from soundofcoloursocketserver import SoundOfColourSocketServer
import json

class SoundOfColour:
    def __init__(self):
        self.tracker = ColouredBallTracker()
        self.tracker.set_update_handler(lambda x=self: x.on_update())
        self.socket_server = None
        self.ball_count = None
        self.show_ui = False

    def on_update(self):
        self.tracker.show_ui(self.show_ui)
        balls = self.tracker.balls()
        self.send_balls_information(balls)

    def send_balls_information(self, balls):
        ball_info = []
        for ball in balls:
            ball_info.append([ball.id, ball.colour.name, int(ball.radius), int(ball.pos[0]), int(ball.pos[1])])
        self.send_to_client(dict(
            balls=ball_info,
            resolution=list(self.tracker.resolution())
        ), 'balls')

    def dict_to_json(self, message_dict):
        return json.dumps(message_dict, separators=(',', ':'))

    def send_to_client(self, message, type=None):
        message["type"] = type
        message_json = self.dict_to_json(message);
        self.socket_server.send_to_all(message_json)



    def on_client_connected(self, socket):
        print("client connected")
        socket.sendMessage('Welcome to Sound Of Colour Server!')

    def on_client_message(self, socket):
        print("client message: " + str(socket.data))
        message = json.loads(socket.data)
        if message["type"] == "show_ui":
            self.show_ui = bool(message["value"])

    def run(self):
        self.tracker.start()
        self.socket_server = SoundOfColourSocketServer(port=8001)
        self.socket_server.set_on_client_connected(lambda socket, x=self: x.on_client_connected(socket))
        self.socket_server.set_on_client_message(lambda socket, x=self: x.on_client_message(socket))
        while True:
            self.socket_server.serveonce()  # this is slow.... move to server
            if self.tracker.thread is None:
                break
            pass
        self.socket_server.close()


if __name__ == '__main__':
    soc = SoundOfColour()
    soc.run()
