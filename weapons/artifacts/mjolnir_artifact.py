
from math import degrees

import pygame

from common import GameVariables, sprites, point2world
from common.vector import tup2vec

from game.world_effects import boom
from weapons.artifacts.deployable_artifact import DeployableArtifact, ArtifactType


class MjolnirArtifact(DeployableArtifact):
	
	def set_surf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0,112,16,16))
	
	def comment_creation(self):
		GameVariables().commentator.comment([{'text': "a gift from the gods"}])
	
	def comment_pick(self):
		return ("", " is worthy to wield mjolnir!")
	
	def step(self):
		super().step()
		if self.vel.getMag() > 1:
			self.angle = -degrees(self.vel.getAngle()) - 90
	
	def on_collision(self, ppos):
		vel = self.vel.getMag()
		if vel > 4:
			boom(self.pos, max(20, 2 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(sprites.image_mjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size()) / 2))