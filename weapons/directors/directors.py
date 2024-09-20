
from typing import Type, Callable, Any

from common import GameVariables, EntityPhysical, Entity
from common.vector import Vector, vectorCopy

from weapons.weapon import Weapon



class WeaponDirector(Entity):
    def __init__(self, weapon: Weapon, weapon_func: Callable[[], Any], *args, **kwargs) -> None:
        GameVariables().register_non_physical(self)
        self.weapon = weapon
        self.weapon_func = weapon_func
        self.shooted_object: EntityPhysical | None = None
        self.shots = self.weapon.shots
    
    def step(self) -> None:
        if self.weapon.burst:
            GameVariables().continuous_fire = True

    def draw(self, win) -> None:
        ...
    
    def shoot(self, energy: float) -> None:
        ...
    
    def get_object(self) -> EntityPhysical:
        return None
    
    def is_end_turn_on_done(self) -> bool:
        return self.weapon.turn_ending

    def remove_from_game(self) -> None:
        GameVariables().unregister_non_physical(self)
    
    def is_done(self) -> bool:
        return self.shots == 0


class ChargeableDirector(WeaponDirector):

    def shoot(self, energy: float) -> None:
        if self.shots == 0:
            return
        kwargs = {
			'pos': vectorCopy(GameVariables().player.pos),
			'direction': GameVariables().player.get_shooting_direction(),
			'shooter': GameVariables().player,
			'energy': energy,
		}
        self.shooted_object = self.weapon_func(**kwargs)
        self.shots -= 1
    
    def get_object(self) -> EntityPhysical:
        return self.shooted_object


class GunDirector(WeaponDirector):
    def shoot(self, energy: float) -> None:
        if self.shots == 0:
            return
        
        kwargs = {
            'pos': vectorCopy(GameVariables().player.pos),
            'direction': GameVariables().player.get_shooting_direction(),
            'shooter': GameVariables().player,
            'energy': energy,
        }
        self.weapon_func(**kwargs)
        self.shots -= 1