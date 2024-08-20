
from random import randint
from math import pi

import pygame

from common.vector import *
from common import GameVariables, WHITE, RED, point2world

from game.team_manager import TeamManager
from game.map_manager import MapManager, GRD
from game.world_effects import boom


class ShootingTarget:
	numTargets = 10
	_reg = []
	def __init__(self):
		GameVariables().register_non_physical(self)
		ShootingTarget._reg.append(self)
		self.pos = Vector(randint(10, MapManager().game_map.get_width() - 10), randint(10, MapManager().game_map.get_height() - 50))
		self.radius = 10
		pygame.draw.circle(MapManager().game_map, GRD, self.pos, self.radius)
		self.points = [self.pos + vectorFromAngle((i / 11) * 2 * pi) * (self.radius - 2) for i in range(10)]
	def step(self):
		for point in self.points:
			if MapManager().game_map.get_at(point.vec2tupint()) != GRD:
				self.explode()
				return
	def explode(self):
		boom(self.pos, 15)
		GameVariables().unregister_non_physical(self)
		if self in ShootingTarget._reg:
			ShootingTarget._reg.remove(self)
		TeamManager().current_team.points += 1 # can be event
		if len(ShootingTarget._reg) < ShootingTarget.numTargets:
			ShootingTarget()
		# todo: add to score list
		
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius))
		pygame.draw.circle(win, RED, point2world(self.pos), int(self.radius - 4))
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius - 8))