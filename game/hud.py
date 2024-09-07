
import pygame
from random import uniform
from typing import List, Dict, Any
from enum import Enum

from common import ColorType, fonts, GameVariables
from common.vector import *

HEALTH_BAR_WIDTH = 40
HEALTH_BAR_HEIGHT = 2

class HealthBar:
	''' team health bar calculations and drawing '''
	# drawBar = True
	# drawPoints = True
	def __init__(self, amount_of_teams: int, initial_health_per_player: int, players_in_team: int, colors: List[ColorType]):
		self.max_health = players_in_team * initial_health_per_player
		self.team_health_visual = [self.max_health] * amount_of_teams
		self.team_health_actual = [self.max_health] * amount_of_teams
		self.team_points = [0] * amount_of_teams
		self.colors = colors
	
	def update_health(self, health_list: List[int]):
		''' update '''
		self.team_health_actual = health_list

	def update_score(self, point_list: List[int]):
		''' update '''
		self.team_points = point_list
	
	def step(self):
		recalc = lambda current, target: current + (target - current) * 0.1
		self.team_health_visual = [recalc(visual, self.team_health_actual[i]) for i, visual in enumerate(self.team_health_visual)]
	
	def draw(self, win):
		x = int(GameVariables().win_width - HEALTH_BAR_WIDTH - 10)
		y = 10

		width = HEALTH_BAR_WIDTH
		height = HEALTH_BAR_HEIGHT
		
		# draw health
		for i, health in enumerate(self.team_health_visual):
			pygame.draw.rect(win, (220,220,220), (x, y + i * 3, width, height))
			value = health / self.max_health
			pygame.draw.rect(win, self.colors[i], (x, y + i * 3, value * width, height))

		# draw points
		max_points = sum(self.team_points)
		if max_points != 0:
			for i, points in enumerate(self.team_points):
				value = points / max_points * width
				pygame.draw.rect(win, (220,220,220), ((x - value - 1, y + i * 3), (value, height)))


class CommentatorState(Enum):
	IDLE = 0
	SHOW = 2

class Commentator:
	''' comment pop ups '''
	def __init__(self) -> None:
		self.state: CommentatorState = CommentatorState.IDLE
		self.surf_que: List[pygame.Surface] = []
		self.timer = 0
		self.current_surf: pygame.Surface = None
	
	def comment(self, text_dict) -> None:
		surf = self.render_comment(text_dict)
		self.surf_que.append(surf)

	def step(self) -> None:
		if self.state == CommentatorState.IDLE:
			if len(self.surf_que) > 0:
				self.timer = int(2.5 * GameVariables().fps)
				self.current_surf = self.surf_que.pop(0)
				self.state = CommentatorState.SHOW
		
		elif self.state == CommentatorState.SHOW:
			self.timer -= 1
			if self.timer == 0:
				self.current_surf = None
				self.state = CommentatorState.IDLE

	def draw(self, win: pygame.Surface) -> None:
		if self.current_surf is not None:
			win.blit(self.current_surf, (int(GameVariables().win_width / 2 - self.current_surf.get_width() / 2), 5))
	
	def render_comment(self, text_dict: List[Dict[str, Any]]) -> pygame.Surface:
		text_surfs: List[pygame.Surface] = []
		for entry in text_dict:
			text = entry.get('text')
			color = entry.get('color', GameVariables().initial_variables.hud_color)
			text_surfs.append(fonts.pixel5_halo.render(text, False, color))
		width = sum([i.get_width() for i in text_surfs])
		surf = pygame.Surface((width, text_surfs[0].get_height()), pygame.SRCALPHA)
		x = 0
		for s in text_surfs:
			surf.blit(s, (x, 0))
			x += s.get_width()
		return surf

class Toast:
	_toasts: List['Toast'] = []
	toastCount = 0
	bottom = 0
	middle = 1
	
	def __init__(self, surf, mode=0):
		Toast._toasts.append(self)
		self.surf = surf
		self.time = 0
		self.mode = mode
		if self.mode == Toast.bottom:
			self.anchor = Vector(GameVariables().win_width / 2, GameVariables().win_height)
		else:
			self.anchor = Vector(GameVariables().win_width // 2, GameVariables().win_height // 2) - tup2vec(self.surf.get_size()) / 2
		self.pos = Vector()
		self.state = 0
		Toast.toastCount += 1
		
	def step(self):
		if self.mode == Toast.bottom:
			if self.state == 0:
				self.pos.y -= 3
				if self.pos.y < -self.surf.get_height():
					self.state = 1
			if self.state == 1:
				self.time += 1
				if self.time == GameVariables().fps * 3:
					self.state = 2
			if self.state == 2:
				self.pos.y += 3
				if self.pos.y > 0:
					Toast._toasts.remove(self)
					Toast.toastCount -= 1
		elif self.mode == Toast.middle:
			self.time += 1
			if self.time == GameVariables().fps * 3:
				Toast._toasts.remove(self)
				Toast.toastCount -= 1
			self.pos = uniform(0,2) * vectorUnitRandom()
			
	def draw(self, win: pygame.Surface):
		if self.mode == Toast.bottom:
			pygame.gfxdraw.box(win, (self.anchor + self.pos - Vector(1,1), tup2vec(self.surf.get_size()) + Vector(2,2)), (255,255,255,200))
			win.blit(self.surf, self.anchor + self.pos)
		
	def updateWinPos(self, pos):
		self.anchor[0] = pos[0]
		self.anchor[1] = pos[1]

class WindFlag:
	''' hud widget, represents wind speed and direction '''
	def __init__(self):
		self.vertices = [Vector(i * 10, 0) for i in range(5)]
		self.acc = [Vector() for _ in range(len(self.vertices))]
		self.vel = [Vector() for _ in range(len(self.vertices))]
	
	def step(self):
		for _ in range(3):
			# calculate acc
			for i in range(len(self.vertices)):
				if i == 0:
					continue

				displacement1 = dist(self.vertices[i], self.vertices[i-1]) - 10
				displacement2 = 0
				if i != len(self.vertices) - 1:
					displacement2 = dist(self.vertices[i], self.vertices[i+1]) - 10

				acc1 = 0.05 * displacement1 * (self.vertices[i-1] - self.vertices[i]).normalize()
				acc2 = Vector()
				if i != len(self.vertices) - 1:
					acc2 = 0.05 * displacement2 * (self.vertices[i+1] - self.vertices[i]).normalize()

				self.acc[i] += acc1 + acc2
				# gravity
				self.acc[i] += Vector(0, 0.01)
				# wind
				self.acc[i] += Vector(GameVariables().physics.wind * 0.05, 0)
				# turbulence
				self.acc[i] += vectorUnitRandom() * 0.01

			for i in range(len(self.vertices)):
				# calculate vel
				self.vel[i] += self.acc[i]
				self.vel[i] *= 0.99
				self.acc[i] = Vector()
			
				# calculate pos
				self.vertices[i] += self.vel[i]
				
	def draw(self, win: pygame.Surface):
		it = 0
		rad = 6
		pos = Vector(25, 18)
		scale = 0.5
		pygame.draw.line(win, (204, 102, 0), pos, pos + Vector(0, 40) * scale, 1)
		for i in range(len(self.vertices) - 1):
			# draw alternating lines red and white
			pygame.draw.line(win, (255, 255 * it, 255 * it), self.vertices[i] * scale + pos, self.vertices[i + 1] * scale + pos, rad)
			it = (it + 1) % 2
			rad -= 1
