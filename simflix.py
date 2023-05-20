import pygame, os, ast, random, cv2, re, subprocess
from vector import *
from timeit import default_timer as timer
import tkinter
from tkinter import filedialog
pygame.init()

root = tkinter.Tk()
root.withdraw() #use to hide tkinter window

bgColor = (20,20,20)
frameSize = (290, 164)

formatDict = {'imagesFormats': ['png', 'jpg', 'jpeg', 'bmp'], 'videoFormats': ['mp4', 'avi', 'mov', 'flv', 'wmv', 'mpg', 'mpeg', 'mkv']}
acceptableFormats = [formatDict[key] for key in formatDict]

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
nameFont = FontStrokeDeco(pygame.font.SysFont('Segoe UI Black', 16, False))

arrow = [(0,14), (12,0), (14,2), (4,14), (14,26), (12,28)]
arrowSize = Vector(14, 28)

RED = (229,9,20)
SCROLL_SPEED = 50

def isAcceptableFormat(fileName):
    return fileName.split('.')[-1] in acceptableFormats

def loadWatched():
    watched = []
    if os.path.exists("watch.ini"):
        with open("watch.ini", "r") as file:
            for line in file.readlines():
                if line[:-1] not in watched:
                    watched.append(line[:-1])
    return watched

def loadFrequencies():
    success = True
    frequencies = {}
    if os.path.exists("frequencies.ini"):
        with open("frequencies.ini", "r") as file:
            line = file.readline()
            try:
                frequencies = ast.literal_eval(line)
            except:
                success = False
    if not success:
        with open("frequencies.ini", "w+") as file:
            file.write(r"{}")
    return frequencies

def loadRatings():
    ratings = {}
    if os.path.exists("ratings.ini"):
        with open("ratings.ini", "r") as file:
            line = file.readline()
            ratings = ast.literal_eval(line)
    else:
        with open("ratings.ini", "w+") as file:
            file.write(r"{}")
    return ratings

def saveFrequencies():
    global frequencies
    with open("frequencies.ini", "w+") as file:
        file.write(str(frequencies))

def saveRatings():
    global ratings
    with open("ratings.ini", "w+") as file:
        file.write(str(ratings))

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

def loadFolderDict():
    global acceptableFormats
    folderDict = {}
    if os.path.exists("folders.ini"):
        with open("folders.ini", "r") as file:
            line = file.readline()
            folderDict = ast.literal_eval(line)
            if 'AcceptableFormats' in folderDict:
                formats = folderDict['AcceptableFormats']
                acceptableFormats = []
                for formatGroup in formats:
                    acceptableFormats += formatDict[formatGroup]
    else:
        with open("folders.ini", "w+") as file:
            example_dict = {'Title': 'path', 'AcceptableFormats': ['imagesFormats', 'videoFormats']}
            file.write(str(example_dict))
    return folderDict

def saveFolderDict(folderDict):
    with open("folders.ini", "w") as file:
        file.write(str(folderDict))

def addToFolderDict(key, path):
    folderDict[key] = path
    saveFolderDict(folderDict)

def getFrequency(path):
    global frequencies
    if path in frequencies:
        return frequencies[path]
    else:
        return 0
    
def setFrequency(path, freq):
    global frequencies
    frequencies[path] = freq
    saveFrequencies()

def getRating(path):
    global ratings
    if path in ratings:
        return ratings[path]
    else:
        return 0
    
def setRating(path, rating):
    global ratings
    ratings[path] = rating
    if rating == 0:
        if path in ratings:
            del ratings[path]
    saveRatings()

def customArtwork(path):
    file = tkinter.filedialog.askopenfile(mode ='r', filetypes =[('Image files', '*.png *.jpg *.jpeg *.bmp')])
    if file is not None: 
        save_path = os.path.join(".\\assets\\thumbnails", os.path.basename(path))
        image = pygame.image.load(file.name).convert()
        # scale image to thumbnail size
        if image.get_width() > image.get_height():
            image = pygame.transform.smoothscale(image, (frameSize[0], int(frameSize[0] * image.get_height() / image.get_width())))
        else:
            image = pygame.transform.smoothscale(image, (int(frameSize[1] * image.get_width() / image.get_height()), frameSize[1]))
        pygame.image.save(image, save_path + '.jpg')
        return save_path + '.jpg'
    return None

watched = loadWatched()
frequencies = loadFrequencies()
ratings = loadRatings()

folderDict = loadFolderDict()

screenInfo = pygame.display.Info()
screenSize = (screenInfo.current_w - 10, screenInfo.current_h - 70)
win = pygame.display.set_mode(screenSize, pygame.RESIZABLE)
clock = pygame.time.Clock()
fps = 60
pygame.display.set_caption('Simflix')
pygame.display.set_icon(pygame.image.load('./assets/simflixIcon.png'))
simflixSurf = pygame.image.load('./assets/simflix.png').convert_alpha()
simflixSurf = pygame.transform.smoothscale(simflixSurf, (simflixSurf.get_width()*0.4, simflixSurf.get_height()*0.4))
folderIconSurf = pygame.image.load('./assets/folderIcon.png').convert_alpha()
folderIconSurf = pygame.transform.smoothscale(folderIconSurf, (folderIconSurf.get_width()*0.06, folderIconSurf.get_height()*0.06))

highlightSurf = pygame.Surface((frameSize[0], frameSize[1]), pygame.SRCALPHA)
pygame.draw.polygon(highlightSurf, (35,35,35), [(frameSize[0] * 0.6, 0), (frameSize[0] * 0.9, 0), (frameSize[0] * 0.9 - 0.3 * frameSize[0], frameSize[1]), (frameSize[0] * 0.6 - 0.3 * frameSize[0], frameSize[1])])
pygame.draw.polygon(highlightSurf, (35,35,35), [(frameSize[0] * 0.45, 0), (frameSize[0] * 0.5, 0), (frameSize[0] * 0.5 - 0.3 * frameSize[0], frameSize[1]), (frameSize[0] * 0.45 - 0.3 * frameSize[0], frameSize[1])])

starSurfs = [None]
starSurfs.append(pygame.image.load('./assets/star.png').convert_alpha())
starSurfs[1] = pygame.transform.smoothscale(starSurfs[1], (starSurfs[1].get_width()*0.5, starSurfs[1].get_height()*0.5))
for i in range(2, 6):
    surf = pygame.Surface((starSurfs[1].get_width() * i, starSurfs[1].get_height()), pygame.SRCALPHA)
    for j in range(i):
        surf.blit(starSurfs[1], (j * starSurfs[1].get_width(), 0))
    starSurfs.append(surf)

def execute(path):
    command = '"' + path + '"'
    print("executing:", command)
    subprocess.Popen(command, shell=True)

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
        self.animation = None
        self.selectedFrame = None
        self.selectedFrameSlider = None
        self.menu = None

        self.stable = False
        self.distableFlag = False
        self.scroll = 0
        AnimatorInit()
    def reposition(self):
        for i, element in enumerate(self.elements):
            element.pos = Vector(5, 100 + i * (frameSize[1] + 100) + self.scroll)
            element.reposition()
    def select(self, frame):
        self.selectedFrame = frame
    def scrollUp(self):
        self.scroll += SCROLL_SPEED
        if self.scroll > 0:
            self.scroll = 0
            return
        for element in self.elements:
            element.scrollUp()
    def scrollDown(self):
        self.scroll -= SCROLL_SPEED
        for element in self.elements:
            element.scrollDown()
    def step(self):
        self.stable = True
        if self.distableFlag:
            self.distableFlag = False
            self.stable = False
        # step for elements
        for element in self.elements:
            element.step()
            if not element.stable:
                self.stable = False
        # step for animations
        if self.animation:
            self.animation.step()
            self.stable = False
            if self.animation.finished:
                self.animation = None

        # step for selected frame
        if self.selectedFrame:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            if not self.selectedFrame.selected:
                self.selectedFrame = None
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if self.selectedFrameSlider:
            if not self.selectedFrameSlider.selected:
                self.selectedFrameSlider = None
        # step for menu
        if self.menu:
            self.distable()
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
        self.menu.done = True
        if key is None:
            return
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
        elif key == 'Open in explorer':
            openInExplorer(context.path)
        elif key == 'Create Slider':
            path = context.path
            name = os.path.basename(path)
            loadFolderToSlider(path, title=name)
            folderDict[name] = path
            saveFolderDict(folderDict)
        elif key == 'Custom Artwork':
            path = context.path
            thumbnail = customArtwork(path)
            if thumbnail:
                context.setSurf(thumbnail)
        elif key == 'Remove Rating':
            setRating(context.path, 0)
        elif key == 'Rate':
            menu = Menu(event.pos, context)
            menu.addButton('Remove Rating', 'Remove Rating')
            menu.addButtonImage('1 stars', starSurfs[1])
            menu.addButtonImage('2 stars', starSurfs[2])
            menu.addButtonImage('3 stars', starSurfs[3])
            menu.addButtonImage('4 stars', starSurfs[4])
            menu.addButtonImage('5 stars', starSurfs[5])
            menu.finalize()
            self.menu = menu
        elif 'stars' in key:
            stars = int(key[0])
            setRating(context.path, stars)
        elif 'Change Thumbnail' in key:
            path = context.path
            menu = Menu(event.pos, context)
            menu.addButtonImage('0.16 thumb', pygame.transform.scale(createThumbnail(path, 0.16), (200,100)))
            menu.addButtonImage('0.33 thumb', pygame.transform.scale(createThumbnail(path, 0.33), (200,100)))
            menu.addButtonImage('0.5 thumb', pygame.transform.scale(createThumbnail(path, 0.5), (200,100)))
            menu.addButtonImage('0.66 thumb', pygame.transform.scale(createThumbnail(path, 0.66), (200,100)))
            menu.addButtonImage('0.83 thumb', pygame.transform.scale(createThumbnail(path, 0.83), (200,100)))
            menu.finalize()
            self.menu = menu
        elif 'thumb' in key:
            seek = float(key.split()[0])
            thumbnail = checkAndCreateThumbnailSurf(context.path, seek, force=True)
            context.setSurf(surf=thumbnail, name=context.nameStr)


    def handleEvents(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.distable()
            if event.button == 1:
                mouse = event.pos
                if self.menu:
                    # if mouse is not on menu
                    if mouse[0] < self.menu.pos.x or mouse[0] > self.menu.pos.x + self.menu.size[0] or mouse[1] < self.menu.pos.y or mouse[1] > self.menu.pos.y + self.menu.size[1]:
                        self.menu = None
                    else:
                        key = self.menu.handleEvents(event)
                        self.handleMenuEvents(key)
                    if self.menu and self.menu.done:
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
                        freq = self.selectedFrame.getFrequency()
                        freq += 1
                        setFrequency(path, freq)
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
                        menu.addButton('Open in explorer', 'Open in explorer')
                        menu.addButton('Change Thumbnail', 'Change Thumbnail')
                        menu.addButton('Rate', 'Rate')
                        menu.finalize()
                        self.menu = menu
                    else:
                        # right click on folder
                        menu = Menu(event.pos, self.selectedFrame)
                        menu.addButton('Play Random', 'Play Random')
                        menu.addButton('Mark Folder as unwatched', 'Mark Folder as unwatched')
                        menu.addButton('Open in explorer', 'Open in explorer')
                        menu.addButton('Create Slider', 'Create Slider')
                        menu.addButton('Custom Artwork', 'Custom Artwork')
                        menu.finalize()
                        self.menu = menu
            elif event.button == 4:
                self.scrollUp()
            elif event.button == 5:
                self.scrollDown()
        elif event.type == pygame.KEYDOWN:
            self.distable()
            if event.key == pygame.K_DELETE:
                if self.selectedFrameSlider:
                    # remove the frame slider
                    self.elements.remove(self.selectedFrameSlider)
                    value = self.selectedFrameSlider.path
                    for key, val in folderDict.items():
                        if val == value:
                            del folderDict[key]
                            break
                    self.selectedFrame = None
                    self.selectedFrameSlider = None
                    saveFolderDict(folderDict)
    def distable(self):
        self.stable = False
        self.distableFlag = True

class FrameSlider:
    """
    A slider that contains frames
    """
    def __init__(self, title, path=''):
        self.frames = []
        self.title = handleName(title)
        self.titleSurf = titleFont.render(self.title, True, (255,255,255))
        self.backSurf = titleFont.render("Back", True, (255,255,255))
        self.pos = Vector()
        self.slideIndex = 0
        self.selected = False
        self.path = path
        self.stable = False
    def scrollUp(self):
        self.pos.y += SCROLL_SPEED
        self.reposition()

    def scrollDown(self):
        self.pos.y -= SCROLL_SPEED
        self.reposition()
        
    def addFrame(self, frame):
        frame.parent = self
        pos = Vector(len(self.frames) * (8 + frameSize[0]), 5 + self.titleSurf.get_height())
        self.frames.append(frame)
        frame.setPos(pos)
    
    def reposition(self):
        for i, frame in enumerate(self.frames):
            index = i - self.slideIndex
            x = index * (8 + frameSize[0])
            y = 5 + self.titleSurf.get_height()
            frame.setPos(Vector(x, y))

    def step(self):
        self.stable = True
        for frame in self.frames:
            frame.step()
            if not frame.stable:
                self.stable = False
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
        if Gui().animation:
            return
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

class AnimatorInit:
    def __init__(self):
        Gui().animation = self
        self.stable = False
        self.finished = False
    def step(self):
        self.stable = True
        self.finished = True
    def draw(self):
        pass

class AnimatorSlider:
    """
        Animates a slider to move
    """
    def __init__(self, slider, offset):
        Gui().animation = self
        self.slider = slider
        self.offset = offset

        self.startVal = 0
        self.endVal = offset
        self.t = 0
        self.dt = 2 / fps

        self.framesInitialValues = [vectorCopy(i.pos) for i in self.slider.frames]
        self.framesFinalValues = [i.pos + offset for i in self.slider.frames]
        self.finished = False
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
            self.finished = True

class Frame:
    """
        A frame is a single icon with an image that can be selected and clicked
    """
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
        self.stable = False
        self.nameStr = None
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
            self.nameStr = name
            nameSurf = nameFont.render(name, True, (255,255,255))
            if nameSurf.get_width() > self.surf.get_width():
                self.surf.blit(nameSurf, (10, frameSize[1] - nameSurf.get_height()))
            else:
                self.surf.blit(nameSurf, (frameSize[0]/2 - nameSurf.get_width()/2, frameSize[1] - nameSurf.get_height()))

        # add border
        borderMask = pygame.Surface(frameSize, pygame.SRCALPHA)
        borderMask.fill((255,255,255,255))
        pygame.draw.rect(borderMask, (0,0,0,0), ((0,0), frameSize), 0, 4)
        self.surf.blit(borderMask, (0,0), special_flags=pygame.BLEND_RGBA_SUB)
    def getFrequency(self):
        global frequencies
        return getFrequency(self.path)
    def getRating(self):
        global ratings
        return getRating(self.path)
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

        if self.animOffsets[0] < 0.00001 or self.animOffsets[1] < 0.00001:
            self.stable = True
        else:
            self.stable = False
    def draw(self):
        # draw rating
        if self.getRating() != 0:
            rating = self.getRating()
            x = self.pos[0] + frameSize[0] // 2 - starSurfs[rating].get_width() // 2
            y = self.pos[1] + frameSize[1] - starSurfs[rating].get_height() - 5 + self.animOffsets[0] * 68
            win.blit(starSurfs[rating], (x, y))

        # draw watch indicator
        if self.watched != 0: 
            start = self.pos + Vector(frameSize[0]/2 - 80, frameSize[1] + 10)
            start.y += self.animOffsets[0] * 15
            end = self.pos + Vector(frameSize[0]/2 + 80, frameSize[1] + 10)
            end.y += self.animOffsets[0] * 15
            pygame.draw.line(win, (91,91,91), start, end, 3)
            pygame.draw.line(win, RED, start, start + (end - start) * self.watched, 3)

        # draw frame
        surf = self.surf.copy()
        posx =  self.animOffsets[0] * frameSize[0] - frameSize[0] - 35
        surf.blit(highlightSurf, (posx,0), special_flags=pygame.BLEND_RGBA_ADD)
        scale = 1 + self.animOffsets[1] * 0.2
        surf = pygame.transform.smoothscale(surf, (int(frameSize[0] * scale), int(frameSize[1] * scale)))
        posOffset = (int(frameSize[0] * (1 - scale) / 2), int(frameSize[1] * (1 - scale) / 2))
        win.blit(surf, self.pos + posOffset)

class Menu:
    def __init__(self, pos, context):
        self.pos = tup2vec(pos)
        self.size = Vector()
        self.elements = []
        self.context = context
        self.done = False
    def addButton(self, key, text):
        button = MenuButton(text, key)
        self.elements.append(button)
        self.recalculate()
    def addButtonImage(self, key, image):
        button = MenuButtonImage(image, key)
        self.elements.append(button)
        self.recalculate()
    def finalize(self):
        # if menu is out of screen to the right, move it to the left
        if self.pos[0] + self.size[0] > win.get_width():
            self.pos[0] = self.pos[0] - self.size[0]
            for element in self.elements:
                element.pos[0] -= self.size[0]
        # if menu is out of screen to the bottom, move it to the top
        if self.pos[1] + self.size[1] > win.get_height():
            self.pos[1] = self.pos[1] - self.size[1]
            for element in self.elements:
                element.pos[1] -= self.size[1]
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

class MenuButtonImage(MenuButton):
    def __init__(self, image, key):
        self.key = key
        self.image = image

        self.pos = Vector()
        self.size = Vector()

        self.selected = False
        self.setTextSurf()
    def setTextSurf(self):
        self.size = Vector(self.image.get_width() + 20, self.image.get_height() + 20)
    def draw(self):
        if self.selected:
            pygame.draw.rect(win, (255,255,255), (self.pos, self.size))
        win.blit(self.image, (self.pos[0] + 10 , self.pos[1] + self.size[1]/2 - self.image.get_height()/2))

def factorToSize(factor, orgSize):
    return (orgSize[0] * factor, orgSize[1] * factor)

def createThumbnail(filePath, seek=0.5):
    """ returns thumbnail Surface from path file """
    file_extension = os.path.splitext(filePath)[1]
    if file_extension.replace('.', '') in formatDict['imagesFormats']:
        frame = pygame.image.load(filePath)
        return frame
    importedVideo = cv2.VideoCapture(filePath)
    width = int(importedVideo.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(importedVideo.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(importedVideo.get(cv2.CAP_PROP_FRAME_COUNT))
    importedVideo.set(cv2.CAP_PROP_POS_FRAMES, int(length * seek))
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

def checkAndCreateThumbnailSurf(filePath, seek=0.5, force=False):
    """ check if there is a tumbnail, if there is, return it as Surface, if not, create one and return it """
    fileName = os.path.basename(filePath)

    if not os.path.exists("./assets/thumbnails"):
        os.mkdir("./assets/thumbnails")

    thumbnailPath = "./assets/thumbnails/" + fileName.replace('.' + fileName.split('.')[-1], '') + '.jpg'

    if not os.path.exists(thumbnailPath) or force:
        thumbnail = createThumbnail(filePath, seek)
        frame_surf = pygame.Surface(frameSize)
        if not thumbnail:
            return None
        
        new_size = (0,0)
        location = (0,0)

        # scale by width:
        new_width = frameSize[0]
        new_height = int(thumbnail.get_height() * (frameSize[0] / thumbnail.get_width()))
        if new_height > frameSize[1]:
            new_size = (new_width, new_height)
            location = (0, -(new_height - frameSize[1]) // 2)
        else:
            # scale by height
            new_height = frameSize[1]
            new_width = int(thumbnail.get_width() * (frameSize[1] / thumbnail.get_height()))
            new_size = (new_width, new_height)
            location = (-(new_width - frameSize[0]) // 2, 0)

        # scale down thumbnail
        try:
            thumbnail = pygame.transform.smoothscale(thumbnail, new_size)
        except ValueError:
            thumbnail = pygame.transform.scale(thumbnail, new_size)

        frame_surf.blit(thumbnail, location)
        thumbnail = frame_surf

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
    # check if there is a thumbnail for the folder
    folderThumbnailPath = ".\\assets\\thumbnails\\" + os.path.basename(folderPath) + '.jpg'
    if os.path.exists(folderThumbnailPath):
        return folderThumbnailPath
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

def addFrame(filePath):
    """ add image frame to slider """
    f = Frame()
    if os.path.splitext(filePath)[1].replace('.', '') in formatDict['imagesFormats']:
        f.setSurf(filePath, name=os.path.basename(filePath))
    elif os.path.splitext(filePath)[1].replace('.', '') in formatDict['videoFormats']:
        thumbnail = checkAndCreateThumbnailSurf(filePath)
        f.setSurf(color=(20, 9, 229), name=os.path.basename(filePath), surf=thumbnail)
    f.path = filePath
    baseName = os.path.basename(filePath)
    if baseName in watched:
        f.watched = 1
    return f

def loadFolderToSlider(folderPath, sliderIndex=-1, title="untitled"):
    """ create slider of all files in folder """
    if not os.path.isdir(folderPath):
        print('[ERROR] folder', folderPath, 'does not exist')
        return
    global watched
    frameSlider = FrameSlider(title, path=folderPath)
    for i, file in enumerate(os.listdir(folderPath)):
        # folder
        if os.path.isdir(folderPath + '\\' + file):
            playables = findPlayableFiles(folderPath + '\\' + file)
            if len(playables) == 0:
                # no playable files in folder
                continue
            elif len(playables) == 1:
                # only one playable file in folder, add it to slider
                f = addFrame(playables[0])
                frameSlider.addFrame(f)
                continue

            f = Frame(folder=True)
            thumbnail = folderThumbnail(folderPath + '\\' + file)

            if thumbnail:
                f.setSurf(color=(20, 9, 229), name=os.path.basename(folderPath + '\\' + file), surf=checkAndCreateThumbnailSurf(thumbnail))
            else:
                f.setSurf(color=RED, name=os.path.basename(folderPath + '\\' + file))
            f.path = folderPath + '\\' + file
            # configure watched amount
            watchedPercentage = calculateFolderWatched(folderPath + '\\' + file)
            f.watched = watchedPercentage
            frameSlider.addFrame(f)
        # file
        elif isAcceptableFormat(file):    
            f = addFrame(folderPath + '\\' + file)
            frameSlider.addFrame(f)
    
    # sort frames by (frequency, name)
    frameSlider.frames.sort(key=lambda x: (-x.getFrequency(), x.path))

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
            playableFiles.append(folder + '\\' + file)
        if os.path.isdir(folder + '\\' + file):
            playableFiles += findPlayableFiles(folder + '\\' + file)
    return playableFiles

def playRandom(folder):
    playable = findPlayableFiles(folder)
    if len(playable) == 0:
        return
    path = random.choice(playable)
    execute(path)

def openInExplorer(path):
    """ open folder in explorer """
    if os.path.isfile(path):
        path = os.path.dirname(path)
    os.startfile(path)

def init():
    for folder in folderDict:
        path = folderDict[folder]
        if folder == 'AcceptableFormats':
            continue
        loadFolderToSlider(path, title=folder)

Gui()
init()

done = False
while not done:
    for event in pygame.event.get():
        Gui().handleEvents(event)
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                Gui().selectedFrameSlider.slide('left')
            elif event.key == pygame.K_RIGHT:
                Gui().selectedFrameSlider.slide('right')
            elif event.key == pygame.K_UP:
                Gui().scrollUp()
            elif event.key == pygame.K_DOWN:
                Gui().scrollDown()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        done = True

    # step
    Gui().step()

    # draw
    if not Gui().stable:
        win.fill(bgColor)
        
        Gui().draw()
        win.fill(bgColor, (0, 0, win.get_width(), 100))
        win.blit(simflixSurf, (win.get_width() - simflixSurf.get_width() - 20, 20))

        pygame.display.update()
        clock.tick(fps)
    
pygame.quit()