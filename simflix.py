import pygame, os, ast, random, cv2, re, subprocess
from vector import *
pygame.init()

bgColor = (20,20,20)
frameSize = (290, 164)

imagesFormats = ['png', 'jpg', 'jpeg', 'bmp']
videoFormats = ['mp4', 'avi', 'mov', 'flv', 'wmv', 'mpg', 'mpeg', 'mkv']
acceptableFormats = imagesFormats + videoFormats

class FontStrokeDeco:
    def __init__(self, font):
        self.font = font

    def render(self, text, antialias=False, color=(255,255,255)):
        text_surf = self.font.render(text, antialias, color)
        text_stroke = self.font.render(text, antialias, (0,0,0))
        bg = pygame.Surface((text_surf.get_width() + 2, text_surf.get_height() + 2), pygame.SRCALPHA)
        bg.blit(text_stroke, (0, 0))
        bg.blit(text_stroke, (2, 0))
        bg.blit(text_stroke, (0, 2))
        bg.blit(text_stroke, (2, 2))
        bg.blit(text_surf, (1, 1))
        return bg

titleFont = pygame.font.SysFont('Tahoma', 26, True)
nameFont = FontStrokeDeco(pygame.font.SysFont('Tahoma', 16, False))



arrow = [(0,14), (12,0), (14,2), (4,14), (14,26), (12,28)]
arrowSize = Vector(14, 28)

RED = (229,9,20)

watched = []

def isAcceptableFormat(fileName):
    return fileName.split('.')[-1] in acceptableFormats

def loadWatched(watched):
    if os.path.exists("watch.ini"):
        with open("watch.ini", "r") as file:
            for line in file.readlines():
                if line[:-1] not in watched:
                    watched.append(line[:-1])

def addToWatched(path):
    baseName = os.path.basename(path)
    if baseName not in watched:
        watched.append(baseName)
    with open("watch.ini", "a+") as file:
        file.write(baseName + "\n")

def removeFromWatched(path):
    # folder
    if os.path.isdir(path):
        playable = findPlayableFiles(path)
        for file in playable:
            removeFromWatched(file)
        return

    # file
    baseName = os.path.basename(path)
    if baseName in watched:
        watched.remove(baseName)
        with open("watch.ini", "w") as file:
            for name in watched:
                file.write(name + "\n")

watched = []
loadWatched(watched)

folderDict = {}
if os.path.exists("folders.ini"):
    with open("folders.ini", "r") as file:
        line = file.readline()
        folderDict = ast.literal_eval(line)

win = pygame.display.set_mode((1440, 720), pygame.RESIZABLE)
clock = pygame.time.Clock()
fps = 60
pygame.display.set_caption('Simflix')
simflixSurf = pygame.image.load('./assets/simflix.png').convert_alpha()
simflixSurf = pygame.transform.smoothscale(simflixSurf, (simflixSurf.get_width()*0.4, simflixSurf.get_height()*0.4))
folderIconSurf = pygame.image.load('./assets/folderIcon.png').convert_alpha()
folderIconSurf = pygame.transform.smoothscale(folderIconSurf, (folderIconSurf.get_width()*0.06, folderIconSurf.get_height()*0.06))

highlightSurf = pygame.Surface((frameSize[0], frameSize[1]), pygame.SRCALPHA)
pygame.draw.polygon(highlightSurf, (70,70,70), [(frameSize[0] * 0.6, 0), (frameSize[0] * 0.9, 0), (frameSize[0] * 0.9 - 0.3 * frameSize[0], frameSize[1]), (frameSize[0] * 0.6 - 0.3 * frameSize[0], frameSize[1])])
pygame.draw.polygon(highlightSurf, (70,70,70), [(frameSize[0] * 0.45, 0), (frameSize[0] * 0.5, 0), (frameSize[0] * 0.5 - 0.3 * frameSize[0], frameSize[1]), (frameSize[0] * 0.45 - 0.3 * frameSize[0], frameSize[1])])
def execute(path):
    command = '"' + path + '"'
    print("executing:", command)
    subprocess.Popen(command, shell=True)
    # os.system(command)

def handleName(name):
    nameBu = name
    name = re.sub(r'\([^()]*\)', '', name)
    name = re.sub(r'\[[^\]]*\]', '', name)
    if '.' in name:
        name = '.'.join(name.split('.')[0:-1]).replace('.', ' ')

    se = re.search(r'(s|S)\d\d', name)
    ep = re.search(r'(e|E)\d\d', name)
    
    name = re.sub(r'(S|s)\d\d', '', name)
    name = re.sub(r'(E|e)\d\d', '', name)
    name = re.sub(r'\d+p', '', name)
    name = re.sub(r'\s+([^\s\w]|_)+\s+', ' ', name)
    
    for word in name.split(' '):
        if sum(1 for c in word if c.isupper()) >= 2:
            name = name.replace(word, '')
    name = re.sub(r'\s+', ' ', name)
    
    name = re.sub(r'[a-zA-Z]\d\d\d', '', name)
    name = re.sub(r'\s+$', '', name)
    name = re.sub(r'\-\-+', '', name)

    if se != None and ep != None:
        name += " " + se.group(0) + ep.group(0)

    if name == "" or name == " ":
        name = nameBu
    return name

class Gui:
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Gui, cls).__new__(cls)
            cls._instance.initiate()
        return cls._instance
    def initiate(self):
        self.elements = []
        self.animations = []
        self.selectedFrame = None
        self.selectedFrameSlider = None
        self.menu = None
    def reposition(self):
        for i, element in enumerate(self.elements):
            element.pos = Vector(5, 100 + i * (frameSize[1] + 100))
            element.reposition()
    def select(self, frame):
        self.selectedFrame = frame
    def step(self):
        for element in self.elements:
            element.step()
        for animation in self.animations:
            animation.step()
        if self.selectedFrame:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            if not self.selectedFrame.selected:
                self.selectedFrame = None
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if self.selectedFrameSlider:
            if not self.selectedFrameSlider.selected:
                self.selectedFrameSlider = None
        if self.menu:
            self.menu.step()
    def draw(self):
        for element in self._instance.elements:
            element.draw()
        if self.selectedFrame:
            self.selectedFrame.draw()
        if self.selectedFrameSlider:
            self.selectedFrameSlider.drawArrows()
        if self.menu:
            self.menu.draw()
    def handleMenuEvents(self, key):
        context = self.menu.context
        if key == 'Mark as unwatched':
            removeFromWatched(context.path)
            context.watched = 0
        elif key == 'Mark as watched':
            addToWatched(context.path)
            context.watched = 1
        elif key == 'Mark Folder as unwatched':
            removeFromWatched(context.path)
            context.watched = 0
        elif key == 'Play Random':
            playRandom(context.path)
        
    def handleEvents(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse = event.pos
                if self.menu:
                    # if mouse is not on menu
                    if mouse[0] < self.menu.pos.x or mouse[0] > self.menu.pos.x + self.menu.size[0] or mouse[1] < self.menu.pos.y or mouse[1] > self.menu.pos.y + self.menu.size[1]:
                        self.menu = None
                    else:
                        key = self.menu.handleEvents(event)
                        self.handleMenuEvents(key)
                    self.menu = None
                    return
                # slide
                if self.selectedFrameSlider:
                    # left or right
                    if mouse[0] < 50:
                        self.selectedFrameSlider.slide("left")    
                        return
                    elif mouse[0] > win.get_width() - 50:
                        self.selectedFrameSlider.slide("right")
                        return
                    # back
                    if mouse[0] > win.get_width() - self.selectedFrameSlider.backSurf.get_width() - 50 - 10 and mouse[1] > self.selectedFrameSlider.pos.y and mouse[1] < self.selectedFrameSlider.pos.y + self.selectedFrameSlider.backSurf.get_height():
                        path = os.path.dirname(self.selectedFrameSlider.path)
                        sliderIndex = self.elements.index(self.selectedFrameSlider)
                        self.elements.remove(self.selectedFrameSlider)
                        loadFolderToSlider(path, sliderIndex, os.path.basename(path))

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
                        self.selectedFrame = None
                        
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            elif event.button == 3:
                if self.selectedFrame:
                    if not self.selectedFrame.folder:
                        # right click on file
                        menu = Menu(event.pos, self.selectedFrame)
                        if self.selectedFrame.watched == 1:
                            menu.addButton('Mark as unwatched', 'Mark as unwatched')
                        else:
                            menu.addButton('Mark as watched', 'Mark as watched')
                        self.menu = menu
                    else:
                        # right click on folder
                        menu = Menu(event.pos, self.selectedFrame)
                        menu.addButton('Play Random', 'Play Random')
                        menu.addButton('Mark Folder as unwatched', 'Mark Folder as unwatched')
                        self.menu = menu

class FrameSlider:
    def __init__(self, title, path=''):
        self.frames = []
        self.title = handleName(title)
        self.titleSurf = titleFont.render(self.title, True, (255,255,255))
        self.backSurf = titleFont.render("Back", True, (255,255,255))
        self.pos = Vector()
        self.slideIndex = 0
        self.selected = False
        self.path = path

    def addFrame(self, frame):
        frame.parent = self
        pos = Vector(len(self.frames) * (8 + frameSize[0]), 5 + self.titleSurf.get_height())
        self.frames.append(frame)
        frame.setPos(pos)
    
    def reposition(self):
        for i, frame in enumerate(self.frames):
            frame.setPos(Vector(i * (8 + frameSize[0]), 5 + self.titleSurf.get_height()))

    def step(self):
        for frame in self.frames:
            frame.step()
        mouse = pygame.mouse.get_pos()
        if mouse[1] > self.pos[1] and mouse[1] < self.pos[1] + self.titleSurf.get_height() + 5 + frameSize[1]:
            self.selected = True
            Gui().selectedFrameSlider = self
        else:
            self.selected = False
    def drawArrows(self):
        ypos = self.pos[1] + self.titleSurf.get_height() + 5 + frameSize[1] / 2 - arrowSize[1] / 2
        leftArrow = [tup2vec(i) + Vector(arrowSize[0], ypos) for i in arrow]
        pygame.draw.polygon(win, (255,255,255), leftArrow)

        rightArrow = [Vector(-i[0], i[1]) + Vector(win.get_width() - arrowSize[0], ypos) for i in arrow]
        pygame.draw.polygon(win, (255,255,255), rightArrow)
    def draw(self):
        win.blit(self.titleSurf, (self.pos[0] + 10, self.pos[1]))
        win.blit(self.backSurf, (win.get_width() - self.backSurf.get_width() - 10 - 50, self.pos[1]))
        for frame in self.frames:
            frame.draw()
        if self.selected:
            self.drawArrows()
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
            if self.slideIndex > len(self.frames):# - framesInWin:
                self.slideIndex = len(self.frames) - framesInWin
                animate = False
            else:
                slideOffset = -1 * (frameSize[0] + 8)

        if animate:
            AnimatorSlider(self, Vector(slideOffset * framesInWin, 0))

class AnimatorSlider:
    def __init__(self, slider, offset):
        Gui().animations.append(self)
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

class Frame:
    def __init__(self, folder=False):
        self.pos = Vector(0,0)

        self.folder = folder
        self.setSurf()
        self.selected = False
        self.parent = None
        self.path = None

        self.watched = 0
        self.animationState = "idle"
        self.animOffsets = [0,0]
    def setPos(self, pos):
        self.pos = self.parent.pos + pos
    def setSurf(self, imagePath=None, color=(255,255,255), name=None, surf=None):
        
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

        elif surf:
            if surf.get_width() > surf.get_height():
                surf = pygame.transform.scale(surf, (frameSize[0], frameSize[0] * surf.get_height() // surf.get_width()))
            else:
                surf = pygame.transform.scale(surf, (frameSize[1] * surf.get_width() // surf.get_height(), frameSize[1]))

            # blit image to surf in center
            self.surf.blit(surf, ((frameSize[0] - surf.get_width()) / 2, (frameSize[1] - surf.get_height()) / 2))
        else:
            self.surf.fill(color)

        if self.folder:
            self.surf.blit(folderIconSurf, (5,5))

        # blit name
        if name:
            name = handleName(name)
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
            self.animationState = "hover"
            Gui().select(self)
        else:
            self.selected = False
            self.animationState = "idle"
        
        if self.animationState == "idle":
            self.animOffsets[0] += (0 - self.animOffsets[0]) * 0.05
            self.animOffsets[1] += (0 - self.animOffsets[1]) * 0.2
        if self.animationState == "hover":
            self.animOffsets[0] += (1 - self.animOffsets[0]) * 0.1
            self.animOffsets[1] += (1 - self.animOffsets[1]) * 0.1
    def draw(self):
        if self.animOffsets[0] > 0.01 or self.animOffsets[1] > 0.01:
            surf = self.surf.copy()
            posx =  self.animOffsets[0] * frameSize[0] - frameSize[0]
            surf.blit(highlightSurf, (posx,0), special_flags=pygame.BLEND_RGBA_ADD)
            scale = 1 + self.animOffsets[1] * 0.2
            surf = pygame.transform.smoothscale(surf, (int(frameSize[0] * scale), int(frameSize[1] * scale)))
            posOffset = (int(frameSize[0] * (1 - scale) / 2), int(frameSize[1] * (1 - scale) / 2))
            win.blit(surf, self.pos + posOffset)
        else:
            win.blit(self.surf, self.pos)
        
        if self.watched != 0: 
            start = self.pos + Vector(frameSize[0]/2 - 80, frameSize[1] + 10)
            start.y += self.animOffsets[0] * 15
            end = self.pos + Vector(frameSize[0]/2 + 80, frameSize[1] + 10)
            end.y += self.animOffsets[0] * 15
            pygame.draw.line(win, (91,91,91), start, end, 3)
            pygame.draw.line(win, RED, start, start + (end - start) * self.watched, 3)

class Menu:
    def __init__(self, pos, context):
        self.pos = tup2vec(pos)
        self.size = Vector()
        self.elements = []
        self.context = context
    def addButton(self, key, text):
        button = MenuButton(text, key)
        self.elements.append(button)
        self.recalculate()
    def recalculate(self):
        self.size = Vector()
        for element in self.elements:
            element.pos = self.pos + Vector(0, self.size[1])
            self.size[0] = max(self.size[0], element.size[0])
            self.size[1] += element.size[1]
        for i, element in enumerate(self.elements):
            element.size[0] = self.size[0]
            element.pos = self.pos + Vector(0, i * element.size[1])
    def handleEvents(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for element in self.elements:
                    if element.selected:
                        return element.key
    def step(self):
        for element in self.elements:
            element.step()
    def draw(self):
        pygame.draw.rect(win, (0,0,0), (self.pos, self.size))
        for element in self.elements:
            element.draw()

class MenuButton:
    def __init__(self, text, key):
        self.key = key
        self.text = text

        self.pos = Vector()
        self.size = Vector()

        self.selected = False
        self.setTextSurf()

    def setTextSurf(self):
        self.textSurf = nameFont.render(self.text, True, (255,255,255))
        self.size = Vector(self.textSurf.get_width() + 20, self.textSurf.get_height() + 20)
    def draw(self):
        if self.selected:
            pygame.draw.rect(win, (255,255,255), (self.pos, self.size))
        win.blit(self.textSurf, (self.pos[0] + 10 , self.pos[1] + self.size[1]/2 - self.textSurf.get_height()/2))
    def step(self):
        mouse = pygame.mouse.get_pos()
        if mouse[0] > self.pos[0] and mouse[0] <= self.pos[0] + self.size[0]\
                and mouse[1] > self.pos[1] and mouse[1] <= self.pos[1] + self.size[1]:
            self.selected = True
        else:
            self.selected = False

def createThumbnail(filePath):
    """ returns thumbnail Surface from path file """
    file_extension = os.path.splitext(filePath)[1]
    if file_extension.replace('.', '') in imagesFormats:
        frame = pygame.image.load(filePath)
        return frame
    importedVideo = cv2.VideoCapture(filePath)
    width = int(importedVideo.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(importedVideo.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(importedVideo.get(cv2.CAP_PROP_FRAME_COUNT))
    importedVideo.set(cv2.CAP_PROP_POS_FRAMES, length // 2)
    ret, frame = importedVideo.read()
    if ret == False:
        return None
    # convert frame to pygame surface
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pygame.image.frombuffer(frame, (width, height), 'RGB')
    return frame

def checkAndCreateThumbnailPath(filePath):
    """ check if there is a tumbnail, if there is, return it as path string, if not, create one and return it as path string"""
    fileName = os.path.basename(filePath)

    if not os.path.exists("./assets/thumbnails"):
        os.mkdir("./assets/thumbnails")

    thumbnailPath = "./assets/thumbnails/" + fileName.replace('.' + fileName.split('.')[-1], '') + '.jpg'
    checkAndCreateThumbnailSurf(filePath)
    return thumbnailPath

def checkAndCreateThumbnailSurf(filePath):
    """ check if there is a tumbnail, if there is, return it as Surface, if not, create one and return it """
    fileName = os.path.basename(filePath)

    if not os.path.exists("./assets/thumbnails"):
        os.mkdir("./assets/thumbnails")

    thumbnailPath = "./assets/thumbnails/" + fileName.replace('.' + fileName.split('.')[-1], '') + '.jpg'

    if not os.path.exists(thumbnailPath):
        thumbnail = createThumbnail(filePath)
        if not thumbnail:
            return None
        if thumbnail.get_width() > thumbnail.get_height():
            thumbnail = pygame.transform.smoothscale(thumbnail, (frameSize[0], frameSize[0] * thumbnail.get_height() // thumbnail.get_width()))
        else:
            thumbnail = pygame.transform.smoothscale(thumbnail, (frameSize[1] * thumbnail.get_width() // thumbnail.get_height(), frameSize[1]))
        pygame.image.save(thumbnail, thumbnailPath)

    else:
        thumbnail = pygame.image.load(thumbnailPath)
    return thumbnail

def checkThumbnail(filePath):
    """ check if there is a tumbnail already created for this file """
    fileBaseName = os.path.basename(filePath)

    if not os.path.exists("./assets/thumbnails"):
        os.mkdir("./assets/thumbnails")

    thumbnailPath = "./assets/thumbnails/" + fileBaseName.replace('.' + fileBaseName.split('.')[-1], '') + '.jpg'

    if not os.path.exists(thumbnailPath):
        return False
    else:
        return True

def folderThumbnail(folderPath):
    """ return thumbnail as path string of a random file in folder """
    thumbnails = []
    playable = findPlayableFiles(folderPath)
    for file in playable:
        if checkThumbnail(file):
            thumbnails.append(file)
    if len(thumbnails) == 0 and len(playable) == 0:
        return None
    elif len(thumbnails) == 0:
        # create thumbnail for the first file
        return checkAndCreateThumbnailPath(playable[0])
    else:
        return random.choice(thumbnails)

def calculateFolderWatched(folderPath):
    """go over all files recursively and calculate watched percentage"""
    playable = findPlayableFiles(folderPath)
    watchedPercentage = 0
    for file in playable:
        if os.path.basename(file) in watched:
            watchedPercentage += 1
    if len(playable) == 0:
        return 0
    return watchedPercentage / len(playable)

def loadFolderToSlider(folderPath, sliderIndex=-1, title="untitled"):
    """ create slider of all files in folder """
    global watched
    frameSlider = FrameSlider(title, path=folderPath)
    for i, file in enumerate(os.listdir(folderPath)):
        # images
        if file.split('.')[-1] in imagesFormats:
            f = Frame()
            f.setSurf(folderPath + '/' + file, name=os.path.basename(folderPath + '/' + file))
            f.path = folderPath + '/' + file
            baseName = os.path.basename(file)
            if baseName in watched:
                f.watched = 1
            frameSlider.addFrame(f)
        # videos
        elif file.split('.')[-1] in videoFormats:
            f = Frame()
            thumbnail = checkAndCreateThumbnailSurf(folderPath + '/' + file)
            f.setSurf(color=(20, 9, 229), name=os.path.basename(folderPath + '/' + file), surf=thumbnail)
            f.path = folderPath + '/' + file
            baseName = os.path.basename(file)
            if baseName in watched:
                f.watched = 1
            frameSlider.addFrame(f)
        # folders
        elif os.path.isdir(folderPath + '/' + file):
            if len(findPlayableFiles(folderPath + '/' + file)) == 0:
                continue
            f = Frame(folder=True)
            thumbnail = folderThumbnail(folderPath + '/' + file)

            if thumbnail:
                f.setSurf(color=(20, 9, 229), name=os.path.basename(folderPath + '/' + file), surf=checkAndCreateThumbnailSurf(thumbnail))
            else:
                f.setSurf(color=RED, name=os.path.basename(folderPath + '/' + file))
            f.path = folderPath + '/' + file
            baseName = os.path.basename(file)
            # configure watched amount
            watchedPercentage = calculateFolderWatched(folderPath + '/' + file)
            f.watched = watchedPercentage
            frameSlider.addFrame(f)
    if sliderIndex == -1:
        Gui().elements.append(frameSlider)
    else:
        Gui().elements.insert(sliderIndex, frameSlider)
    Gui().reposition()

def findPlayableFiles(folder):
    """ return all playable files in folder recursively """
    playableFiles = []
    for file in os.listdir(folder):
        if isAcceptableFormat(file):
            playableFiles.append(folder + '/' + file)
        if os.path.isdir(folder + '/' + file):
            playableFiles += findPlayableFiles(folder + '/' + file)
    return playableFiles

def playRandom(folder):
    playable = findPlayableFiles(folder)
    if len(playable) == 0:
        return
    path = random.choice(playable)
    execute(path)

def init():
    for folder in folderDict:
        path = folderDict[folder]
        loadFolderToSlider(path, title=folder)

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
    win.blit(simflixSurf, (win.get_width() - simflixSurf.get_width() - 20, 20))
    gui.draw()

    pygame.display.update()
    clock.tick(fps)
pygame.quit()