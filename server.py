from websocket_server import WebsocketServer
from detect import Detector
import threading
import time
import pygame
import pygame.camera
import numpy as np
import sys
import json

# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])


# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'])


# Called when a client sends a message
def message_received(client, server, message):
	print("Client(%d) said %s" % client['id'],message)

def new_viewer(client, server):
	print("New client connected and was given id %d" % client['id'])

def viewer_left(client, server):
	print("Client(%d) disconnected" % client['id'])


def viewer_message(client,server,message):
	print("Client(%d) said %s" % client['id'],message)
	

PORT=9001
server = WebsocketServer(PORT,host="0.0.0.0")
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)

VIDEO_PORT = 9000
video_server = WebsocketServer(VIDEO_PORT,host="0.0.0.0")
video_server.set_fn_new_client(new_viewer)
video_server.set_fn_client_left(viewer_left)
video_server.set_fn_message_received(viewer_message)

detector = Detector(server)
pygame.init()
#screen = pygame.display.set_mode(flags=pygame.FULLSCREEN)
screen = pygame.display.set_mode((800,800))
X,Y = pygame.display.get_surface().get_size()

def displayFrame(frame):
    surface = pygame.surfarray.make_surface(frame) 
    screen.blit(surface, (0, 0))


def displayText(string,center=(X // 2, Y // 2),color=(0,255,0),size=32):
    font = pygame.font.Font('freesansbold.ttf', size) 
    text = font.render(string, True,color )
    textRect = text.get_rect()  
    textRect.center = center
    screen.blit(text, textRect) 


def overlayRect(w,h,c=None,color=None):
    rect = pygame.Rect(0,0,0,0)
    rect.width = w
    rect.height = h
    if c is None:
        rect.center = (X // 2, Y // 2)
    else:
        rect.center = c
    if color is None:
        color = (0,0,255)
    pygame.draw.rect(screen,color,rect,3)


def event_check():
    for e in pygame.event.get():
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: 
            displayText("System is shutting down...")
            camera.stop()
            detector.cleanup()
            sys.exit()

pygame.display.set_caption('Smart Helmet')
pygame.mouse.set_visible(1)
displayText("System initializing...")
t = threading.Thread(target=server.run_forever, daemon = True).start()
v = threading.Thread(target=video_server.run_forever, daemon = True).start()
attempts = 0
target_size = round((detector.box_width*X) / detector.width)
pygame.display.update()
time.sleep(1.5)
screen.fill(0)
pygame.camera.init()
print(pygame.camera.list_cameras())
DEVICE = pygame.camera.list_cameras()[0]
SIZE = (X,Y)
camera = pygame.camera.Camera(DEVICE, SIZE)
camera.start()
detector.is_streaming = True

while True:
    if not detector.is_streaming:
        screen.fill(0)
        attempts += 1
        displayText("Camera offline. Attempting to start..."+str(attempts))
        overlayRect(target_size,target_size)
        displayText("Average Distance:  {} feet".format(10),center=(round(X*0.33), round(Y*0.9)),size=32)
        #detector.startStream()
    else:
        attempts = 0
        #frame_dict = detector.getFrame()
        #frame = frame_dict["image"]
        #color = frame_dict["color"]
        if camera.query_image():
            picture = camera.get_image()
            picture = pygame.transform.scale(picture, SIZE)
            screen.blit(picture,(0,0))
            #frame = pygame.surfarray.array3d(surf)
            #displayFrame(frame) 
            overlayRect(target_size,target_size)
            displayText("Average Distance:  {} feet".format(10),center=(X//4, round(Y*0.9)),size=64)
    pygame.display.update()
    if len(video_server.clients)>0:
        outgoing = pygame.surfarray.array3d(screen)
        video_server.send_message_to_all(json.dumps(outgoing.tolist()))

    event_check()


