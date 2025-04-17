

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

    def on_game_init(self, game_data: dict=None):
        for mode in self.modes:
            mode.on_game_init(game_data)

    def on_turn_begin(self):
        ''' on cycle update '''
        for mode in self.modes:
            mode.on_turn_begin()

    def on_turn_end(self):
        ''' on cycle update '''
        for mode in self.modes:
            mode.on_turn_end()

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
    
    def on_new_round(self):
        super().on_new_round()
        for mode in self.modes:
            mode.on_new_round()

    def debug_print(self) -> str:
        output = ''
        for mode in self.modes:
            output += mode.debug_print()
        return output
    
    def on_sudden_death_turn(self) -> None:
        for mode in self.modes:
            mode.on_sudden_death_turn()

