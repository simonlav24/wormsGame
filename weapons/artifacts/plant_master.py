from math import degrees
from random import uniform

import pygame

from common import GameVariables, sprites, point2world
from common.vector import vectorUnitRandom, normalize

from weapons.artifacts.deployable_artifact import DeployableArtifact, ArtifactType


class PlantMasterLeaf(DeployableArtifact):
	
	def set_surf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (48, 64, 16,16))

		self.is_wind_affected = True
		self.turbulance = vectorUnitRandom()
	
	def comment_creation(self):
		GameVariables().commentator.comment([{'text': "a leaf of heavens tree"}])
	
	def comment_pick(self):
		return ("", "  became master of plants")
	
	def step(self):
		super().step()
		self.angle += self.vel.x * 4

		# aerodynamic drag
		self.turbulance.rotate(uniform(-1, 1))
		velocity = self.vel.getMag()
		force =  - 0.15 * 0.5 * velocity * velocity * normalize(self.vel)
		force += self.turbulance * 0.1
		self.acc += force
	
	def on_collision(self, ppos):
		self.turbulance *= 0.9