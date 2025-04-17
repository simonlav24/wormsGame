
from typing import List
from random import randint, uniform, choice

import pygame
import pygame.gfxdraw

from common import GameVariables, GameGlobals, GameConfig, feels, fonts, WHITE, BLACK, PlantMode, mouse_pos_in_world, ICreateGame
from common.vector import Vector, dist
from common.game_config import GameMode, RandomMode

from game.game_play_mode import (
    GamePlayCompound, 
    TerminatorGamePlay,
    PointsGamePlay,
    TargetsGamePlay,
    DVGGamePlay, 
    CTFGamePlay,
    ArenaGamePlay,
    ArtifactsGamePlay,
    DarknessGamePlay,
    StatsGamePlay,
    MissionsGamePlay
)

from game.state_machine import StateMachine, sudden_death
from game.time_manager import TimeManager
from game.map_manager import MapManager, SKY
from game.background import BackGround
from game.team_manager import TeamManager
from game.visual_effects import EffectManager
from game.world_effects import boom

from game.hud import Commentator, Hud
from gui.radial_menu import RadialMenu, RadialButton
from game.game_creator import GameCreator

from entities.props import PetrolCan
from entities.deployables import HealthPack, WeaponPack, UtilityPack
from entities.worm import Worm

from weapons.weapon_manager import WeaponManager
from weapons.weapon import weapon_bg_color, WeaponCategory
from weapons.plants import PlantSeed
from weapons.mine import Mine

from weapons.misc.springs import MasterOfPuppets
from weapons.misc.armageddon import Armageddon


class Game(ICreateGame):
    ''' game manager class.  '''
    def __init__(self, game_creator: GameCreator=None):
        self.reset()
        GameVariables().set_config(game_creator.game_config)
        GameVariables().commentator = Commentator()
        GameVariables().hud = Hud()
        GameVariables().state_machine = StateMachine(game_creator)

        self.evaluate_config(game_creator.game_config)
        
        WeaponManager()

        self.background = BackGround(feels[GameVariables().config.feel_index], GameVariables().config.option_darkness)
        self.background.set_closed(GameVariables().config.option_closed_map)

        self.cheat_code = "" # cheat code

        self.load_step_incremental = 0
        self.load_step_incremental_max = GameVariables().config.worms_per_team * 4

        self.radial_weapon_menu: RadialMenu = None
        GameVariables().state_machine.update()
    
    def reset(self):
        ''' reset all game singletons '''
        GameVariables.reset()
        MapManager.reset()
        TeamManager.reset()
        TimeManager.reset()
        EffectManager.reset()
        WeaponManager.reset()
    
    def evaluate_config(self, game_config: GameConfig):
        self.game_config: GameConfig = game_config

        if self.game_config.feel_index == -1:
            self.game_config.feel_index = randint(0, len(feels) - 1)

        GameVariables().game_mode = GamePlayCompound()
        GameVariables().stats = StatsGamePlay()
        GameVariables().game_mode.add_mode(GameVariables().stats)

        game_mode_map = {
            GameMode.TERMINATOR: TerminatorGamePlay(),
            GameMode.POINTS: PointsGamePlay(),
            GameMode.TARGETS: TargetsGamePlay(),
            GameMode.DAVID_AND_GOLIATH: DVGGamePlay(),
            GameMode.CAPTURE_THE_FLAG: CTFGamePlay(),
            GameMode.ARENA: ArenaGamePlay(),
            GameMode.MISSIONS: MissionsGamePlay(GameVariables().stats),
        }

        GameVariables().game_mode.add_mode(game_mode_map.get(self.game_config.game_mode))

        if self.game_config.option_artifacts:
            GameVariables().game_mode.add_mode(ArtifactsGamePlay())
        if self.game_config.option_darkness:
            GameVariables().game_mode.add_mode(DarknessGamePlay())

    def handle_event(self, event) -> bool:
        ''' handle pygame event, return true if event handled '''

        if self.radial_weapon_menu:
            self.radial_weapon_menu.handle_event(event)
            menu_event = self.radial_weapon_menu.get_event()
            if menu_event:
                WeaponManager().switch_weapon(menu_event)
                self.radial_weapon_menu = None
                return True
        
        is_handled = WeaponManager().handle_event(event)
        
        return is_handled

    def step(self):
        pass
    
    def __loading_step(self):
        self.load_step_incremental += 1
        loading_surf = fonts.pixel10_halo.render("Simon's Worms Loading", False, WHITE)
        pos = (GameGlobals().win_width / 2 - loading_surf.get_width() / 2, GameGlobals().win_height / 2 - loading_surf.get_height() / 2)
        width = loading_surf.get_width()
        height = loading_surf.get_height()
        
        win = GameGlobals().win
        # win.fill(BLACK)
        win.blit(loading_surf, pos)
        pygame.draw.rect(win, WHITE, ((pos[0], pos[1] + 20), ((self.load_step_incremental / self.load_step_incremental_max) * width, height)))
        pygame.draw.rect(win, BLACK, ((pos[0], pos[1] + 20), ((self.load_step_incremental / self.load_step_incremental_max) * width, height)), 1)

        GameGlobals().screen.blit(pygame.transform.scale(win, GameGlobals().screen.get_rect().size), (0, 0))
        pygame.display.update()

    def weapon_menu_init(self):
        current_team = TeamManager().current_team
        
        layout = []

        for category in reversed(list(WeaponCategory)):
            weapons_in_category = WeaponManager().get_weapons_list_of_category(category)
            weapons_in_category = [weapon for weapon in weapons_in_category if current_team.ammo(weapon.index) != 0]
            if len(weapons_in_category) == 0:
                continue
            get_amount = lambda x: str(current_team.ammo(x.index)) if current_team.ammo(x.index) > 0 else ''
            
            sub_layout: List[RadialButton] = []
            for weapon in reversed(weapons_in_category):
                surf_portion = WeaponManager().get_surface_portion(weapon)
                is_enabled = WeaponManager().is_weapon_enabled(weapon)
                button = RadialButton(weapon, weapon.name, get_amount(weapon), weapon_bg_color[category], surf_portion, is_enabled=is_enabled)
                sub_layout.append(button)

            is_enabled = not all(not button.is_enabled for button in sub_layout)
            main_button = RadialButton(weapons_in_category[0], '', '', weapon_bg_color[category], WeaponManager().get_surface_portion(weapons_in_category[0]), sub_layout, is_enabled=is_enabled)
            layout.append(main_button)

        self.radial_weapon_menu = RadialMenu(layout, Vector(GameGlobals().win_width // 2, GameGlobals().win_height // 2))

    def cheat_activate(self, code: str):
        code = code[:-1].lower()
        mouse_pos = mouse_pos_in_world()

        if code == "gibguns":
            for team in TeamManager().teams:
                for i, _ in enumerate(team.weapon_set):
                    team.weapon_set[i] = 100
            for weapon in WeaponManager().weapons:
                weapon.round_delay = 0
            GameVariables().config.option_cool_down = False
            WeaponManager().cool_down_list.clear()
            WeaponManager().cool_down_list_surfaces.clear()
        elif code == "gibguns1":
            for team in TeamManager().teams:
                for i, _ in enumerate(team.weapon_set):
                    team.weapon_set[i] = 1
        elif code == "suddendeath":
            sudden_death()
        elif code == "wind":
            GameVariables().physics.wind = uniform(-1, 1)
        elif code == "goodbyecruelworld":
            boom(GameVariables().player.pos, 100)
        elif code == "boomhere":
            boom(mouse_pos, 20)
        elif code == "armageddon":
            Armageddon()
        elif code[0:5] == "gunme" and len(code) == 6:
            amount = int(code[5])
            for i in range(amount):
                WeaponPack(mouse_pos)
        elif code[0:9] == "utilizeme" and len(code) == 10:
            amount = int(code[9])
            for i in range(amount):
                UtilityPack(mouse_pos)
        elif code == "aspirin":
            HealthPack(mouse_pos)
        elif code == "globalshift":
            for worm in GameVariables().get_worms():
                # if worm in TeamManager().current_team.worms:
                    # continue
                worm.gravity = worm.gravity * -1
        elif code == "petrolcan":
            PetrolCan(mouse_pos)
        elif code == "megaboom":
            GameVariables().mega_weapon_trigger = True
        elif code == "comeflywithme":
            TeamManager().current_team.ammo(WeaponManager()["jet pack"], 6)
            TeamManager().current_team.ammo(WeaponManager()["rope"], 6)
            TeamManager().current_team.ammo(WeaponManager()["ender pearl"], 6)
        elif code == "masterofpuppets":
            MasterOfPuppets()
        elif code == "deathtouch":
            pos = Vector(mouse_pos)
            closest = None
            closest_dist = 100000
            for worm in GameVariables().get_worms():
                if dist(worm.pos, pos) < closest_dist:
                    closest_dist = dist(worm.pos, pos)
                    closest = worm
            if closest:
                closest.damage(1000)
