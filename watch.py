import os, subprocess
from vector import *
import pygame
pygame.init()
pygame.font.init()
myfont = pygame.font.SysFont('Arial', 16)

# TODO
# actual path search like windows
# create ini if not exists
# download the vector addon

PROGRAM_DIR = 
SERIES_DIR = 
VIDEO_FORMS = ["avi", "mp4", "mkv"]

REGULAR = 0
WATCHED = 1
FOLDER = 2

textColor = (255,255,255)
margin = 3

win = pygame.display.set_mode((1280, 720))
pygame.display.set_caption('Watch')

# read watched episodes
watched = []
with open("watch.ini", "r") as file:
    for line in file.readlines():
        watched.append(line[:-1])

def getEpisodesNames(path):
    listed = os.listdir(path)
    out = []
    for file in listed:
        for form in VIDEO_FORMS:
            if form in file:
                out.append(file)
    return out

def listFolders(path):
    return [f.path.replace(".\\", "") for f in os.scandir(path) if f.is_dir()]

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
        color = (0,0,0)
        if self.mode == WATCHED:
            color = (0,0,100)
        if self.selected:
            color = (255,0,0)
        pygame.draw.rect(win, color, (self.pos, self.size))
        win.blit(self.surf, self.pos)
        

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

folders = listFolders(SERIES_DIR)
state = "prepare series"
layer0 = []
selectedElement = None
buffer = []

win.fill((255,255,255))

run = True
while run:
    redraw = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "choose series":
                state = "prepare episodes"
                
                buffer.append(selectedElement.label)
            
            if state == "choose episode":
                # episode was chosen
                state = "execute"
                buffer.append(selectedElement.label)
                selectedElement.mode = WATCHED
                
                # add to watched list
                if selectedElement.label in watched:
                    print("already watched this")
                else:
                    with open("watch.ini", "a") as file:
                        file.write(selectedElement.label + "\n")
                # open file to watch
                file2watch = SERIES_DIR
                for b in buffer:
                    file2watch += "\\" + b
                print("watch:", file2watch)
                command = PROGRAM_DIR + " " + '"' + file2watch + '"'
                print("executing:", command)
                
                os.system(command)
                buffer = buffer[:-1]
                state = "choose episode"
                        
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        run = False
    
    if state == "prepare series":
        stack = Stack()
        folders = listFolders(SERIES_DIR)
        for folder in folders:
            folder = folder.split("\\")[-1]
            b = Button(folder)
            stack.elements.append(b)
        
        stack.calculate()
        stack.draw()
        layer0.append(stack)
        state = "choose series"
    
    if state == "prepare episodes":
        layer0 = []
        stack = Stack()
        episodes = getEpisodesNames(SERIES_DIR + "\\" + selectedElement.label)
        for episode in episodes:
            b = Button(episode)
            if episode in watched:
                b.mode = WATCHED
            stack.elements.append(b)
        
        stack.calculate()
        stack.draw()
        layer0.append(stack)
        state = "choose episode"
        
    
    # step
    for element in layer0:
        change = element.step()
        if change:
            redraw = True
    
    # draw
    if redraw:
        win.fill((255,255,255))
        for element in layer0:
            element.draw()
    
    pygame.display.update()
pygame.quit()
