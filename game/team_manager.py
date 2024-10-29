
from typing import List, Dict, Any
from random import choice, shuffle

import pygame

from common import desaturate, GameVariables, sprites, SingletonMeta, EntityWorm, fonts, PATH_TEAMS_LIST
from common.team_data import TeamData, read_teams, read_teams_play
from game.hud import HealthBar


class Team:
    def __init__(self, data: TeamData) -> None:
        self.data: TeamData=data
        self.color = data.color
        self.weapon_set: List[int] = []
        self.worms: List[EntityWorm] = []
        self.name = data.team_name
        self.damage = 0
        self.kill_count = 0
        self.points = 0
        self.artifacts = []
        self.hat_options = data.hats
        self.hat_surf = None
    
    def make_hat(self, index) -> None:
        self.hat_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.hat_surf.blit(sprites.sprite_atlas, (0,0), (16 * (index % 8),16 * (index // 8),16,16))
        pixels = pygame.PixelArray(self.hat_surf)
        color = desaturate(self.color)
        pixels.replace((101, 101, 101), color)
        pixels.replace((81, 81, 81), tuple(max(i - 30,0) for i in color))
        del pixels
    
    def get_health(self):
        return sum([worm.health for worm in self.worms])

    def __len__(self) -> int:
        return len(self.worms)

    def get_new_worm_name(self) -> str:
        if len(self.data.names) > 0:
            return self.data.names.pop(0)
    
    def ammo(self, weapon_index: int, amount: int=None, absolute: bool=False) -> None:
        # adding amount of weapon to team
        if self.weapon_set[weapon_index] == -1:
            return self.weapon_set[weapon_index]
        if amount and not absolute:
            self.weapon_set[weapon_index] += amount
        elif amount and absolute:
            self.weapon_set[weapon_index] = amount
        return self.weapon_set[weapon_index]


class TeamManager(metaclass=SingletonMeta):
    def __init__(self):
        self.teams: List[Team] = []
        self.load_teams()

        num_of_teams = len(self.teams)
        GameVariables().num_of_teams = num_of_teams
        GameVariables().turns_in_round = GameVariables().num_of_teams
        self.current_team: Team = None
        self.team_choser = 0
        shuffle(self.teams)

        # todo: calculate for david vs goliath
        self.health_bar_hud = HealthBar(
            num_of_teams,
            GameVariables().config.worm_initial_health,
            GameVariables().config.worms_per_team,
            [team.color for team in self.teams]
        )

        # score list
        self.score_list: List[Dict[str, Any]] = []
    
    def load_teams(self) -> None:
        available_teams = read_teams()
        teams_in_play = read_teams_play()
        
        data_list = [TeamData.model_validate(data) for data in available_teams]
        self.teams = [Team(data) for data in data_list if data.team_name in teams_in_play]

        self.generate_hats()

    def get_info(self) -> List[Dict[str, Any]]:
        info = []
        for team in self.teams:
            if GameVariables().game_mode.is_points_game():
                score = team.points
            else:
                score = team.get_health()
            info.append(
                {
                    'name': team.name,
                    'color': team.color,
                    'score': score
                }
            )
        return tuple(info)

    def get_by_name(self, name: str) -> Team:
        for team in self.teams:
            if team.name == name:
                return team
        return None

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
            team.make_hat(hat_choice)
            hats_chosen.append(hat_choice)

    def step(self) -> None:
        # todo: update with worms
        self.health_bar_hud.update_health([team.get_health() for team in self.teams])
        self.health_bar_hud.update_score([team.points for team in self.teams])
        self.health_bar_hud.step()
    
    def draw(self, win: pygame.Surface) -> None:
        self.health_bar_hud.draw(win)

        x = 5
        y = win.get_height() - 25
        for score_dict in self.score_list:
            win.blit(score_dict['surf'], (x, y))
            y -= score_dict['surf'].get_height() + 1

    def give_point_to_team(self, team: Team, worm: EntityWorm, points) -> None:
        team.points += points

        # update point list
        if len(self.score_list) > 0:
            if self.score_list[0]['worm'] == worm.name_str:
                last_score_dict = self.score_list.pop(0)
                points += last_score_dict['points']

        # create surf
        s1 = fonts.pixel5_halo.render(f'{worm.name_str}: ', False, team.color)
        s2 = fonts.pixel5_halo.render(f'{points}', False, GameVariables().initial_variables.hud_color)
        surf = pygame.Surface((s1.get_width() + s2.get_width(), s1.get_height()), pygame.SRCALPHA)
        surf.blit(s1, (0,0))
        surf.blit(s2, (s1.get_width(), 0))

        score_surf = {
            'worm': worm.name_str,
            'points': points,
            'surf': surf
        }
        self.score_list.insert(0, score_surf)
        if len(self.score_list) > 10:
            self.score_list.pop(-1)