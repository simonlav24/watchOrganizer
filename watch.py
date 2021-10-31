import os, subprocess, ast
if not os.path.exists("vector.py"):
	print("fetching vector")
	import urllib.request
	with urllib.request.urlopen('https://raw.githubusercontent.com/simonlav24/wormsGame/master/vector.py') as f:
		text = f.read().decode('utf-8')
		with open("vector.py", "w+") as vectorpy:
			vectorpy.write(text)
from vector import *
import pygame
pygame.init()
pygame.font.init()
myfont = pygame.font.SysFont('Tahoma', 16)
myfont.bold = True

PROGRAM_DIR = ""
START_DIR = "D:\\"
BACK_LABEL = "<-- Back"

REGULAR = 0
WATCHED = 1
FOLDER = 2
SPECIAL = 3

colorPal = {"font" : pygame.font.SysFont('Tahoma', 16),
            "special":(227,122,64),  
			"watched": (71,179,156), 
			"selected":   (222,91,74),  
			"folders": (50,78,91),    
			"button":(239,202,78),  
			"background": (255,255,255),
            "text": (255,255,255)}
            
colorPalNet = {"font" : pygame.font.Font(".\BebasNeue-Regular.ttf", 22),
            "special":(19,24,52),
			"watched": (222,222,222),   
			"selected":  (230,230,9) ,#
			"folders": (193,7,30),  #
			"button":(67,70,94),#  
			"background": (19,24,52),#
            "text": (255,255,255)}#

theme = colorPalNet

textColor = theme["text"]
margin = 3
scrollSpeed = 40

win = pygame.display.set_mode((700 + 2 * margin, 720))
pygame.display.set_caption('Watch')
icon = pygame.image.load('watch.png')
pygame.display.set_icon(icon)

# read watched episodes
watched = []
if os.path.exists("watch.ini"):
	with open("watch.ini", "r") as file:
		for line in file.readlines():
			watched.append(line[:-1])

# read folders dict
folderDict = {}
if os.path.exists("folders.ini"):
	with open("folders.ini", "r") as file:
		line = file.readline()
		folderDict = ast.literal_eval(line)

def execute(path):
	command = PROGRAM_DIR + " " + '"' + path + '"'
	print("executing:", command)
	os.system(command)
	
def listFiles(path):
	out = []
	scanned = os.listdir(path)
	for file in scanned:
		if ".BIN" in file:
			continue
		if os.path.isdir(path + "\\" + file):
			out.append((file, True))
		else:
			out.append((file, False))
	
	# sort folders first
	index = 0
	for i, f in enumerate(out):
		if f[1]:
			out[index], out[i] = out[i], out[index]
			index += 1
	return out

def layerOffset(offset):
	for element in layer0:
		element.offset(offset)

def currentFolder():
	return currentDir.split("\\")[-1]

def saveFolderDict():
	file = open("folders.ini", 'w')
	file.write(str(folderDict))
	file.close()

class Label:
	def __init__(self, label="label"):
		self.size = Vector(700, 25)
		self.pos = Vector()
		self.label = label
		self.labelize(self.label)
		self.initialize()
	def initialize(self):
		pass
	def labelize(self, string):
		self.label = string
		self.surf = theme["font"].render(self.label, True, textColor)
	def step(self):
		pass
	def draw(self):
		color = theme["folders"]
		pygame.draw.rect(win, color, (self.pos, self.size))
		win.blit(self.surf, self.pos + Vector(self.size.x/2, 0) - Vector(self.surf.get_size()[0]/2, 0))

class Button(Label):
	def initialize(self):
		self.selected = False
		self.mode = REGULAR
		self.rating = 0
		self.specialPoint = False
	def step(self):
		global selectedElement
		mouse = pygame.mouse.get_pos()
		if mouse[0] > self.pos[0] and mouse[0] <= self.pos[0] + self.size[0]\
				and mouse[1] > self.pos[1] and mouse[1] <= self.pos[1] + self.size[1]:
			if self.selected:
				return False
			self.selected = True
			selectedElement = self
			return True
		else:
			self.selected = False
	def draw(self):
		color = theme["button"]
		if self.mode == WATCHED:
			color = theme["watched"]
		if self.mode == FOLDER:
			color = theme["folders"]
		if self.mode == SPECIAL:
			color = theme["special"]
		if self.selected:
			color = theme["selected"]
		pygame.draw.rect(win, color, (self.pos, self.size))
		win.blit(self.surf, self.pos + Vector(margin, 0))
		if self.specialPoint:
			poly = [Vector(self.size.x - margin, margin), Vector(self.size.x - margin, self.size.y - margin), Vector(self.size.x - margin - self.size.y, self.size.y//2)]
			pygame.draw.polygon(win, theme["special"], [self.pos + i for i in poly])
			
class Stack:
	def __init__(self):
		self.elements = []
		self.pos = Vector(margin, margin)
		self.size = Vector()
	def calculate(self):
		posPointer = vectorCopy(self.pos)
		for i in self.elements:
			i.pos = vectorCopy(posPointer)
			posPointer.y += i.size.y + margin
	def offset(self, offset):
		global redraw
		self.pos += offset
		if self.pos.y >= 0:
			self.pos.y = margin
		self.calculate()
		redraw = True
	def step(self):
		changed = False
		for i in self.elements:
			change = i.step()
			if change:
				changed = True
		return changed
	def draw(self):
		for i in self.elements:
			i.draw()

state = None
state = "prepare"
layer0 = []
selectedElement = None
currentDir = START_DIR

run = True
while run:
	redraw = False

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if state == "choose" and selectedElement:
				# special buttons
				if selectedElement.mode == SPECIAL:
					if selectedElement.label == BACK_LABEL:
						currentDir = currentDir.replace(currentDir.split("\\")[-1], "")[:-1]
				# folder buttons
				elif selectedElement.mode == FOLDER:
					prevfolder = currentFolder()
					currentDir += "\\" + selectedElement.label
					currentFolderStr = currentFolder()
					folderDict[prevfolder] = currentFolderStr
					saveFolderDict()
				# file buttons
				else:
					# add to watched list
					if selectedElement.label in watched:
						pass
					else:
						with open("watch.ini", "a+") as file:
							file.write(selectedElement.label + "\n")
							watched.append(selectedElement.label)
					if selectedElement.mode != "folder":
						selectedElement.mode = WATCHED
					execute(currentDir + "\\" + selectedElement.label)
				state = "prepare"
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll down
			layerOffset(Vector(0, scrollSpeed))
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll up
			layerOffset(Vector(0, -scrollSpeed))
		if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
			if state == "choose":
				currentDir = currentDir.replace(currentDir.split("\\")[-1], "")[:-1]
				state = "prepare"
		
	keys = pygame.key.get_pressed()
	if keys[pygame.K_ESCAPE]:
		run = False
	
	if state == "prepare":
		stack = Stack()
		files = listFiles(currentDir)
		
		# add folder label
		l = Label(currentFolder())
		stack.elements.append(l)
		
		# add back button
		b = Button(BACK_LABEL)
		b.mode = SPECIAL
		stack.elements.append(b)
		
		# print(currentFolder())
		
		for file in files:
			b = Button(file[0])
			if file[1]:
				b.mode = FOLDER
				# print("current:", currentFolder())
				if currentFolder() in folderDict.keys():
					# print("last:", folderDict[currentFolder()])
					if folderDict[currentFolder()] == file[0]:
						b.specialPoint = True
			if file[0] in watched:
				b.mode = WATCHED
			stack.elements.append(b)
		
		stack.calculate()
		redraw = True
		layer0 = [stack]
		state = "choose"
	
	# step
	for element in layer0:
		change = element.step()
		if change:
			redraw = True
	
	# draw
	if redraw:
		win.fill(theme["background"])
		for element in layer0:
			element.draw()
	
		pygame.display.update()
pygame.quit()
