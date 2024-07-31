
import pygame
from math import pi, cos, sin, atan2, sqrt, degrees
from typing import Any, Tuple, List
from abc import ABC, abstractmethod

import globals

from pygame import Vector2

class GuiBase(ABC):
	@abstractmethod
	def handle_event(self, event) -> None:
		''' handle pygame events '''

	@abstractmethod
	def step(self) -> None:
		''' step loop '''

	@abstractmethod
	def draw(self, win: pygame.Surface) -> None:
		''' draw self '''


def draw_arc(win, center, outer_radius, inner_radius, start, end, color) -> None:
	''' draw arc '''
	points1 = []
	res = int(100 * ((end - start) / (2 * pi)))
	
	for i in range(res):
		t = start + (i / (res - 1)) * (end - start)
		point1 = Vector2(outer_radius * cos(t),outer_radius * sin(t))
		points1.append(point1)
	
	for i in range(res):
		t = end + (i / (res - 1)) * (start - end)
		point1 = Vector2(inner_radius * cos(t),inner_radius * sin(t))
		points1.append(point1)
	
	points1 = [i + center for i in points1]
	pygame.draw.polygon(win, color, points1)


def is_pos_in_arc(pos: Vector2, center: Vector2, inner, outer, start, end) -> bool:
	''' position in map space '''

	pos_in_center = pos - center
	pos_radial = Vector2(sqrt(pos_in_center.x ** 2 + pos_in_center.y ** 2),
					  	 atan2(pos_in_center.y, pos_in_center.x))
	if pos_radial.y < 0:
		pos_radial.y += 2 * pi
	
	if outer > pos_radial.x > inner and end > pos_radial.y > start:
		return True
	return False

# class RadialMenu0(GuiBase):
# 	def __init__(self, layout) -> None:
# 		self.elements = []
# 		self.outer_radius = 60
# 		self.inner_radius = 30
# 		self.build(layout)
	
# 	def build(self, layout) -> None:
# 		pass

# 	def step(self):
# 		for e in self.elements:
# 			e.step()
			
# 	def recalculate(self):
# 		NumButtons = len(self.elements)
# 		buttonArcAngle = 2 * pi / NumButtons
# 		# update buttons rects
# 		for i, button in enumerate(self.elements):
# 			buttonRect = ((self.inner_radius, i * buttonArcAngle), (self.outer_radius, i * buttonArcAngle + buttonArcAngle))
# 			button.rect = buttonRect
			
# 	def addButton(self, key, bgColor) -> 'RadialButton':
# 		b = RadialButton(key, bgColor)
# 		self.elements.insert(0, b)
# 		self.recalculate()
# 		return b
		
# 	def draw(self):
# 		for e in self.elements:
# 			e.draw()
# 		if self.focus:
# 			mouse = Vector(pygame.mouse.get_pos()[0] / globals.scalingFactor, pygame.mouse.get_pos()[1] / globals.scalingFactor)
# 			globals.game_manager.win.blit(RadialMenu.toster[0], mouse + Vector(5,5))


# class RadialButton0(GuiBase):
# 	def __init__(self, key: Any, super_script: str, tool_tip: str=None, bgColor: ColorType=WHITE):
# 		self.rect = None
# 		self.key = key
# 		self.bgColor = bgColor
# 		self.selected = False
# 		self.color = bgColor
# 		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
# 		self.tool_tip = tool_tip
# 		self.super_script = super_script
# 		self.tool_tip_surf = None
# 		if tool_tip:
# 			self.tool_tip_surf = globals.pixelFont5.render(str(self.ammo), False, BLACK)
# 		self.subButtons = []
# 		self.level = 0
# 		self.category = None
		
# 	def step(self):
# 		mouse = Vector(pygame.mouse.get_pos()[0] / globals.scalingFactor, pygame.mouse.get_pos()[1]/globals.scalingFactor)
# 		mouseInMenu = mouse - Vector(globals.winWidth // 2, globals.winHeight // 2)
# 		mouseinner_radiusadial = Vector(sqrt(mouseInMenu[0]**2 + mouseInMenu[1]**2), atan2(mouseInMenu[1], mouseInMenu[0]))
# 		if mouseinner_radiusadial[1] < 0:
# 			mouseinner_radiusadial[1] += 2 * pi
# 		if mouseinner_radiusadial[0] > self.rect[0][0] and mouseinner_radiusadial[0] < self.rect[1][0]\
# 			and ((mouseinner_radiusadial[1] > self.rect[0][1] and mouseinner_radiusadial[1] < self.rect[1][1]) or\
# 			(mouseinner_radiusadial[1] + 2*pi > self.rect[0][1] and mouseinner_radiusadial[1] + 2*pi < self.rect[1][1]) or\
# 			(mouseinner_radiusadial[1] - 2*pi > self.rect[0][1] and mouseinner_radiusadial[1] - 2*pi < self.rect[1][1])):
# 			self.selected = True
# 			if self.level == 1:
# 				RadialMenu.focus = True
# 			self.color = RED
# 			RadialMenu.events[self.level] = self.key
# 			if self.level == 0:
# 				RadialMenu.events[self.level + 1] = self.key
# 			if self.level == 1 and RadialMenu.toster[1] != self.key:
# 				textSurf = globals.pixelFont5.render(self.key, False, WHITE)
# 				RadialMenu.toster[0] = pygame.Surface(tup2vec(textSurf.get_size()) + Vector(2,2))
# 				RadialMenu.toster[0].blit(textSurf, (1,1))
# 				RadialMenu.toster[1] = self.key
# 		else:
# 			self.selected = False
# 			self.color =  [self.color[i] + (self.bgColor[i] - self.color[i]) * 0.2 for i in range(3)]

# 		# add sub buttons
# 		if self.level == 0:
# 			if RadialMenu.events[self.level] == self.key and len(self.subButtons) == 0:
# 				# self key is category, add all weapons in that category
# 				for weapon in globals.weapon_manager.weapons:
# 					if globals.team_manager.currentTeam.ammo(weapon) == 0:
# 						continue
# 					active = True
# 					round_count = globals.game_manager.roundCounter
# 					if globals.game_manager.useListMode and globals.game_manager.inUsedList(weapon.name) or weapon.round_delay < round_count:
# 						active = False
# 					if weapon.category == self.category:
# 						b = self.addSubButton(weapon)
# 						b.level = self.level + 1
# 						globals.weapon_manager.blitWeaponSprite(b.surf, (0,0), weapon.name)
# 						if not active:
# 							b.surf.fill((200, 200, 200), special_flags= pygame.BLEND_SUB)
# 							b.surf.fill((200, 200, 200), special_flags= pygame.BLEND_ADD)
# 			if RadialMenu.events[self.level] != self.key:
# 				self.subButtons.clear()
			
# 		for e in self.subButtons:
# 			e.step()
			
# 	def recalculate(self):
# 		offset = (self.rect[1][1] + self.rect[0][1])/2 - ((pi / 10) * len(self.subButtons)) /2
# 		outer_radius = 90
# 		inner_radius = 65
# 		NumButtons = len(self.subButtons)
# 		buttonArcAngle = pi / 10
# 		# update buttons rects
# 		for i, button in enumerate(self.subButtons):
# 			buttonRect = ((inner_radius, i * buttonArcAngle + offset), (outer_radius, i * buttonArcAngle + buttonArcAngle + offset))
# 			button.rect = buttonRect
			
# 	def addSubButton(self, key):
# 		b = RadialButton(key, self.bgColor)
# 		self.subButtons.insert(0, b)
# 		self.recalculate()
# 		return b
		
# 	def draw(self):
# 		draw_arc(Vector(globals.winWidth // 2, globals.winHeight // 2), self.rect[1][0], self.rect[0][0], self.rect[0][1], self.rect[1][1], self.color)
# 		if self.surf:
# 			posRadial = (tup2vec(self.rect[0]) + tup2vec(self.rect[1])) / 2
# 			pos = vectorFromAngle(posRadial[1], posRadial[0]) + Vector(globals.winWidth // 2, globals.winHeight // 2)
# 			globals.game_manager.win.blit(self.surf, pos - Vector(8,8))
# 			if self.amount:
# 				globals.game_manager.win.blit(self.amount, pos + Vector(4,4))
# 		for e in self.subButtons:
# 			e.draw()

SurfacePortion = Tuple[pygame.Surface, Tuple[int, int, int, int]] | None

RADIUS_LEVEL = (
	(30, 60),
	(65, 90)
)

SUB_BUTTON_ANGLE = pi / 10

class RadialButton(GuiBase):
	def __init__(self, key: Any, tooltip: str='', super_text: str='', back_color=None, surf_portion: SurfacePortion=None, layout: List['RadialButton']=None):
		self.key = key
		self.tooltip = globals.pixelFont5halo.render(tooltip, False, (255,255,255))
		self.super_text = None
		self.surf_portion = surf_portion
		if super_text != '':
			self.super_text = globals.pixelFont5.render(super_text, False, (0,0,0))
		self.layout = layout

		self.level = 0 # level of button in menu hierarchy
		self.start_angle: float = 0
		self.end_angle: float = 0
		self.center: Vector2 = None

		self.color = back_color if back_color is not None else (128, 128, 128)
		self.back_color = back_color if back_color is not None else (128, 128, 128)
		self.in_focus = False

		self.elements: List[RadialButton] = []
		self.is_open = False		
	
	@property
	def inner_radius(self):
		return RADIUS_LEVEL[self.level][0]

	@property
	def outer_radius(self):
		return RADIUS_LEVEL[self.level][1]

	def build(self) -> None:
		if self.layout is None:
			return
		element_angle: float = SUB_BUTTON_ANGLE
		half_start = self.end_angle - (self.end_angle - self.start_angle) / 2 - (element_angle * len(self.layout)) / 2
		angle: float = half_start

		for element in self.layout:
			self.elements.append(element)
			element.start_angle = angle
			angle += element_angle
			element.end_angle = angle
			element.center = self.center
			element.level += 1

			element.build()

	def handle_event(self, event) -> Any:
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.in_focus:
				return self.key
		for element in self.elements:
			result = element.handle_event(event)
			if result is not None:
				return result
		return None

	def step(self) -> None:
		self.color =  [self.color[i] + (self.back_color[i] - self.color[i]) * 0.2 for i in range(3)]

		self.in_focus = False
		mouse = Vector2(pygame.mouse.get_pos()[0] / globals.scalingFactor, pygame.mouse.get_pos()[1] / globals.scalingFactor)
		if is_pos_in_arc(mouse, self.center, self.inner_radius, self.outer_radius, self.start_angle, self.end_angle):
			self.in_focus = True
			self.color = (255,0,0)
		
		if self.is_open:
			for element in self.elements:
				element.step()

	def draw(self, win: pygame.Surface) -> None:
		draw_arc(win, self.center, self.inner_radius, self.outer_radius, self.start_angle, self.end_angle, self.color)

		angle = self.start_angle + (self.end_angle - self.start_angle) / 2
		radius = self.inner_radius + (self.outer_radius - self.inner_radius) / 2
		pos = Vector2(self.center + Vector2.from_polar((radius , degrees(angle))))

		surf = self.surf_portion[0]
		rect = self.surf_portion[1]
		win.blit(surf, pos - Vector2(8, 8), rect)
		
		if self.super_text is not None:
			win.blit(self.super_text, pos + Vector2(4, 4))

		if self.is_open:
			for element in self.elements:
				element.draw(win)
	
	def draw_tooltip(self, win: pygame.Surface):
		if self.tooltip is None:
			return
		mouse = Vector2(pygame.mouse.get_pos()[0] / globals.scalingFactor, pygame.mouse.get_pos()[1] / globals.scalingFactor)
		win.blit(self.tooltip, mouse + Vector2(5, 5))
	
	def get_focused(self) -> 'RadialButton':
		if self.in_focus:
			return self
		for element in self.elements:
			if element.in_focus:
				return element
	
	def unfold(self) -> None:
		self.is_open = True
	
	def fold(self) -> None:
		self.is_open = False


class RadialMenu(GuiBase):
	def __init__(self, layout: List[RadialButton], center: Vector2):
		self.layout = layout
		self.elements: List[RadialButton] = []
		self.center = center
		self.build()

		self.last_focused: RadialButton = None

	def build(self) -> None:
		element_angle: float = 2 * pi / len(self.layout)
		angle: float = 0

		for element in self.layout:
			self.elements.append(element)
			element.start_angle = angle
			angle += element_angle
			element.end_angle = angle
			element.center = self.center

			element.build()

	
	def handle_event(self, event) -> None:
		for element in self.elements:
			returned_event = element.handle_event(event)
			if event is not None:
				self.event = returned_event

	def step(self) -> None:
		for element in self.elements:
			element.step()
			if element.in_focus:
				if self.last_focused:
					self.last_focused.fold()
				self.last_focused = element
				element.unfold()
	
	def draw(self, win: pygame.Surface) -> None:
		for element in self.elements:
			element.draw(win)

		focused_element = self.get_focused()
		if focused_element is not None:
			
			focused_element.draw_tooltip(win)
		
	def get_focused(self) -> RadialButton:
		for element in self.elements:
			focused = element.get_focused()
			if focused is not None:
				return focused
		return None

	def get_event(self) -> Any:
		if self.event is not None:
			event = self.event 
			self.event = None
			return event
		return None

def main_test() -> None:
	pygame.init()
	myfont = pygame.font.SysFont('Tahoma', 16)
	win = pygame.display.set_mode((1280, 720))
	clock = pygame.time.Clock()

	layout = [
		RadialButton('weapon_group_1', 'missiles', '', (128,0,0), [
			RadialButton('missile1', 'missile', '3'),
			RadialButton('missile2', 'buster', '2'),
			RadialButton('missile3', 'termin', '1'),
		]),
		RadialButton('weapon_group_2', 'grenades', '', (0,128,0), [
			RadialButton('grenade1', 'g1', '6'),
			RadialButton('grenade2', 'g2', '3'),
			RadialButton('grenade3', 'g3', '7'),
		]),
		RadialButton('weapon_group_3', 'tools', '', (0,0,128), [
			RadialButton('tool1', 'tool1', '8'),
			RadialButton('tool2', 'tool2', '2'),
			RadialButton('tool3', 'tool3', '9'),
		]),
	]

	radial_menu = RadialMenu(layout, Vector2(win.get_width() / 2, win.get_height() / 2))
	
	run = True
	while run:
		for event in pygame.event.get():
			radial_menu.handle_event(event)
			if event.type == pygame.QUIT:
				run = False
			
		keys = pygame.key.get_pressed()
		if keys[pygame.K_ESCAPE]:
			run = False
		
		# step
		radial_menu.step()
		
		# draw
		win.fill((255,255,255))
		radial_menu.draw(win)
		
		clock.tick(30)
		pygame.display.update()
	pygame.quit()
		

if __name__ == '__main__':
	main_test()
