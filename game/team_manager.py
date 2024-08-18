
from typing import List, Protocol
import json
from random import choice, shuffle
from pydantic import BaseModel

import pygame

from common import desaturate, ColorType, GameVariables, sprites, SingletonMeta
from game.hud import HealthBar


class WormInterface(Protocol):
    health: int


class TeamData(BaseModel):
    ''' saved team data '''
    team_name: str
    color: ColorType
    names: List[str]
    hats: str


class Team:
    def __init__(self, data: TeamData) -> None:
        self.name_list = data.names
        self.color = data.color
        self.weapon_set: List[int] = []
        self.worms: List[WormInterface] = []
        self.name = data.team_name
        self.damage = 0
        self.kill_count = 0
        self.points = 0
        self.artifacts = []
        self.hat_options = data.hats
        self.hat_surf = None
    
    def makeHat(self, index) -> None:
        self.hat_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.hat_surf.blit(sprites.sprite_atlas, (0,0), (16 * (index % 8),16 * (index // 8),16,16))
        pixels = pygame.PixelArray(self.hat_surf)
        color = desaturate(self.color)
        pixels.replace((101, 101, 101), color)
        pixels.replace((81, 81, 81), tuple(max(i - 30,0) for i in color))
        del pixels
    
    def __len__(self) -> int:
        return len(self.worms)

    def get_new_worm_name(self) -> str:
        if len(self.name_list) > 0:
            return self.name_list.pop(0)
    
    def ammo(self, weapon_index: int, amount: int=None, absolute: bool=False) -> None:
        # adding amount of weapon to team
        print(weapon_index)
        if amount and not absolute:
            self.weapon_set[weapon_index] += amount
        elif amount and absolute:
            self.weapon_set[weapon_index] = amount
        return self.weapon_set[weapon_index]


class TeamManager(metaclass=SingletonMeta):
    def __init__(self):

        with open('teams.json', 'r') as file:
            teams = json.load(file)
        data_list = [TeamData.model_validate(data) for data in teams]
        self.teams: List[Team] = [Team(data) for data in data_list]

        self.generate_hats()

        self.num_of_teams = len(self.teams)
        self.current_team: Team = None
        self.team_choser = 0
        shuffle(self.teams)

        # todo: calculate for david vs goliath
        self.health_bar_hud = HealthBar(
            self.num_of_teams,
            GameVariables().config.worm_initial_health,
            GameVariables().config.worms_per_team,
            [team.color for team in self.teams]
        )
    
    def generate_hats(self) -> None:
        hats_chosen = []
        for team in self.teams:
            index_choice = []
            options = team.hat_options.replace(" ", "").split(",")
            for option in options:
                if "-" in option:
                    index_choice += [i for i in range(int(option.split("-")[0]), int(option.split("-")[1]) + 1)]
                else:
                    index_choice.append(int(option))
            hat_choice = choice([hat for hat in index_choice if hat not in hats_chosen])
            team.makeHat(hat_choice)
            hats_chosen.append(hat_choice)

    def step(self) -> None:
        # todo: update with worms
        self.health_bar_hud.step()
    
    def draw(self, win: pygame.Surface) -> None:
        self.health_bar_hud.draw(win)