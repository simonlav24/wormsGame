
from random import uniform, choice
from typing import List

import pygame

from common import GameVariables, blit_weapon_sprite, point2world, LEFT, sprites
from common.vector import vector_from_angle, vectorUnitRandom, Vector, tup2vec

from game.map_manager import MapManager, SKY, GRD
from game.visual_effects import Blast
from entities import Debrie
from weapons.artifacts.deployable_artifact import DeployableArtifact, ArtifactType


class PickAxeArtifact(DeployableArtifact):

	def set_surf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "pick axe")
	
	def comment_creation(self):
		GameVariables().commentator.comment([{'text': 'a game changer'}])

	def comment_pick(self):
		return ("its mining time for ", "")
		
	
	def step(self):
		super().step()
		self.angle -= self.vel.x*4


def mine(**kwargs):
	worm = GameVariables().player
	position = worm.pos + worm.get_shooting_direction().normalize() * 20
	position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

	colors = []
	for _ in range(10):
		sample = (position + Vector(8,8) + vectorUnitRandom() * uniform(0,8)).vec2tupint()
		if MapManager().is_on_map(sample):
			color = MapManager().ground_map.get_at(sample)
			if not color == SKY:
				colors.append(color)
	if len(colors) == 0:
		colors = Blast._color

	for _ in range(16):
		d = Debrie(position + Vector(8,8), 4, colors, 2, False)
		d.radius = choice([2,1])

	pygame.draw.rect(MapManager().game_map, SKY, (position, Vector(16,16)))
	pygame.draw.rect(MapManager().ground_map, SKY, (position, Vector(16,16)))


def build(**kwargs) -> Vector:
	if kwargs.get('stamp', False) == True:
		position = kwargs.get('position')
		blit_weapon_sprite(MapManager().ground_map, position, "build")
		MapManager().ground_map.blit(sprites.sprite_atlas, position, (80, 112, 16, 16))
		return None
	
	worm = GameVariables().player
	position = worm.pos + worm.get_shooting_direction().normalize() * 20
	position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

	pygame.draw.rect(MapManager().game_map, GRD, (position, Vector(16,16)))
	blit_weapon_sprite(MapManager().ground_map, position, "build")
	return position
