
import json
from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Tuple

import pygame

import common
from common import GREY, sprites, fonts, ColorType, blit_weapon_sprite, GameVariables, GameState, draw_target, draw_girder_hint, RIGHT, point2world, SingletonMeta, mouse_pos_in_world, ArtifactType
from common.vector import *
import common.drawing_utilities

from game.team_manager import TeamManager
from weapons.earth_spike import calc_earth_spike_pos

class WeaponStyle(Enum):
    CHARGABLE = 0
    GUN = 1
    PUTABLE = 2
    CLICKABLE = 3
    UTILITY = 4


class WeaponCategory(Enum):
    MISSILES = 0
    GRENADES = 1
    GUNS = 2
    FIREY = 3
    BOMBS = 4
    TOOLS = 5
    AIRSTRIKE = 6
    LEGENDARY = 7
    UTILITIES = 8
    ARTIFACTS = 9


weapon_bg_color = {
    WeaponCategory.MISSILES : (255, 255, 255),
    WeaponCategory.GRENADES : (204, 255, 204),
    WeaponCategory.GUNS : (255, 204, 153),
    WeaponCategory.FIREY : (255, 204, 204),
    WeaponCategory.BOMBS : (200, 255, 200),
    WeaponCategory.TOOLS : (224, 224, 235),
    WeaponCategory.AIRSTRIKE : (204, 255, 255),
    WeaponCategory.LEGENDARY : (255, 255, 102),
    WeaponCategory.UTILITIES : (254, 254, 254),
    WeaponCategory.ARTIFACTS : (255, 255, 101),
}

class Weapon(BaseModel):
    ''' weapon base model '''
    index: int
    name: str
    style: WeaponStyle
    category: WeaponCategory
    initial_amount: int
    is_fused: bool = False
    round_delay: int = 0
    artifact: ArtifactType = ArtifactType.NONE
    draw_hint: bool = False

    def get_bg_color(self) -> ColorType:
        ''' returns weapons background color '''
        return weapon_bg_color[self.category]

class WeaponManager(metaclass=SingletonMeta):
    ''' weapons manager '''
    def __init__(self) -> None:

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
        self.surf = fonts.pixel5.render(self.current_weapon.name, False, GameVariables().initial_variables.hud_color)
        self.multipleFires = ["flame thrower", "minigun", "laser gun", "bubble gun", "razor leaf"]
        
        self.current_gun = None

        # read weapon set if exits and adjust basic set
        # if globals.game_manager.game_config.weapon_set is not None:
        #     # zero out basic set
        #     self.basic_set = [0 for i in self.basic_set]

        #     weaponSet = ET.parse('./assets/weaponsSets/' + globals.game_manager.game_config.weapon_set + '.xml').getroot()
        #     for weapon in weaponSet:
        #         name = weapon.attrib["name"]
        #         amount = int(weapon.attrib["amount"])
        #         self.basic_set[self.weaponDict[name]] = amount

    def __getitem__(self, item: str) -> int:
        ''' return index of weapon by string '''
        return self.weapon_dict[item].index

    def can_open_menu(self) -> bool:
        return self.current_gun is None
    
    def can_switch_weapon(self) -> bool:
        return self.current_gun is None

    def add_to_cool_down(self, weapon: Weapon) -> None:
        ''' add weapon to list of cool downs '''
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

    def get_weapon(self, name: str) -> Weapon:
        ''' get weapon by name '''
        return self.weapon_dict[name]

    def can_shoot(self) -> bool:
        ''' check if can shoot current weapon '''
        # if no ammo
        if TeamManager().current_team.ammo(self.current_weapon.index) == 0:
            return False
        
        # if not active
        if not self.is_current_weapon_active():
            return False

        # if in use list
        if GameVariables().config.option_cool_down and self.current_weapon in self.cool_down_list:
            return False
        
        if (not GameVariables().player_in_control) or (not GameVariables().player_can_shoot):
            return False
        
        return True

    def switch_weapon(self, weapon: Weapon):
        """ switch weapon and draw weapon sprite """

        if not self.can_switch_weapon():
            return
        self.current_weapon = weapon
        self.render_weapon_count()

        GameVariables().weapon_hold.fill((0,0,0,0))
        if self.can_shoot():
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
    
    # def add_artifact_moves(self, artifact):
    #     # when team pick up artifact add them to weapon_set
    #     for w in self.weapons[self.weaponCount + self.utilityCount:]:
    #         if w[6] == artifact:
    #             if w[0] in ["magic bean", "pick axe", "build"]:
    #                 TeamManager().current_team.ammo(w[0], 1, True)
    #                 continue
    #             if w[0] == "fly":
    #                 TeamManager().current_team.ammo(w[0], 3, True)
    #                 continue
    #             TeamManager().current_team.ammo(w[0], -1, True)

    def currentArtifact(self):
        if self.current_weapon.category == WeaponCategory.ARTIFACTS:
            return self.weapons[self.currentIndex()][6]

    def currentIndex(self):
        return self.current_weapon.index
    
    def is_current_weapon_active(self) -> bool:
        ''' check if current weapon active in this round '''
        # check for round delay
        # if self.current_weapon.round_delay < GameVariables().game_turn_count:
        #     return False
        # todo this
        
        # check for cool down
        if GameVariables().config.option_cool_down and self.current_weapon in self.cool_down_list:
            return False
        
        return True

    def render_weapon_count(self):
        ''' changes surf to fit current weapon '''
        color = GameVariables().initial_variables.hud_color
        # if no ammo in current team
        ammo = TeamManager().current_team.ammo(self.current_weapon.index)
        if ammo == 0 or not self.is_current_weapon_active() or (GameVariables().config.option_cool_down and self.current_weapon in self.cool_down_list):
            color = GREY
        weaponStr = self.current_weapon.name

        # special addings
        # if self.current_weapon == "drill missile":
        #     weaponStr += " (drill)" if DrillMissile.mode else " (rocket)"
        
        # add quantity
        if ammo != -1:
            weaponStr += " " + str(ammo)
            
        # add fuse
        if self.current_weapon.is_fused:
            weaponStr += "  delay: " + str(GameVariables().fuse_time // GameVariables().fps)
            
        self.surf = fonts.pixel5_halo.render(weaponStr, False, color)

    def handle_event(self, event) -> bool:
        ''' handle pygame events '''
        # weapon change by keyboard
        if GameVariables().game_state == GameState.PLAYER_PLAY:
            if not event.type == pygame.KEYDOWN:
                return False
            weaponsSwitch = False
            if event.key == pygame.K_1:
                keyWeapons = [self.weapon_dict[w] for w in ["missile", "gravity missile", "homing missile"]]
                weaponsSwitch = True
            elif event.key == pygame.K_2:
                keyWeapons = [self.weapon_dict[w] for w in ["grenade", "sticky bomb", "electric grenade"]]
                weaponsSwitch = True
            elif event.key == pygame.K_3:
                keyWeapons = [self.weapon_dict[w] for w in ["cluster grenade", "raon launcher"]]
                weaponsSwitch = True
            elif event.key == pygame.K_4:
                keyWeapons = [self.weapon_dict[w] for w in ["petrol bomb", "flame thrower"]]
                weaponsSwitch = True
            elif event.key == pygame.K_5:
                keyWeapons = [self.weapon_dict[w] for w in ["TNT", "mine", "sheep"]]
                weaponsSwitch = True
            elif event.key == pygame.K_6:
                keyWeapons = [self.weapon_dict[w] for w in ["shotgun", "long bow", "gamma gun", "laser gun"]]
                weaponsSwitch = True
            elif event.key == pygame.K_7:
                keyWeapons = [self.weapon_dict[w] for w in ["girder", "baseball"]]
                weaponsSwitch = True
            elif event.key == pygame.K_8:
                keyWeapons = [self.weapon_dict[w] for w in ["drill missile", "laser gun", "minigun"]]
                weaponsSwitch = True
            elif event.key == pygame.K_9:
                keyWeapons = [self.weapon_dict[w] for w in ["minigun"]]
                weaponsSwitch = True
            elif event.key == pygame.K_0:
                pass
            elif event.key == pygame.K_MINUS:
                keyWeapons = [self.weapon_dict[w] for w in ["rope"]]
                weaponsSwitch = True
            elif event.key == pygame.K_EQUALS:
                keyWeapons = [self.weapon_dict[w] for w in ["parachute"]]
                weaponsSwitch = True
            
            elif event.key == pygame.K_KP1:
                keyWeapons = [self.weapon_dict[w] for w in ["fireworks", "fire ball", "earth spike"]]
                weaponsSwitch = True
            

            if weaponsSwitch:
                if len(keyWeapons) > 0:
                    if self.current_weapon in keyWeapons:
                        index = keyWeapons.index(self.current_weapon)
                        index = (index + 1) % len(keyWeapons)
                        weaponSwitch = keyWeapons[index]
                    else:
                        weaponSwitch = keyWeapons[0]
                self.switch_weapon(weaponSwitch)
                self.render_weapon_count()
        return False

    def draw(self, win: pygame.Surface) -> None:
        # draw use list
        space = 0
        for i, surf in enumerate(self.cool_down_list_surfaces):
            if i == 0:
                win.blit(surf, (30 + 80 * i, GameVariables().win_height - 5 - surf.get_height()))
            else:
                space += self.cool_down_list_surfaces[i-1].get_width() + 10
                win.blit(surf, (30 + space, GameVariables().win_height - 5 - surf.get_height()))

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
    
        if self.current_weapon == "trampoline":
            # todo: draw trampoline hint
            pass
        
        if self.current_weapon.category == WeaponCategory.AIRSTRIKE:
            mouse = mouse_pos_in_world()
            flip = False if GameVariables().airstrike_direction == RIGHT else True
            win.blit(pygame.transform.flip(sprites.air_strike_indicator, flip, False), point2world(mouse - tup2vec(sprites.air_strike_indicator.get_size())/2))
        
        # todo: draw earth spike hitn
        if self.current_weapon.name == "earth spike" and GameVariables().game_state in [GameState.PLAYER_PLAY] and TeamManager().current_team.ammo(self["earth spike"]) != 0:
            spikeTarget = calc_earth_spike_pos()
            if spikeTarget:
                draw_target(win, spikeTarget)
