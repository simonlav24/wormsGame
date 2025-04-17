
from typing import List, Dict

from common import GameVariables, EntityWorm

from game.game_play_mode.game_play_mode import GamePlayMode


class DVGGamePlay(GamePlayMode):
    def on_game_init(self, game_data: dict=None):
        super().on_game_init(game_data)
        
        # gather teams
        teams: Dict[str, List[EntityWorm]] = {}
        for worm in GameVariables().get_worms():
            team_name = worm.get_team_data().team_name
            if team_name not in teams.keys():
                teams[team_name] = []
            teams[team_name].append(worm)
        
        initial_health = GameVariables().config.worm_initial_health

        for team in teams.values():
            length = len(team)
            for i in range(length):
                if i == 0:
                    team[i].health = initial_health + (length - 1) * (initial_health // 2)
                else:
                    team[i].health = initial_health // 2





