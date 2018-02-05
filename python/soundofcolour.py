from colouredballtracker import ColouredBallTracker
from python.soundofcoloursocketserver import SoundOfColourSocketServer
import cv2
import imageprocessing as imageprocessing
from properties import *
import traceback
import logging
from functools import reduce
from collections import OrderedDict


class TaskPerFrame:
    def __init__(self, id, task, data, client=None):
        self.task = task
        self.id = id
        self.data = data
        self.client = client
        self.result = None

    def update(self, data):
        self.data = data


class SoundOfColour(PropertiesListener):
    def __init__(self):
        self.tracker = ColouredBallTracker()
        #  self.tracker.set_update_handler(lambda x=self: x.on_tracker_update())
        self.tracker.set_frame_handler(lambda y, x=self: x.on_tracker_frame(y))

        self.socket_server = None  # type: SoundOfColourSocketServer
        # self.show_ui = False

        self.properties = Properties('sound-of-colour')

        self.tracker.properties.add_listener(self)

        self.message_handlers = dict(
            show_ui=self.on_message_show_ui,
            stabilize=self.on_message_stabilize,
            prop=self.on_message_prop,
            prop_description=self.on_message_prop_description,
            prop_all=self.on_message_prop_all,
            mouse=self.on_message_mouse,
            tasks_per_frame=self.on_message_tasks_per_frame
        )

        self.tasks_per_frame = OrderedDict()

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

    def on_tracker_frame(self, frame_count):
        """
        Called by tracker when a new video frame was processed.

        we look at all the tasks (per client) that need to be done and send each client what it needs...

        tasks are setup using the tasks_per_frame message
        :return:
        """
        if len(self.tasks_per_frame) == 0:
            # print(str(frame_count))
            return

        # now we build up all the tasks out clients want us to send / per frame.
        clients = []
        for task in list(self.tasks_per_frame.values()):
            result = None
            taskname = task.task
            if taskname == "frame":
                result = self.task_frame_as_result(task.data, frame_count)
            elif taskname == "balls":
                result = self.task_balls_as_result(task.data, frame_count)
            elif taskname == "sample":
                result = self.task_sample_as_result(task.data, frame_count)
            elif taskname == "track":
                result = self.task_track_as_result(task.data, frame_count)
            if result is not None:
                task.result = dict(
                    task=taskname,
                    result=result
                )
                if task.client not in clients:
                    clients.append(task.client)

        # collate messages per client...
        for client in clients:
            messages = []
            for task in list(self.tasks_per_frame.values()):
                if client is task.client:
                    messages.append(task.result)
            self.send_to_client(client, _type="tasks_per_frame", message=dict(tasks=messages))

    def task_frame_as_result(self, setup, frame_count):
        modulus = self.as_int(setup, "modulus", 1)
        if frame_count % modulus != 0:
            return

        quality = self.as_int(setup, "quality", 50)
        ratio = self.as_float(setup, "ratio", 1.0)
        image_format = self.as_str(setup, "format", "jpg")

        image = imageprocessing.image_as_base64_encoded_image(
            self.tracker.frame,
            quality=quality,
            image_format=image_format, ratio=ratio)

        if image is not None:
            return dict(
                image=dict(
                    data=image,
                    format=image_format)
            )

    def task_balls_as_result(self, setup, frame_count):
        ball_info = [self.ball_to_ball_info(x) for x in self.tracker.balls()]
        return dict(
            balls=ball_info,
            resolution=list(self.tracker.resolution())
        )

    def ball_to_ball_info(self, ball):
        return [ball.id, ball.colour.name, int(ball.radius), int(ball.pos[0]), int(ball.pos[1])]

    def task_track_as_result(self, setup, frame_count):
        colour = setup['colour'];
        first_match_ball = next((x for x in self.tracker.balls() if x.colour.name == colour), None)
        if first_match_ball is not None:
            histogram_hsv = self.tracker.sample_histogram_hsv(
                int(first_match_ball.pos[0]),
                int(first_match_ball.pos[1]),
                int(first_match_ball.radius))
            return dict(histogram_hsv=histogram_hsv, ball=self.ball_to_ball_info(first_match_ball) )
        return None

    def task_sample_as_result(self, setup, frame_count):

        width, height = self.tracker.resolution()
        x = int(width * float(setup['x']))
        y = int(height * float(setup['y']))
        radius = int(width * float(setup['radius']))

        event = setup['event']
        if event == 'colour':
            hsv = self.tracker.sample_colour(x, y, radius)
            # print(str(hsv))
            return dict(hsv=hsv, event=event)
        elif event == 'histogram':
            histogram = self.tracker.sample_histogram(x, y, radius)
            # print(str(histogram))
            pixel_count = reduce(lambda x, y: x + y, histogram[0])
            return dict(histogram=histogram, event=event, pixel_count=pixel_count)
        elif event == 'histogram_hsv':
            histogram_hsv = self.tracker.sample_histogram_hsv(x, y, radius)
            # print(str(histogram))
            pixel_count = reduce(lambda x, y: x + y, histogram_hsv[0])
            return dict(histogram_hsv=histogram_hsv, event=event, pixel_count=pixel_count)

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

    def on_client_closed(self, socket):
        tasks_to_remove = []
        for task in list(
                self.tasks_per_frame.values()):  # this caused threading issues when modifying when iterating...
            if task.client is socket:
                tasks_to_remove.append(task.id)
        print("Client Closing, removing tasks related to client #" + str(len(tasks_to_remove)))
        for id in tasks_to_remove:
            self.stop_task(id)

    def on_message_show_ui(self, message, socket, type):
        self.tracker.show_ui(bool(message["value"]))  # should this be a message that is async?

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

        # we FAKE a mouse event here...
        self.tracker.mouse.handle_event(cv2event, int(width * x), int(height * y), None, None)

    def on_message_tasks_per_frame(self, message, socket, type):
        """
        Called to setup/stop/update a task that the server should send after each frame...

        JSON would look like

        {
            "tasks": [
                {
                    "task": "frame",
                    "id": 458,
                    "state": "start" | "stop" | "update",
                    "data" : {
                       .....
                    }
                }

            ]
        }

        :param message:
        :param socket:
        :param type:
        :return:
        """
        tasks = message['tasks']
        for task_info in tasks:
            state = task_info['state']  # state
            id = task_info['id']  # must be globally unique
            if state == 'start':
                if id in self.tasks_per_frame:
                    print("cannot start a task per frame that is already running")
                    return
                task = TaskPerFrame(id, task_info['task'], task_info['data'], client=socket)
                print("starting task " + str(task_info['task']))
                self.tasks_per_frame[id] = task
            elif state == 'stop':
                self.stop_task(id)

            elif state == 'update':
                if id not in self.tasks_per_frame:
                    print("cannot update a task per frame that is already running")
                    return
                # print("update task " + str(task_info['task']))
                self.tasks_per_frame[id].update(task_info['data'])

    def stop_task(self, id):
        if id not in self.tasks_per_frame:
            print("cannot stop a task per frame that is not running")
            return
        task = self.tasks_per_frame[id]
        print("stop task " + task.task)
        self.tasks_per_frame.pop(id)

    # def on_message_sample(self, message, socket, type):

    def get_prop(self, obj=None, key=None, ):
        if obj is None:
            return None
        if key is None:
            return None
        if key in obj:
            return obj[key]
        return None

    def as_int(self, obj=None, key=None, default=None):
        val = self.get_prop(obj, key)
        if val is None:
            return default
        return int(val)

    def as_float(self, obj=None, key=None, default=None):
        val = self.get_prop(obj, key)
        if val is None:
            return default
        return float(val)

    def as_str(self, obj=None, key=None, default=None):
        val = self.get_prop(obj, key)
        if val is None:
            return default
        return str(val)

    # def frame_as_message(self, quality: int = 50, ratio: float = 1.0, image_format: str = "jpg"):

    def on_message_stabilize(self, message, socket, type):
        self.tracker.state.start("stabilize")

    def on_message_prop(self, message, socket, type):
        prop_path = message["path"]
        prop_value = message["value"]
        print("prop " + str(socket.data))
        self.tracker.properties.set_value_of(prop_path, value=prop_value, from_run_time=True)

    def on_message_prop_description(self, message, socket, type):
        used_props = (self.tracker.properties, self.properties)
        description = collections.OrderedDict()
        for prop in used_props:
            description[prop.name] = prop.as_description()

        return description

    def on_message_prop_all(self, message, socket, type):
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
                # todo combine all events that need to occur on Main thread into a single Queue or other mechanism
                self.socket_server.serveonce()  # handle all socket server events
                if self.tracker.perform_main_thread_events_and_check_if_need_to_quit():  # handle all tracker event, including UI.
                    break

        except KeyboardInterrupt:
            print("CRTL + C -> starting to stop tracker...")
            pass

        print("Closing socket server...")
        self.socket_server.close()

        print("Closing Coloured Ball Tracker...")
        self.tracker.stop_and_wait_until_stopped()




if __name__ == '__main__':

    soc = SoundOfColour()
    soc.run()

