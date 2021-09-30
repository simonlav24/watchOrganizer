import os, subprocess
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

colorPal = {"orange":(227,122,64),
			"green": (71,179,156),
			"red":   (222,91,74),
			"black": (50,78,91),
			"yellow":(239,202,78),
			"white": (255,255,255)}

textColor = colorPal["white"]
margin = 3
scrollSpeed = 40

win = pygame.display.set_mode((700 + 2 * margin, 720))
pygame.display.set_caption('Watch')

# read watched episodes
watched = []
if os.path.exists("watch.ini"):
	with open("watch.ini", "r") as file:
		for line in file.readlines():
			watched.append(line[:-1])

def execute(path):
	command = PROGRAM_DIR + " " + '"' + path + '"'
	print("executing:", command)
	os.system(command)
	
def listFiles(path):
	out = []
	scanned = os.listdir(path)
	for file in scanned:
		if os.path.isdir(path + "\\" + file):
			out.append((file, True))
	for file in scanned:
		if not os.path.isdir(path + "\\" + file):
			out.append((file, False))
	return out

def layerOffset(offset):
	for element in layer0:
		element.offset(offset)

class Button:
	def __init__(self, label="button"):
		self.size = Vector(700, 25)
		self.pos = Vector()
		self.label = label
		self.labelize(self.label)
		self.selected = False
		self.mode = REGULAR
	def labelize(self, string):
		self.label = string
		self.surf = myfont.render(self.label, True, textColor)
	def step(self):
		global selectedElement
		mouse = pygame.mouse.get_pos()
		self.selected = False
		if mouse[0] > self.pos[0] and mouse[0] <= self.pos[0] + self.size[0]\
				and mouse[1] > self.pos[1] and mouse[1] <= self.pos[1] + self.size[1]:
			self.selected = True
			selectedElement = self
			return True
	def draw(self):
		color = colorPal["black"]
		if self.mode == WATCHED:
			color = colorPal["green"]
		if self.mode == FOLDER:
			color = colorPal["yellow"]
		if self.mode == SPECIAL:
			color = colorPal["orange"]
		if self.selected:
			color = colorPal["red"]
		pygame.draw.rect(win, color, (self.pos, self.size))
		win.blit(self.surf, self.pos + Vector(margin, 0))
		
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

win.fill(colorPal["white"])

run = True
while run:
	redraw = False

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if state == "choose" and selectedElement:
				if selectedElement.mode == SPECIAL:
					if selectedElement.label == BACK_LABEL:
						currentDir = currentDir.replace(currentDir.split("\\")[-1], "")[:-1]
				elif selectedElement.mode == FOLDER:
					currentDir += "\\" + selectedElement.label
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
		
	keys = pygame.key.get_pressed()
	if keys[pygame.K_ESCAPE]:
		run = False
	
	if state == "prepare":
		stack = Stack()
		files = listFiles(currentDir)
		
		# add back button
		b = Button(BACK_LABEL)
		b.mode = SPECIAL
		stack.elements.append(b)
		
		for file in files:
			b = Button(file[0])
			if file[1]:
				b.mode = FOLDER
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
		win.fill(colorPal["white"])
		for element in layer0:
			element.draw()
	
	pygame.display.update()
pygame.quit()
