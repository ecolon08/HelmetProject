from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import threading
import json
import time
import cv2
import random
import numpy as np
from http.server import SimpleHTTPRequestHandler
import ssl
import socketserver

class ClientHandler(WebSocket):
    role = None
    backend = None
    def handleMessage(self):
       parsed = None
       try:
           parsed = json.loads(self.data)
       finally:
           if parsed is not None and "role" in parsed.keys():
               self.role = parsed["role"]
               print("New client connected as %s"%self.role)

    def handleConnected(self):
       self.backend.clients.append(self)

    def handleClose(self):
       self.backend.clients.remove(self)
       print(self.address, 'closed')

class UIHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                return
       
class Backend:
    def __init__(self,wsPort=9001,httpPort=80):
        self.clients = []
        handler = ClientHandler
        handler.backend = self
        self.wsServer = SimpleWebSocketServer('0.0.0.0', wsPort,handler )
        self.httpServer = socketserver.TCPServer(('0.0.0.0', httpPort), UIHandler)
        self.httpServer.socket = ssl.wrap_socket(self.httpServer.socket, server_side=True, certfile='cert.pem', keyfile='key.pem', ssl_version=ssl.PROTOCOL_TLSv1_2)
        self.zone = "init"
        
    def online(self):
        try:
            threading.Thread(target=self.wsServer.serveforever,daemon=True).start()
            threading.Thread(target=self.httpServer.serve_forever,daemon=True).start()
            return True
        except:
            return False
    def sendFrame(self,frame):
        [client.sendMessage(frame) for client in self.clients if client.role == "viewer"]

    def setZone(self,zone):
        assert zone is int and zone in range(0,2)
        self.zone = zone

    def notifyHelmet(self):
        while True:
            try:
                msg = json.dumps({"range":self.zone})
                [client.sendMessage(msg) for client in self.clients if client.role == "helmet"]
                time.sleep(0.3)
            except:
                pass
        
if __name__ == "__main__":
    cam = cv2.VideoCapture(0)
    backend = Backend()
    if backend.online():
        while True:
            ready, test = cam.read()
            if ready:
                frame = cv2.cvtColor(test, cv2.COLOR_BGR2RGBA)
                backend.sendFrame(frame.tobytes())
