from simplewebsocketserver import SimpleWebSocketServer, WebSocket
import time


class SoundOfColourSocket(WebSocket):
    def handleMessage(self):

        for client in self.server.clients:
            if client != self:
                client.sendMessage(self.address[0] + u' - ' + self.data)

    def handleConnected(self):
        print(self.address, 'connected')
        for client in self.server.clients:
            client.sendMessage(self.address[0] + u' - connected')
        self.server.clients.append(self)

    def handleClose(self):
        self.server.clients.remove(self)
        print(self.address, 'closed')
        for client in self.server.clients:
            client.sendMessage(self.address[0] + u' - disconnected')


class SoundOfColourSocketServer(SimpleWebSocketServer):
    def __init__(self, host='', port=8001):
        self.clients = []
        super().__init__(host, port, SoundOfColourSocket, 0.001)
        print("Socket Server Listening on port: " + str(port))

    def send_to_all(self, message):
        for client in self.clients:
            client.sendMessage(message)


if __name__ == "__main__":
    server = SoundOfColourSocketServer(port=8001)
    while True:
        server.serveonce()
        time.sleep(3)
        print("hello")
