
import json
from typing import List, Dict, Tuple, Callable, Any
from random import randint, choice

import pygame

import common
from common import GREY, sprites, fonts, blit_weapon_sprite, GameVariables, GameState, draw_target, draw_girder_hint, RIGHT, point2world, SingletonMeta, mouse_pos_in_world, ArtifactType, GameGlobals
from common.vector import *
import common.drawing_utilities

from weapons.weapon import Weapon, WeaponCategory, WeaponStyle
from weapons.weapon_funcs import weapon_funcs
from weapons.directors.directors import WeaponDirector
from game.team_manager import TeamManager
from game.time_manager import TimeManager
from weapons.earth_spike import calc_earth_spike_pos
from weapons.tools import draw_trampoline_hint


class WeaponManager(metaclass=SingletonMeta):
    ''' weapons manager '''
    def __init__(self) -> None:
        
        GameVariables().register_cycle_observer(self)

        self.cool_down_list: List[Weapon] = [] # weapon cool down list
        self.cool_down_list_surfaces: List[pygame.Surface] = [] # weapon cool down surfaces

        # load weapons
        with open('weapons.json', 'r') as file:
            data = json.load(file)
        
        self.weapons: List[Weapon] = [Weapon.model_validate(weapon) for weapon in data]
        
        # initialize dicts
        mapped = map(lambda x: x.name, self.weapons)
        self.weapon_dict: Dict[str, Weapon] = {key: value for key, value in zip(list(mapped), self.weapons)}
        common.drawing_utilities.weapon_name_to_index = {key: value.index for key, value in self.weapon_dict.items()}

        # basic set for teams 
        self.basic_set: List[int] = [weapon.initial_amount if weapon.artifact == ArtifactType.NONE else 0 for weapon in self.weapons]
        
        for team in TeamManager().teams:
            team.weapon_set = self.basic_set.copy()

        self.current_weapon: Weapon = self.weapons[0]
        # self.surf = fonts.pixel5.render(self.current_weapon.name, False, GameVariables().initial_variables.hud_color)
        self.multipleFires = ["flame thrower", "minigun", "laser gun", "bubble gun", "razor leaf"]
        
        self.weapon_director: WeaponDirector = WeaponDirector(weapon_funcs)

        # read weapon set if exits and adjust basic set
        # if game_manager.game_config.weapon_set is not None:
        #     # zero out basic set
        #     self.basic_set = [0 for i in self.basic_set]

        #     weaponSet = ET.parse('./assets/weaponsSets/' + game_manager.game_config.weapon_set + '.xml').getroot()
        #     for weapon in weaponSet:
        #         name = weapon.attrib["name"]
        #         amount = int(weapon.attrib["amount"])
        #         self.basic_set[self.weaponDict[name]] = amount

    def __getitem__(self, item: str) -> int:
        ''' return index of weapon by string '''
        return self.weapon_dict[item].index
    
    def can_switch_weapon(self) -> bool:
        return self.weapon_director.can_switch_weapon()

    def add_to_cool_down(self, weapon: Weapon) -> None:
        ''' add weapon to list of cool downs '''
        if weapon.style in [WeaponStyle.SPECIAL, WeaponStyle.UTILITY, WeaponStyle.WORM_TOOL]:
            return
        self.cool_down_list_surfaces.append(fonts.pixel5_halo.render(weapon.name, False, GameVariables().initial_variables.hud_color))
        self.cool_down_list.append(weapon)

        if len(self.cool_down_list) > 4:
            self.cool_down_list_surfaces.pop(0)
            self.cool_down_list.pop(0)

    def get_weapons_list_of_category(self, category: WeaponCategory) -> List[Weapon]:
        ''' return a list of all weapons of category '''
        return [weapon for weapon in self.weapons if weapon.category == category]

    def get_surface_portion(self, weapon: Weapon) -> Tuple[pygame.Surface, Tuple[int, int, int, int]] | None:
        index = weapon.index
        x = index % 8
        y = 9 + index // 8
        rect = (x * 16, y * 16, 16, 16)
        return (sprites.sprite_atlas, rect)

    def is_weapon_enabled(self, weapon: Weapon) -> bool:
        if GameVariables().game_round_count >= weapon.round_delay:
            return True
        return False

    def get_weapon(self, name: str) -> Weapon:
        ''' get weapon by name '''
        return self.weapon_dict[name]

    def can_shoot(self, check_ammo: bool=True, check_cool_down: bool=True, check_state: bool=True, check_delay: bool=True) -> bool:
        ''' check if can shoot current weapon '''
        # check delay
        if check_delay:
            if self.current_weapon.round_delay > GameVariables().game_round_count:
                return False

        # if no ammo
        if check_ammo:
            if TeamManager().current_team.ammo(self.current_weapon.index) == 0:
                return False
        
        # if in cool down
        if check_cool_down:
            if self.current_weapon in self.cool_down_list:
                return False
        
        if check_state:
            if (not GameVariables().is_player_in_control()) or (not GameVariables().can_player_shoot()):
                return False
        
        return True

    def on_turn_end(self) -> None:
        self.weapon_director.on_turn_end()
    
    def on_turn_begin(self) -> None:
        pass

    def switch_weapon(self, weapon: Weapon):
        """ switch weapon and draw weapon sprite """

        if not self.can_switch_weapon():
            return
        self.current_weapon = weapon
        self.render_weapon_count()

        GameVariables().weapon_hold.fill((0,0,0,0))
        if self.can_shoot(check_state=False):
            if weapon.category in [WeaponCategory.GRENADES, WeaponCategory.GUNS, WeaponCategory.TOOLS, WeaponCategory.LEGENDARY, WeaponCategory.FIREY, WeaponCategory.BOMBS]:
                if weapon.name in ["covid 19", "parachute", "earthquake"]:
                    return
                if weapon.name == "gemino mine":
                    blit_weapon_sprite(GameVariables().weapon_hold, (0,0), "mine")
                    return
                blit_weapon_sprite(GameVariables().weapon_hold, (0,0), weapon.name)
                return
            
            if weapon.name in ["flare", "artillery assist"]:
                blit_weapon_sprite(GameVariables().weapon_hold, (0,0), "flare")
                return
            
            if weapon.category in [WeaponCategory.MISSILES]:
                GameVariables().weapon_hold.blit(sprites.sprite_atlas, (0,0), (64,112,16,16))
            
            if weapon.category in [WeaponCategory.AIRSTRIKE]:
                if weapon.name == "chum bucket":
                    GameVariables().weapon_hold.blit(sprites.sprite_atlas, (0,0), (16,96,16,16))
                    return
                GameVariables().weapon_hold.blit(sprites.sprite_atlas, (0,0), (64,64,16,16))

    def render_weapon_count(self):
        ''' changes surf to fit current weapon '''

        amount = TeamManager().current_team.ammo(self.current_weapon.index)
        enabled = True
        if not self.can_shoot(check_state=False):
            enabled = False
        GameVariables().hud.render_weapon_count(self.current_weapon, amount, enabled=enabled)


    def handle_event(self, event) -> bool:
        handled = False
        self.hot_keys_switch(event)
        
        self.weapon_director.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            handled |= self.fire()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.current_weapon.style == WeaponStyle.CLICKABLE:
                handled |= self.fire()
            if (
                self.can_shoot(check_ammo=False, check_cool_down=False, check_delay=False, check_state=True) and 
                WeaponManager().current_weapon.name in ["homing missile", "seeker"]
            ):
                mouse_pos = mouse_pos_in_world()
                GameVariables().point_target = vectorCopy(mouse_pos)

        return handled



    def hot_keys_switch(self, event) -> bool:
        ''' handle pygame events, return true if event handled '''
        # weapon change by keyboard
        if GameVariables().game_state == GameState.PLAYER_PLAY:
            if not event.type == pygame.KEYDOWN:
                return False
            is_weapon_switched = False
            if event.key == pygame.K_1:
                key_weapons = [self.weapon_dict[w] for w in ["missile", "gravity missile", "homing missile"]]
                is_weapon_switched = True
            elif event.key == pygame.K_2:
                key_weapons = [self.weapon_dict[w] for w in ["grenade", "sticky bomb", "electric grenade"]]
                is_weapon_switched = True
            elif event.key == pygame.K_3:
                key_weapons = [self.weapon_dict[w] for w in ["cluster grenade", "raon launcher"]]
                is_weapon_switched = True
            elif event.key == pygame.K_4:
                key_weapons = [self.weapon_dict[w] for w in ["petrol bomb", "flame thrower"]]
                is_weapon_switched = True
            elif event.key == pygame.K_5:
                key_weapons = [self.weapon_dict[w] for w in ["TNT", "mine", "sheep"]]
                is_weapon_switched = True
            elif event.key == pygame.K_6:
                key_weapons = [self.weapon_dict[w] for w in ["shotgun", "long bow", "gamma gun", "laser gun"]]
                is_weapon_switched = True
            elif event.key == pygame.K_7:
                key_weapons = [self.weapon_dict[w] for w in ["girder", "baseball"]]
                is_weapon_switched = True
            elif event.key == pygame.K_8:
                key_weapons = [self.weapon_dict[w] for w in ["drill missile", "laser gun", "minigun"]]
                is_weapon_switched = True
            elif event.key == pygame.K_9:
                key_weapons = [self.weapon_dict[w] for w in ["minigun"]]
                is_weapon_switched = True
            elif event.key == pygame.K_0:
                pass
            elif event.key == pygame.K_MINUS:
                key_weapons = [self.weapon_dict[w] for w in ["rope"]]
                is_weapon_switched = True
            elif event.key == pygame.K_EQUALS:
                key_weapons = [self.weapon_dict[w] for w in ["parachute"]]
                is_weapon_switched = True            

            if is_weapon_switched:
                if len(key_weapons) > 0:
                    if self.current_weapon in key_weapons:
                        index = key_weapons.index(self.current_weapon)
                        index = (index + 1) % len(key_weapons)
                        weaponSwitch = key_weapons[index]
                    else:
                        weaponSwitch = key_weapons[0]
                self.switch_weapon(weaponSwitch)
                self.render_weapon_count()
                return True
        return False

    def step(self):
        # Fire
        self.weapon_director.step()
    
    def draw(self, win: pygame.Surface) -> None:
        # draw use list
        self.weapon_director.draw(win)
        space = 0
        for i, surf in enumerate(self.cool_down_list_surfaces):
            if i == 0:
                win.blit(surf, (30 + 80 * i, GameGlobals().win_height - 5 - surf.get_height()))
            else:
                space += self.cool_down_list_surfaces[i - 1].get_width() + 10
                win.blit(surf, (30 + space, GameGlobals().win_height - 5 - surf.get_height()))

    def draw_weapon_hint(self, win: pygame.Surface) -> None:
        ''' draw specific weapon indicator '''
        
        if not self.current_weapon.draw_hint:
            return

        if self.current_weapon.name in ["homing missile", "seeker"]:
            draw_target(win, GameVariables().point_target)
        
        if not GameVariables().game_state == GameState.PLAYER_PLAY:
            return

        if self.current_weapon.name == "girder":
            draw_girder_hint(win)
    
        if self.current_weapon.name == "trampoline":
            draw_trampoline_hint(win)
        
        if self.current_weapon.category == WeaponCategory.AIRSTRIKE:
            mouse = mouse_pos_in_world()
            flip = False if GameVariables().airstrike_direction == RIGHT else True
            win.blit(pygame.transform.flip(sprites.air_strike_indicator, flip, False), point2world(mouse - tup2vec(sprites.air_strike_indicator.get_size())/2))
        
        if self.current_weapon.name == "earth spike" and GameVariables().game_state in [GameState.PLAYER_PLAY] and TeamManager().current_team.ammo(self["earth spike"]) != 0:
            spikeTarget = calc_earth_spike_pos()
            if spikeTarget:
                draw_target(win, spikeTarget)

    def give_extra_starting_weapons(self) -> None:
        ''' give teams starting legendary weapons, utilities and tools '''
        legendary = ["holy grenade", "gemino mine", "bee hive", "electro boom", "pokeball", "green shell", "guided missile", "fireworks"]
        if GameVariables().initial_variables.allow_air_strikes:
            legendary.append("mine strike")

        for team in TeamManager().teams:
            chosen_weapon = WeaponManager().get_weapon(choice(legendary)).index
            team.ammo(chosen_weapon, 1)
            if randint(0,2) >= 1:
                chosen_weapon = WeaponManager().get_weapon(choice(["moon gravity", "teleport", "jet pack", "aim aid", "switch worms"])).index
                team.ammo(chosen_weapon, 1)
            if randint(0,6) == 1:
                chosen_weapon = WeaponManager().get_weapon(choice(["portal gun", "trampoline", "ender pearl"])).index
                team.ammo(chosen_weapon, 3)

    def fire(self, weapon: Weapon=None) -> bool:
        ''' fire weapon, return True if fired '''
        if not self.can_shoot(check_state=True, check_ammo=False, check_cool_down=True, check_delay=True):
            return False

        if not weapon:
            weapon = self.current_weapon
        
        self.weapon_director.add_actor(weapon, TeamManager().current_team)
        if GameVariables().config.option_cool_down:
            self.add_to_cool_down(weapon)
        return True