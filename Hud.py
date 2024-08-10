
import pygame
from random import choice, uniform
from typing import List, Dict, Any
from enum import Enum

import globals
from Constants import ColorType
from vector import *
from GameVariables import GameVariables
from GameEvent import GameEvents, EventComment

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
		self.colors = colors
	
	def update(self, health_list: List[int], special_marks: List[bool]=None):
		''' update '''
		self.team_health_actual = health_list
		# todo marks
	
	def step(self):
		recalc = lambda current, target: current + (target - current) * 0.1
		self.team_health_visual = [recalc(visual, self.team_health_actual[i]) for i, visual in enumerate(self.team_health_visual)]
	
	def draw(self, win):
		x = int(GameVariables().win_width - HEALTH_BAR_WIDTH - 10)
		y = 10

		width = HEALTH_BAR_WIDTH
		height = HEALTH_BAR_HEIGHT
		
		for i, health in enumerate(self.team_health_visual):
			pygame.draw.rect(win, (220,220,220), (x, y + i * 3, width, height))
			value = health / self.max_health
			pygame.draw.rect(win, self.colors[i], (x, y + i * 3, int(value) * width, height))

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
	
	def step(self) -> None:
		# handle events
		my_events: List[EventComment] = []
		events_list = GameEvents().get_events()
		for event in events_list:
			if isinstance(event, EventComment):
				my_events.append(event)
		
		[events_list.remove(event) for event in my_events]

		for event in my_events:
			surf = self.render_comment(event.text_dict)
			self.surf_que.append(surf)

		if self.state == CommentatorState.IDLE:
			if len(self.surf_que) > 0:
				self.timer = 2 * globals.fps + globals.fps // 2
				self.current_surf = self.surf_que.pop(0)
				self.state = CommentatorState.SHOW
		
		elif self.state == CommentatorState.SHOW:
			self.timer -= 1
			if self.timer == 0:
				self.current_surf = None
				self.state = CommentatorState.IDLE

	def draw(self, win: pygame.Surface) -> None:
		if self.current_surf is not None:
			win.blit(self.current_surf, (int(GameVariables().win_width/2 - self.current_surf.get_width() / 2), 5))
	
	def render_comment(self, text_dict: List[Dict[str, Any]]) -> pygame.Surface:
		text_surfs: List[pygame.Surface] = []
		for entry in text_dict:
			text = entry.get('text')
			color = entry.get('color', GameVariables().initial_variables.hud_color)
			text_surfs.append(globals.pixelFont5halo.render(text, False, color))
		width = sum([i.get_width() for i in text_surfs])
		surf = pygame.Surface((width, text_surfs[0].get_height()), pygame.SRCALPHA)
		x = 0
		for s in text_surfs:
			surf.blit(s, (x, 0))
			x += s.get_width()
		return surf

	# @staticmethod
	# def commentDeath(worm, cause):
	# 	if cause == Commentator.CAUSE_DAMAGE:
	# 		strings = choice(Commentator.stringsDmg)
	# 	elif cause == Commentator.CAUSE_FLEW:
	# 		strings = choice(Commentator.stringsFlw)
	# 	output = [
	# 		{'text': strings[0]},
	# 		{'text': worm.nameStr, 'color': worm.team.color},
	# 		{'text': strings[1]},
	# 	]
	# 	Commentator.comment(output)

	
		

class Toast:
	_toasts = []
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
				if self.time == globals.fps * 3:
					self.state = 2
			if self.state == 2:
				self.pos.y += 3
				if self.pos.y > 0:
					Toast._toasts.remove(self)
					Toast.toastCount -= 1
		elif self.mode == Toast.middle:
			self.time += 1
			if self.time == globals.fps * 3:
				Toast._toasts.remove(self)
				Toast.toastCount -= 1
			self.pos = uniform(0,2) * vectorUnitRandom()
			
	def draw(self):
		if self.mode == Toast.bottom:
			pygame.gfxdraw.box(globals.game_manager.win, (self.anchor + self.pos - Vector(1,1), tup2vec(self.surf.get_size()) + Vector(2,2)), (255,255,255,200))
		globals.game_manager.win.blit(self.surf, self.anchor + self.pos)
		
	def updateWinPos(self, pos):
		self.anchor[0] = pos[0]
		self.anchor[1] = pos[1]
		

class WindFlag:
	''' hud widget, represents wind speed and direction '''
	_instance = None
	
	def __init__(self):
		WindFlag._instance = self
		self.vertices = [Vector(i * 10, 0) for i in range(5)]
		self.acc = [Vector() for i in range(len(self.vertices))]
		self.vel = [Vector() for i in range(len(self.vertices))]
	
	def step(self):
		for step in range(3):
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
				
	def draw(self):
		it = 0
		rad = 6
		pos = Vector(25, 18)
		scale = 0.5
		pygame.draw.line(globals.game_manager.win, (204, 102, 0), pos, pos + Vector(0, 40) * scale, 1)
		for i in range(len(self.vertices) - 1):
			# draw alternating lines red and white
			pygame.draw.line(globals.game_manager.win, (255, 255*it, 255*it), self.vertices[i] * scale + pos, self.vertices[i + 1] * scale + pos, rad)
			it = (it + 1) % 2
			rad -= 1