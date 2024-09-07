
from random import randint

import pygame

from common.vector import Vector, dist, tup2vec
from common import GameVariables, ArtifactType, EntityWorm, point2world


from entities import PhysObj



class DeployableArtifact(PhysObj):
	def __init__(self, pos, artifact_type: ArtifactType):
		super().__init__(pos)
		self.pos = pos
		self.vel = Vector(randint(-2,2), 0)
		self.radius = 3
		self.damp = 0.2
		self.angle = 0
		GameVariables().cam_track = self
		self.artifact_type = artifact_type
		self.set_surf()
		self.is_gone = False
		
	def set_surf(self):
		pass
	
	def comment_creation(self):
		pass
	
	def comment_pick(self):
		pass
	
	def step(self):
		super().step()
	
	def remove_from_game(self):
		super().remove_from_game()
		self.is_gone = True
		
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))