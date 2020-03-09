import pyrealsense2 as rs
import numpy as np
import json



class Detector:
    def __init__(self,server,w=640,h=480,fps=30):
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.width = w            
        self.height = h
        self.fps = fps
        #configure the realsense's color and depth stream given dimensions for width and height
        self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, fps)
        self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, fps)
        self.box_width = 64
        self.box_height = 64
        #create array containing range values of interest in feet
        self.ranges = [20,10,5]
        self.colors = [(0,255,0),(0,255,255),(0,0,255)] #Green, Yellow, Red
        #defining measure area/box coordinates within image
        self.box_width_min = int((self.width - self.box_width)//2 -1)        #coordinates to center box within image. This is the first horizontal coordinate for the measure box
        self.box_height_min = int((self.height - self.box_height)//2 -1)     #y-coordinate to center box within image
        self.box_width_max = int(self.box_width_min + self.box_width)
        self.box_height_max = int(self.box_height_min + self.box_height)
        self.profile = None
        self.depth_scale = None
        self.server = server
        self.counter = 0
        self.is_streaming = False


    def startStream(self):
        try:
            #start streaming
            self.profile = self.pipeline.start(self.config)
            self.depth_scale = self.profile.get_device().first_depth_sensor().get_depth_scale()
            self.is_streaming = True
        except:
            self.is_streaming = False


    def getFrame(self):
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        resized_depth_image = depth_image[self.box_height_min : self.box_height_max : 1,self.box_width_min : self.box_width_max : 1].astype(float)
         
        resized_depth_image = resized_depth_image * self.depth_scale
        
        avg_dist = np.mean(resized_depth_image)
        
        avg_dist = round(avg_dist * 3.28084)
        
        text_color = self.colors[2]
        if avg_dist >= self.ranges[0]:
            text_color = self.colors[0]
        elif avg_dist >= self.ranges[1]:
            text_color = self.colors[1]
        elif avg_dist >= self.ranges[2]:
            text_color = self.colors[2]
        if self.counter > 10:
            self.server.send_message_to_all(json.dumps({"range":self.colors.index(text_color),"distance":avg_dist}))
            self.counter = 0 
        else:
            self.counter = self.counter + 1

        return {"image":color_image,"color":text_color,"distance":avg_dist}        
    
        
        def cleanup(self):
            self.pipeline.stop()
