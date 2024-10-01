

from typing import Dict, List
from random import choice

import pygame

from common import EntityWorm, GamePlayMode

class GamePlayCompound(GamePlayMode):
    def __init__(self):
        self.modes: List[GamePlayMode] = []

    def add_mode(self, mode: GamePlayMode | None):
        if mode is None:
            return
        self.modes.append(mode)

    def on_game_init(self):
        for mode in self.modes:
            mode.on_game_init()

    def on_cycle(self):
        ''' on cycle update, precondition: new turn worm is determined '''
        for mode in self.modes:
            mode.on_cycle()

    def on_deploy(self):
        ''' on drop deployable update '''
        for mode in self.modes:
            mode.on_deploy()

    def step(self):
        for mode in self.modes:
            mode.step()        

    def draw(self, win: pygame.Surface):
        for mode in self.modes:
            mode.draw(win)

    def hud_draw(self, win: pygame.Surface):
        for mode in self.modes:
            mode.hud_draw(win)

    def on_worm_damage(self, worm: EntityWorm, damage: int):
        for mode in self.modes:
            mode.on_worm_damage(worm, damage)

    def on_worm_death(self, worm: EntityWorm):
        for mode in self.modes:
            mode.on_worm_death(worm)

    def win_bonus(self) -> int:
        result = 0
        for mode in self.modes:
            result += mode.win_bonus()
        return result
    
    def is_game_over(self) -> bool:
        result = False
        for mode in self.modes:
            result |= mode.is_game_over()
        return result

    def is_points_game(self) -> bool:
        result = False
        for mode in self.modes:
            result |= mode.is_points_game()
        return result

