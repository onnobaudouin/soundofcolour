from colouredballtracker import ColouredBallTracker
import time
from soundofcoloursocketserver import SoundOfColourSocketServer


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
        # count = len(balls)
        # if count != self.ball_count:
        #    self.ball_count = count
        #    print('number of balls: ' + str(len(balls)))
        messages = []
        for ball in balls:
            msg = [ball.id, ball.colour.name, ball.radius, int(ball.pos[0]), int(ball.pos[1])]
            msg = ",".join([str(i) for i in msg])
            messages.append(msg)
        message = ";".join(messages)
        if message != "":
            width, height = self.tracker.resolution()
            message = str(width) + ';' + str(height) + ";" +  message

            self.socket_server.send_to_all(message)

    def on_client_connected(self, socket):
        print("client connected")
        socket.sendMessage('Welcome to Sound Of Colour Server!')

    def on_client_message(self, socket):
        print("client message: " + str(socket.data))
        message = socket.data
        if message == "show_ui":
            self.show_ui = True

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
