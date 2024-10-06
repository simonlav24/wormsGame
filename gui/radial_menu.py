
import pygame
from math import pi, cos, sin, atan2, sqrt, degrees, fmod
from typing import Any, Tuple, List
from abc import ABC, abstractmethod

from common import fonts, GameVariables, GameGlobals
from pygame import Vector2

SurfacePortion = Tuple[pygame.Surface, Tuple[int, int, int, int]] | None

RADIUS_LEVEL = (
	(30, 60),
	(65, 90)
)

SUB_BUTTON_ANGLE = pi / 10

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


def is_pos_in_arc(pos: Vector2, center: Vector2, inner, outer, start, end, iprint=False) -> bool:
	''' position in map space '''

	pos_in_center = pos - center
	# if iprint:
	# 	print(pos_in_center, atan2(pos_in_center.y, pos_in_center.x))
	
	# mouse_angle = atan2(pos_in_center.y, pos_in_center.x)
	# if mouse_angle < 0:
	# 	mouse_angle += 2 * pi

	pos_radial = Vector2(sqrt(pos_in_center.x ** 2 + pos_in_center.y ** 2),
					  	 atan2(pos_in_center.y, pos_in_center.x))

	if pos_radial.y < 0:
		pos_radial.y += 2 * pi
	
	# print('org', start, end)
	# start = fmod(start - pi, 2 * pi) - pi
	# end = fmod(end - pi, 2 * pi) - pi
	# print('func', start, end)

	angle = - 4 * pi
	while angle <= 4 * pi:
		if outer > pos_radial.x > inner and end > pos_radial.y + angle > start:
			return True
		angle += 2 * pi
	return False

class RadialButton(GuiBase):
	def __init__(self, key: Any, tooltip: str='', super_text: str='', back_color=None, surf_portion: SurfacePortion=None, layout: List['RadialButton']=None, is_enabled=True):
		self.key = key
		self.tooltip = fonts.pixel5_halo.render(tooltip, False, (255,255,255))
		self.super_text = None
		if super_text != '':
			self.super_text = fonts.pixel5.render(super_text, False, (0,0,0))
		self.layout = layout

		self.level = 0 # level of button in menu hierarchy
		self.start_angle: float = 0
		self.end_angle: float = 0
		self.center: Vector2 = None
		self.is_enabled = is_enabled

		self.color = back_color if back_color is not None else (128, 128, 128)
		self.back_color = back_color if back_color is not None else (128, 128, 128)
		self.in_focus = False

		self.elements: List[RadialButton] = []
		self.is_open = False

		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(surf_portion[0], (0, 0), surf_portion[1])
		if not self.is_enabled:
			self.surf.fill((200, 200, 200), special_flags= pygame.BLEND_SUB)
			self.surf.fill((200, 200, 200), special_flags= pygame.BLEND_ADD)
	
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
		mouse = Vector2(pygame.mouse.get_pos()[0] / GameGlobals().scale_factor, pygame.mouse.get_pos()[1] / GameGlobals().scale_factor)
		# if self.key.name == 'missile':
		# 	print(mouse, self.center, self.inner_radius, self.outer_radius, self.start_angle, self.end_angle)
		if is_pos_in_arc(mouse, self.center, self.inner_radius, self.outer_radius, self.start_angle, self.end_angle, self.key.name=='missile'):
			if self.is_enabled:
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

		if not self.is_enabled:
			pass
		win.blit(self.surf, pos - Vector2(8, 8))
		
		if self.super_text is not None:
			win.blit(self.super_text, pos + Vector2(4, 4))

		if self.is_open:
			for element in self.elements:
				element.draw(win)
	
	def draw_tooltip(self, win: pygame.Surface):
		if self.tooltip is None:
			return
		mouse = Vector2(pygame.mouse.get_pos()[0] / GameGlobals().scale_factor, pygame.mouse.get_pos()[1] / GameGlobals().scale_factor)
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

	def center_out(self) -> None:
		''' set center position '''
		self.center = (GameGlobals().win_width // 2, GameGlobals().win_height // 2)
		for element in self.elements:
			element.center_out()


class RadialMenu(GuiBase):
	def __init__(self, layout: List[RadialButton], center: Vector2):
		self.layout = layout
		self.elements: List[RadialButton] = []
		self.center = center
		self.build()

		self.last_focused: RadialButton = None
		self.event = None

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

	def center_out(self) -> None:
		''' set center position '''
		self.center = (GameGlobals().win_width // 2, GameGlobals().win_height // 2)
		for element in self.elements:
			element.center_out()
	
	def handle_event(self, event) -> None:
		for element in self.elements:
			returned_event = element.handle_event(event)
			if returned_event is not None:
				self.event = returned_event

	def step(self) -> None:
		self.center_out()
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

