

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
		super().__init__(pos, direction, energy, "cluster grenade")

	def death_response(self):
		megaBoom = False
		boom(self.pos, 25)
		if randint(0,50) == 1 or GameVariables().mega_weapon_trigger:
			megaBoom = True
		if megaBoom:
				for j in range(10):
					k = Missile(self.pos, (uniform(-0.5,0.5),uniform(-0.7,-0.1)), 0.5)
					k.vel.x += self.vel.x * 0.5
					k.vel.y += self.vel.y * 0.5
					k.is_wind_affected = 0
					k.is_boom_affected = False
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
			m.is_wind_affected = 0
			m.is_boom_affected = False
			m.color = (0,50,0)
			m.radius = 1.5
			m.surf.fill((0,0,0,0))
			m.surf.blit(sprites.sprite_atlas, (0,0), (0,96,16,16))
			if i == 0:
				GameVariables().cam_track = m