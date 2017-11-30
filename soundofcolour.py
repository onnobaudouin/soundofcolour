from colouredballtracker import ColouredBallTracker
import time
from soundofcoloursocketserver import SoundOfColourSocketServer


class SoundOfColour:
    def __init__(self):
        self.tracker = ColouredBallTracker()
        self.tracker.set_update_handler(lambda x=self: x.on_update())
        self.socket_server = None
        self.ball_count = None

    def on_update(self):
        balls = self.tracker.balls()
        # count = len(balls)
        # if count != self.ball_count:
        #    self.ball_count = count
        #    print('number of balls: ' + str(len(balls)))
        messages = []
        for ball in balls:
            msg = []
            msg.append(ball.id)
            msg.append(ball.colour.name)
            msg.append(ball.radius)
            msg.append(int(ball.pos[0]))
            msg.append(int(ball.pos[1]))
            msg = ",".join([str(i) for i in msg])
            messages.append(msg)
        message = ";".join(messages)
        self.socket_server.send_to_all(message)

    def run(self):
        self.tracker.start()
        self.socket_server = SoundOfColourSocketServer(port=8001)
        while True:
            time.sleep(0.1)
            if self.tracker.thread is None:
                break
            pass
        self.socket_server.close()


if __name__ == '__main__':
    soc = SoundOfColour()
    soc.run()

