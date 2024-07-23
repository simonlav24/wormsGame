
import pygame
from math import pi, cos, sin, atan2, sqrt

from vector import *
from Constants import *
import globals

from tempFuncs import *

def drawArc(center, outr, inr, start, end, color):
	points1 = []
	res = int(100 * ((end - start) / (2 * pi)))
	
	for i in range(res):
		t = start + (i / (res - 1)) * (end - start)
		point1 = Vector(outr * cos(t),outr * sin(t))
		points1.append(point1)
	
	for i in range(res):
		t = end + (i / (res - 1)) * (start - end)
		point1 = Vector(inr * cos(t),inr * sin(t))
		points1.append(point1)
	
	points1 = [i + center for i in points1]
	pygame.draw.polygon(globals.game_manager.win, color, points1)

class RadialMenu:
	events = [None, None]
	menu = None
	toster = [None, None]
	focus = False
	
	def __init__(self):
		self.elements = []
		self.outr = 60
		self.inr = 30
		
	def step(self):
		RadialMenu.focus = False
		for e in self.elements:
			e.step()
			
	def recalculate(self):
		NumButtons = len(self.elements)
		buttonArcAngle = 2 * pi / NumButtons
		# update buttons rects
		for i, button in enumerate(self.elements):
			buttonRect = ((self.inr, i * buttonArcAngle), (self.outr, i * buttonArcAngle + buttonArcAngle))
			button.rect = buttonRect
			
	def addButton(self, key, bgColor):
		b = RadialButton(key, bgColor)
		self.elements.insert(0, b)
		self.recalculate()
		return b
		
	def draw(self):
		for e in self.elements:
			e.draw()
		if self.focus:
			mouse = Vector(pygame.mouse.get_pos()[0] / globals.scalingFactor, pygame.mouse.get_pos()[1] / globals.scalingFactor)
			globals.game_manager.win.blit(RadialMenu.toster[0], mouse + Vector(5,5))

class RadialButton:
	def __init__(self, key, bgColor):
		self.rect = None
		self.key = key
		self.bgColor = bgColor
		self.selected = False
		self.color = bgColor
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.ammo = globals.team_manager.currentTeam.ammo(self.key)
		self.amount = None
		if self.ammo > 0:
			self.amount = globals.pixelFont5.render(str(self.ammo), False, BLACK)
		self.subButtons = []
		self.level = 0
		self.category = None
		
	def step(self):
		mouse = Vector(pygame.mouse.get_pos()[0] / globals.scalingFactor, pygame.mouse.get_pos()[1]/globals.scalingFactor)
		mouseInMenu = mouse - Vector(globals.winWidth // 2, globals.winHeight // 2)
		mouseInRadial = Vector(sqrt(mouseInMenu[0]**2 + mouseInMenu[1]**2), atan2(mouseInMenu[1], mouseInMenu[0]))
		if mouseInRadial[1] < 0:
			mouseInRadial[1] += 2 * pi
		if mouseInRadial[0] > self.rect[0][0] and mouseInRadial[0] < self.rect[1][0]\
			and ((mouseInRadial[1] > self.rect[0][1] and mouseInRadial[1] < self.rect[1][1]) or\
			(mouseInRadial[1] + 2*pi > self.rect[0][1] and mouseInRadial[1] + 2*pi < self.rect[1][1]) or\
			(mouseInRadial[1] - 2*pi > self.rect[0][1] and mouseInRadial[1] - 2*pi < self.rect[1][1])):
			self.selected = True
			if self.level == 1:
				RadialMenu.focus = True
			self.color = RED
			RadialMenu.events[self.level] = self.key
			if self.level == 0:
				RadialMenu.events[self.level + 1] = self.key
			if self.level == 1 and RadialMenu.toster[1] != self.key:
				textSurf = globals.pixelFont5.render(self.key, False, WHITE)
				RadialMenu.toster[0] = pygame.Surface(tup2vec(textSurf.get_size()) + Vector(2,2))
				RadialMenu.toster[0].blit(textSurf, (1,1))
				RadialMenu.toster[1] = self.key
		else:
			self.selected = False
			self.color =  [self.color[i] + (self.bgColor[i] - self.color[i]) * 0.2 for i in range(3)]

		# add sub buttons
		if self.level == 0:
			if RadialMenu.events[self.level] == self.key and len(self.subButtons) == 0:
				# self key is category, add all weapons in that category
				for weapon in globals.weapon_manager.weapons:
					if globals.team_manager.currentTeam.ammo(weapon[0]) == 0:
						continue
					active = True
					if globals.game_manager.useListMode and globals.game_manager.inUsedList(weapon[0]) or weapon[5] != 0:
						active = False
					if weapon[3] == self.category:
						b = self.addSubButton(weapon[0])
						b.level = self.level + 1
						globals.weapon_manager.blitWeaponSprite(b.surf, (0,0), weapon[0])
						if not active:
							b.surf.fill((200, 200, 200), special_flags= pygame.BLEND_SUB)
							b.surf.fill((200, 200, 200), special_flags= pygame.BLEND_ADD)
			if RadialMenu.events[self.level] != self.key:
				self.subButtons.clear()
			
		for e in self.subButtons:
			e.step()
			
	def recalculate(self):
		offset = (self.rect[1][1] + self.rect[0][1])/2 - ((pi / 10) * len(self.subButtons)) /2
		outr = 90
		inr = 65
		NumButtons = len(self.subButtons)
		buttonArcAngle = pi / 10
		# update buttons rects
		for i, button in enumerate(self.subButtons):
			buttonRect = ((inr, i * buttonArcAngle + offset), (outr, i * buttonArcAngle + buttonArcAngle + offset))
			button.rect = buttonRect
			
	def addSubButton(self, key):
		b = RadialButton(key, self.bgColor)
		self.subButtons.insert(0, b)
		self.recalculate()
		return b
		
	def draw(self):
		drawArc(Vector(globals.winWidth // 2, globals.winHeight // 2), self.rect[1][0], self.rect[0][0], self.rect[0][1], self.rect[1][1], self.color)
		if self.surf:
			posRadial = (tup2vec(self.rect[0]) + tup2vec(self.rect[1])) / 2
			pos = vectorFromAngle(posRadial[1], posRadial[0]) + Vector(globals.winWidth // 2, globals.winHeight // 2)
			globals.game_manager.win.blit(self.surf, pos - Vector(8,8))
			if self.amount:
				globals.game_manager.win.blit(self.amount, pos + Vector(4,4))
		for e in self.subButtons:
			e.draw()