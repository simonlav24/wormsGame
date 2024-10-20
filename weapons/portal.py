
from math import degrees, sin, cos, pi
from random import randint, uniform, choice

import pygame

from common.vector import *
from common import GameVariables, point2world, sprites, darken

from game.map_manager import MapManager, GRD
from game.visual_effects import EffectManager

RADIUS_OF_CONTACT = 8
RADIUS_OF_RELEASE = 10

class Portal:
	def __init__(self, pos: Vector, direction: Vector, first: bool):
		GameVariables().register_non_physical(self)
		GameVariables().register_cycle_observer(self)
		self.direction = direction
		self.dir_neg = direction * -1
		self.pos = pos - direction * 5
		self.hold_pos = pos
		self.brother: Portal | None = None
	
		width, height = 8, 20
		
		self.color = (105, 255, 249) if first else (255, 194, 63)
		self.points = []
		angle = self.direction.getAngle()
		amount = 25
		for i in range(amount):
			t = (i / amount) * 2 * pi
			point = Vector(cos(t), sin(t))
			point[0] *= width / 2
			point[1] *= height / 2
			point.rotate(angle)
			point += self.pos
			self.points.append(point)
		self.points_translate = [vectorUnitRandom() for i in range(amount)]


		self.stable = True
		self.is_boom_affected = False
		self.health = 0
		
		self.posBro = Vector()
	
	def step(self):
		# check if self on map
		if not MapManager().game_map.get_at(self.hold_pos.vec2tupint()) == GRD:
			self.remove_from_game()
			if self.brother:
				self.brother.remove_from_game()
			return

		if self.brother:
			bro = (self.pos - GameVariables().player.pos)
			angle = self.direction.getAngle() - (self.pos - GameVariables().player.pos).getAngle()
			broAngle = self.brother.dir_neg.getAngle()
			finalAngle = broAngle + angle
			bro.setAngle(finalAngle)
			self.posBro = self.brother.pos - bro
			
		if self.brother:
			for obj in GameVariables().get_physicals():
				if distus(obj.pos, self.pos) <= RADIUS_OF_CONTACT * RADIUS_OF_CONTACT:
					bro = (self.pos - obj.pos)
					angle = self.direction.getAngle() - (self.pos - obj.pos).getAngle()
					broAngle = self.brother.dir_neg.getAngle()
					finalAngle = broAngle + angle
					bro.setAngle(finalAngle)
					obj.pos = self.brother.pos - bro
					
					posT = self.brother.pos - obj.pos
					posT.normalize()
					obj.pos = self.brother.pos + posT * RADIUS_OF_RELEASE
					
					angle = self.direction.getAngle() - obj.vel.getAngle()
					finalAngle = broAngle + angle
					obj.vel.setAngle(finalAngle)

					for i in range(randint(4, 8)):
						EffectManager().create_particle(self.brother.pos, obj.vel + vectorUnitRandom() * 0.5, self.brother.color)
		
		if randint(0, 30) == 1:
			point = choice(self.points)
			EffectManager().create_particle(point, Vector(uniform(-1,1), -2), self.color)


	def on_turn_begin(self):
		pass

	def on_turn_end(self):
		if self.brother is None:
			self.remove_from_game()

	def transform(self, vec: Vector) -> Vector:
		time = GameVariables().time_overall * 0.1
		x = vec[0] + 0.5 * sin(0.5 * vec[1] - time)
		y = vec[1] + 0.5 * sin(0.5 * vec[0] - time)
		return Vector(x, y)

	def draw(self, win: pygame.Surface):

		points = [point2world(self.transform(p)) for p in self.points]
		pygame.draw.polygon(win, darken(self.color), points)
		pygame.draw.lines(win, self.color, True, points, 1)

	def remove_from_game(self):
		GameVariables().unregister_non_physical(self)
		GameVariables().unregister_cycle_observer(self)


def fire_portal_gun(*args, **kwargs) -> Portal:
	steps = 500
	second_portal: Portal = kwargs.get('shooted_object')
	new_portal = None
	for t in range(5 , steps):
		testPos = kwargs.get('pos') + kwargs.get('direction') * t
		GameVariables().add_extra(testPos, (255,255,255), 3)
		
		# missed
		if t == steps - 1:
			if second_portal is not None:
				second_portal.remove_from_game()

		if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue

		# if hits map:
		if MapManager().game_map.get_at(testPos.vec2tupint()) == GRD:
			
			response = Vector(0,0)
			
			for i in range(12):
				ti = (i / 12) * 2 * pi
				
				check = testPos + Vector(8 * cos(ti), 8 * sin(ti))
				
				if check.x >= MapManager().game_map.get_width() or check.y >= MapManager().game_map.get_height() or check.x < 0 or check.y < 0:
					continue
				if MapManager().game_map.get_at(check.vec2tupint()) == GRD:
					# extra.append((check.x, check.y, (255,255,255), 100))
					response +=  Vector(8 * cos(ti), 8 * sin(ti))
			
			direction = response.normalize()
			
			new_portal = Portal(testPos, direction, second_portal is None)
			if second_portal is not None:
				new_portal.brother = second_portal
				second_portal.brother = new_portal
			break
	return new_portal



