import http.server
import socketserver
import multiprocessing



def webServer(port):
    

    Handler = http.server.SimpleHTTPRequestHandler

    httpd = socketserver.TCPServer(("", port), Handler)

    print("serving at port", port)
    httpd.serve_forever()
    

def startWebServerInSeperateProcess(port=8000):
    
    web_process = multiprocessing.Process(target=webServer,args=(port,))
    web_process.start()
    return web_process


def stopWebServerInSeperateProcess(web_process):    
    if(web_process is not None):
        if(web_process.is_alive()):
            print("terminating web process")
            web_process.terminate()
