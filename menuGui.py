import pygame
from vector import *

class Gui:
	_instance = None
	def __init__(self, window, font, scalingFactor, fps):
		Gui._instance = self
		self.win = window
		self.font = font
		self.scalingFactor = scalingFactor
		self.fps = fps

MENU_ELEMENT = -1
MENU_MENU   = 0
MENU_BUTTON = 1
MENU_UPDOWN = 2
MENU_TOGGLE = 3
MENU_COMBOS = 4
MENU_TEXT   = 5
MENU_DIV	= 6
MENU_DRAGIMAGE	= 7
MENU_INPUT	= 8
MENU_LOADBAR = 9
MENU_SURF = 10
MENU_IMAGE = 11

HORIZONTAL = 0
VERTICAL = 1

WHITE = (255,255,255,255)
BLACK = (0,0,0,255)

def mouseInWin():
	return Vector(pygame.mouse.get_pos()[0] / Gui._instance.scalingFactor, pygame.mouse.get_pos()[1] / Gui._instance.scalingFactor)

def clearMenu():
	Menu._reg.clear()
	MenuElementInput._reg.clear()

def getMenubyName(name):
	for menu in Menu._reg:
		if menu.name == name:
			return menu
	return None

def handleEvents(event, handleMenuEvents):
	if event.type == pygame.MOUSEBUTTONDOWN:
		for inp in MenuElementInput._reg:
			inp.mode = "fixed"
		if event.button == 1:
			for menu in Menu._reg:
				if menu.event:
					menu.processInternalEvents()
					handleMenuEvents(menu.event)

	if event.type == pygame.KEYDOWN:
		for inp in MenuElementInput._reg:
			if inp.mode == "editing":
				inp.processKey(event)
				break

class Menu:
	_reg = []
	_buttonColor = (82,65,60)
	_textElementColor = (62,45,40)
	_toggleColor = (0,255,0)
	_selectedColor = (0,180,0)
	_subButtonColor = (182,165,160)
	_subSelectColor = (255,255,255)
	_dragging = False
	_offsetDrag = Vector()
	
	def __init__(self, pos=None, size=None, name="", orientation=VERTICAL, margin=1, register=False, customSize=None):
		self.pos = Vector()
		if pos:
			self.pos = tup2vec(pos)
		self.size = Vector()
		if size:
			self.size = tup2vec(size)
		self.name = name
		self.elements = []
		self.orientation = orientation
		self.focused = True
		self.event = None
		self.margin = margin # distance between elements
		self.type = MENU_MENU
		self.menu = None
		self.customSize = customSize
		self.offset = None
		if register:
			Menu._reg.append(self)
	def getSuperPos(self):
		if self.menu:
			return self.menu.getSuperPos() + self.pos
		return self.pos
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
		for element in self.elements:
			element.size[0] = self.size[0]
			element.size[1] = self.size[1]
			if element.customSize:
				element.size[self.orientation] = element.customSize
			else:
				element.size[self.orientation] = sizePerElem

			element.pos[self.orientation] = accSize
			accSize += element.size[self.orientation] + self.margin
		for element in self.elements:
			if element.type == MENU_MENU:
				element.recalculate()
			if element.type == MENU_DRAGIMAGE:
				element.setImage(element.imagePath)
	def getValues(self):
		values = {}
		for element in self.elements:
			values[element.key] = element.value
		return values
	def step(self):
		if not self.focused:
			return
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
			self.event.mode = "editing"
	def evaluate(self, dic):
		for element in self.elements:
			element.evaluate(dic)
	def draw(self):
		for element in self.elements:
			element.draw()
	def insert(self, type=MENU_BUTTON, key="key", value="value", text=None, customSize=None, items=None, stepSize=None,
					limitMin=False, limitMax=False, limMin=0, limMax=100, values=None, showValue=True, image=None, inputText="",
					color = WHITE, maxValue=100, draggable=True, comboMap={}):
		if type == MENU_BUTTON:
			b = MenuElementButton()
		elif type == MENU_TOGGLE:
			b = MenuElementToggle()
		elif type == MENU_COMBOS:
			b = MenuElementComboSwitch()
			if items:
				b.setItems(items, mapping=comboMap)
				b.setCurrentItem(text)
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
		elif type == MENU_DRAGIMAGE:
			b = MenuElementDragImage()
			if image:
				b.setImage(image)
			b.draggable = draggable
		elif type == MENU_IMAGE:
			b = MenuElementImage()
			if image:
				b.setImage(image)
		elif type == MENU_MENU:
			b = Menu()
		elif type == MENU_TEXT:
			b = MenuElementText()
		elif type == MENU_LOADBAR:
			b = MenuElementLoadBar()
			b.color = color
			b.maxValue = maxValue
		elif type == MENU_SURF:
			b = MenuElementSurf()
		if key != "key":
			b.key = key
		if value != "value":
			b.value = value
		if text:
			b.renderSurf(text)
		if customSize:
			b.customSize = customSize
		self.addElement(b)
		return b

class MenuElement:
	def __init__(self):
		self.pos = Vector()
		self.size = Vector()
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
	def getSuperPos(self):
		return self.menu.getSuperPos()
	def initialize(self):
		pass
	def setIndex(self, num):
		self.index = num
	def renderSurf(self, text=None):
		if text == "":
			text="input"
		if text:
			self.text = text
		self.surf = Gui._instance.font.render(self.text, True, WHITE)
	def evaluate(self, dic):
		dic[self.key] = self.value
	def step(self):
		pass
	def draw(self):
		buttonPos = self.getSuperPos() + self.pos
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(Gui._instance.win, color, (buttonPos, self.size))
		if self.surf:
			Gui._instance.win.blit(self.surf, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2, buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))

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
		buttonPos = self.getSuperPos() + self.pos
		posInButton = mousePos - buttonPos
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			self.selected = True
			return self
		else:
			self.selected = False
		return None
	def draw(self):
		buttonPos = self.getSuperPos() + self.pos
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(Gui._instance.win, color, (buttonPos, self.size))
		Gui._instance.win.blit(self.surf, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2, buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))
	
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
		buttonPos = self.getSuperPos() + self.pos
		posInButton = mousePos - buttonPos
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			self.selected = True
			if posInButton[1] > posInButton[0] * (self.size[1] / self.size[0]): # need replacement
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
		buttonPos = self.getSuperPos() + self.pos
		border = 1
		arrowSize = self.size[1] // 2
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(Gui._instance.win, color, (buttonPos, self.size))
		rightColor = Menu._subSelectColor if self.selected and self.mode == 1 else Menu._subButtonColor
		leftColor = Menu._subSelectColor if self.selected and not self.mode == 1 else Menu._subButtonColor
		pygame.draw.polygon(Gui._instance.win, rightColor, [(buttonPos[0] + self.size[0] - arrowSize, buttonPos[1] + border), (buttonPos[0] + self.size[0] - border - 1, buttonPos[1] + border), (buttonPos[0] + self.size[0] - border - 1, buttonPos[1] + arrowSize)])
		pygame.draw.polygon(Gui._instance.win, leftColor, [(buttonPos[0] + border ,buttonPos[1] + self.size[1] - arrowSize), (buttonPos[0] + border, buttonPos[1] + self.size[1] - border - 1), (buttonPos[0] + arrowSize, buttonPos[1] + self.size[1] - border - 1)])
		Gui._instance.win.blit(self.surf, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2, buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))

class MenuElementToggle(MenuElementButton):
	def initialize(self):
		self.text = "Tg"
		self.surf = None
		self.value = False
		self.type = MENU_TOGGLE
		self.border = 1
	def draw(self):
		color = Menu._selectedColor if self.selected else self.color
		buttonPos = self.getSuperPos() + self.pos
		pygame.draw.rect(Gui._instance.win, color, (buttonPos, self.size))
		if self.value:
			pygame.draw.rect(Gui._instance.win, Menu._toggleColor, ((buttonPos[0] + self.border, buttonPos[1] + self.border), (self.size[0] - 2 * self.border, self.size[1] - 2 * self.border)))
		Gui._instance.win.blit(self.surf, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2, buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))

class MenuElementComboSwitch(MenuElementButton):
	def initialize(self):
		self.surf = None
		self.value = "value"
		self.currentIndex = 0
		self.type = MENU_COMBOS
		self.items = []
		self.forward = False
		self.mapping = {}
	def setItems(self, strings, mapping={}):
		self.mapping = mapping
		for string in strings:
			stringToRender = string
			if string in self.mapping.keys():
				stringToRender = self.mapping[string]
			surf = Gui._instance.font.render(stringToRender, True, WHITE)
			self.items.append((string, surf))
		self.value = self.items[self.currentIndex][0]
	def setCurrentItem(self, item):
		for i, it in enumerate(self.items):
			if it[0] == item:
				self.currentIndex = i
				break
		self.value = self.items[self.currentIndex][0]
	def step(self):
		mousePos = mouseInWin()
		buttonPos = self.getSuperPos() + self.pos
		posInButton = (mousePos[0] - buttonPos[0], mousePos[1] - buttonPos[1])
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
		buttonPos = self.getSuperPos() + self.pos
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(Gui._instance.win, color, (buttonPos, self.size))
		if self.currentIndex == -1:
			surf = self.surf
		else:
			surf = self.items[self.currentIndex][1]
		Gui._instance.win.blit(surf, (buttonPos[0] + self.size[0]/2 - surf.get_width()/2, buttonPos[1] + self.size[1]/2 - surf.get_height()/2))
		arrowBorder = 3
		arrowSize = self.size[1]
		polygonRight = [Vector(self.size[0] - arrowSize / 2, arrowBorder), Vector(self.size[0] - arrowBorder, self.size[1] / 2), Vector(self.size[0] - arrowSize / 2, self.size[1] - arrowBorder)]
		polygonLeft = [Vector(arrowSize / 2, arrowBorder), Vector(arrowBorder, self.size[1] / 2), Vector(arrowSize / 2, self.size[1] - arrowBorder)]
		rightColor = Menu._subSelectColor if self.selected and self.forward else Menu._subButtonColor
		leftColor = Menu._subSelectColor if self.selected and not self.forward else Menu._subButtonColor
		pygame.draw.polygon(Gui._instance.win, rightColor, [buttonPos + i for i in polygonRight])
		pygame.draw.polygon(Gui._instance.win, leftColor, [buttonPos + i for i in polygonLeft])

class MenuElementImage(MenuElement):
	def initialize(self):
		self.type = MENU_IMAGE
		self.imageSurf = None
	def setImage(self, image, rect=None, background=None):
		self.imageSurf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
		if background:
			self.imageSurf.fill(background)
		self.imageSurf.blit(image, (0, 0), rect)
	def draw(self):
		buttonPos = self.getSuperPos() + self.pos
		Gui._instance.win.blit(self.imageSurf, (buttonPos[0], buttonPos[1]))

class MenuElementDragImage(MenuElement):
	def initialize(self):
		self.type = MENU_DRAGIMAGE
		self.imageSurf = None
		self.imagePath = None
		self.dragDx = 0
		self.draggable = True
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
		buttonPos = self.getSuperPos() + self.pos
		Gui._instance.win.blit(self.surf, buttonPos)
		pygame.draw.rect(Gui._instance.win, Menu._buttonColor, (buttonPos, self.surf.get_size()), 2)
	def recalculateImage(self):
		self.surf.fill((0,0,0,0))
		self.surf.blit(self.imageSurf, (self.size[0] // 2  + self.dragDx, 0))
	def step(self):
		mousePos = mouseInWin()
		buttonPos = self.getSuperPos() + self.pos
		posInButton = (mousePos[0] - buttonPos[0], mousePos[1] - buttonPos[1])
		if self.draggable:
			if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
				# if pygame mouse pressed
				if pygame.mouse.get_pressed()[0]:
					vel = pygame.mouse.get_rel()
					if abs(vel[0]) > 100:
						return
					self.dragDx += vel[0] / Gui._instance.scalingFactor
					if self.imageSurf.get_width() < self.size[0]:
						return
					if self.dragDx > -self.size[0] // 2:
						self.dragDx = -self.size[0] // 2
					elif self.dragDx < -self.imageSurf.get_width() + self.size[0] // 2:
						self.dragDx = -self.imageSurf.get_width() + self.size[0] // 2

					self.recalculateImage()

class MenuElementSurf(MenuElement):
	def initialize(self):
		self.type = MENU_SURF
		self.surf = None
	def setSurf(self, surf):
		self.surf = surf
	def draw(self):
		buttonPos = self.getSuperPos() + self.pos
		Gui._instance.win.blit(self.surf, buttonPos)
		pygame.draw.rect(Gui._instance.win, Menu._buttonColor, (buttonPos, self.surf.get_size()), 2)

class MenuElementInput(MenuElementButton):
	_reg = []
	def initialize(self):
		MenuElementInput._reg.append(self)
		self.mode = "fixed"
		self.inputText = ""
		self.oldInputText = ""
		self.value = self.inputText
		self.type = MENU_INPUT
		self.surf = None
		self.cursorSpeed = Gui._instance.fps // 4
		self.showCursor = False
		self.timer = 0
		self.cursor = Gui._instance.font.render("|", True, (255,255,255))
	def processKey(self, event):
		if event.key == pygame.K_BACKSPACE:
			self.inputText = self.inputText[:-1]
		else:
			self.inputText += event.unicode
		self.value = self.inputText
	def step(self):
		if self.mode == "editing":
			self.timer += 1
			if self.timer >= self.cursorSpeed:
				self.showCursor = not self.showCursor
				self.timer = 0
			if self.inputText != self.oldInputText:
				self.renderSurf(self.inputText)
				self.oldInputText = self.inputText
		mousePos = mouseInWin()
		buttonPos = self.getSuperPos() + self.pos
		posInButton = (mousePos[0] - buttonPos[0], mousePos[1] - buttonPos[1])
		if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
			self.selected = True
			return self
		else:
			self.selected = False
		return None
	def draw(self):
		buttonPos = self.getSuperPos() + self.pos
		color = Menu._selectedColor if self.selected else self.color
		pygame.draw.rect(Gui._instance.win, color, (buttonPos, self.size))

		Gui._instance.win.blit(self.surf, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2, buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))
		if self.mode == "editing" and self.showCursor:
			Gui._instance.win.blit(self.cursor, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2 + self.surf.get_width(), buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))

class MenuElementLoadBar(MenuElement):
	def initialize(self):
		self.type = MENU_LOADBAR
		self.color = (255,255,0)
		self.value = 0
		self.maxValue = 100
		self.direction = 1
	def draw(self):
		buttonPos = self.getSuperPos() + self.pos
		pygame.draw.rect(Gui._instance.win, Menu._textElementColor, (buttonPos, self.size))
		# calculate size
		if self.maxValue == 0:
			print("division by zero error")
			return
		size = Vector(self.size[0] * (self.value / self.maxValue), self.size[1])

		# draw bar left to right direction
		if self.direction == 1:
			pygame.draw.rect(Gui._instance.win, Menu._textElementColor, (buttonPos, self.size), 2)
			pygame.draw.rect(Gui._instance.win, self.color, (buttonPos + Vector(2,2), size - Vector(4,4)))
		# draw bar right to left direction
		else:
			pygame.draw.rect(Gui._instance.win, Menu._textElementColor, (buttonPos + Vector(self.size[0] - size[0], 0), size), 2)
			pygame.draw.rect(Gui._instance.win, self.color, (buttonPos + Vector(self.size[0] - size[0] + 2, 2), size - Vector(4,4)))

class MenuAnimator:
	_reg = []
	def __init__(self, menu, posStart, posEnd, trigger=None, args=None, ease="inout"):
		MenuAnimator._reg.append(self)
		self.posStart = posStart
		self.posEnd = posEnd
		self.timer = 0
		self.fullTime = Gui._instance.fps * 1
		self.trigger = trigger
		self.args = args
		# set first positions
		self.menu = menu
		self.ease = ease
		menu.pos = posStart
	def easeIn(self, t):
		return t * t
	def easeOut(self, t):
		return 1 - (1 - t) * (1 - t)
	def easeInOut(self, t):
		if t < 0.5:
			return 2 * t * t
		else:
			return 1 - (2 * (1 - t)) * (1 - t)
	def step(self):
		if self.ease == "in":
			ease = self.easeOut(self.timer / self.fullTime)
		elif self.ease == "out":
			ease = self.easeIn(self.timer / self.fullTime)
		elif self.ease == "inout":
			ease = self.easeInOut(self.timer / self.fullTime)
		self.menu.pos = self.posEnd * ease + (1 - ease) * self.posStart
		self.timer += 1
		if self.timer > self.fullTime:
			self.finish()
	def finish(self):
		self.menu.pos = self.posEnd
		MenuAnimator._reg.remove(self)
		if self.trigger:
			if self.args:
				self.trigger(*self.args)
			else:
				self.trigger()

class ElementAnimator:
	def __init__(self, element, start, end, duration = -1, timeOffset=0):
		MenuAnimator._reg.append(self)
		self.element = element
		self.start = start
		self.end = end
		self.timer = -timeOffset
		self.fullTime = duration
		if self.fullTime == -1:
			self.duration = Gui._instance.fps * 1
		
	def step(self):
		self.timer += 1
		if self.timer < 0:
			return
		self.element.value = self.start + (self.end - self.start) * (self.timer / self.fullTime)
		if self.timer > self.fullTime:
			self.element.value = self.end
			MenuAnimator._reg.remove(self)
