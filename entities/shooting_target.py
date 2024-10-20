
from random import randint
from math import pi

import pygame

from common.vector import *
from common import GameVariables, WHITE, RED, point2world

from game.map_manager import MapManager, GRD
from game.world_effects import boom


class ShootingTarget:
	
	def __init__(self):
		GameVariables().register_non_physical(self)
		GameVariables().get_targets().append(self)
		self.pos = Vector(randint(10, MapManager().game_map.get_width() - 10), randint(10, MapManager().game_map.get_height() - 50))
		self.radius = 10
		pygame.draw.circle(MapManager().game_map, GRD, self.pos, self.radius)
		self.points = [self.pos + vector_from_angle((i / 11) * 2 * pi) * (self.radius - 2) for i in range(10)]
		self.is_done = False
	
	def step(self):
		for point in self.points:
			if MapManager().game_map.get_at(point.vec2tupint()) != GRD:
				self.explode()
				return
	
	def explode(self):
		boom(self.pos, 15)
		GameVariables().unregister_non_physical(self)
		self.is_done = True
		GameVariables().get_targets().remove(self)
		
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius))
		pygame.draw.circle(win, RED, point2world(self.pos), int(self.radius - 4))
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius - 8))