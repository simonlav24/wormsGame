
import pygame
from random import uniform, randint, choice
from math import cos, sin, pi

from common import blit_weapon_sprite, ColorType, GameVariables, point2world
from common.game_event import GameEvents, EventComment
from common.vector import *

from entities.physical_entity import PhysObj
from entities.gun_shell import GunShell
from game.world_effects import boom



class Grenade (PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.color = (0,100,0)
		self.damp = 0.4
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "grenade")
		self.angle = 0

	def deathResponse(self):
		rad = 30
		if randint(0,50) == 1 or GameVariables().mega_weapon_trigger:
			rad *= 2
		boom(self.pos, rad)

	def secondaryStep(self):
		self.angle -= self.vel.x * 4 * GameVariables().dt
		self.timer += 1 * GameVariables().dt
		if self.timer >= GameVariables().fuse_time:
			self.dead = True
		self.stable = False

	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))


class HolyGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 3
		self.color = (230, 230, 0)
		self.damp = 0.5
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "holy grenade")
		self.angle = 0
		
	def deathResponse(self):
		boom(self.pos, 45)
		
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		self.timer += 1
		if self.timer == GameVariables().fuse_time + 2 * GameVariables().fps:
			self.dead = True
		if self.timer == GameVariables().fuse_time + GameVariables().fps:
			comments = [
				[{'text': "o lord bless this thy "}, {'text': 'hand grenade', 'color': (210,210,0)}],
				[{'text': "blow thine enemy to tiny bits"}],
				[{'text': "feast upon the lambs and sloths and carp"}],
				[{'text': "three shall be the number thou shalt count"}],
				[{'text': "thou shall snuff that"}],
			]
			GameEvents().post(EventComment(choice(comments)))


class Banana(Grenade):
	def __init__(self, pos, direction, energy, used = False):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255, 204, 0)
		self.damp = 0.5
		self.timer = 0
		self.angle = 0
		self.used = used
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "banana")
		self.angle = 0

	def collisionRespone(self, ppos):
		if self.used:
			self.dead = True

	def deathResponse(self):
		if self.used:
			boom(self.pos, 40)
			return
		boom(self.pos, 40)
		for i in range(5):
			angle = (i * pi) / 6 + pi / 6
			direction = (cos(angle)*uniform(0.2,0.6), -sin(angle))
			m = Banana(self.pos, direction, uniform(0.3,0.8), True)
			m.boomAffected = False
			if i == 2:
				GameVariables().cam_track = m

	def secondaryStep(self):
		if not self.used: 
			self.timer += 1
		if self.timer == GameVariables().fuse_time:
			self.dead = True
		self.angle -= self.vel.x*4