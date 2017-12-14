from colouredballtracker import ColouredBallTracker
from soundofcoloursocketserver import SoundOfColourSocketServer
import json
import cv2
import base64
from properties import *
import traceback
import logging


class SoundOfColour(PropertiesListener):
    def __init__(self):
        self.tracker = ColouredBallTracker()
        self.tracker.set_update_handler(lambda x=self: x.on_tracker_update())
        self.socket_server = None
        self.ball_count = None
        self.show_ui = False

        self.properties = Properties('sound-of-colour')

        self.tracker.properties.add_listener(self)

        self.message_handlers = dict(
            show_ui=self.on_message_show_ui,
            frame=self.on_message_frame,
            stabilize=self.on_message_stabilize,
            prop=self.on_message_prop,
            prop_description=self.on_message_prop_description,
            prop_all=self.on_message_prop_all
        )

    def on_prop_updated(self, prop: PropertyNode, from_runtime_change: bool=True):
        #if from_runtime_change is False:
        #    print("Prop changed but was non-ui")
        #    return
        if prop.type != PropNodeType.group:
            print("sending to clients: " + prop.path_as_str())
            self.send_to_all_clients(_type='prop', message=dict(
                path=prop.path_as_str(),
                value=prop.contents()
            ))

    def on_tracker_update(self):
        self.tracker.show_ui(self.show_ui)
        balls = self.tracker.balls()
        self.send_balls_information_to_all_clients(balls)

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
            image = cv2.resize(image, new_size,
                               interpolation=cv2.INTER_LINEAR)  # INTER_CUBIC | INTER_LINEAR | INTER_AREA

        if encode_as == ".jpg":
            ret, buf = cv2.imencode(encode_as, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        else:
            ret, buf = cv2.imencode(encode_as, image)

        if ret is True:
            return str(base64.b64encode(buf).decode())
        else:
            return None

    def send_balls_information_to_all_clients(self, balls):
        ball_info = []
        for ball in balls:
            ball_info.append([ball.id, ball.colour.name, int(ball.radius), int(ball.pos[0]), int(ball.pos[1])])
        self.send_to_all_clients('balls', dict(
            balls=ball_info,
            resolution=list(self.tracker.resolution())
        ))

    def dict_to_json(self, message_dict):
        return json.dumps(message_dict, separators=(',', ':'))

    def create_json_message(self, _type, message_dict):
        message_dict["type"] = _type
        return self.dict_to_json(message_dict)

    def send_to_all_clients(self, _type, message):
        self.socket_server.send_to_all(self.create_json_message(_type, message))

    def send_to_client(self, socket, _type, message):
        socket.sendMessage(self.create_json_message(_type, message))

    def on_client_connected(self, socket):
        print("client connected")
        self.send_to_client(socket, 'welcome', dict())

    def on_message_show_ui(self, message, socket, type):
        self.show_ui = bool(message["value"])

    def on_message_frame(self, message, socket, type):
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
            self.send_to_client(socket, "frame", dict(
                image=dict(
                    data=image,
                    format=format)
            ))

    def on_message_stabilize(self, message, socket, type):
        self.tracker.state.start("stabilize")

    def on_message_prop(self, message, socket, type):
        prop_path = message["path"]
        prop_value = message["value"]
        print("prop " + str(socket.data))
        self.tracker.properties.set_value_of(prop_path, value=prop_value, from_run_time=False)


    def on_message_prop_description(self, message, socket, type):
        used_props = (self.tracker.properties, self.properties)
        description = collections.OrderedDict()
        for prop in used_props:
            description[prop.name] = prop.as_description()
        self.send_to_client(socket, type, description)

    def on_message_prop_all(self, message, socket, type):
        which_prop = message['properties_name']
        p = None
        if which_prop == "coloured_ball_tracker":
            p = self.tracker.properties
        elif which_prop == "sound-of-colour":
            p = self.properties
        if p is not None:
            self.send_to_client(socket, type, p.contents())

    def on_client_message(self, socket):
        if socket.data == "undefined":
            return
        try:
            message = json.loads(socket.data)
        except json.JSONDecodeError:
            print("error decoding json: " + socket.data)
            return

        type = message["type"]
        if type in self.message_handlers:
            fun = self.message_handlers[type]
            try:
                fun(message, socket, type)
            except Exception as e:
                logging.error(traceback.format_exc())

        else:
            print("unknown message: " + str(socket.data))

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
