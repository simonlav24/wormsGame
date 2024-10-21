

from random import randint, uniform
from math import pi

import pygame

from common import GameVariables, point2world, sprites, blit_weapon_sprite
from common.vector import *

from game.map_manager import MapManager, GRD
from entities import PhysObj, Worm

class Bee:
	def __init__(self, pos, angle):
		GameVariables().register_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.stable = False
		self.is_boom_affected = False
		self.radius = 1
		self.color = (230, 230, 0)
		self.angle = angle
		self.target: Worm | None = None
		self.lifespan = 330
		self.unreachable = []
		self.vel = Vector()
		self.surf = None
	
	def remove_from_game(self):
		GameVariables().unregister_physical(self)
	
	def step(self):
		self.lifespan -= 1
		GameVariables().game_distable()
		if self.lifespan == 0:
			self.remove_from_game()
			return
		if self.target:
			self.angle = (self.target.pos - self.pos).getAngle()
		else:
			self.angle += uniform(-0.6,0.6)
		ppos = self.pos + vector_from_angle(self.angle)
		if ppos.x >= MapManager().game_map.get_width() or ppos.y >= MapManager().game_map.get_height() or ppos.x < 0 or ppos.y < 0:
			ppos = self.pos + vector_from_angle(self.angle) * -1
			self.angle += pi
		try:
			if MapManager().game_map.get_at((ppos.vec2tupint())) == GRD:
				ppos = self.pos + vector_from_angle(self.angle) * -1
				self.angle += pi
				if self.target:
					self.unreachable.append(self.target)
					self.target = None
		except IndexError:
			print("bee index error")
		self.pos = ppos
		
		if self.lifespan % 40 == 0:
			self.unreachable = []
		
		if self.lifespan < 300:
			closest_dist = 100
			for worm in GameVariables().get_worms():
				if worm in self.unreachable:
					continue
				distance = dist(self.pos, worm.pos)
				if distance < 50 and distance < closest_dist:
					self.target = worm
					closest_dist = distance
			if self.target:
				if dist(self.pos, self.target.pos) > 50 or self.target.health <= 0:
					self.target = None
					return
				if dist(self.pos, self.target.pos) < self.target.radius:
					# sting
					self.target.vel.y -= 2
					if self.target.vel.y < -2:
						self.target.vel.y = 2
					if self.pos.x > self.target.pos.x:
						self.target.vel.x -= 1
					else:
						self.target.vel.x += 1
					self.remove_from_game()
					self.target.damage(uniform(1,8))
	
	def draw(self, win: pygame.Surface):
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())))

class BeeHive(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.color = (255, 204, 0)
		self.damp = 0.4
		self.unload = False
		self.beeCount = 50
		
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0, 0), "bee hive")
		self.angle = 0
	
	def step(self):
		super().step()
		self.angle -= self.vel.x*4
		if self.beeCount <= 0:
			self.dead = True
		
	def on_collision(self, ppos):
		out = randint(1,3)
		for _ in range(out):
			b = Bee(self.pos, uniform(0, 2 * pi))
			b.surf = sprites.bee
			self.beeCount -= 1
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
