''' aerial weapons '''

from random import randint

import pygame

from common import point2world, GameVariables, sprites
from common.vector import *

from game.world_effects import boom
from game.map_manager import MapManager, GRD, SKY
from weapons.grenades import Grenade
from weapons.missiles import Seeker

class Seagull(Seeker):
	_reg = []
	def __init__(self, pos, direction, energy):
		self.initialize(pos, direction, energy)
		Seagull._reg.append(self)
		self.timer = 15 * GameVariables().fps
		self.target = Vector()
		self.chum = None
	
	def deathResponse(self):
		boom(self.pos, 30)
		self.removeFromGame()
	
	def removeFromGame(self):
		if self in Seagull._reg:
			Seagull._reg.remove(self)
		GameVariables().unregister_non_physical(self)
		self.chum.dead = True
	
	def secondaryStep(self):
		self.target = self.chum.pos
	
	def draw(self, win: pygame.Surface):
		flip_x = self.vel.x > 0
		width = 16
		height = 13
		frame = GameVariables().time_overall // 2 % 3
		surf = pygame.Surface((16,16), pygame.SRCALPHA)
		surf.blit(sprites.sprite_atlas, (0,0), (frame * 16,80, 16, 16))
		win.blit(pygame.transform.flip(surf, flip_x, False), point2world(self.pos - Vector(width//2, height//2)))
		

class Chum(Grenade):
	_chums = []
	def __init__(self, pos, direction, energy, radius=0):
		Chum._chums.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = radius
		if radius == 0:
			self.radius = randint(1,3)
		self.color = (255, 102, 102)
		self.bounceBeforeDeath = -1
		self.damp = 0.5
		self.sticked = False
		self.stick = None
		self.timer = 0
		self.alarm = randint(0,3) * GameVariables().fps
		self.ticking = False
		self.summoned = False
		self.boomAffected = False
	
	def collisionRespone(self, ppos):
		if not self.summoned:
				self.ticking = True
				self.summoned = True
		if not self.sticked:
			self.sticked = True
			self.stick = vectorCopy((self.pos + ppos)/2)
			MapManager().game_map.set_at(self.stick.integer(), GRD)
	
	def deathResponse(self):
		Chum._chums.remove(self)
		if self.stick:
			MapManager().game_map.set_at(self.stick.integer(), SKY)
	
	def secondaryStep(self):
		if self.ticking:
			if self.timer == self.alarm:
				s = Seagull(Vector(self.pos.x + randint(-100,100), -10), Vector(randint(-100,100), 0), 1)
				s.target = self.pos
				s.chum = self
			self.timer += 1
		if self.stick:
			self.pos = self.stick
			if not MapManager().is_ground_at(self.stick):
				self.sticked = False
				self.stick = None
	
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
