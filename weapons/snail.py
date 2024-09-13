

from math import degrees

import pygame

from common.vector import *
from common import GameVariables, point2world, RIGHT, LEFT, sprites

from game.map_manager import MapManager
from game.world_effects import boom
from entities import PhysObj


class Snail:
	around = [Vector(1,0), Vector(1,-1), Vector(0,-1), Vector(-1,-1), Vector(-1,0), Vector(-1,1), Vector(0,1), Vector(1,1)]
	def __init__(self, pos, anchor, clockwise=RIGHT):
		GameVariables().register_non_physical(self)
		self.pos = pos
		self.pos.integer()
		self.clockwise = clockwise
		self.anchor = anchor
		self.life = 0
		self.surf = pygame.Surface((6,6), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (70,48,6,6))
		if self.clockwise == LEFT:
			self.surf = pygame.transform.flip(self.surf, True, False)

	def climb(self):
		steps = 0
		while True:
			steps += 1
			if steps > 20:
				break
			revolvment = self.pos - self.anchor
			index = Snail.around.index(revolvment)
			candidate = self.anchor + Snail.around[(index + self.clockwise * -1) % 8]
			if MapManager().is_ground_at(candidate):
				self.anchor = candidate
			else:
				self.pos = candidate
				break
	
	def step(self):
		self.life += 1
		for _ in range(3):
				self.climb()
		for worm in GameVariables().get_worms():
			if distus(self.pos, worm.pos) < (3 + worm.radius) * (3 + worm.radius):
				GameVariables().unregister_non_physical(self)
				boom(self.pos, 30)
				return
	
	def draw(self, win: pygame.Surface):
		normal = MapManager().get_normal(self.pos, Vector(), 4, False, False)
		angle = round((-degrees(normal.getAngle()) - 90) / 22) * 22
		win.blit(pygame.transform.rotate(self.surf, angle) , point2world(self.pos - Vector(3,3)))

class SnailShell(PhysObj):
	def __init__(self, pos, direction, energy, facing: int):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 1
		self.bounce_before_death = 1
		self.damp = 0.2
		self.is_worm_collider = True
		self.is_extra_collider = True
		self.clockwise = facing
		self.timer = 0
		self.surf = pygame.Surface((6,6), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (64,48, 6,6))

	def set_surf(self, surf):
		self.surf = surf
	
	def on_collision(self, ppos):
		finalPos = vectorCopy(self.pos)
		finalAnchor = None

		for t in range(50):
			testPos = self.pos + normalize(self.vel) * t
			testPos.integer()
			if MapManager().is_ground_at(testPos):
				finalAnchor = testPos
				break
			else:
				finalPos = testPos

		if not finalAnchor:
			print("shell error")
			return
		GameVariables().cam_track = Snail(finalPos, finalAnchor, self.clockwise)
	
	def draw(self, win: pygame.Surface):
		self.timer += 1
		win.blit(pygame.transform.rotate(self.surf, (self.timer % 4) * 90), point2world(self.pos - Vector(3,3)))