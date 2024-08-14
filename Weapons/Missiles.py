

import pygame
from typing import List
from math import cos, pi, sin, radians, degrees
from random import uniform, randint, choice

from Common import blit_weapon_sprite
from Constants import ColorType
from GameVariables import GameVariables, point2world
from PhysicalEntity import PhysObj
from WorldEffects import boom
from vector import *
from Effects import Blast

class Missile (PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255,255,0)
		self.bounceBeforeDeath = 1
		self.windAffected = 1
		self.boomRadius = 28
		self.megaBoom = False or GameVariables().mega_weapon_trigger
		if randint(0,50) == 1:
			self.megaBoom = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "missile")
	def deathResponse(self):
		if self.megaBoom:
			self.boomRadius *= 2
		boom(self.pos, self.boomRadius)
	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), randint(5,8), 30, 3)