from math import cos, pow, log2
from msilib.schema import Verb
import pygame, os, argparse, subprocess, datetime
from random import randint, choice
from main import renderMountains, renderCloud, feels
from perlinNoise import generateNoise
from vector import *
import tkinter
from tkinter.filedialog import askopenfile 

pygame.init()
pygame.font.init()
font1 = pygame.font.Font("fonts\pixelFont.ttf", 5)
fpsClock = pygame.time.Clock()
fps = 30

scalingFactor = 3
winWidth = 1280 // scalingFactor
winHeight = 720 // scalingFactor
win = pygame.Surface((winWidth, winHeight))

screenWidth = 1280
screenHeight = 720
screen = pygame.display.set_mode((screenWidth,screenHeight))

WHITE = (255,255,255,255)
BLACK = (0,0,0,255)

MENU_ELEMENT = -1
MENU_MENU   = 0
MENU_BUTTON = 1
MENU_UPDOWN = 2
MENU_TOGGLE = 3
MENU_COMBOS = 4
MENU_TEXT   = 5
MENU_DIV	= 6
MENU_IMAGE	= 7
MENU_INPUT	= 8
HORIZONTAL = 0
VERTICAL = 1

trueFalse = ["-f", "-dig", "-dark", "-used", "-closed", "-warped", "-rg", "-place", "-art"]
feelIndex = randint(0, len(feels) - 1)

class BackGround:
	def __init__(self):
		self.feelIndex = feelIndex
		self.recreate()
		self.cloudsPos = [i * (winWidth + 170)/3 for i in range(3)]
	def recreate(self):
		feel = feels[self.feelIndex]
		self.imageMountain = renderMountains((180, 110), feel[3])
		self.imageMountain2 = renderMountains((180, 150), feel[2])
		colorRect = pygame.Surface((2,2))
		pygame.draw.line(colorRect, feel[0], (0,0), (2,0))
		pygame.draw.line(colorRect, feel[1], (0,1), (2,1))
		self.imageSky = pygame.transform.smoothscale(colorRect, (winWidth, winHeight))
		self.clouds = [renderCloud() for i in range(3)]
	def draw(self):
		win.blit(self.imageSky, (0,0))
		x = 0
		while x < winWidth:
			win.blit(self.imageMountain, (x, winHeight - self.imageMountain.get_height()))
			win.blit(self.imageMountain2, (x, winHeight - self.imageMountain.get_height()))
			x += self.imageMountain.get_width()
		for i, c in enumerate(self.clouds):
			self.cloudsPos[i] = self.cloudsPos[i] + 0.1
			if self.cloudsPos[i] > winWidth:
				self.cloudsPos[i] = -170
			win.blit(c, (self.cloudsPos[i] ,winHeight // 2))

def browseFile():
	root = tkinter.Tk()
	root.withdraw()
	file = askopenfile(mode ='r', filetypes =[('Image Files', '*.png')])
	if file is not None: 
		return file.name
	
def mouseInWin():
	return (pygame.mouse.get_pos()[0] / scalingFactor, pygame.mouse.get_pos()[1] / scalingFactor)

def evaluateMenuForm():
	outdict = {}
	for menu in Menu._reg:
		menu.evaluate(outdict)
	return outdict

class Menu:
	_reg = []
	_buttonColor = (82,65,60)
	_textElementColor = (62,45,40)
	_toggleColor = (0,255,0)
	_selectedColor = (0,180,0)
	_unicode = "|"
	def __init__(self, pos=None, size=None, name="", orientation=VERTICAL, margin=1, register=False, customSize=None):
		self.pos = [0,0]
		if pos:
			self.pos = pos
		self.size = [0,0]
		if size:
			self.size = size
		self.name = name
		self.elements = []
		self.orientation = orientation
		self.event = None
		self.margin = margin # distance between elements
		self.type = MENU_MENU
		self.menu = None
		self.customSize = customSize
		if register:
			Menu._reg.append(self)
	def addElement(self, newElement):
		newElement.menu = self
		self.elements.append(newElement)
		self.recalculate()
	def recalculate(self):
		numElements = len(self.elements)
		customSizedElements = [i for i in self.elements if i.customSize]
		CustomSizedPortion = sum(i.customSize for i in customSizedElements)
		emptySpace = self.size[self.orientation] - CustomSizedPortion - (numElements - 1) * self.margin
		if numElements - len(customSizedElements) != 0:
			sizePerElem = emptySpace / (numElements - len(customSizedElements))
		
		accSize = 0
		for i, element in enumerate(self.elements):
			element.size[0] = self.size[0]
			element.size[1] = self.size[1]
			if element.customSize:
				element.size[self.orientation] = element.customSize
			else:
				element.size[self.orientation] = sizePerElem
			
			element.pos[0] = self.pos[0]
			element.pos[1] = self.pos[1]
			element.pos[self.orientation] = self.pos[self.orientation] + accSize
			accSize += element.size[self.orientation] + self.margin

		for i, element in enumerate(self.elements):
			if element.type == MENU_MENU:
				element.recalculate()
			if element.type == MENU_IMAGE:
				element.setImage(element.imagePath)
	def getValues(self):
		values = {}
		for element in self.elements:
			values[element.key] = element.value
		return values
	def step(self):
		updated = False
		event = None
		for element in self.elements:
			result = element.step()
			if result:
				updated = True
				event = result
		self.event = event
		return event
	def update(self):
		pass
	def processInternalEvents(self):
		"""clicked on element in menu"""
		if not self.event:
			return
		elif self.event.type == MENU_TOGGLE:
			self.event.value = not self.event.value
		elif self.event.type == MENU_COMBOS:
			self.event.advance()
		elif self.event.type == MENU_UPDOWN:
			self.event.advance()
		elif self.event.type == MENU_INPUT:
			self.event.focus = True
			Menu._unicode = "|"
	def evaluate(self, dic):
		for element in self.elements:
			element.evaluate(dic)
	def draw(self):
		for element in self.elements:
			element.draw()
	def insert(self, type=MENU_BUTTON, key="key", value="value", text=None, customSize=None, items=None, stepSize=None,
					limitMin=False, limitMax=False, limMin=0, limMax=100, values=None, showValue=True, image=None, inputText=""):
		if type == MENU_BUTTON:
			b = MenuElementButton()
		elif type == MENU_TOGGLE:
			b = MenuElementToggle()
		elif type == MENU_COMBOS:
			b = MenuElementComboSwitch()
			if items:
				b.setItems(items)
		elif type == MENU_UPDOWN:
			b = MenuElementUpDown()
			if stepSize:
				b.stepSize = stepSize
			b.limitMin = limitMin
			b.limitMax = limitMax
			b.limMin = limMin
			b.limMax = limMax
			if values:
				b.values = values
			b.showValue = showValue
		elif type == MENU_INPUT:
			b = MenuElementInput()
			b.inputText = inputText
		elif type == MENU_IMAGE:
			b = MenuElementImage()
			if image:
				b.setImage(image)
		elif type == MENU_MENU:
			b = Menu()
		elif type == MENU_TEXT:
			b = MenuElementText()

		b.key = key
		b.value = value
		if text:
			b.renderSurf(text)
		if customSize:
			b.customSize = customSize
		self.addElement(b)
		return b

class MenuElement:
	def __init__(self):
		self.pos = [0,0]
		self.size = [0,0]
		self.name = "element"
		self.customSize = None
		self.color = Menu._buttonColor
		self.selected = False
		self.key = "key"
		self.value = "value"
		self.menu = None
		self.type = MENU_ELEMENT
		self.surf = None
		self.initialize()
	def initialize(self):
		pass
	def setIndex(self, num):
		self.index = num
	def renderSurf(self, text=None):
		if text:
			self.text = text
		self.surf = font1.render(self.text, True, WHITE)
	def evaluate(self, dic):
		dic[self.key] = self.value
	def step(self):
		pass
	def draw(self):
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(win, color, (self.pos, self.size))
		if self.surf:
			win.blit(self.surf, (self.pos[0] + self.size[0]/2 - self.surf.get_width()/2, self.pos[1] + self.size[1]/2 - self.surf.get_height()/2))

class MenuElementText(MenuElement):
	def initialize(self):
		self.color = Menu._textElementColor

class MenuElementButton(MenuElement):
	def initialize(self):
		self.text = "Bu"
		self.surf = None
		self.type = MENU_BUTTON
	def step(self):
		mousePos = mouseInWin()
		posInButton = (mousePos[0] - self.pos[0], mousePos[1] - self.pos[1])
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			self.selected = True
			return self
		else:
			self.selected = False
		return None
	def draw(self):
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(win, color, (self.pos, self.size))
		win.blit(self.surf, (self.pos[0] + self.size[0]/2 - self.surf.get_width()/2, self.pos[1] + self.size[1]/2 - self.surf.get_height()/2))
	
class MenuElementUpDown(MenuElementButton):
	def initialize(self):
		self.text = ""
		self.showValue = True
		self.value = 0
		self.mode = 0
		self.renderSurf(str(self.value))
		self.type = MENU_UPDOWN
		self.limitMin = False
		self.limitMax = False
		self.limMin = 0
		self.limMax = 100
		self.values = None
		self.stepSize = 1
	def advance(self):
		if self.values:
			current = self.values.index(self.value)
			current = (current + 1) % len(self.values)
			self.value = self.values[current]
			return
		pot = self.value + self.mode * self.stepSize
		if self.limitMin and pot < self.limMin:
			pot = self.limMin
		if self.limitMax and pot > self.limMax:
			pot = self.limMax
		self.value = pot
	def step(self):
		mousePos = mouseInWin()
		posInButton = (mousePos[0] - self.pos[0], mousePos[1] - self.pos[1])
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			self.selected = True
			if posInButton[1] > posInButton[0]: # need replacement
				self.mode = -1
			else:
				self.mode = 1
			if self.showValue:
				self.renderSurf(str(self.value))
			return self
		else:
			self.selected = False
		return None
	def draw(self):
		border = 1
		arrowSize = self.size[1] // 2
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(win, color, (self.pos, self.size))
		pygame.draw.polygon(win, WHITE, [(self.pos[0] + self.size[0] - arrowSize, self.pos[1] + border), (self.pos[0] + self.size[0] - border - 1, self.pos[1] + border), (self.pos[0] + self.size[0] - border - 1, self.pos[1] + arrowSize)])
		pygame.draw.polygon(win, WHITE, [(self.pos[0] + border ,self.pos[1] + self.size[1] - arrowSize), (self.pos[0] + border, self.pos[1] + self.size[1] - border - 1), (self.pos[0] + arrowSize, self.pos[1] + self.size[1] - border - 1)])
		win.blit(self.surf, (self.pos[0] + self.size[0]/2 - self.surf.get_width()/2, self.pos[1] + self.size[1]/2 - self.surf.get_height()/2))

class MenuElementToggle(MenuElementButton):
	def initialize(self):
		self.text = "Tg"
		self.surf = None
		self.value = False
		self.type = MENU_TOGGLE
		self.border = 1
	def draw(self):
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(win, color, (self.pos, self.size))
		if self.value:
			pygame.draw.rect(win, Menu._toggleColor, ((self.pos[0] + self.border, self.pos[1] + self.border), (self.size[0] - 2 * self.border, self.size[1] - 2 * self.border)))
		win.blit(self.surf, (self.pos[0] + self.size[0]/2 - self.surf.get_width()/2, self.pos[1] + self.size[1]/2 - self.surf.get_height()/2))

class MenuElementComboSwitch(MenuElementButton):
	def initialize(self):
		self.surf = None
		self.value = "value"
		self.currentIndex = 0
		self.type = MENU_COMBOS
		self.items = []
		self.forward = False
	def setItems(self, strings):
		for string in strings:
			surf = font1.render(string, True, WHITE)
			self.items.append((string, surf))
		self.value = self.items[self.currentIndex][0]
	def step(self):
		mousePos = mouseInWin()
		posInButton = (mousePos[0] - self.pos[0], mousePos[1] - self.pos[1])
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			self.selected = True
			if posInButton[0] > self.size[0] // 2:
				self.forward = True
			else:
				self.forward = False
			return self
		else:
			self.selected = False
		return None
	def advance(self):
		addition = 1 if self.forward else -1
		self.currentIndex = (self.currentIndex + addition) % len(self.items)
		self.value = self.items[self.currentIndex][0]
	def draw(self):
		border = 5
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(win, color, (self.pos, self.size))
		if self.currentIndex == -1:
			surf = self.surf
		else:
			surf = self.items[self.currentIndex][1]
		win.blit(surf, (self.pos[0] + self.size[0]/2 - surf.get_width()/2, self.pos[1] + self.size[1]/2 - surf.get_height()/2))
		arrowBorder = 3
		arrowSize = self.size[1]
		polygonRight = [Vector(self.size[0] - arrowSize / 2, arrowBorder), Vector(self.size[0] - arrowBorder, self.size[1] / 2), Vector(self.size[0] - arrowSize / 2, self.size[1] - arrowBorder)]
		polygonLeft = [Vector(arrowSize / 2, arrowBorder), Vector(arrowBorder, self.size[1] / 2), Vector(arrowSize / 2, self.size[1] - arrowBorder)]
		pygame.draw.polygon(win, WHITE, [tup2vec(self.pos) + i for i in polygonRight])
		pygame.draw.polygon(win, WHITE, [tup2vec(self.pos) + i for i in polygonLeft])

class MenuElementDivider(MenuElement):
	def initialize(self):
		self.type = MENU_DIV
		self.divSize = 5
	def draw(self):
		pass

class MenuElementImage(MenuElement): #make it movable ? :)
	def initialize(self):
		self.type = MENU_IMAGE
		self.imageSurf = None
		self.imagePath = None
		self.dragDx = 0
	def setImage(self, path):
		if self.size[0] < 0 or self.size[1] < 0:
			return
		self.surf = pygame.Surface(self.size, pygame.SRCALPHA)
		self.imagePath = path
		self.value = path
		self.imageSurf = pygame.image.load(path).convert()
		ratio = self.imageSurf.get_width() / self.imageSurf.get_height()
		imageSize = (self.size[1] * ratio, self.size[1])
		self.imageSurf = pygame.transform.smoothscale(self.imageSurf, (imageSize[0], imageSize[1]))
		self.imageSurf.set_colorkey((0,0,0))
		self.dragDx = - self.imageSurf.get_width() // 2
		self.recalculateImage()
	def draw(self):
		win.blit(self.surf, self.pos)
		pygame.draw.rect(win, Menu._buttonColor, (self.pos, self.surf.get_size()), 2)
	def recalculateImage(self):
		self.surf.fill((0,0,0,0))
		self.surf.blit(self.imageSurf, (self.size[0] // 2  + self.dragDx, 0))
	def step(self):
		mousePos = mouseInWin()
		posInButton = (mousePos[0] - self.pos[0], mousePos[1] - self.pos[1])
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			# if pygame mouse pressed
			if pygame.mouse.get_pressed()[0]:
				vel = pygame.mouse.get_rel()
				if abs(vel[0]) > 100:
					return
				self.dragDx += vel[0] / 2
				if self.imageSurf.get_width() < self.size[0]:
					return
				if self.dragDx > -self.size[0] // 2:
					self.dragDx = -self.size[0] // 2
				elif self.dragDx < -self.imageSurf.get_width() + self.size[0] // 2:
					self.dragDx = -self.imageSurf.get_width() + self.size[0] // 2
					

				self.recalculateImage()

class MenuElementInput(MenuElementButton):
	def initialize(self):
		self.focus = False
		self.inputText = "auto"
		self.value = self.inputText
		self.type = MENU_INPUT
		self.surf = None
	def typing(self):
		if self.inputText != Menu._unicode:
			self.inputText = Menu._unicode
			self.renderSurf(self.inputText)

	def step(self):
		if not self.menu.event is self:
			if self.focus:
				self.value = self.inputText[:-1]
				self.renderSurf(self.value)
			self.focus = False
		if self.focus:
			self.typing()
		mousePos = mouseInWin()
		posInButton = (mousePos[0] - self.pos[0], mousePos[1] - self.pos[1])
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			self.selected = True
			return self
		else:
			self.selected = False
		return None

def grabMapsFrom(path, maps):
	for imageFile in os.listdir(path):
		if imageFile[-4:] != ".png":
			continue
		string = path + "/" + imageFile
		maps.append(string)

maps = []
grabMapsFrom('wormsMaps', maps)
if os.path.exists('wormsMaps/moreMaps'):
	grabMapsFrom('wormsMaps/moreMaps', maps)

def handleMenuEvents(event):
	key = event.key
	# print(event.key, event.value)
	if key == "random_image":
		path = choice(maps)
		picture.setImage(path)
	if key == "-feel":
		bg.feelIndex = event.value
		bg.recreate()
	if key == "browse":
		filepath = browseFile()
		if filepath:
			picture.setImage(filepath)
	if key == "generate":
		# mapChoice = subprocess.check_output("python ./perlinNoise.py -d").decode('utf-8')[:-2]
		width, height = 800, 300
		noise = generateNoise(width, height)
		x = datetime.datetime.now()
		if not os.path.exists("wormsMaps/PerlinMaps"):
			os.mkdir("wormsMaps/PerlinMaps")
		imageString = "wormsMaps/PerlinMaps/perlin" + str(x.day) + str(x.month) + str(x.year % 100) + str(x.hour) + str(x.minute) + ".png"
		pygame.image.save(noise, imageString)
		picture.setImage(imageString)
	if key == "play":
		values = evaluateMenuForm()
		string = "main.py "
		for key in values.keys():
			if key[0] == "-":
				if key == "--game_mode":
					modeDict = {"battle" : 0, "points" : 1, "terminator" : 2, "targets" : 3, "david vs goliath" : 4, "ctf" : 5, "arena" : 6}
					string += key + " " + str(modeDict[values[key]]) + " "
					continue
				if key in trueFalse:
					if values[key]:
						string += key + " "
					continue
				if key == "-random":
					if values[key] == "none":
						continue
					string += key + " "
					if values[key] == "in team":
						string += "2" + " "
					else:
						string += "1" + " "
					continue
				if key == "-map":
					string += key + " " + values[key] + " "
					continue
				if key == "-ratio" and values[key] == "auto":
					continue
				string += key + " " + str(values[key]) + " "
		# print(string)
		subprocess.Popen(string, shell=True)
		exit(0)

picture = None

def handleEvents(event):
	if event.type == pygame.MOUSEBUTTONDOWN:
		if event.button == 1:
			for menu in Menu._reg:
				if menu.event:
					menu.processInternalEvents()
					handleMenuEvents(menu.event)
	if event.type == pygame.KEYDOWN:
		Menu._unicode = Menu._unicode[:-1]
		Menu._unicode += event.unicode
		Menu._unicode += "|"

def initializeMenuOptions():
	global picture
	mainMenu = Menu(name="menu", pos=[40,40], size=[winWidth - 80, 160], register=True)
	mainMenu.insert(MENU_BUTTON, key="play", text="play", customSize=16)
	
	optionsAndPictureMenu = Menu(name="options and picture", orientation=HORIZONTAL)
	
	# options vertical sub menu
	optionsMenu = Menu(name="options")

	subMode = Menu(orientation=HORIZONTAL, customSize=15)
	subMode.insert(MENU_TEXT, text="game mode")
	subMode.insert(MENU_COMBOS, key="--game_mode", text="battle", items=["battle", "points", "terminator", "targets", "david vs goliath", "ctf", "arena"])
	optionsMenu.addElement(subMode)
	
	# toggles
	toggles = [("cool down", "-used", True), ("artifacts", "-art", True), ("closed map", "-closed", False), ("forts", "-f", False), ("digging", "-dig", False), ("darkness", "-dark", False)]
	for i in range(0, len(toggles) - 1, 2):
		first = toggles[i]
		second = toggles[i + 1]
		subOpt = Menu(orientation = HORIZONTAL, customSize = 15)
		subOpt.insert(MENU_TOGGLE, key=first[1], text=first[0], value=first[2])
		subOpt.insert(MENU_TOGGLE, key=second[1], text=second[0], value=second[2])
		optionsMenu.addElement(subOpt)
	
	# counters
	counters = [("worms per team", 8, 1, 8, 1, "-wpt"), ("worm health", 100, 0, 1000, 50, "-ih"), ("packs", 1, 0, 10, 1, "-pm")]
	for c in counters:
		subOpt = Menu(orientation=HORIZONTAL)
		subOpt.insert(MENU_TEXT, text=c[0])
		subOpt.insert(MENU_UPDOWN, key=c[5], value=c[1], text=str(c[1]), limitMax=True, limitMin=True, limMin=c[2], limMax=c[3], stepSize=c[4])		
		optionsMenu.addElement(subOpt)
	
	# random turns
	subMode = Menu(orientation=HORIZONTAL)
	subMode.insert(MENU_TEXT, text="random turns")
	subMode.insert(MENU_COMBOS, key="-random", items=["none", "in team", "complete"])	
	optionsMenu.addElement(subMode)
	
	# sudden death
	subMode = Menu(orientation=HORIZONTAL)
	subMode.insert(MENU_TOGGLE, key="sudden death toggle", value=True, text="sudden death")
	subMode.insert(MENU_UPDOWN, key="-sd", value=16, text="16", limitMin=True, limMin=0, customSize=19)
	subMode.insert(MENU_COMBOS, key="sudden death style", items=["all", "tsunami", "plague"])
	optionsMenu.addElement(subMode)
	
	optionsAndPictureMenu.addElement(optionsMenu)

	# map options vertical sub menu
	mapMenu = Menu(name="map menu", orientation=VERTICAL)
	picture = mapMenu.insert(MENU_IMAGE, key="-map", image=choice(maps))
	
	# map buttons
	subMap = Menu(orientation = HORIZONTAL, customSize=15)
	subMap.insert(MENU_BUTTON, key="random_image", text="random")
	subMap.insert(MENU_BUTTON, key="browse", text="browse")
	subMap.insert(MENU_BUTTON, key="generate", text="generate")

	mapMenu.addElement(subMap)
	
	# recolor & ratio
	subMap = Menu(orientation = HORIZONTAL, customSize = 15)
	subMap.insert(MENU_TOGGLE, key="-rg", text="recolor")
	subMap.insert(MENU_TEXT, text="ratio")
	subMap.insert(MENU_INPUT, key="-ratio", text="auto", inputText="auto")
	
	mapMenu.addElement(subMap)
	optionsAndPictureMenu.addElement(mapMenu)
	mainMenu.addElement(optionsAndPictureMenu)
	
	# background feel menu
	bgMenu = Menu(pos=[winWidth - 20, winHeight - 20], size=[20, 20], register=True)
	bgMenu.insert(MENU_UPDOWN, text="bg", key="-feel", value=feelIndex, values=[i for i in range(len(feels))], showValue=False)

# setup
initializeMenuOptions()

bg = BackGround()

### main loop

run = True
while run:
	for event in pygame.event.get():
		handleEvents(event)
		if event.type == pygame.QUIT:
			run = False
	keys = pygame.key.get_pressed()
	if keys[pygame.K_ESCAPE]:
		run = False
	
	# step
	for menu in Menu._reg:
		menu.step()

	# draw
	bg.draw()
	
	for menu in Menu._reg:
		menu.draw()

	screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
	pygame.display.update()
	fpsClock.tick()
  
pygame.quit()