
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


class PickAxe():
	''' non-physical.
		pickaxe logic and graphics  '''
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "pick axe")
		self.animating = 0
		self.shoot_action = self.mine
		self.initial_shoot = False
	
	def mine(self, **kwargs):
		if not self.initial_shoot:
			self.initial_shoot = True
			self.ammo += 1
			return

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
			d = Debrie(position + Vector(8,8), 8, colors, 2, False)
			d.radius = choice([2,1])

		pygame.draw.rect(MapManager().game_map, SKY, (position, Vector(16,16)))
		pygame.draw.rect(MapManager().ground_map, SKY, (position, Vector(16,16)))

		self.animating = 90

	def step(self):
		super().step()
		if self.animating > 0:
			self.animating -= 5
			self.animating = max(self.animating, 0)
	
	def draw(self, win: pygame.Surface):
		super().draw(win)
		worm = GameVariables().player
		position = worm.pos + worm.get_shooting_direction().normalize() * 20
		# closest grid of 16
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)
		pygame.draw.rect(win, (255,255,255), (point2world(position), Vector(16,16)), 1)

		angle = - self.animating * worm.facing

		weaponSurf = pygame.transform.rotate(pygame.transform.flip(self.surf, worm.facing == LEFT, False), angle)
		win.blit(weaponSurf, point2world(worm.pos - tup2vec(weaponSurf.get_size())/2 + Vector(worm.facing * 9, -4)))


class MineBuild():
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.used_locations: List[Vector] = []
		self.shoot_action = self.build
		self.initial_shoot = False

	def build(self, **kwargs):
		if not self.initial_shoot:
			self.initial_shoot = True
			self.ammo += 1
			return
		
		worm = GameVariables().player
		position = worm.pos + worm.get_shooting_direction().normalize() * 20
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

		pygame.draw.rect(MapManager().game_map, GRD, (position, Vector(16,16)))
		if position + Vector(0,16) in self.used_locations:
			blit_weapon_sprite(MapManager().ground_map, position, "build")
			MapManager().ground_map.blit(sprites.sprite_atlas, position + Vector(0,16), (80,112,16,16))
		elif position + Vector(0,-16) in self.used_locations:
			MapManager().ground_map.blit(sprites.sprite_atlas, position, (80,112,16,16))
		else:
			blit_weapon_sprite(MapManager().ground_map, position, "build")

		self.used_locations.append(position)

	def draw(self, win: pygame.Surface):
		super().draw(win)
		worm = GameVariables().player
		position = worm.pos + worm.get_shooting_direction().normalize() * 20
		# closest grid of 16
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)
		pygame.draw.rect(win, (255,255,255), (point2world(position), Vector(16,16)), 1)