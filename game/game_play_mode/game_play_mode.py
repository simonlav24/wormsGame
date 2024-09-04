

from typing import Dict, List
from random import choice

import pygame

from common import GameVariables, draw_target, draw_dir_indicator, EntityWorm
from common.game_event import GameEvents, EventWormDamage, EventComment
from common import SingletonMeta

from game.team_manager import TeamManager

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

    def on_worm_damage(self, worm: EntityWorm, damage: int):
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
        ''' on cycle update, precondition: new turn worm is determined '''
        for mode in self.modes:
            mode.on_cycle()

    def step(self):
        for mode in self.modes:
            mode.step()

        # handle events
        for event in GameEvents().get_events():
            if(isinstance(event, EventWormDamage)):
                for mode in self.modes:
                    mode.on_worm_damage(event.worm, event.damage)
                event.done()

    def draw(self, win: pygame.Surface):
        for mode in self.modes:
            mode.draw(win)

    def hud_draw(self, win: pygame.Surface):
        for mode in self.modes:
            mode.hud_draw(win)

    def on_worm_damage(self, worm: EntityWorm, damage: int):
        for mode in self.modes:
            mode.on_worm_damage(worm)

    def on_worm_death(self):
        for mode in self.modes:
            mode.on_worm_death()

    def win_bonus(self):
        for mode in self.modes:
            mode.win_bonus()



class DarknessGamePlay(GamePlayMode):
    pass
