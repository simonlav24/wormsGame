
from random import uniform, randint
from math import pi
from typing import List
from enum import Enum

import pygame

from common import GameVariables, point2world, ColorType, sprites, EntityWorm
from common.vector import *

from game.world_effects import boom
from weapons.guns import fireMiniGun
from weapons.autonomous_object import AutonomousObject


class SentryState(Enum):
	IDLE = 1
	SEARCHING = 2
	FIRING = 3


class SentryGun(AutonomousObject):
	def __init__(self, pos: Vector, team_color: ColorType, team_name: str, **kwargs):
		super().__init__(pos, **kwargs)
		self.color = (0, 102, 0)
		self.is_boom_affected = True
		self.radius = 9
		self.health = 50
		self.team_color = team_color
		self.team_name = team_name
		self.target: EntityWorm = None
		self.damp = 0.1
		self.shots = 10 # shots per turn
		self.timer = 20
		self.times_fired = randint(5,7) # turns to fire untill dead
		self.angle = 0
		self.angle2for = uniform(0, 2*pi)
		self.surf = pygame.Surface((17, 26), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (80, 32, 17, 26))
		self.electrified = False
		pygame.draw.circle(self.surf, self.team_color, tup2vec(self.surf.get_size())//2, 2)
		self.inner_state = SentryState.IDLE
	
	def engage(self) -> bool:
		self.inner_state = SentryState.SEARCHING
		return super().engage()
	
	def step(self):
		super().step()

		if self.inner_state == SentryState.SEARCHING:
			close_worms = []
			for worm in GameVariables().get_worms():
				if worm.get_team_data().team_name == self.team_name:
					continue
				distance = distus(worm.pos, self.pos)
				if distance < 10000:
					close_worms.append((worm, distance))
			if len(close_worms) > 0:
				close_worms.sort(key = lambda elem: elem[1])
				self.target = close_worms[0][0]
				self.inner_state = SentryState.FIRING
			else:
				self.target = None

		elif self.inner_state == SentryState.FIRING:
			if not self.target:
				return
			self.timer -= 1
			self.stable = False
			self.angle2for = (self.target.pos - self.pos).getAngle()
			if self.timer <= 0 and self.target:
				direction = self.target.pos - self.pos
				fireMiniGun(pos=self.pos, direction=direction)
				self.angle = direction.getAngle()
				self.shots -= 1
				if self.shots == 0:
					self.shots = 10
					self.timer = 20
					self.times_fired -= 1
					self.target = None
					if self.times_fired == 0:
						self.health = 0
					self.inner_state = SentryState.IDLE
					self.done()
		
		if self.electrified:
			if GameVariables().time_overall % 2 == 0:
				self.angle = uniform(0, 2 * pi)
				fireMiniGun(self.pos, vectorFromAngle(self.angle))
			self.electrified = False
		
		self.angle += (self.angle2for - self.angle) * 0.2
		if not self.target and GameVariables().time_overall % (GameVariables().fps * 2) == 0:
			self.angle2for = uniform(0, 2 * pi)
		
		# extra "damp"
		if self.vel.x > 0.1:
			self.vel.x = 0.1
		if self.vel.x < -0.1:
			self.vel.x = -0.1
		if self.vel.y < 0.1:
			self.vel.y = 0.1
			
		if self.health <= 0:
			self.remove_from_game()
			boom(self.pos, 20)
	
	def draw(self, win: pygame.Surface):
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))
		pygame.draw.line(win, self.team_color, point2world(self.pos), point2world(self.pos + vectorFromAngle(self.angle) * 18))
	
	def damage(self, value, damageType=0):
		dmg = value
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0