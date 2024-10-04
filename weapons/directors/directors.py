
from typing import Type, Callable, Any, List
from enum import Enum

from common import GameVariables, EntityPhysical, Entity, mouse_pos_in_world, TeamData
from common.vector import Vector, vectorCopy

from game.team_manager import Team
from weapons.weapon import Weapon


class WeaponActor:
    def __init__(self, weapon: Weapon, team: Team, weapon_func: Callable[[], Any], *args, **kwargs):
        self.weapon = weapon
        self.team = team

        self.weapon_func = weapon_func
        self.shots = self.weapon.shots
        self.shooted_object: EntityPhysical | None = None

    def fire(self, energy: float):
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
    
    def is_done(self) -> bool:
        return self.shots == 0

class WeaponDirectorNew:
    def __init__(self):
        self.actors: List[WeaponActor] = []
        self.turn_ending = False

    def on_turn_end(self) -> None:
        for actor in self.actors:
            if actor.weapon.decrease_on_turn_end:
                self.decrease(actor)
        self.actors.clear()
    
    def handle_pygame_event(self, event) -> None:
        pass

    def step(self):
        pass

    def decrease(self, actor: WeaponActor) -> None:
        if actor.team.ammo(self.actor.weapon.index) != -1:
            actor.team.ammo(self.actor.weapon.index, -1)

    def fire(self):
        actor = self.actors[-1]

        actor.fire()
        if actor.is_done():
            if actor.weapon.decrease:
                self.decrease(actor)
            
            self.turn_ending = actor.weapon.turn_ending

    def get_object(self) -> EntityPhysical:
        ...

    



    





class WeaponDirector(Entity):
    def __init__(self, weapon: Weapon, weapon_func: Callable[[], Any], team_data: TeamData, *args, **kwargs) -> None:
        self.weapon = weapon
        self.weapon_func = weapon_func
        self.shooted_object: EntityPhysical | None = None
        self.shots = self.weapon.shots
        self.team_data = team_data
    
    def is_decrease(self) -> bool:
        return self.weapon.decrease

    def step(self) -> None:
        if self.weapon.burst:
            GameVariables().continuous_fire = True

    def draw(self, win) -> None:
        ...
    
    def shoot(self, energy: float) -> None:
        ...
    
    def get_object(self) -> EntityPhysical:
        return self.shooted_object
    
    def is_end_turn_on_done(self) -> bool:
        return self.weapon.turn_ending
    
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


class ClickableDirector(WeaponDirector):
    def shoot(self, energy: float) -> None:
        if self.shots == 0:
            return
        kwargs = {
			'pos': mouse_pos_in_world(),
			'shooter': GameVariables().player,
		}
        self.shooted_object = self.weapon_func(**kwargs)
        self.shots -= 1


class WormToolDirector(ChargeableDirector):
    def __init__(self, weapon: Weapon, weapon_func: Callable[[], Any], team_data: TeamData, *args, **kwargs) -> None:
        super().__init__(weapon, weapon_func, team_data, *args, **kwargs)
        self.decrease = True

    def shoot(self, energy: float) -> None:
        if self.shots == 0:
            return
        kwargs = {
			'pos': vectorCopy(GameVariables().player.pos),
			'direction': GameVariables().player.get_shooting_direction(),
			'shooter': GameVariables().player,
			'energy': energy,
		}
        activated = self.weapon_func(**kwargs)
        self.decrease = activated

        self.shots -= 1
    
    def is_decrease(self) -> bool:
        return self.decrease


class PortalDirector(ChargeableDirector):
    def shoot(self, energy: float) -> None:
        if self.shots == 0:
            return
        kwargs = {
			'pos': vectorCopy(GameVariables().player.pos),
			'direction': GameVariables().player.get_shooting_direction(),
			'shooter': GameVariables().player,
			'energy': energy,
            'portal': self.shooted_object
		}
        self.shooted_object = self.weapon_func(**kwargs)
        self.shots -= 1