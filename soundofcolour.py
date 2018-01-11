from colouredballtracker import ColouredBallTracker
from soundofcoloursocketserver import SoundOfColourSocketServer
import json
import cv2
import imageprocessing as imageprocessing
from properties import *
import traceback
import logging
from functools import reduce


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
            prop_all=self.on_message_prop_all,
            mouse=self.on_message_mouse,
            request_balls=self.on_message_request_balls,
            sample=self.on_message_sample
        )

        self.clients_requesting_balls = []
        self.clients_requesting_frames = []  # todo

    def on_prop_updated(self, prop: PropertyNode, from_runtime_change: bool = True):
        """
        Callback from our properties
        :param prop:
        :param from_runtime_change:
        :return:
        """
        if prop.type != PropNodeType.group:
            print("sending to clients: " + prop.path_as_str())
            self.send_to_all_clients(_type='prop', message=dict(
                path=prop.path_as_str(),
                value=prop.contents()
            ))

    def on_tracker_update(self):
        """
        Called by tracker when it gets more information on balls
        data is PUSHED, not polled.
        :return:
        """
        self.tracker.show_ui(self.show_ui)
        balls = self.tracker.balls()
        self.send_balls_information_to_clients(balls)

    def send_balls_information_to_clients(self, balls):
        if len(self.clients_requesting_balls) == 0:
            return
        ball_info = []
        for ball in balls:
            ball_info.append([ball.id, ball.colour.name, int(ball.radius), int(ball.pos[0]), int(ball.pos[1])])

        # only send to those that requested it!!!
        self.send_to_clients(self.clients_requesting_balls, 'balls', dict(
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

    def send_to_clients(self, clients, _type, message):
        message = self.create_json_message(_type, message)
        for socket in clients:
            socket.sendMessage(message)

    def send_to_client(self, socket, _type, message):
        socket.sendMessage(self.create_json_message(_type, message))

    def on_client_connected(self, socket):
        print("client connected")
        self.send_to_client(socket, 'welcome', dict())

    def on_client_closed(self, socket):
        if socket in self.clients_requesting_balls:
            self.clients_requesting_balls.remove(socket)

    def on_message_show_ui(self, message, socket, type):
        """
        Client triggers show_ui.
        //this is not a property as yet...
        :param message:
        :param socket:
        :param type:
        :return:
        """
        self.show_ui = bool(message["value"])

    def on_message_request_balls(self, message, socket, type):
        self.clients_requesting_balls.append(socket)

    def on_message_mouse(self, message, socket, type):
        event = message['event']
        x = float(message['x'])
        y = float(message['y'])
        if event == 'up':
            cv2event = cv2.EVENT_RBUTTONUP
        elif event == 'down':
            cv2event = cv2.EVENT_RBUTTONDOWN
        else:
            cv2event = cv2.EVENT_MOUSEMOVE
        width, height = self.tracker.resolution()

        print("mouse " + event + " " + str(x) + " " + str(y))

        self.tracker.mouse.handle_event(cv2event, int(width * x), int(height * y), None, None)

    def on_message_sample(self, message, socket, type):
        event = message['event']
        if event == 'colour':
            width, height = self.tracker.resolution()
            x = int(width * float(message['x']))
            y = int(height * float(message['y']))
            radius = int(width * float(message['radius']))
            hsv = self.tracker.sample_colour(x, y, radius)
            # print(str(hsv))
            return dict(hsv=hsv, event=event)
        elif event == 'histogram':
            width, height = self.tracker.resolution()
            x = int(width * float(message['x']))
            y = int(height * float(message['y']))
            radius = int(width * float(message['radius']))
            histogram = self.tracker.sample_histogram(x, y, radius)
            # print(str(histogram))
            pixel_count = reduce(lambda x, y: x + y, histogram[0])
            return dict(histogram=histogram, event=event, pixel_count=pixel_count)
        elif event == 'histogram_hsv':
            width, height = self.tracker.resolution()
            x = int(width * float(message['x']))
            y = int(height * float(message['y']))
            radius = int(width * float(message['radius']))
            histogram_hsv = self.tracker.sample_histogram_hsv(x, y, radius)
            # print(str(histogram))
            pixel_count = reduce(lambda x, y: x + y, histogram_hsv[0])
            return dict(histogram_hsv=histogram_hsv, event=event, pixel_count=pixel_count)

    def on_message_frame(self, message, socket, type):
        """
        Client requests last frame as base64 encoded image...
        :param message:
        :param socket:
        :param type:
        :return:
        """
        quality = 50
        if "quality" in message:
            quality = int(message["quality"])
        ratio = 1.0
        if "ratio" in message:
            ratio = float(message["ratio"])
        image_format = "jpg"
        if "format" in message:
            image_format = str(message["format"])

        image = imageprocessing.image_as_base64_encoded_image(
            self.tracker.last_frame,
            quality=quality,
            image_format=image_format, ratio=ratio)

        if image is not None:
            return dict(
                image=dict(
                    data=image,
                    format=image_format)
            )

    def on_message_stabilize(self, message, socket, type):
        """
        Client requests to start stabilizing image
        :param message:
        :param socket:
        :param type:
        :return:
        """
        self.tracker.state.start("stabilize")

    def on_message_prop(self, message, socket, type):
        """
        Client set a value of a property...
        :param message:
        :param socket:
        :param type:
        :return:
        """
        prop_path = message["path"]
        prop_value = message["value"]
        print("prop " + str(socket.data))
        self.tracker.properties.set_value_of(prop_path, value=prop_value, from_run_time=True)

    def on_message_prop_description(self, message, socket, type):
        """
        Client requests the properties this server holds. i.e. it's property API...
        :param message:
        :param socket:
        :param type:
        :return:
        """
        used_props = (self.tracker.properties, self.properties)
        description = collections.OrderedDict()
        for prop in used_props:
            description[prop.name] = prop.as_description()

        return description

    def on_message_prop_all(self, message, socket, type):
        """
        Client requests all the propery values for a specif property set...
        :param message:
        :param socket:
        :param type:
        :return:
        """
        which_prop = message['properties_name']
        p = None
        if which_prop == "coloured_ball_tracker":
            p = self.tracker.properties
        elif which_prop == "sound-of-colour":
            p = self.properties
        if p is not None:
            return p.contents()

    def on_client_message(self, socket):
        """
        receives a json messages and passes it to a message handler...
        :param socket:
        :return:
        """
        if socket.data == "undefined":
            return
        try:
            message = json.loads(socket.data)
        except json.JSONDecodeError:
            print("error decoding json: " + socket.data)
            return

        type = message["type"]

        if type in self.message_handlers:
            message_handler = self.message_handlers[type]

            try:
                data = message_handler(message, socket, type)
                if data is not None:
                    self.send_to_client(socket, type, data)

            except Exception as e:
                logging.error(traceback.format_exc())

        else:
            print("unknown message: " + str(socket.data))

    def run(self):
        try:
            self.tracker.start()
            self.socket_server = SoundOfColourSocketServer(port=8001)
            self.socket_server.set_on_client_connected(lambda socket, x=self: x.on_client_connected(socket))
            self.socket_server.set_on_client_message(lambda socket, x=self: x.on_client_message(socket))
            self.socket_server.set_on_client_closed(lambda socket, x=self: x.on_client_closed(socket))
            while True:
                self.socket_server.serveonce()  # this is slow.... move to server
                if self.tracker.is_thread_running() is False:
                    print("ColouredBallTracker was shut down by itself - closing whole program")
                    break

        except KeyboardInterrupt:
            print("CRTL + C -> starting to stop tracker...")
            pass
        except SystemExit:
            print("System Exit Called...")
            pass
        finally:
            self.tracker.stop_and_wait_until_stopped()
            self.socket_server.close()


if __name__ == '__main__':
    soc = SoundOfColour()
    soc.run()
