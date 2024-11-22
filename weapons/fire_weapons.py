

import pygame
from random import uniform, randint
from math import cos, sin, pi, radians

from common.vector import *
from common import GameVariables, blit_weapon_sprite, point2world

from entities import PhysObj
from game.world_effects import boom
from game.visual_effects import Blast
from entities.fire import Fire


class PetrolBomb(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (158,66,43)
		self.bounce_before_death = 1 
		self.damp = 0.5
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "petrol bomb")
		self.angle = 0
	
	def secondaryStep(self):
		self.angle -= self.vel.x * 4
		Blast(self.pos + vectorUnitRandom() * randint(0,4) + vector_from_angle(-radians(self.angle)-pi/2) * 8, randint(3,6), 150)
	
	def death_response(self):
		boom(self.pos, 15)
		if randint(0,50) == 1 or GameVariables().mega_weapon_trigger:
			for i in range(80):
				s = Fire(self.pos, 5)
				s.vel = Vector(cos(2*pi*i/80), sin(2*pi*i/80))*uniform(3,4)
		else:
			for i in range(40):
				s = Fire(self.pos, 5)
				s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2)
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))


class ChilliPepper(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "chilli pepper")
		self.damp = 0.5
		self.angle = 0
		self.is_boom_affected = False
		self.bounce_before_death = 6
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , (int(self.pos.x - GameVariables().cam_pos[0] - surf.get_size()[0]/2), int(self.pos.y - GameVariables().cam_pos[1] - surf.get_size()[1]/2)))
	
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
	
	def on_collision(self, ppos):
		super().on_collision(ppos)
		boom(ppos, 25)
		for i in range(40):
			s = Fire(self.pos, 5)
			s.vel = Vector(cos(2 * pi * i / 40), sin(2 * pi * i / 40)) * uniform(1.3, 2)