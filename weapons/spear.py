
from typing import List

import pygame

from common import point2world, sprites, GameVariables, EntityWorm
from common.vector import *

from game.map_manager import MapManager, GRD
from entities import PhysObj


class Spear(PhysObj):
	def __init__(self, pos, direction, energy, worm_ignore: EntityWorm):
		super().__init__(pos)
		GameVariables().move_to_back_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.damp = 0.4
		self.stable = False
		self.bounce_before_death = 1
		self.color = (204, 102, 0)
		self.triangle = [Vector(0,2), Vector(7,0), Vector(0,-2)]
		self.is_worm_collider = True
		self.worms: List[EntityWorm] = []
		self.ignore = [worm_ignore]
	
	def step(self):
		super().step()
		for worm in GameVariables().get_worms():
			if worm in self.ignore:
				continue
			if distus(self.pos, worm.pos) < (worm.radius + 3) * (worm.radius + 3):
				self.worms.append(worm)
				worm.damage(20 + self.vel.getMag() * 1.5)
				self.ignore.append(worm)
		for i, worm in enumerate(self.worms):
			worm.pos = vectorCopy(self.pos) - 5 * normalize(self.vel) * i
			worm.vel *= 0
		for target in GameVariables().get_targets():
			if dist(self.pos + normalize(self.vel) * 8, target.pos) < target.radius + 1:
				self.is_boom_affected = False
				target.explode()
				return
	
	def death_response(self):
		self.pos += self.vel
		point = self.pos - normalize(self.vel) * 30
		pygame.draw.line(MapManager().game_map, GRD, self.pos, point, self.radius)
		pygame.draw.polygon(MapManager().game_map, GRD, [self.pos + rotateVector(i, self.vel.getAngle()) for i in self.triangle])
		
		pygame.draw.line(MapManager().ground_map, self.color, self.pos, point, self.radius)
		pygame.draw.polygon(MapManager().ground_map, (230,235,240), [self.pos + rotateVector(i, self.vel.getAngle()) for i in self.triangle])
		
		if len(self.worms) > 0:
			MapManager().stain(self.pos, sprites.blood, sprites.blood.get_size(), False)
		if len(self.worms) > 1:
			name = self.ignore[0].name_str
			color = self.ignore[0].get_team_data().color
			GameVariables().commentator.comment([{'text': name, 'color': color}, {'text': ' the impaler!'}])

	def draw(self, win: pygame.Surface):
		point = self.pos - normalize(self.vel) * 30
		pygame.draw.line(win, self.color, point2world(self.pos), point2world(point), self.radius)
		pygame.draw.polygon(win, (230,235,240), [point2world(self.pos + rotateVector(i, self.vel.getAngle())) for i in self.triangle])
		