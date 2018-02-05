import http.server
import socketserver
import multiprocessing


def webserverloop(port):
    handler = http.server.SimpleHTTPRequestHandler

    httpd = socketserver.TCPServer(("", port), handler)

    print("serving at port", port)
    httpd.serve_forever()


def startWebServerInSeperateProcess(port=8000):
    web_process = multiprocessing.Process(target=webserverloop, args=(port,))
    web_process.start()
    return web_process


def stopWebServerInSeperateProcess(web_process):
    if web_process is not None:
        if web_process.is_alive():
            print("terminating web process")
            web_process.terminate()
