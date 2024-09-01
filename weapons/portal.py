
from math import degrees, sin, cos, pi

import pygame

from common.vector import *
from common import GameVariables, point2world, GameState

from game.map_manager import MapManager, GRD

RADIUS_OF_CONTACT = 8
RADIUS_OF_RELEASE = 10

class Portal:
	_reg = []
	def __init__(self, pos: Vector, direction: Vector):
		Portal._reg.append(self)
		GameVariables().register_non_physical(self)
		self.direction = direction
		self.dirNeg = direction * -1
		self.pos = pos - direction * 5
		self.holdPos = pos
		self.brother: Portal | None = None
		width, height = 8,20
		
		s = pygame.Surface((width, height)).convert_alpha()
		s.fill((255,255,255,0))
		if len(Portal._reg) % 2 == 0:
			self.color = (255, 194, 63)
		else:
			self.color = (105, 255, 249)
			
		pygame.draw.ellipse(s, self.color, ((0,0), (width, height)))
		self.surf = pygame.transform.rotate(s, -degrees(self.direction.getAngle()))
		
		self.stable = True
		self.is_boom_affected = False
		self.health = 0
		
		self.posBro = Vector()
	
	def step(self):
		if not MapManager().game_map.get_at(self.holdPos.vec2tupint()) == GRD:
			GameVariables().unregister_non_physical(self)
			Portal._reg.remove(self)
			
			if self.brother:
				GameVariables().unregister_non_physical(self.brother)
				Portal._reg.remove(self.brother)			
			return
			
		if GameVariables().game_state == GameState.PLAYER_PLAY and not self.brother:
			GameVariables().unregister_non_physical(self)
			if self in Portal._reg:
				print(2)
				Portal._reg.remove(self)
			return
		
		if self.brother:
			Bro = (self.pos - GameVariables().player.pos)
			angle = self.direction.getAngle() - (self.pos - GameVariables().player.pos).getAngle()
			broAngle = self.brother.dirNeg.getAngle()
			finalAngle = broAngle + angle
			Bro.setAngle(finalAngle)
			self.posBro = self.brother.pos - Bro
			
		if self.brother:
			for worm in GameVariables().get_physicals():
				if worm in Portal._reg:
					continue
				if distus(worm.pos, self.pos) <= RADIUS_OF_CONTACT * RADIUS_OF_CONTACT:
					Bro = (self.pos - worm.pos)
					angle = self.direction.getAngle() - (self.pos - worm.pos).getAngle()
					broAngle = self.brother.dirNeg.getAngle()
					finalAngle = broAngle + angle
					Bro.setAngle(finalAngle)
					worm.pos = self.brother.pos - Bro
					
					posT = self.brother.pos - worm.pos
					posT.normalize()
					worm.pos = self.brother.pos + posT * RADIUS_OF_RELEASE
					
					angle = self.direction.getAngle() - worm.vel.getAngle()
					finalAngle = broAngle + angle
					worm.vel.setAngle(finalAngle)
	
	def draw(self, win: pygame.Surface):
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))




def firePortal(pos: Vector, direction: Vector, power: int=15):
	steps = 500
	for t in range(5,steps):
		testPos = pos + direction * t
		GameVariables().add_extra(testPos, (255,255,255), 3)
		
		# missed
		if t == steps - 1:
			if len(Portal._reg) % 2 == 1:
				p = Portal._reg.pop(-1)
				if p in GameVariables().get_physicals():
					GameVariables().get_physicals().remove(p)

		if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue

		# if hits map:
		if MapManager().game_map.get_at(testPos.vec2tupint()) == GRD:
			
			response = Vector(0,0)
			
			for i in range(12):
				ti = (i/12) * 2 * pi
				
				check = testPos + Vector(8 * cos(ti), 8 * sin(ti))
				
				if check.x >= MapManager().game_map.get_width() or check.y >= MapManager().game_map.get_height() or check.x < 0 or check.y < 0:
					continue
				if MapManager().game_map.get_at(check.vec2tupint()) == GRD:
					# extra.append((check.x, check.y, (255,255,255), 100))
					response +=  Vector(8 * cos(ti), 8 * sin(ti))
			
			direction = response.normalize()
			
			p = Portal(testPos, direction)
			if len(Portal._reg) % 2 == 0:
				brother = Portal._reg[-2]
				p.brother = brother
				brother.brother = p
			break



