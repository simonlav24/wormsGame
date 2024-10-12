''' weapon directors and actors. handle weapon shooting and events handling '''

from typing import List

import pygame

from common import GameVariables, EntityPhysical, mouse_pos_in_world, GameState, point2world, blit_weapon_sprite, LEFT
from common.vector import vectorCopy, Vector, tup2vec

from game.team_manager import Team
from game.time_manager import TimeManager
from weapons.weapon import Weapon, WeaponStyle

def end_turn():
    ''' switch to player_retreat state and set remaining time '''
    GameVariables().game_state = GameVariables().game_next_state
    if GameVariables().game_state == GameState.PLAYER_RETREAT:
        TimeManager().time_remaining_etreat()

def decrease(weapon: Weapon, team: Team):
    ''' decrease the weapon count of the team by -1 '''
    if team.ammo(weapon.index) != 0:
        team.ammo(weapon.index, -1)
    GameVariables().hud.render_weapon_count(weapon, team.ammo(weapon.index))

class WeaponDirector:
    ''' creating and handling weapon actors '''
    def __init__(self, weapon_funcs):
        self.actors: List[WeaponActorBase] = []
        self.weapon_funcs = weapon_funcs

    def add_actor(self, weapon: Weapon, team: Team):
        actor = None
        weapon_func = self.weapon_funcs[weapon.name]

        args = (weapon, weapon_func, team)
        if weapon.style == WeaponStyle.CHARGABLE:
            actor = ActorChargeable(*args)

        elif weapon.style == WeaponStyle.GUN:
            actor = ActorGun(*args)

        elif weapon.style == WeaponStyle.PUTABLE:
            actor = ActorPutable(*args)
        
        elif weapon.style == WeaponStyle.CLICKABLE:
            actor = ActorClickable(*args)
        
        elif weapon.style == WeaponStyle.UTILITY:
            actor = ActorPutable(*args)
        
        elif weapon.style == WeaponStyle.WORM_TOOL:
            actor = ActorWormTool(*args)

        elif weapon.style == WeaponStyle.SPECIAL:
            if weapon.name in ['build', 'pick axe']:
                actor = ActorMineBuild(*args)



        if actor is not None and actor.weapon in [actor.weapon for actor in self.actors]:
            actor = None
        if actor is not None and not actor.is_done:
            if len(self.actors) > 0:
                self.actors[0].secondary = True
            self.actors.append(actor)

    def step(self) -> None:
        for actor in self.actors:
            actor.step()
        if not GameVariables().player.alive:
            for actor in self.actors:
                actor.on_worm_death()
        self.actors = [actor for actor in self.actors if not actor.is_done]
        if len(self.actors) == 1:
            self.actors[0].secondary = False
    
    def draw(self, win: pygame.Surface) -> None:
        for actor in self.actors:
            actor.draw(win)

    def handle_event(self, event) -> None:
        for actor in self.actors:
            actor.handle_event(event)
    
    def on_turn_end(self):
        for actor in self.actors:
            actor.on_turn_end()
        self.actors.clear()
    
    def can_switch_weapon(self):
        result = True
        for actor in self.actors:
            result &= actor.can_switch_weapon()
        return result


class WeaponActorBase:
    def __init__(self, weapon: Weapon, weapon_func, team: Team):
        self.weapon = weapon
        self.shots: int = weapon.shots
        self.is_done: bool = False
        self.weapon_func = weapon_func
        self.team = team

        self.shooted_object: EntityPhysical = None
        self.secondary: bool = False
        if not self.can_shoot():
            self.is_done = True

    def step(self) -> None:
        ...

    def draw(self, win: pygame.Surface) -> None:
        ...

    def handle_event(self, event) -> None:
        ...
    
    def abort(self) -> None:
        self.is_done = True

    def can_shoot(self) -> bool:
        return not self.team.ammo(self.weapon.index) == 0

    def on_worm_death(self) -> None:
        self.is_done = True

    def fire(self, **kwargs) -> EntityPhysical:
        if self.shots == 0:
            return
        args_dict = {
			'pos': kwargs.get('pos', vectorCopy(GameVariables().player.pos)),
			'direction': GameVariables().player.get_shooting_direction(),
			'shooter': GameVariables().player,
			'energy': kwargs.get('energy', 0.0),
            'shooted_object': self.shooted_object
		}
        is_abort = GameVariables().on_fire(**(args_dict | {'weapon_func': self.weapon_func}))
        if is_abort:
            self.abort()
            return None
        self.shooted_object = self.weapon_func(**args_dict)
        if self.weapon.can_fail:
            if not self.shooted_object:
                # failed shot
                self.abort()
                return None
            else:
                self.shooted_object = None
        

        self.shots -= 1
        self.finalize()
        return self.shooted_object

    def on_turn_end(self):
        if self.weapon.decrease_on_turn_end:
            decrease(self.weapon, self.team)
    
    def finalize(self):
        if self.shooted_object is not None:
            GameVariables().cam_track = self.shooted_object

        if self.shots == 0:
            if self.weapon.decrease:
                decrease(self.weapon, self.team)
                
            if self.weapon.turn_ending:
                end_turn()
            self.is_done = True
    
    def can_switch_weapon(self) -> bool:
        return False


class ActorChargeable(WeaponActorBase):
    def __init__(self, weapon: Weapon, weapon_func, team: Team):
        super().__init__(weapon, weapon_func, team)
        self.energy = 0.0
        self.energizing = True

    def handle_event(self, event) -> None:
        super().handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.energizing = True
            self.energy = 0.0

        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            if self.energizing:
                self.energizing = False
                self.fire(energy=self.energy)

    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        if self.energizing:
            i = 0
            while i < 20 * self.energy:
                pos = vectorCopy(GameVariables().player.pos)
                pygame.draw.line(win, (0,0,0), point2world(pos), point2world(pos + GameVariables().player.get_shooting_direction() * i))
                i += 1

    def step(self) -> None:
        super().step()
        if self.energizing:
            self.energy += 0.05
            if self.energy >= 1.0:
                self.energizing = False
                self.fire(energy=self.energy)


class ActorGun(WeaponActorBase):
    def handle_event(self, event) -> None:
        super().handle_event(event)
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            self.fire()
    
    def step(self) -> None:
        super().step()
        if self.weapon.burst:
            self.fire()
    
    def can_switch_weapon(self) -> bool:
        return False
    
    def on_worm_death(self) -> None:
        super().on_worm_death()
        decrease(self.weapon, self.team)


class ActorPutable(WeaponActorBase):
    def handle_event(self, event) -> None:
        super().handle_event(event)
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            self.fire()


class ActorClickable(WeaponActorBase):
    def handle_event(self, event) -> None:
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.fire(pos=mouse_pos_in_world())


class ActorWormTool(WeaponActorBase):
    def __init__(self, weapon, weapon_func, team):
        super().__init__(weapon, weapon_func, team)
        self.is_done = False

    def handle_event(self, event) -> None:
        super().handle_event(event)

        if not self.secondary and GameVariables().game_state == GameState.PLAYER_PLAY:
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                tool = GameVariables().player.get_tool()
                if tool is not None:
                    tool.release()
                elif self.can_shoot():
                    self.fire()
    
    def can_switch_weapon(self) -> bool:
        return True
    
    def on_turn_end(self):
        super().on_turn_end()
        tool = GameVariables().player.get_tool()
        if tool is not None:
            tool.release()

    def abort(self) -> None:
        pass

    def finalize(self):
        super().finalize()
        GameVariables().cam_track = GameVariables().player
        if (GameVariables().game_state != GameState.PLAYER_PLAY and
            not self.weapon.decrease_on_turn_end):
            self.is_done = True


class ActorMineBuild(WeaponActorBase):
    def __init__(self, weapon, weapon_func, team):
        super().__init__(weapon, weapon_func, team)
        self.used_locations: List[Vector] = []
        self.initial_shooted = False
        self.animation_offset = 0

        self.surf = None
        if weapon.name == 'pick axe':
            self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
            blit_weapon_sprite(self.surf, (0,0), "pick axe")

    def finalize(self):
        if self.shooted_object is not None:
            if self.shooted_object + Vector(0, 16) in self.used_locations:
                args_dict = {
                    'stamp': True,
                    'position': self.shooted_object + Vector(0, 16)
                }
                self.weapon_func(**args_dict)
            if self.shooted_object + Vector(0, -16) in self.used_locations:
                args_dict = {
                    'stamp': True,
                    'position': self.shooted_object
                }
                self.weapon_func(**args_dict)
        
        self.animation_offset = 90
        self.used_locations.append(self.shooted_object)
        self.shooted_object = None
        super().finalize()

    def handle_event(self, event) -> None:
        super().handle_event(event)
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            if self.initial_shooted:
                self.fire()
            self.initial_shooted = True

    def step(self):
        super().step()
        if self.animation_offset > 0:
            self.animation_offset -= 5
            self.animation_offset = max(self.animation_offset, 0)

    def draw(self, win):
        super().draw(win)
        worm = GameVariables().player
        position = worm.pos + worm.get_shooting_direction().normalize() * 20
        # closest grid of 16
        position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)
        pygame.draw.rect(win, (255,255,255), (point2world(position), Vector(16,16)), 1)

        if self.surf is not None:
            angle = - self.animation_offset * worm.facing
            weapon_surf = pygame.transform.rotate(pygame.transform.flip(self.surf, worm.facing == LEFT, False), angle)
            win.blit(weapon_surf, point2world(worm.pos - tup2vec(weapon_surf.get_size()) / 2 + Vector(worm.facing * 9, - 4 + self.animation_offset * 0.1)))
