import pygame
from random import uniform, randint
from math import sin, pi

from common import GameVariables, sprites, point2world
from common.vector import *
from game.map_manager import MapManager, SKY, GRD
from entities import PhysObj, Fire
from game.world_effects import boom


class ExplodingProp(PhysObj):
	def deathResponse(self):
		boom(self.pos, 20)
		pygame.draw.rect(MapManager().objects_col_map, SKY, (int(self.pos.x -3),int(self.pos.y -5), 7,10))
		for i in range(40):
			s = Fire(self.pos, 5)
			s.vel = vectorFromAngle(2 * pi * i / 40, uniform(1.3,2))
		if self in PetrolCan._cans:
			PetrolCan._cans.remove(self)
	
	def damage(self, value, damageType=0):
		dmg = value * GameVariables().damage_mult
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0


class PetrolCan(ExplodingProp):
	_cans = [] 
	def __init__(self, pos = (0,0)):
		PetrolCan._cans.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 6
		self.color = (191, 44, 44)
		self.damp = 0.1
		self.health = 5
		self.extraCollider = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (64, 96, 16, 16))

	def secondaryStep(self):
		if self.health <= 0:
			self.dead = True

	def draw(self, win: pygame.Surface):
		win.blit(self.surf , point2world(self.pos - tup2vec(self.surf.get_size())/2))
		pygame.draw.rect(MapManager().objects_col_map, GRD, (int(self.pos.x -6),int(self.pos.y -8), 12,16))



