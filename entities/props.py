import pygame
from random import uniform, randint
from math import sin, pi

from common import GameVariables, sprites, point2world, DamageType
from common.vector import *
from game.map_manager import MapManager, SKY_COL, GRD_COL
from entities import PhysObj, Fire
from game.world_effects import boom


class ExplodingProp(PhysObj):
	def __init__(self, pos, **kwargs) -> None:
		super().__init__(pos, **kwargs)
		GameVariables().get_exploding_props().append(self)
		GameVariables().get_obscuring_objects().append(self)
		self.health = 5

	def death_response(self):
		self.is_extra_collider = False
		boom(self.pos, 20)
		for i in range(40):
			s = Fire(self.pos, 5)
			s.vel = vector_from_angle(2 * pi * i / 40, uniform(1.3, 2))
	
	def remove_from_game(self) -> None:
		super().remove_from_game()
		GameVariables().get_exploding_props().remove(self)
		GameVariables().get_obscuring_objects().remove(self)

	def damage(self, value: int, damage_type: DamageType=DamageType.HURT, kill: bool=False) -> None:
		dmg = value * GameVariables().damage_mult
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0


class PetrolCan(ExplodingProp):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.radius = 6
		self.color = (191, 44, 44)
		self.damp = 0.1
		self.is_extra_collider = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (64, 96, 16, 16))

	def death_response(self):
		pygame.draw.rect(MapManager().objects_col_map, SKY_COL, (int(self.pos.x -6),int(self.pos.y -8), 12,16))
		super().death_response()

	def step(self):
		super().step()
		if self.health <= 0:
			self.dead = True

	def draw(self, win: pygame.Surface):
		win.blit(self.surf , point2world(self.pos - tup2vec(self.surf.get_size())/2))
		pygame.draw.rect(MapManager().objects_col_map, GRD_COL, (int(self.pos.x -6),int(self.pos.y -8), 12,16))



