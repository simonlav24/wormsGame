
import pygame

from common import GameVariables, EntityPhysical
from common.vector import vectorCopy

from entities import Worm

class ShootGun:
	def __init__(self, **kwargs) -> None:
		GameVariables().register_non_physical(self)
		self.ammo = kwargs.get('count')
		self.shoot_action = kwargs.get('func')
		self.end_turn = kwargs.get('end_turn', True)
		self.burst = kwargs.get('burst', False)

		self.shooted_object: EntityPhysical | None = None

	def step(self) -> None:
		if self.burst:
			GameVariables().continuous_fire = True

	def draw(self, win: pygame.Surface) -> None:
		pass

	def shoot(self, energy: float) -> None:
		if self.ammo == 0:
			return
		
		kwargs = {
			'pos': vectorCopy(Worm.player.pos),
			'direction': Worm.player.get_shooting_direction(),
			'shooter': Worm.player,
			'energy': energy,
		}
		self.shooted_object = self.shoot_action(**kwargs)
		self.ammo -= 1
	
	def get_object(self) -> EntityPhysical:
		result = self.shooted_object
		self.shooted_object = None
		return result

	def is_done(self) -> bool:
		return self.ammo == 0
	
	def is_end_turn(self) -> bool:
		return self.end_turn
	
	def remove(self) -> None:
		GameVariables().unregister_non_physical(self)