import pygame, os, ast, random
from vector import *
pygame.init()

bgColor = (20,20,20)
frameSize = (290, 164)

imagesFormats = ['png', 'jpg', 'jpeg', 'bmp']
videoFormats = ['mp4', 'avi', 'mov', 'flv', 'wmv', 'mpg', 'mpeg', 'mkv']

titleFont = pygame.font.SysFont('Tahoma', 26, True)
nameFont = pygame.font.SysFont('Tahoma', 16, False)

arrow = [(0,14), (12,0), (14,2), (4,14), (14,26), (12,28)]
arrowSize = Vector(14, 28)

RED = (229,9,20)

watched = []
if os.path.exists("watch.ini"):
	with open("watch.ini", "r") as file:
		for line in file.readlines():
			watched.append(line[:-1])

def addToWatched(path):
    baseName = os.path.basename(path)
    if baseName not in watched:
        watched.append(baseName)
    with open("watch.ini", "a+") as file:
        file.write(baseName + "\n")

folderDict = {}
if os.path.exists("folders.ini"):
	with open("folders.ini", "r") as file:
		line = file.readline()
		folderDict = ast.literal_eval(line)

win = pygame.display.set_mode((1440, 720), pygame.RESIZABLE)
clock = pygame.time.Clock()
fps = 60
pygame.display.set_caption('Simflix')
simflix = pygame.image.load('./assets/simflix.png')
simflix = pygame.transform.smoothscale(simflix, (simflix.get_width()*0.4, simflix.get_height()*0.4))

def execute(path):
	command = path
	print("executing:", command)
	os.system(command)

class Gui:
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Gui, cls).__new__(cls)
            cls._instance.initiate()
        return cls._instance
    def initiate(self):
        self.elements = []
        self.selectedFrame = None
        self.selectedFrameSlider = None
    def createFrameSlider(self, title):
        f = FrameSlider(title)
        f.pos = Vector(5, 100 + len(self._instance.elements) * (frameSize[1] + 100))
        return f
    def select(self, frame):
        self.selectedFrame = frame
    def step(self):
        for element in self.elements:
            element.step()
        if self.selectedFrame:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            if not self.selectedFrame.selected:
                self.selectedFrame = None
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if self.selectedFrameSlider:
            if not self.selectedFrameSlider.selected:
                self.selectedFrameSlider = None
    def draw(self):
        for element in self._instance.elements:
            element.draw()
    def handleEvents(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse = event.pos
                # slide
                clicked = False
                if self.selectedFrameSlider:
                    if mouse[0] < 50:
                        self.selectedFrameSlider.slide("left")    
                        clicked = True
                    elif mouse[0] > win.get_width() - 50:
                        self.selectedFrameSlider.slide("right")
                        clicked = True
                if clicked:
                    return
                
                # open file
                if self.selectedFrame:
                    if not self.selectedFrame.folder:
                        # open file
                        path = self.selectedFrame.path
                        execute(path)
                        addToWatched(path)
                        self.selectedFrame.watched = 1
                    else:
                        # open folder
                        path = self.selectedFrame.path
                        sliderIndex = self.elements.index(self.selectedFrameSlider)
                        self.elements.remove(self.selectedFrameSlider)
                        loadFolderToSlider(path, sliderIndex, os.path.basename(path))
                
class FrameSlider:
    def __init__(self, title):
        self.frames = []
        self.title = title
        self.titleSurf = titleFont.render(title, True, (255,255,255))
        self.pos = Vector()
        self.slideIndex = 0
        self.selected = False

    def addFrame(self, frame):
        frame.parent = self
        pos = Vector(len(self.frames) * (8 + frameSize[0]), 5 + self.titleSurf.get_height())
        self.frames.append(frame)
        frame.setPos(pos)
    def step(self):
        for frame in self.frames:
            frame.step()
        mouse = pygame.mouse.get_pos()
        if mouse[1] > self.pos[1] and mouse[1] < self.pos[1] + self.titleSurf.get_height() + 5 + frameSize[1]:
            self.selected = True
            Gui().selectedFrameSlider = self
        else:
            self.selected = False
                
    def draw(self):
        win.blit(self.titleSurf, (self.pos[0] + 10, self.pos[1]))
        for frame in self.frames:
            frame.draw()
        if self.selected:
            ypos = self.pos[1] + self.titleSurf.get_height() + 5 + frameSize[1] / 2 - arrowSize[1] / 2
            leftArrow = [tup2vec(i) + Vector(arrowSize[0], ypos) for i in arrow]
            pygame.draw.polygon(win, (255,255,255), leftArrow)

            rightArrow = [Vector(-i[0], i[1]) + Vector(win.get_width() - arrowSize[0], ypos) for i in arrow]
            pygame.draw.polygon(win, (255,255,255), rightArrow)
    def slide(self, button):
        framesInWin = win.get_width() // (frameSize[0] + 8)
        slideOffset = 0
        animate = True
        if button == 'left':
            # slide right
            self.slideIndex -= framesInWin
            if self.slideIndex < 0:
                self.slideIndex = 0
                animate = False
            else:
                slideOffset = 1 * (frameSize[0] + 8)

        elif button == 'right':
            # slide left
            self.slideIndex += framesInWin
            if self.slideIndex > len(self.frames) - framesInWin:
                self.slideIndex = len(self.frames) - framesInWin
                animate = False
            else:
                slideOffset = -1 * (frameSize[0] + 8)

        if animate:
            AnimatorSlider(self, Vector(slideOffset * framesInWin, 0))

class AnimatorSlider:
    def __init__(self, slider, offset):
        Gui().elements.append(self)
        self.slider = slider
        self.offset = offset

        self.startVal = 0
        self.endVal = offset
        self.t = 0
        self.dt = 2 / fps

        self.framesInitialValues = [vectorCopy(i.pos) for i in self.slider.frames]
        self.framesFinalValues = [i.pos + offset for i in self.slider.frames]
    def ease(self, t):
        return t * t * t * (t * (t * 6 - 15) + 10)
    def step(self):
        for i, frame in enumerate(self.slider.frames):
            t = self.ease(self.t)
            frame.pos = self.framesInitialValues[i] * (1 - t) + self.framesFinalValues[i] * t

        self.t += self.dt
        if self.t >= 1:
            for i, frame in enumerate(self.slider.frames):
                frame.pos = self.framesFinalValues[i]

    def draw(self):
        pass

class Frame:
    def __init__(self):
        self.pos = Vector(0,0)
        self.setSurf()
        self.selected = False
        self.parent = None
        self.path = None

        self.folder = False
        self.watched = 0
    def setPos(self, pos):
        self.pos = self.parent.pos + pos
    def setSurf(self, imagePath=None, color=(255,255,255), name=None):
        self.surf = pygame.Surface(frameSize, pygame.SRCALPHA)
        self.surf.fill((0,0,0))
        if imagePath:
            image = pygame.image.load(imagePath).convert()

            if image.get_width() > image.get_height():
                image = pygame.transform.scale(image, (frameSize[0], frameSize[0] * image.get_height() // image.get_width()))
            else:
                image = pygame.transform.scale(image, (frameSize[1] * image.get_width() // image.get_height(), frameSize[1]))

            # blit image to surf in center
            self.surf.blit(image, ((frameSize[0] - image.get_width()) / 2, (frameSize[1] - image.get_height()) / 2))

        else:
            self.surf.fill(color)

        # blit name
        if name:
            nameSurf = nameFont.render(name, True, (255,255,255))
            self.surf.blit(nameSurf, (frameSize[0]/2 - nameSurf.get_width()/2, frameSize[1] - nameSurf.get_height()))

        # add border
        borderMask = pygame.Surface(frameSize, pygame.SRCALPHA)
        borderMask.fill((255,255,255,255))
        pygame.draw.rect(borderMask, (0,0,0,0), ((0,0), frameSize), 0, 4)
        self.surf.blit(borderMask, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

    def step(self):
        mouse = pygame.mouse.get_pos()
        if mouse[0] > self.pos[0] and mouse[0] <= self.pos[0] + frameSize[0]\
                and mouse[1] > self.pos[1] and mouse[1] <= self.pos[1] + frameSize[1]:
            self.selected = True
            Gui().select(self)
        else:
            self.selected = False
    def draw(self):
        win.blit(self.surf, self.pos)
        if self.watched != 0:
            start = self.pos + Vector(frameSize[0]/2 - 80, frameSize[1] + 10)
            end = self.pos + Vector(frameSize[0]/2 + 80, frameSize[1] + 10)
            pygame.draw.line(win, (91,91,91), start, end, 3)
            pygame.draw.line(win, RED, start, start + (end - start) * self.watched, 3)

def loadFolderToSlider(path, sliderIndex, title):
    frameSlider = Gui().createFrameSlider(title)
    for i, file in enumerate(os.listdir(path)):
        if i == 20: break
        if file.split('.')[-1] in imagesFormats:
            f = Frame()
            f.setSurf(path + '/' + file, name=os.path.basename(path + '/' + file))
            f.path = path + '/' + file
            baseName = os.path.basename(file)
            if baseName in watched:
                f.watched = 1
            frameSlider.addFrame(f)
        elif file.split('.')[-1] in videoFormats:
            f = Frame()
            f.setSurf(color=(20, 9, 229), name=os.path.basename(path + '/' + file))
            f.path = path + '/' + file
            baseName = os.path.basename(file)
            if baseName in watched:
                f.watched = 1
            frameSlider.addFrame(f)
        elif os.path.isdir(path + '/' + file):
            f = Frame()
            f.setSurf(color=(229, 229, 9), name=os.path.basename(path + '/' + file))
            f.path = path + '/' + file
            baseName = os.path.basename(file)
            if baseName in watched:
                f.watched = 1
            f.folder = True
            frameSlider.addFrame(f)
    Gui().elements.insert(sliderIndex, frameSlider)

def init():
    for folder in folderDict:
        path = folderDict[folder]
        loadFolderToSlider(path, -1, folder)

gui = Gui()
init()

done = False
while not done:
    for event in pygame.event.get():
        gui.handleEvents(event)
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                gui.selectedFrameSlider.slide('left')
            elif event.key == pygame.K_RIGHT:
                gui.selectedFrameSlider.slide('right')
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        done = True

    gui.step()

    win.fill(bgColor)
    win.blit(simflix, (win.get_width() - simflix.get_width() - 20, 5))
    gui.draw()

    pygame.display.update()
    clock.tick(fps)
pygame.quit()