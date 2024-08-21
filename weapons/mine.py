

from random import randint

import pygame

from common import GameVariables, point2world
from common.vector import *

from game.visual_effects import EffectManager
from game.world_effects import boom
from entities.physical_entity import PhysObj


class Mine(PhysObj):
	def __init__(self, pos=(0,0), delay=0):
		super().__init__(pos)
		self._mines.append(self)
		self.radius = 2
		self.color = (52,66,71)
		self.damp = 0.35
		self.activated = False
		self.alive = delay == 0
		self.timer = delay
		self.exploseTime = randint(5, 100)
		self.is_wind_affected = 0

	def step(self):
		super().step()
		if not self.alive:
			self.timer -= 1
			if self.timer == 0:
				self.alive = True
				self.damp = 0.55
			return
		if not self.activated:
			for worm in PhysObj._worms:
				if worm.health <= 0:
					continue
				if distus(self.pos, worm.pos) < 625:
					self.activated = True
		else:
			self.timer += 1
			self.stable = False
			if self.timer == self.exploseTime:
				self.dead = True
				
		if self.activated:
			EffectManager().add_light(vectorCopy(self.pos), 50, (100,0,0,100))

	def death_response(self):
		boom(self.pos, 30)

	def draw(self, win: pygame.Surface):
		if GameVariables().config.option_digging:
			if self.activated:
				pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
				if self.timer % 2 == 0:
					pygame.draw.circle(win, (222,63,49), point2world(self.pos), 1)
			return

		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)		
		if not self.activated:
			pygame.draw.circle(win, (222,63,49), point2world(self.pos), 1)
		else:
			if self.timer % 2 == 0:
				pygame.draw.circle(win, (222,63,49), point2world(self.pos), 1)


class Gemino(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (52,66,71)
		self.bounce_before_death = 5
		self.damp = 0.6
	
	def on_collision(self, ppos):
		m = Mine(self.pos)
		m.vel = vectorUnitRandom() 
	
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(GameVariables().cam_pos[0]), int(self.pos.y) - int(GameVariables().cam_pos[1])), int(self.radius)+1)
		pygame.draw.circle(win, (222,63,49), (int(self.pos.x) - int(GameVariables().cam_pos[0]), int(self.pos.y) - int(GameVariables().cam_pos[1])), 1)