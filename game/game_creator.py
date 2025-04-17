
from random import randint, uniform, choice

import pygame

from common import GameVariables, GameGlobals, GameConfig, fonts, WHITE, BLACK, PlantMode
from common.game_config import RandomMode

from game.state_save import save_game, load_game

from game.time_manager import TimeManager
from game.map_manager import MapManager, SKY
from game.team_manager import TeamManager

from entities.props import PetrolCan
from entities.worm import Worm

from weapons.weapon_manager import WeaponManager
from weapons.weapon import WeaponCategory
from weapons.plants import PlantSeed
from weapons.mine import Mine


class GameCreator:
    def __init__(self):
        self.game_config: GameConfig = None

        self.load_step_incremental = 0
        self.load_step_incremental_max = 0
    
    def set_config(self, game_config: GameConfig) -> None:
        self.game_config = game_config
        self.load_step_incremental_max = self.game_config.worms_per_team * 4

    def create_game(self) -> None:
        raise NotImplementedError("create_game() must be implemented in subclasses")

    def create_map(self) -> None:
        raise NotImplementedError("create_map() must be implemented in subclasses")

    def loading_step(self):
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


class GameCreatorNewGame(GameCreator):
    def create_game(self) -> None:
        ''' create new game based on config '''
        # create map
        self.create_map()
            
        # check for sky opening for airstrikes
        closed_sky_counter = 0
        for i in range(100):
            if MapManager().is_ground_at((randint(0, MapManager().game_map.get_width()-1), randint(0, 10))):
                closed_sky_counter += 1
        if closed_sky_counter > 50:
            GameVariables().initial_variables.allow_air_strikes = False
            for team in TeamManager().teams:
                for i, _ in enumerate(team.weapon_set):
                    if WeaponManager().weapons[i].category == WeaponCategory.AIRSTRIKE:
                        team.weapon_set[i] = 0

        # select current team
        TeamManager().current_team = TeamManager().teams[0]

        # place worms
        self.place_worms_random()
        
        # give random legendary starting weapons:
        WeaponManager().give_extra_starting_weapons()

        # place mines
        if not self.game_config.option_digging:
            amount = randint(2,4)
            for _ in range(amount):
                mine = MapManager().place_object(Mine, None, True)
                mine.damp = 0.1

        # place petrol cans
        amount = randint(2,4)
        for _ in range(amount):
            MapManager().place_object(PetrolCan, None, False)

        # place plants
        if not self.game_config.option_digging:
            amount = randint(0, 2)
            for _ in range(amount):
                MapManager().place_object(PlantSeed, ((0,0), (0,0), 0, PlantMode.VENUS), False)

        # choose starting worm
        starting_worm = TeamManager().current_team.worms.pop(0)
        TeamManager().current_team.worms.append(starting_worm)

        if self.game_config.random_mode != RandomMode.NONE:
            starting_worm = choice(TeamManager().current_team.worms)
        
        GameVariables().player = starting_worm
        GameVariables().cam_track = starting_worm

        # reset time
        TimeManager().time_reset()
        WeaponManager().switch_weapon(WeaponManager().current_weapon)

        # randomize wind
        GameVariables().physics.wind = uniform(-1, 1)

        # handle game mode
        self.init_handle_game_mode()

    def create_map(self) -> None:
        ''' create game map '''
        custom_height = 512
        if self.game_config.map_ratio != -1:
            custom_height = self.game_config.map_ratio

        if self.game_config.option_digging:
            MapManager().create_map_digging(custom_height)
        elif 'noise' in self.game_config.map_path:
            MapManager().create_map_by_image_path(self.game_config.map_path, custom_height, True)
        else:
            MapManager().create_map_by_image_path(self.game_config.map_path, custom_height, self.game_config.is_recolor)
        

    def place_worms_random(self) -> None:
        ''' create worms and place them randomly '''
        team_choser = TeamManager().teams.index(TeamManager().current_team)
        for i in range(self.game_config.worms_per_team * len(TeamManager().teams)):
            if self.game_config.option_forts:
                place = MapManager().get_good_place(div=i)
            else:
                place = MapManager().get_good_place()
            if self.game_config.option_digging:
                pygame.draw.circle(MapManager().game_map, SKY, place, 35)
                pygame.draw.circle(MapManager().ground_map, SKY, place, 35)
                pygame.draw.circle(MapManager().ground_secondary, SKY, place, 30)
            current_team = TeamManager().teams[team_choser]
            new_worm_name = current_team.get_new_worm_name()
            current_team.worms.append(Worm(place, new_worm_name, current_team))
            team_choser = (team_choser + 1) % GameVariables().num_of_teams
            self.loading_step()

    def init_handle_game_mode(self) -> None:
        ''' on init, handle game mode parameter and variables '''
        # digging match
        if GameVariables().config.option_digging:
            for _ in range(80):
                mine = MapManager().place_object(Mine, None)
                mine.damp = 0.1
            # more digging
            for team in TeamManager().teams:
                team.ammo(WeaponManager()["minigun"], 5)
                team.ammo(WeaponManager()["drill missile"], 3)
                team.ammo(WeaponManager()["laser gun"], 3)
            GameVariables().config.option_closed_map = True

        GameVariables().game_mode.on_game_init()


class GameCreatorLoadGame(GameCreator):
    def __init__(self):
        super().__init__()
        self.game_data: dict = None

    def create_game(self):
        path = self.game_config.game_load_state_path
        self.game_data = load_game(path)

        self.create_map()

        # place objects
        # todo:

        # choose starting worm
        starting_worm = TeamManager().current_team.worms.pop(0)
        TeamManager().current_team.worms.append(starting_worm)

        if self.game_config.random_mode != RandomMode.NONE:
            starting_worm = choice(TeamManager().current_team.worms)
        
        GameVariables().player = starting_worm
        GameVariables().cam_track = starting_worm

        # reset time
        TimeManager().time_reset()
        WeaponManager().switch_weapon(WeaponManager().current_weapon)

        # randomize wind
        GameVariables().physics.wind = uniform(-1, 1)

        # todo: game mode on load


    def create_map(self):
        map_surf = self.game_data['ground_map']
        MapManager().create_map_by_surf(map_surf)        



