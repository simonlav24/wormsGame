

import pygame
from random import uniform
from math import cos, sin, pi

from common.vector import Vector
from common import GameVariables, blit_weapon_sprite

from entities import PhysObj
from game.world_effects import boom
from game.visual_effects import Blast
from entities.fire import Fire


class ChilliPepper(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "chilli pepper")
		self.damp = 0.5
		self.angle = 0
		self.boomAffected = False
		self.bounceBeforeDeath = 6
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , (int(self.pos.x - GameVariables().cam_pos[0] - surf.get_size()[0]/2), int(self.pos.y - GameVariables().cam_pos[1] - surf.get_size()[1]/2)))
	
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
	
	def collisionRespone(self, ppos):
		boom(ppos, 25)
		for i in range(40):
			s = Fire(self.pos, 5)
			s.vel = Vector(cos(2 * pi * i / 40), sin(2 * pi * i / 40)) * uniform(1.3, 2)