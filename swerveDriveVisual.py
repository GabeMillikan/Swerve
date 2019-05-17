import cv2
import numpy as np
import time
import keyboard
import math

QuitButton = "q" #button to quit (pressing ctrl+C in console will always work)
ControlSpeed = 0.001 #controller sensetivity
RobotSize = (35, 35)#in inches
ViewScale = (100,100) #how many inches to draw
ViewSize = (800,800) #pixels of image, to accommodate multiple screen resolutions (squares are best here)
ControlBoardHeight = 100 #in pixels


VectorDrawScale = 15 #vector magnitude multiplier

TranslationVectorColor = (255,0,0) #blue,green,red
TranslationVectorThickness = 2 # pixels (>0)

RotationVectorColor = (0,0,255) #blue,green,red
RotationVectorThickness = 2 # pixels (>0)

FinalVectorColor = (255,255,255) #blue,green,red
FinalVectorThickness = 2 # pixels (>0)

WheelGrid = (2,2)#add more wheels (vector field?)


#/CLASSES SETUP\#
class vectorClass():
	def __init__(self, origin, magnitude, angle):
		self.origin = origin
		self.magnitude = magnitude
		self.angle = angle
		self.end = (math.cos(self.angle)*self.magnitude, math.sin(self.angle)*self.magnitude)
		self.end = (self.end[0] + self.origin[0], self.end[1]+self.origin[1])
	def draw(self, screen, color, addArrow=True, thicc=1):
		originPix = (int(round(screen.center[0]+self.origin[0]*screen.pixelsPerInch)), int(round(screen.center[1]+self.origin[1]*screen.pixelsPerInch)))
		vecEndpoint_inches = (math.cos(self.angle)*self.magnitude, math.sin(self.angle)*self.magnitude)
		endPtPix = (vecEndpoint_inches[0]*screen.pixelsPerInch, vecEndpoint_inches[1]*screen.pixelsPerInch)
		endPtPix = (endPtPix[0] + originPix[0], endPtPix[1] + originPix[1])
		endPtPix = (int(round(endPtPix[0])), int(round(endPtPix[1])))
		cv2.line(screen.image, originPix, endPtPix, color, thicc)
		if addArrow:
			arw1 = vectorClass(self.end, self.magnitude/8, (self.angle+3.14159)+0.5) 
			arw2 = vectorClass(self.end, self.magnitude/8, (self.angle+3.14159)-0.5)
			arw1.draw(screen, color, addArrow = False, thicc=thicc)
			arw2.draw(screen, color, addArrow = False, thicc=thicc)
		

class wheelClass():
	def __init__(self, offsetX, offsetY):
		self.offsetX = offsetX
		self.offsetY = offsetY

class robotClass():
	def __init__(self, width, length, wheelsX = 2, wheelsY = 2):
		self.width = width
		self.length = length
		self.wheels = []
		for x in range(wheelsX):
			for y in range(wheelsY):
				self.wheels.append(wheelClass(self.width*x/(wheelsX-1) - self.width/2, self.length*y/(wheelsY-1) - self.length/2))
	
	def draw(self, screen, controlF):
		cv2.circle(screen.image, (int(round(screen.center[0])),int(round(screen.center[1]))) , 3, (0,255,0), -1)
		for wheel in self.wheels:
			whlCenter = (int(round(screen.center[0]+wheel.offsetX*screen.pixelsPerInch)), int(round(screen.center[1]+wheel.offsetY*screen.pixelsPerInch)))
			cv2.circle(screen.image, whlCenter, 3, (255,255,0), -1)
			vecT = vectorClass((wheel.offsetX, wheel.offsetY), controlF.t_magnitude*VectorDrawScale, controlF.t_rotation*2*3.14159)
			vecT.draw(screen, TranslationVectorColor, thicc=TranslationVectorThickness)
			hypot = (wheel.offsetX**2 + wheel.offsetY**2)**0.5
			masterAngle = math.atan2(wheel.offsetY, wheel.offsetX) + (90*3.14159/180)
			vecR = vectorClass(vecT.end, controlF.rotationSpeed*VectorDrawScale, masterAngle)
			vecR.draw(screen, RotationVectorColor, thicc = RotationVectorThickness)
			
			vecTX = vecT.magnitude*math.cos(vecT.angle)
			vecTY = vecT.magnitude*math.sin(vecT.angle)
			
			vecRX = vecR.magnitude*math.cos(vecR.angle)
			vecRY = vecR.magnitude*math.sin(vecR.angle)
			
			vecFE = (vecTX+vecRX, vecTY+vecRY)
			vecFA = math.atan2(vecFE[1], vecFE[0])
			vecFM = (vecFE[0]**2 + vecFE[1]**2)**0.5
			
			FinalVec = vectorClass((wheel.offsetX, wheel.offsetY), vecFM, vecFA)
			FinalVec.draw(screen, FinalVectorColor, thicc = FinalVectorThickness)

class screenClass():
	def __init__(self, screenPixels, screenInches, sliderFrame):
		self.screenPixels = screenPixels
		self.center = (screenPixels[0]/2, screenPixels[1]/2)
		self.screenInches = screenInches
		self.image = np.zeros((screenPixels[1]+sliderFrame.height,screenPixels[0],3), np.uint8)
		self.pixelsPerInch = screenPixels[0]/screenInches[0]
	def drawScale(self, controlF):
		cv2.line(self.image, (10 , int(controlF.height+10)), (int(10+(self.pixelsPerInch*5)) ,int(controlF.height+10)), (255,255,255), 3)
		cv2.putText(self.image, "5 inches", (10 , int(controlF.height+25)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255))
	def clean(self, controlF):
		self.image = np.zeros((self.screenPixels[1]+controlF.height,self.screenPixels[0],3), np.uint8)

class controlSliders():
	def __init__(self, height):
		self.height = height
		self.rotationSpeed = 0.5
		self.t_magnitude = 0.5
		self.t_rotation = 0.5
	def draw(self, screen):
		if self.rotationSpeed>1:
			self.rotationSpeed = 1
		if self.rotationSpeed<0:
			self.rotationSpeed = 0
		if self.t_magnitude>1:
			self.t_magnitude = 1
		if self.t_magnitude<0:
			self.t_magnitude = 0
		if self.t_rotation>1:
			self.t_rotation = 0 #backwards because circle
		if self.t_rotation<0:
			self.t_rotation = 1
	
		scx = screen.screenPixels[0]
		scy = screen.screenPixels[1]
		#background
		cv2.rectangle(screen.image, (0,scy), (scx,scy+self.height), (255, 255, 255), -1)
		#RotationSpeed
		cv2.line(screen.image, (40,int(scy+self.height/2)), (int(scx/3)-20,int(scy+self.height/2)), (200,200,200), 3)
		RotPixRange = (40, int(scx/3)-20)
		#MoveSpeed
		cv2.line(screen.image, (int(scx/3)+20,int(scy+self.height/2)), (int(scx*2/3)-20,int(scy+self.height/2)), (200,200,200), 3)
		MovPixRange = (int(scx/3)+20,int(scx*2/3)-20) 
		#MoveDirection
		cv2.circle(screen.image, (int((scx*2/3))+int(self.height/2 -10), int(scy+self.height/2)), int(self.height/2 -10), (200,200,200), 5)
		TraRadius = int(self.height/2 -10)
		TraCenter = (int((scx*2/3))+int(self.height/2 -10), int(scy+self.height/2))
		
		##draw draggers
		RotPix = int((RotPixRange[1]-RotPixRange[0])*self.rotationSpeed + RotPixRange[0])
		cv2.circle(screen.image, (RotPix, int(scy+self.height/2)), 10, (100,100,100), -1)
		
		MovPix = int((MovPixRange[1]-MovPixRange[0])*self.t_magnitude + MovPixRange[0])
		cv2.circle(screen.image, (MovPix, int(scy+self.height/2)), 10, (100,100,100), -1)
		
		TraPix = (math.cos(self.t_rotation*3.14159*2)*TraRadius, math.sin(self.t_rotation*3.14159*2)*TraRadius)
		TraPix = (int(TraPix[0])+TraCenter[0], int(TraPix[1])+TraCenter[1])
		cv2.circle(screen.image, TraPix, 10, (100,100,100), -1)
		
#\END/#



#/get classes\#
controlFrame = controlSliders(ControlBoardHeight)
screen = screenClass(ViewSize, ViewScale, controlFrame)
robot = robotClass(RobotSize[0], RobotSize[1], wheelsX = WheelGrid[0], wheelsY = WheelGrid[1])

#\END/#
while keyboard.is_pressed(QuitButton)==False:
	screen.clean(controlFrame)
	
	
	#/CONTROL\#
	if keyboard.is_pressed("R"):
		controlFrame.rotationSpeed -= ControlSpeed
	if keyboard.is_pressed("T"):
		controlFrame.rotationSpeed += ControlSpeed
	if keyboard.is_pressed("I"):
		controlFrame.t_magnitude -= ControlSpeed
	if keyboard.is_pressed("O"):
		controlFrame.t_magnitude += ControlSpeed
	if keyboard.is_pressed("M"):
		controlFrame.t_rotation -= ControlSpeed
	if keyboard.is_pressed("N"):
		controlFrame.t_rotation += ControlSpeed
	
	#\END/#
	
	
	#/draw classes\#
	controlFrame.draw(screen)
	robot.draw(screen, controlFrame)
	#\END/#

	#/draw to screen\#
	screen.image = cv2.flip(screen.image, 0) ##make bottom of screen
	screen.drawScale(controlFrame)

	#/add text\#
	cv2.putText(screen.image, "rotation speed", (40,int((controlFrame.height/2)+25)), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,0))
	cv2.putText(screen.image, "hotkey R & T", (40,int((controlFrame.height/2)+40)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0))
	cv2.putText(screen.image, "movement speed", (int(screen.screenPixels[0]/3)+20,int((controlFrame.height/2)+25)), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,0))
	cv2.putText(screen.image, "hotkey I & O", (int(screen.screenPixels[0]/3)+20,int((controlFrame.height/2)+40)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0))
	cv2.putText(screen.image, "direction", (int(screen.screenPixels[0]*5/6),int((controlFrame.height/2)+5)), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,0))
	cv2.putText(screen.image, "hotkey N & M", (int(screen.screenPixels[0]*5/6),int((controlFrame.height/2)+25)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0))
	cv2.putText(screen.image, 'PRESS "'+QuitButton+'" TO QUIT', (0, screen.screenPixels[1] + controlFrame.height-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255))
	#\END/#
	cv2.imshow('3863 Newbury Park robotics', screen.image)
	cv2.waitKey(1)
#\END/#





