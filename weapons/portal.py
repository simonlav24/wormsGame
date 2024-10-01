
from math import degrees, sin, cos, pi

import pygame

from common.vector import *
from common import GameVariables, point2world, sprites

from game.map_manager import MapManager, GRD

RADIUS_OF_CONTACT = 8
RADIUS_OF_RELEASE = 10

class Portal:
	_reg = []
	def __init__(self, pos: Vector, direction: Vector, first: bool):
		GameVariables().register_non_physical(self)
		GameVariables().register_cycle_observer(self)
		self.direction = direction
		self.dirNeg = direction * -1
		self.pos = pos - direction * 5
		self.holdPos = pos
		self.brother: Portal | None = None
		width, height = 32, 16
		
		surf = pygame.Surface((width, height), pygame.SRCALPHA)

		if first:
			surf.blit(sprites.sprite_atlas, (0,0), (32, 128, width, height))
		else:
			surf.blit(sprites.sprite_atlas, (0,0), (0, 128, width, height))
			
		self.surf = pygame.transform.rotate(surf, 90 - degrees(self.direction.getAngle()))
		
		self.stable = True
		self.is_boom_affected = False
		self.health = 0
		
		self.posBro = Vector()
	
	def step(self):
		# check if self on map
		if not MapManager().game_map.get_at(self.holdPos.vec2tupint()) == GRD:
			self.remove_from_game()
			if self.brother:
				self.brother.remove_from_game()
			return

		if self.brother:
			Bro = (self.pos - GameVariables().player.pos)
			angle = self.direction.getAngle() - (self.pos - GameVariables().player.pos).getAngle()
			broAngle = self.brother.dirNeg.getAngle()
			finalAngle = broAngle + angle
			Bro.setAngle(finalAngle)
			self.posBro = self.brother.pos - Bro
			
		if self.brother:
			for obj in GameVariables().get_physicals():
				if distus(obj.pos, self.pos) <= RADIUS_OF_CONTACT * RADIUS_OF_CONTACT:
					Bro = (self.pos - obj.pos)
					angle = self.direction.getAngle() - (self.pos - obj.pos).getAngle()
					broAngle = self.brother.dirNeg.getAngle()
					finalAngle = broAngle + angle
					Bro.setAngle(finalAngle)
					obj.pos = self.brother.pos - Bro
					
					posT = self.brother.pos - obj.pos
					posT.normalize()
					obj.pos = self.brother.pos + posT * RADIUS_OF_RELEASE
					
					angle = self.direction.getAngle() - obj.vel.getAngle()
					finalAngle = broAngle + angle
					obj.vel.setAngle(finalAngle)
	
	def on_turn_end(self):
		if self.brother is None:
			self.remove_from_game()

	def draw(self, win: pygame.Surface):
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))

	def remove_from_game(self):
		GameVariables().unregister_non_physical(self)
		GameVariables().unregister_cycle_observer(self)


def fire_portal_gun(*args, **kwargs) -> Portal:
	steps = 500
	second_portal: Portal = kwargs.get('portal')
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



