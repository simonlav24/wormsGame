
import pygame
from math import pi, copysign
from random import uniform, choice

from common import GameVariables, point2world, sprites
from common.vector import *

from entities.physical_entity import PhysObj

class GunShell(PhysObj):
	def __init__(self, pos, vel=None, index=0, direction: Vector=Vector()):
		super().__init__(pos)
		self.pos = pos
		facing = copysign(1, direction[0])
		if facing == 0:
			facing = choice([-1,1])
		self.vel = Vector(-uniform(1,2.5) * facing, uniform(-8,-5))
		if vel:
			self.vel = vel
		self.radius = 2
		self.bounce_before_death = 4
		self.index = index
		self.damp = 0.2
		if index == 0:
			self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
			self.surf.blit(sprites.sprite_atlas, (0,0), (16,112,16,16))
		self.angle = uniform(0, 2 * pi)
		self.sound_collision = False

	def apply_force(self):
		self.acc.y += GameVariables().physics.global_gravity * 2.5

	def step(self):
		super().step()
		self.angle -= self.vel.x * 4

	def draw(self, win: pygame.Surface):
		if self.index == 0:
			angle = 45 * round(self.angle / 45)
			surf = pygame.transform.rotate(self.surf, angle)
			win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())/2))
		if self.index == 1:
			pygame.draw.circle(win, (25,25,25), point2world(self.pos), 3, 1)




