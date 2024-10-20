''' aerial weapons '''

from random import randint, uniform
from math import cos, sin, pi

import pygame

from common import point2world, GameVariables, sprites
from common.vector import *

from game.world_effects import boom
from game.map_manager import MapManager, GRD, SKY
from entities import Fire
from weapons.grenades import PhysObj
from weapons.missiles import SeekerBase, Missile
from weapons.mine import Mine



def fire_airstrike(**kwargs):
	pos = kwargs.get('pos')
	x = pos[0]
	y = 5
	for i in range(5):
		f = Missile((x - 40 + 20*i, y - i), (GameVariables().airstrike_direction ,0), 0.1)
		f.megaBoom = False
		f.is_boom_affected = False
		f.radius = 1
		f.boomRadius = 19
		if i == 2:
			GameVariables().cam_track = f

def fire_minestrike(**kwargs):
	pos = kwargs.get('pos')
	megaBoom = False
	if randint(0,50) == 1 or GameVariables().mega_weapon_trigger:
		megaBoom = True
	x = pos[0]
	y = 5
	if megaBoom:
		for i in range(20):
			m = Mine((x - 40 + 4*i, y - i))
			m.vel.x = GameVariables().airstrike_direction
			if i == 10:
				GameVariables().cam_track = m
	else:
		for i in range(5):
			m = Mine((x - 40 + 20*i, y - i))
			m.vel.x = GameVariables().airstrike_direction
			if i == 2:
				GameVariables().cam_track = m

def fire_napalmstrike(**kwargs):
	pos = kwargs.get('pos')
	x = pos[0]
	y = 5
	for i in range(70):
		f = Fire((x - 35 + i, y ))
		f.vel = Vector(cos(uniform(pi, 2 * pi)), sin(uniform(pi, 2 * pi))) * 0.5
		if i == 2:
			GameVariables().cam_track = f

class Seagull(SeekerBase):
	def __init__(self, pos, direction, energy):
		super().__init__(pos, direction, energy)
		self.timer = 15 * GameVariables().fps
		self.target = Vector()
		self.chum = None
	
	def death_response(self):
		boom(self.pos, 30)
		self.remove_from_game()
	
	def remove_from_game(self):
		GameVariables().unregister_non_physical(self)
		self.chum.dead = True
	
	def step(self):
		super().step()
		self.target = self.chum.pos
	
	def draw(self, win: pygame.Surface):
		flip_x = self.vel.x > 0
		width = 16
		height = 13
		frame = GameVariables().time_overall // 2 % 3
		surf = pygame.Surface((16,16), pygame.SRCALPHA)
		surf.blit(sprites.sprite_atlas, (0,0), (frame * 16,80, 16, 16))
		win.blit(pygame.transform.flip(surf, flip_x, False), point2world(self.pos - Vector(width//2, height//2)))
		

class Chum(PhysObj):
	def __init__(self, pos, direction, energy, radius=0):
		super().__init__(pos)
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = radius
		if radius == 0:
			self.radius = randint(1,3)
		self.color = (255, 102, 102)
		self.damp = 0.5
		self.sticked = False
		self.stick = None
		self.alarm = randint(0,3) * GameVariables().fps
		self.ticking = False
		self.summoned = False
		self.is_boom_affected = False
		self.timer = 0
	
	def on_collision(self, ppos):
		if not self.summoned:
				self.ticking = True
				self.summoned = True
		if not self.sticked:
			self.sticked = True
			self.stick = vectorCopy((self.pos + ppos)/2)
			MapManager().game_map.set_at(self.stick.integer(), GRD)
	
	def death_response(self):
		if self.stick:
			MapManager().game_map.set_at(self.stick.integer(), SKY)
	
	def step(self):
		super().step()
		if self.ticking:
			if self.timer == self.alarm:
				s = Seagull(Vector(self.pos.x + randint(-100,100), -10), Vector(randint(-100,100), 0), 1)
				s.target = self.pos
				s.chum = self
			self.timer += 1
		if self.stick:
			self.pos = self.stick
			if not MapManager().is_ground_at(self.stick):
				self.sticked = False
				self.stick = None
	
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
