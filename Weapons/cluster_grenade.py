

import pygame
from random import uniform, randint

from common import blit_weapon_sprite, GameVariables, sprites
from common.vector import *

from entities.gun_shell import GunShell
from game.world_effects import boom

from weapons.grenades import Grenade
from weapons.missiles import Missile

class ClusterGrenade (Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.color = (0,50,0)
		self.bounceBeforeDeath = -1
		self.damp = 0.4
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "cluster grenade")
		self.angle = 0
	def deathResponse(self):
		megaBoom = False
		boom(self.pos, 25)
		if randint(0,50) == 1 or GameVariables().mega_weapon_trigger:
			megaBoom = True
		if megaBoom:
				for j in range(10):
					k = Missile(self.pos, (uniform(-0.5,0.5),uniform(-0.7,-0.1)), 0.5)
					k.vel.x += self.vel.x * 0.5
					k.vel.y += self.vel.y * 0.5
					k.windAffected = 0
					k.boomAffected = False
					k.boomRadius = 20
					k.color = (0,50,0)
					k.radius = 1.5
					k.surf.fill((0,0,0,0))
					k.surf.blit(sprites.sprite_atlas, (0,0), (0,96,16,16))
					if j == 5:
						GameVariables().cam_track = k
				return
		for i in range(-1,2):
			m = Missile(self.pos, (i*0.3,-0.7), 0.5)
			m.megaBoom = False
			m.vel.x += self.vel.x * 0.5
			m.vel.y += self.vel.y * 0.5
			m.windAffected = 0
			m.boomAffected = False
			m.color = (0,50,0)
			m.radius = 1.5
			m.surf.fill((0,0,0,0))
			m.surf.blit(sprites.sprite_atlas, (0,0), (0,96,16,16))
			if i == 0:
				GameVariables().cam_track = m