
from enum import Enum

import pygame

from common import GameVariables, point2world, RIGHT, LEFT, EntityWorm
from common.vector import *

from game.world_effects import boom
from weapons.autonomous_object import AutonomousObject


class RaonState(Enum):
	FUSING = 0
	IDLE = 1
	SEARCHING = 2
	ADVANCING = 3

class Raon(AutonomousObject):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		GameVariables()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.color = (255, 204, 0)
		self.damp = 0.2
		self.target: EntityWorm = None
		self.inner_state = RaonState.FUSING
		self.timer = 10
		self.facing = RIGHT
	
	def engage(self) -> bool:
		self.inner_state = RaonState.ADVANCING
		self.timer = 20
		return super().engage()

	def step(self):
		super().step()

		if self.inner_state == RaonState.FUSING:
			self.timer -= 1
			if self.timer == 0:
				self.inner_state = RaonState.IDLE

		elif self.inner_state == RaonState.IDLE:
			close_worms = []
			for worm in GameVariables().get_worms():
				distance = distus(worm.pos, self.pos)
				if distance < 10000:
					close_worms.append((worm, distance))
			if len(close_worms) > 0:
				close_worms.sort(key = lambda elem: elem[1])
				self.target = close_worms[0][0]
			else:
				self.target = None
			if self.target:
				self.facing = RIGHT if self.target.pos.x > self.pos.x else LEFT

		elif self.inner_state == RaonState.ADVANCING:
			if self.target is None:
				return
			GameVariables().game_distable()
			self.move(self.facing)
			self.timer -= 1
			if self.timer == 0:
				self.inner_state = RaonState.IDLE

		if self.proximity() and not self.inner_state == RaonState.FUSING:
			self.dead = True
	
	def death_response(self):
		boom(self.pos, 25)
	
	def proximity(self):
		if self.target is None:
			return False
		if distus(self.target.pos, self.pos) < (self.radius + self.target.radius + 2) * (self.radius + self.target.radius + 2):
			return True
		return False
		
	def electrified(self):
		self.dead = True
	
	def draw(self, win: pygame.Surface):
		pygame.draw.rect(win, self.color, (point2world(self.pos - Vector(self.radius, self.radius)), (self.radius * 2, self.radius * 2)))
		pygame.draw.line(win, (255,0,0), point2world(self.pos + Vector(self.radius-1, self.radius)), point2world(self.pos + Vector(-self.radius, self.radius)))
		pygame.draw.line(win, (0,0,0), point2world(self.pos + Vector(0, self.radius - 1)), point2world(self.pos + Vector(0, self.radius + 2)))
		pygame.draw.line(win, (0,0,0), point2world(self.pos + Vector(-2, self.radius - 1)), point2world(self.pos + Vector(-2, self.radius + 2)))
		pygame.draw.line(win, (0,0,0), point2world(self.pos + Vector(2, self.radius - 1)), point2world(self.pos + Vector(2, self.radius + 2)))
		if self.target is not None:
			pygame.draw.circle(win, (255,255,255), point2world(self.pos + Vector(self.facing * self.radius/2,0)), 2)
			win.set_at(point2world(self.pos + Vector(self.facing * (self.radius/2), -1)), (0,0,0))
		
		else:
			pygame.draw.circle(win, (255,255,255), point2world(self.pos), 2)
			win.set_at(point2world(self.pos), (0,0,0))