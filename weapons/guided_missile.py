

import pygame
from math import pi, degrees, cos, sin, atan2
from random import uniform, randint

from common import blit_weapon_sprite, GameVariables, point2world
from common.vector import *

from entities import PhysObj, Fire
from game.world_effects import boom
from game.visual_effects import Blast
from game.map_manager import MapManager, GRD

class GuidedMissile(PhysObj):
	def __init__(self, pos):
		self.initialize()
		self.pos = pos
		self.speed = 5.5
		self.vel = Vector(0, -self.speed)
		self.stable = False
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "guided missile")
		self.radius = 3
	def applyForce(self):
		pass
	def turn(self, direc):
		self.vel.rotate(direc * 0.1)
	def step(self):
		GameVariables().cam_track = self
		self.pos += self.vel
		if pygame.key.get_pressed()[pygame.K_LEFT]:
			self.vel.rotate(-0.3)
		elif pygame.key.get_pressed()[pygame.K_RIGHT]:
			self.vel.rotate(0.3)
		Blast(self.pos - self.vel * 1.5 + vectorUnitRandom() * 2 - 10 * normalize(self.vel), randint(5,8))
		
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi
		collision = False
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + self.pos.x, (self.radius) * sin(r) + self.pos.y)
			if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() - GameVariables().water_level or testPos.x < 0:
				if GameVariables().config.option_closed_map:
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if MapManager().game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				collision = True
			
			r += pi /8
		
		if collision:
			boom(self.pos, 35)
			if randint(0,30) == 1 or GameVariables().mega_weapon_trigger:
				for i in range(80):
					s = Fire(self.pos, 5)
					s.vel = Vector(cos(2 * pi * i / 40), sin(2 * pi * i / 40)) * uniform(1.3, 4)
			self.removeFromGame()
		if self.pos.y > MapManager().game_map.get_height():
			self.removeFromGame()
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(self.surf, -90 -degrees(self.vel.getAngle()))
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))