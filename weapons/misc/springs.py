
from typing import List

import pygame

from common import GameVariables, EntityPhysical, point2world
from common.vector import Vector, dist, distus

from game.map_manager import MapManager


class MasterOfPuppets:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.springs: List[PointSpring] = []
		self.timer = 0
		for worm in GameVariables().get_worms():
			# point = Vector(worm.pos.x, 0)
			for t in range(200):
				posToCheck = worm.pos - Vector(0, t * 5)
				if MapManager().is_ground_at(posToCheck):
					break
				if posToCheck.y < 0:
					break
			rest = dist(posToCheck, worm.pos) / 2
			p = PointSpring(0.01, rest, worm, posToCheck)
			self.springs.append(p)
	
	def step(self):
		self.timer += 1
		if self.timer >= GameVariables().fps * 15:
			self.springs.clear()
			GameVariables().unregister_non_physical(self)
		for p in self.springs:
			p.step()
	
	def draw(self, win: pygame.Surface):
		for p in self.springs:
			p.draw(win)

class PointSpring:
	def __init__(self, k, rest, obj: EntityPhysical, point: Vector):
		self.k = k
		self.rest = rest
		self.obj = obj
		self.point = point
		self.alive = True
	
	def step(self):
		force = self.point - self.obj.pos
		x = force.getMag() - self.rest
		x = x * -1
		force.setMag(-1 * self.k * x)
		
		if distus(self.obj.pos, self.point) > self.rest * self.rest:
			self.obj.acc += force
		if not self.obj.alive:
			self.alive = False
	
	def draw(self, win: pygame.Surface):
		if not self.alive:
			return
		pygame.draw.line(win, (255, 220, 0), point2world(self.obj.pos), point2world(self.point))