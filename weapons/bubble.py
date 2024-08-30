

import pygame
from random import randint, uniform

from common import GameVariables, point2world, EntityPhysical
from common.vector import *

from game.map_manager import MapManager, SKY
from game.visual_effects import DropLet

class Bubble:
	cought = []
	def __init__(self, pos, direction, energy):
		GameVariables().register_non_physical(self)
		self.pos = vectorCopy(pos)
		self.acc = Vector()
		self.vel = Vector(direction[0], direction[1]).rotate(uniform(-0.1, 0.1)) * energy * 5
		self.radius = 1
		self.grow = randint(7, 13)
		self.color = (220,220,220)
		self.catch = None
		self.ignore: EntityPhysical = None
	
	def apply_force(self):
		self.acc.y -= GameVariables().physics.global_gravity * 0.3
		self.acc.x += GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * 0.5
	
	def step(self):
		GameVariables().game_distable()
		self.apply_force()
		self.vel += self.acc * GameVariables().dt
		self.pos += self.vel * GameVariables().dt
		self.vel.x *= 0.99
		self.acc *= 0
		
		if self.radius <= self.grow and GameVariables().time_overall % 5 == 0:
			self.radius += 1 * GameVariables().dt
			
		if not self.catch:
			for obj in GameVariables().get_physicals():
				if obj == self.ignore or obj in Bubble.cought or obj in GameVariables().get_debries():
					continue
				if dist(obj.pos, self.pos) < obj.radius + self.radius:
					self.catch = obj
					Bubble.cought.append(self.catch)
					GameVariables().cam_track = self
		else:
			self.catch.pos = self.pos
			self.catch.vel *= 0

		if GameVariables().config.option_closed_map and (self.pos.x - self.radius <= 0 or self.pos.x + self.radius >= MapManager().game_map.get_width() - GameVariables().water_level):
			self.burst()
		if self.pos.y < 0 and (MapManager().is_ground_at((int(self.pos.x + self.radius), 0)) or MapManager().is_ground_at((int(self.pos.x - self.radius), 0))):
			self.burst()
		if self.pos.y < -50:
			self.burst()
		if self.pos.y - self.radius <= 0 and MapManager().is_ground_at((int(self.pos.x), 0)):
			self.burst()
		if randint(0, 300) == 1:
			if not MapManager().is_ground_at(self.pos.integer()):
				self.burst()
	
	def burst(self):
		if self.catch:
			self.catch.vel = self.vel * 0.6
			if self == GameVariables().cam_track:
				GameVariables().cam_track = self.catch
		self.catch = None
		pygame.draw.circle(MapManager().game_map, SKY, self.pos, self.radius)
		pygame.draw.circle(MapManager().ground_map, SKY, self.pos, self.radius)
		GameVariables().unregister_non_physical(self)
		for _ in range(min(int(self.radius), 8)):
			d = DropLet(self.pos + vectorUnitRandom() * self.radius, vectorUnitRandom())
			d.vel += self.vel
			d.radius = 1
	
	def draw(self, win: pygame.Surface):
		pygame.gfxdraw.circle(win, *point2world(self.pos), int(self.radius), self.color)