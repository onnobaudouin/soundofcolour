from colouredballtracker import ColouredBallTracker
import time
from soundofcoloursocketserver import SoundOfColourSocketServer
import json
import cv2
import base64
import numpy as np


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

    def get_last_frame_as_base64_encoded_image(self, quality=20, format="jpg", ratio=1.0):
        image = self.tracker.last_frame
        if image is None:
            return None
        encode_as = ".jpg"
        if format == "png":
            encode_as = ".png"

        if ratio != 1.0:
            if ratio <= 0.01 or ratio > 1:
                return None
            new_size = (int(image.shape[1] * ratio), int(image.shape[0] * ratio))
            image = cv2.resize(image, new_size, interpolation=cv2.INTER_LINEAR)  # INTER_CUBIC | INTER_LINEAR | INTER_AREA

        if encode_as == ".jpg":
            ret, buf = cv2.imencode(encode_as, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        else:
            ret, buf = cv2.imencode(encode_as, image)

        if ret is True:
            return str(base64.b64encode(buf).decode())
        else:
            return None

    def send_balls_information(self, balls):
        ball_info = []
        for ball in balls:
            ball_info.append([ball.id, ball.colour.name, int(ball.radius), int(ball.pos[0]), int(ball.pos[1])])
        self.send_to_client('balls', dict(
            balls=ball_info,
            resolution=list(self.tracker.resolution())
        ))

    def dict_to_json(self, message_dict):
        return json.dumps(message_dict, separators=(',', ':'))

    def send_to_client(self, _type, message):
        message["type"] = _type
        message_json = self.dict_to_json(message);
        self.socket_server.send_to_all(message_json)

    def on_client_connected(self, socket):
        print("client connected")
        socket.sendMessage('Welcome to Sound Of Colour Server!')

    def on_client_message(self, socket):
        message = json.loads(socket.data)
        type = message["type"]
        if type == "show_ui":
            self.show_ui = bool(message["value"])
            print("client message: " + str(socket.data))
        elif type == "frame":
            quality = 50
            if "quality" in message:
                quality = int(message["quality"])
            ratio = 1.0
            if "ratio" in message:
                ratio = float(message["ratio"])
            format = "jpg"
            if "format" in message:
                format = str(message["format"])

            image = self.get_last_frame_as_base64_encoded_image(quality=quality, format=format, ratio=ratio)
            if image is not None:
                self.send_to_client("frame", dict(
                    image=dict(
                        data=image,
                        format=format)
                ))
        elif type == "stabilize":
            self.tracker.state.start("stabilize")

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
