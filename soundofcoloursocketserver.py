from simplewebsocketserver import SimpleWebSocketServer, WebSocket
import time


class SoundOfColourSocket(WebSocket):
    def handleMessage(self):
        # for client in self.server.clients:
        #    if client != self:
        #        client.sendMessage(self.address[0] + u' - ' + self.data)
        self.server.handle_message(self)

    def handleConnected(self):
        print(self.address, 'connected')
        # for client in self.server.clients:
        #    client.sendMessage(self.address[0] + u' - connected')
        self.server.clients.append(self)
        self.server.handle_connected(self)

    def handleClose(self):
        self.server.clients.remove(self)
        print(self.address, 'closed')
        # for client in self.server.clients:
        #    client.sendMessage(self.address[0] + u' - disconnected')


class SoundOfColourSocketServer(SimpleWebSocketServer):
    def __init__(self, host='', port=8001):
        self.clients = []
        self.client_connected_handler = None
        self.client_message_handler = None

        super().__init__(host, port, SoundOfColourSocket, 0.001)
        print("Socket Server Listening on port: " + str(port))

    def send_to_all(self, message):
        for client in self.clients:
            client.sendMessage(message)

    def set_on_client_connected(self, client_connected_handler):
        self.client_connected_handler = client_connected_handler

    def set_on_client_message(self, client_message_handler):
        self.client_message_handler = client_message_handler

    def handle_socket_event(self, handler, socket):
        if handler is not None:
           handler(socket)

    def handle_connected(self, socket):
        self.handle_socket_event(self.client_connected_handler, socket)

    def handle_message(self, socket):
        self.handle_socket_event(self.client_message_handler, socket)


if __name__ == "__main__":
    server = SoundOfColourSocketServer(port=8001)
    while True:
        server.serveonce()
        time.sleep(3)
        print("hello")
