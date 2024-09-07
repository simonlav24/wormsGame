
import pygame

from common import GameVariables, blit_weapon_sprite

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