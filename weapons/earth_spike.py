


from random import uniform, randint, choice
from math import pi

import pygame

from common import GameVariables, sprites
from common.vector import *

from game.map_manager import MapManager, GRD
from entities import Debrie
from game.team_manager import TeamManager


def calc_earth_spike_pos():
	dot = 1.0 - GameVariables().player.get_shooting_angle() / pi
	x_from_worm = GameVariables().player.pos.x + dot * 70 * GameVariables().player.facing
	if MapManager().is_ground_at(Vector(x_from_worm, GameVariables().player.pos.y).integer()):
		y = GameVariables().player.pos.y
		while MapManager().is_ground_at(Vector(x_from_worm, y).integer()):
			y -= 2
			if y < 0:
				return None
	else:
		y = GameVariables().player.pos.y
		while not MapManager().is_ground_at(Vector(x_from_worm, y).integer()):
			y += 2
			if y > MapManager().game_map.get_height():
				return None
	return Vector(x_from_worm, y)


class EarthSpike:
	def __init__(self, pos):
		self.squareSize = Vector(16,32)
		self.pos = pos
		GameVariables().register_non_physical(self)
		self.timer = 0
		self.surf = pygame.Surface((32, 32), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), ((32, 96), (32, 32)))
		if randint(0, 1) == 0:
			self.surf = pygame.transform.flip(self.surf, True, False)
		self.colors = [(139, 140, 123), (91, 92, 75), (208, 195, 175), (48, 35, 34)]
	
	def step(self):
		if self.timer < 5:
			for i in range(randint(5,10)):
				d = Debrie(self.pos + Vector(randint(-8,8), -2), 10, self.colors, 1, False)
				d.vel = vectorUnitRandom() / 3.0
				d.vel.y = uniform(-10, -8)
				d.radius = choice([2,1])
		if self.timer == 5:
			surf = pygame.transform.scale(self.surf, (32, 16))
			rectPos = self.pos + Vector(-surf.get_width() // 2, 3 - surf.get_height())
			#win.blit(surf, point2world(rectPos))
			MapManager().stain(self.pos - Vector(0, 3), sprites.hole, (32,32), True)
			
		if self.timer == 6:
			rectPos = self.pos + Vector(-self.surf.get_width() // 2, 3 - self.surf.get_height())
			for obj in GameVariables().get_physicals():
				if obj in GameVariables().get_debries():
					continue
				if obj.pos.x > rectPos.x + 8 and obj.pos.x <= rectPos.x + self.surf.get_width() - 8 \
						and obj.pos.y > rectPos.y and obj.pos.y <= rectPos.y + self.surf.get_height():
					obj.pos += Vector(0, -self.surf.get_height())
					obj.vel.x = obj.pos.x - self.pos.x
					obj.vel.y -= randint(7,9)
					if obj in GameVariables().get_worms() and not obj in TeamManager().current_team.worms:
						obj.damage(randint(25,35))
			
			MapManager().ground_map.blit(self.surf, rectPos)
			surf = self.surf.copy()
			pixels = pygame.PixelArray(surf)
			for i in self.colors:
				pixels.replace(i, GRD)
			del pixels
			MapManager().game_map.blit(surf, rectPos)
		self.timer += 1
	
	def draw(self, win: pygame.Surface):
		pass