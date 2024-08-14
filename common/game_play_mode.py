
import pygame
from typing import Dict, List

from common.game_variables import GameVariables
from common import SingletonMeta

class GamePlayMode:
    ''' handles game mode '''
    def __init__(self):
        pass

    def on_game_init(self):
        pass

    def on_cycle(self):
        pass

    def step(self):
        pass

    def draw(self, win: pygame.Surface):
        pass

    def hud_draw(self, win: pygame.Surface):
        pass

    def on_worm_damage(self, worm):
        pass

    def on_worm_death(self):
        pass

    def win_bonus(self):
        pass


class GamePlay(metaclass=SingletonMeta):
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
        for mode in self.modes:
            mode.on_cycle()

    def step(self):
        for mode in self.modes:
            mode.step()

    def draw(self, win: pygame.Surface):
        for mode in self.modes:
            mode.draw(win)

    def hud_draw(self, win: pygame.Surface):
        for mode in self.modes:
            mode.hud_draw(win)

    def on_worm_damage(self, worm):
        for mode in self.modes:
            mode.on_worm_damage(worm)

    def on_worm_death(self):
        for mode in self.modes:
            mode.on_worm_death()

    def win_bonus(self):
        for mode in self.modes:
            mode.win_bonus()


class TerminatorGamePlay(GamePlayMode):
    def __init__(self):
        self.worm_to_target_map: Dict[str, str]
        self.hit_this_turn = False

    def on_game_init(self):
        pass

    def on_cycle(self):
        pass

class DarknessGamePlay(GamePlayMode):
    pass
