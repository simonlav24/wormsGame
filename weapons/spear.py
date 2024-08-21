


import pygame

from common import point2world, sprites
from common.game_event import EventComment, GameEvents
from common.vector import *

from game.map_manager import MapManager, GRD
from entities import PhysObj, Worm
from entities.shooting_target import ShootingTarget


class Spear(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0, self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.damp = 0.4
		self.stable = False
		self.bounce_before_death = 1
		self.color = (204, 102, 0)
		self.triangle = [Vector(0,2), Vector(7,0), Vector(0,-2)]
		self.is_worm_collider = True
		self.worms = []
		self.ignore = [Worm.player]
	
	def step(self):
		super().step()
		for worm in PhysObj._worms:
			if worm in self.ignore:
				continue
			if distus(self.pos, worm.pos) < (worm.radius + 3) * (worm.radius + 3):
				self.worms.append(worm)
				worm.damage(20 + self.vel.getMag()*1.5)
				self.ignore.append(worm)
		for i, worm in enumerate(self.worms):
			worm.pos = vectorCopy(self.pos) - 5 * normalize(self.vel) * i
			worm.vel *= 0
		for target in ShootingTarget._reg:
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
			name = Worm.player.name_str
			color = Worm.player.team.color
			GameEvents().post(EventComment([{'text': name, 'color': color}, {'text': ' the impaler!'}]))

	def draw(self, win: pygame.Surface):
		point = self.pos - normalize(self.vel) * 30
		pygame.draw.line(win, self.color, point2world(self.pos), point2world(point), self.radius)
		pygame.draw.polygon(win, (230,235,240), [point2world(self.pos + rotateVector(i, self.vel.getAngle())) for i in self.triangle])
		