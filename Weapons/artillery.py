

import pygame
from random import randint

from common import blit_weapon_sprite, GameVariables, point2world, sprites
from common.vector import *

from game.visual_effects import SmokeParticles
from entities.physical_entity import PhysObj
from weapons.missiles import Missile


class Artillery(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (128, 0, 0)
		self.damp = 0.5
		self.timer = 0
		self.bombing = False
		self.boomAffected = False
		self.booms = randint(3,5)
		self.boomCount = 20 if randint(0,50) == 0 or GameVariables().mega_weapon_trigger else self.booms
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "flare")
		self.angle = 0
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	
	def secondaryStep(self):
		if not self.bombing:
			self.angle -= self.vel.x*4
			if self.stable:
				self.timer += 1
			else:
				self.timer = 0
			if randint(0, 5) == 0:
				SmokeParticles._sp.addSmoke(self.pos, color=(200,0,0))
			self.stable = False
			if self.timer == 50:
				self.bombing = True
		else:
			self.stable = False
			self.timer += 1
			if self.timer % 10 == 0:
				m = Missile((self.pos[0] + randint(-20,20), 0),(0,0),0 )
				m.windAffected = 0
				m.boomAffected = False
				m.megaBoom = False
				m.surf.fill((0,0,0,0))
				m.surf.blit(sprites.sprite_atlas, (0,0), (0,96,16,16))
				if self.boomCount == self.booms:
					GameVariables().cam_track = m
				self.boomCount -= 1
			if self.boomCount == 0:
				self.dead = True