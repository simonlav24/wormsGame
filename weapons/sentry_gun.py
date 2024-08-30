
from random import uniform, randint
from math import pi

import pygame


from common import GameVariables, point2world, ColorType, sprites
from common.vector import *

from game.world_effects import boom
from entities import PhysObj
from weapons.guns import fireMiniGun


class SentryGun(PhysObj):
	_sentries = []
	def __init__(self, pos, team_color: ColorType):
		self._sentries.append(self)
		super().__init__(pos)
		self.pos = Vector(pos[0],pos[1])
		
		self.color = (0, 102, 0)
		self.is_boom_affected = True
		self.radius = 9
		self.health = 50
		self.teamColor = team_color
		self.target = None
		self.damp = 0.1
		self.shots = 10
		self.firing = False
		self.timer = 20
		self.timesFired = randint(5,7)
		self.angle = 0
		self.angle2for = uniform(0, 2*pi)
		self.surf = pygame.Surface((17, 26), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (80, 32, 17, 26))
		self.electrified = False
		pygame.draw.circle(self.surf, self.teamColor, tup2vec(self.surf.get_size())//2, 2)
	
	def fire(self):
		self.firing = True
	
	def engage(self):
		close = []
		for worm in GameVariables().get_worms():
			if worm.team.color == self.teamColor:
				continue
			distance = distus(worm.pos, self.pos)
			if distance < 10000:
				close.append((worm, distance))
		if len(close) > 0:
			close.sort(key = lambda elem: elem[1])
			self.target = close[0][0]
		else:
			self.target = None
	
	def secondaryStep(self):
		if self.firing:
			if not self.target:
				return
			self.timer -= 1
			self.stable = False
			self.angle2for = (self.target.pos - self.pos).getAngle()
			if self.timer <= 0 and self.target:
				direction = self.target.pos - self.pos
				fireMiniGun(self.pos, direction)
				self.angle = direction.getAngle()
				self.shots -= 1
				if self.shots == 0:
					self.firing = False
					self.shots = 10
					self.timer = 20
					self.timesFired -= 1
					self.target = None
					if self.timesFired == 0:
						self.health = 0
		
		if self.electrified:
			if GameVariables().time_overall % 2 == 0:
				self.angle = uniform(0,2*pi)
				fireMiniGun(self.pos, vectorFromAngle(self.angle))
		
		self.angle += (self.angle2for - self.angle)*0.2
		if not self.target and GameVariables().time_overall % (GameVariables().fps*2) == 0:
			self.angle2for = uniform(0,2*pi)
		
		# extra "damp"
		if self.vel.x > 0.1:
			self.vel.x = 0.1
		if self.vel.x < -0.1:
			self.vel.x = -0.1
		if self.vel.y < 0.1:
			self.vel.y = 0.1
			
		if self.health <= 0:
			self.remove_from_game()
			self._sentries.remove(self)
			boom(self.pos, 20)
			
	def draw(self, win: pygame.Surface):
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))
		pygame.draw.line(win, self.teamColor, point2world(self.pos), point2world(self.pos + vectorFromAngle(self.angle) * 18))
	
	def damage(self, value, damageType=0):
		dmg = value
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0