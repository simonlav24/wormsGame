
from math import atan2, cos, sin, pi

import pygame

from common import GameVariables, point2world, blit_weapon_sprite
from common.vector import *

from game.map_manager import MapManager, GRD
from entities import PhysObj, Worm


class EndPearl(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,0,150)
	
	def on_collision(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi
		while r < angle + pi:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() - GameVariables().water_level or testPos.x < 0:
				if GameVariables().config.option_closed_map:
					response += ppos - testPos
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if MapManager().game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		self.remove_from_game()
		
		response.normalize()
		pos = self.pos + response * (Worm.player.radius + 2)
		Worm.player.pos = pos
	
	def draw(self, win: pygame.Surface):
		blit_weapon_sprite(win, point2world(self.pos - Vector(8,8)), "ender pearl")