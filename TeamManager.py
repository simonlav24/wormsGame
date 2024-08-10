
import pygame
from typing import List
import json
from random import choice, shuffle
from pydantic import BaseModel

import globals
from Weapons.WeaponManager import Weapon
from Common import desaturate, ColorType
from Hud import HealthBar
from GameVariables import GameVariables

class TeamData(BaseModel):
    team_name: str
    color: ColorType
    names: List[str]
    hats: str


class Team:
    def __init__(self, data: TeamData):
        self.nameList = data.names
        self.color = data.color
        self.weaponCounter = globals.weapon_manager.basic_set.copy()
        self.worms = []
        self.name = data.team_name
        self.damage = 0
        self.killCount = 0
        self.points = 0
        self.flagHolder = False
        self.artifacts = []
        self.hatOptions = data.hats
        self.hatSurf = None
    
    def makeHat(self, index):
        self.hatSurf = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.hatSurf.blit(globals.game_manager.sprites, (0,0), (16 * (index % 8),16 * (index // 8),16,16))
        pixels = pygame.PixelArray(self.hatSurf)
        color = desaturate(self.color)
        pixels.replace((101, 101, 101), color)
        pixels.replace((81, 81, 81), tuple(max(i - 30,0) for i in color))
        del pixels
    
    def __len__(self):
        return len(self.worms)

    def get_new_worm_name(self) -> str:
        if len(self.nameList) > 0:
            return self.nameList.pop(0)
    
    def ammo(self, weapon: Weapon, amount: int=None, absolute: bool=False):
        # adding amount of weapon to team
        if amount and not absolute:
            self.weaponCounter[weapon.index] += amount
        elif amount and absolute:
            self.weaponCounter[weapon.index] = amount
        return self.weaponCounter[weapon.index]


class TeamManager:
    def __init__(self):
        globals.team_manager = self

        with open('teams.json', 'r') as file:
            teams = json.load(file)
        data_list = [TeamData.model_validate(data) for data in teams]
        self.teams: List[Team] = [Team(data) for data in data_list]
        
        # hats
        hatsChosen = []
        for team in self.teams:
            indexChoice = []
            options = team.hatOptions.replace(" ", "").split(",")
            for option in options:
                if "-" in option:
                    indexChoice += [i for i in range(int(option.split("-")[0]), int(option.split("-")[1]) + 1)]
                else:
                    indexChoice.append(int(option))
            hatChoice = choice([hat for hat in indexChoice if hat not in hatsChosen])
            team.makeHat(hatChoice)
            hatsChosen.append(hatChoice)

        self.totalTeams = len(self.teams)
        self.currentTeam: Team = None
        self.teamChoser = 0
        shuffle(self.teams)

        # todo: calculate for david vs goliath
        self.health_bar_hud = HealthBar(self.totalTeams,
                                        GameVariables().config.worm_initial_health,
                                        GameVariables().config.worms_per_team,
                                        [team.color for team in self.teams])
    
    def step(self) -> None:

        self.health_bar_hud.step()
    
    def draw(self, win: pygame.Surface) -> None:
        self.health_bar_hud.draw(win)