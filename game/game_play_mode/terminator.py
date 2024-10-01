
from typing import Dict
from random import choice

import pygame

from common import GameVariables, EntityWorm, draw_target, draw_dir_indicator
from game.game_play_mode.game_play_mode import GamePlayMode


class TerminatorGamePlay(GamePlayMode):
    def __init__(self):
        self.hit_this_turn = False
        self.current_target: EntityWorm = None
        self.worm_to_target: Dict[EntityWorm, EntityWorm] = {}

    def pick_target(self):
        current_worm = GameVariables().player
        target = self.worm_to_target.get(current_worm, None)
        if target is not None and not target.alive:
            target = None

        if target is None:
            worms = [worm for worm in GameVariables().get_worms() if
                     worm.get_team_data().team_name != GameVariables().player.get_team_data().team_name]
            if len(worms) == 0:
                return
            target = choice(worms)
            
        
        self.current_target = target
        self.worm_to_target[GameVariables().player] = self.current_target
        
        wormComment = {'text': self.current_target.name_str, 'color': self.current_target.team.color}
        comments = [
            [wormComment, {'text': ' is marked for death'}],
            [{'text': 'kill '}, wormComment],
            [wormComment, {'text': ' is the weakest link'}],
            [{'text': 'your target: '}, wormComment],
        ]
        GameVariables().commentator.comment(choice(comments))

    def draw(self, win: pygame.Surface):
        if self.current_target is None:
            return
        draw_target(win, self.current_target.pos)
        draw_dir_indicator(win, self.current_target.pos)

    def on_game_init(self):
        self.pick_target()

    def on_cycle(self):
        self.hit_this_turn = False
        self.pick_target()
    
    def on_worm_damage(self, worm: EntityWorm, damage: int):
        if self.hit_this_turn:
            return
        if worm is self.current_target:
            self.hit_this_turn = True
            GameVariables().player.give_point(1)
    
    def on_worm_death(self, worm: EntityWorm):
        if worm is self.current_target:
            self.hit_this_turn = False
            GameVariables().player.give_point(2)
            self.pick_target()
    
    def is_points_game(self) -> bool:
        return True
    
    def win_bonus(self) -> int:
        return 3
