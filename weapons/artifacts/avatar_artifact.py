
import pygame

from common import GameVariables, sprites

from weapons.artifacts.deployable_artifact import DeployableArtifact, ArtifactType




class AvatarArtifact(DeployableArtifact):
	
	def set_surf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0,112,16,16))
	
	def comment_creation(self):
		GameVariables().commentator.comment([{'text': "who is the next avatar?"}])
	
	def comment_pick(self):
		return ("everything changed when ", " attacked")
	
	def step(self):
		super().step()
		self.angle -= self.vel.x * 4