
from typing import List

import pygame

from common import GameVariables, draw_dir_indicator

from game.game_play_mode.game_play_mode import GamePlayMode
from entities.shooting_target import ShootingTarget



class TargetsGamePlay(GamePlayMode):
    def __init__(self):
        super().__init__()

        self.number_of_targets = 10
        self.targets: List[ShootingTarget] = []
    
    def on_game_init(self):
        super().on_game_init()
        self.targets = [ShootingTarget() for _ in range(self.number_of_targets)]

    def step(self):
        super().step()

        for target in self.targets:
            if target.is_done:
                GameVariables().player.give_point(1)
        
        self.targets = [target for target in self.targets if not target.is_done]
        for _ in range(self.number_of_targets - len(self.targets)):
            self.targets.append(ShootingTarget())
    
    def on_cycle(self):
        # todo: change to on round end decrease
        self.number_of_targets -= 1
        if(self.number_of_targets == 1):
            GameVariables().commentator.comment([{'text': 'final targets round'}])
    
    def draw(self, win: pygame.Surface):
        super().draw(win)
        [draw_dir_indicator(win, target.pos) for target in self.targets]




