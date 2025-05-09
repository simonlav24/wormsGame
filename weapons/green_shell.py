
from random import randint

import pygame

from common import GameVariables, sprites, RIGHT, LEFT, point2world
from common.vector import *

from entities import PhysObj


class GreenShell(PhysObj):
	def __init__(self, pos):
		super().__init__(pos)
		GameVariables().get_electrocuted().append(self)
		self.ignore = []

		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(0,-0.5)
		self.radius = 6
		self.damp = 0.01
		self.timer = 0
		self.is_boom_affected = False
		self.facing = RIGHT
		self.ignore = []
		self.speed = 3
		self.is_worm_collider = True
	
	def on_out_of_map(self):
		self.dead = True
	
	def remove_from_game(self) -> None:
		super().remove_from_game()
		GameVariables().get_electrocuted().remove(self)

	def step(self):
		super().step()
		self.timer += 1
			
		if not self.speed == 0:
			self.is_worm_collider = True
			self.damp = 0.01
			self.is_boom_affected = False
			self.stable = False
			for _ in range(self.speed):
				moved = self.move(self.facing)
			
			if not moved:
				self.facing *= -1
				
			for worm in GameVariables().get_physicals():
				if worm == self or worm in self.ignore:
					continue
				if distus(worm.pos, self.pos) < (self.radius + worm.radius) * (self.radius + worm.radius):
					self.ignore.append(worm)
					worm.vel = Vector(self.facing * randint(1,2),-randint(2,4))*0.8
					if worm in GameVariables().get_worms():
						worm.damage(randint(10, 25))
		else:
			self.is_worm_collider = False
			self.damp = 0.5
			self.is_boom_affected = True
			self.stable = True
				
		if self.timer % 20 == 0:
			self.ignore = []
		
		if self.timer == 100:
			self.speed = 2
		if self.timer == 200:
			self.speed = 1
		if self.timer >= 300:
			if self.timer == 300:
				GameVariables().game_distable()
			self.speed = 0
			if int(self.vel.x) >= 1:
				if self.vel.x >= 0:
					self.facing = RIGHT
				else:
					self.facing = LEFT
				if int(self.vel.x) >= 3:
					self.speed = 3
				else:
					self.speed = int(self.vel.x)
				
				self.timer = (3 - self.speed) * 100
	
	def draw(self, win: pygame.Surface):
		if not self.speed == 0:
			index = int((self.timer*(self.speed/3) % 12)/3)
		else:
			index = 0	
		win.blit(sprites.sprite_atlas, point2world(self.pos - Vector(16,16)/2), ((index*16, 48), (16,16)))

	def electrocute(self, origin: Vector) -> None:
		if self.speed < 3:
			self.facing = LEFT if self.pos.x > self.pos.x else RIGHT
			self.speed = 3
			self.timer = 0