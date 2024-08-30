
from random import randint
from math import sin, cos, pi

import pygame

from common.vector import Vector, dist
from common import GameVariables, point2world, RIGHT, LEFT

from entities import PhysObj
from game.world_effects import boom
from game.visual_effects import Blast
from game.map_manager import MapManager

class TNT(PhysObj):
	def __init__(self, pos):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.radius = 2
		self.color = (230,57,70)
		self.bounce_before_death = -1
		self.damp = 0.2
		self.timer = 0

	def secondaryStep(self):
		self.timer += 1
		self.stable = False
		if self.timer == GameVariables().fps * 4:
			self.dead = True

	def death_response(self):
		boom(self.pos, 40)
		
	def draw(self, win: pygame.Surface):
		pygame.draw.rect(win, self.color, (int(self.pos.x -2) - int(GameVariables().cam_pos[0]),int(self.pos.y -4) - int(GameVariables().cam_pos[1]) , 3,8))
		pygame.draw.line(win, (90,90,90), point2world(self.pos + Vector(-1,-4)), point2world(self.pos + Vector(-1, -5*(GameVariables().fps * 4 - self.timer)/(GameVariables().fps * 4) - 4)), 1)
		if randint(0,10) == 1:
			Blast(self.pos + Vector(-1, -5*(GameVariables().fps * 4 - self.timer)/(GameVariables().fps * 4) - 4), randint(3,6), 150)


class Sheep(PhysObj):
	trigger = False
	def __init__(self, pos):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(0,-3)
		self.radius = 6
		self.color = (250,240,240)
		self.damp = 0.2
		self.timer = 0
		self.facing = RIGHT
		self.is_wind_affected = 0
	
	def secondaryStep(self):
		self.timer += 1
		self.stable = False
		moved = self.move(self.facing)
		if self.timer % 3 == 0:
			moved = self.move(self.facing)
		if not moved:
			if MapManager().is_ground_around(self.pos, self.radius+1):
				self.facing *= -1
		if self.timer % (GameVariables().fps / 2) == 0 and MapManager().is_ground_around(self.pos, self.radius+1):
			self.vel.y -= 4.5
		if Sheep.trigger and self.timer > 5:
			self.dead = True
		else:
			Sheep.trigger = False
		if self.timer >= 300:
			self.dead = True
	
	def death_response(self):
		Sheep.trigger = False
		boom(self.pos, 35)
	
	def draw(self, win: pygame.Surface):
		rad = self.radius + 1
		wig = 0.4 * sin(0.5 * self.timer)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(pi/4 + wig), rad * sin(pi/4 + wig))), 2)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(3*pi/4 - wig), rad * sin(3*pi/4 - wig))), 2)
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(self.facing*self.radius,0)), 4)


class Bull(PhysObj):
	def __init__(self, pos):
		super().__init__(pos)
		self.ignore = []
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(0,-3)
		self.radius = 6
		self.color = (165, 39, 40)
		self.damp = 0.2
		self.hits = 5
		self.timer = 0
		self.facing = RIGHT
		self.is_boom_affected = False
	
	def step(self):
		super().step()
		self.stable = False
		self.timer += 1
		moved = self.move(self.facing)
		moved = self.move(self.facing)
		if not moved:
			if MapManager().is_ground_around(self.pos, self.radius+1):
				self.hits -= 1
				boom(self.pos, 35)
				self.vel += Vector(-self.facing * 3, -1)
		for worm in GameVariables().get_worms():
			if worm in self.ignore:
				continue
			if dist(worm.pos, self.pos) < self.radius:
				self.ignore.append(worm)
				self.hits -= 1
				boom(self.pos, 35)
				self.vel += Vector(-self.facing * 3, -1)
		if self.timer % 10 == 0:
			self.ignore = []
		if self.hits == 0:
			self.dead = True
		if self.timer >= 300:
			boom(self.pos, 35)
			self.dead = True
	
	def draw(self, win: pygame.Surface):
		rad = self.radius + 1
		wig = 0.4*sin(0.5*self.timer)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(pi/4 + wig), rad * sin(pi/4 + wig))), 2)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(3*pi/4 - wig), rad * sin(3*pi/4 - wig))), 2)
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		pygame.draw.circle(win, self.color, point2world(self.pos + Vector(self.facing*(self.radius +1),-1)), 4)


