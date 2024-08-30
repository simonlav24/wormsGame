

from typing import Dict, List
from random import choice

import pygame

from common import GameVariables, draw_target, draw_dir_indicator
from common.game_event import GameEvents, EventWormDamage, EventComment
from common import SingletonMeta

from game.team_manager import TeamManager
from entities import PhysObj, Worm

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

    def on_worm_damage(self, worm: Worm, damage: int):
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

    def on_worm_damage(self, worm: Worm, damage: int):
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
        self.hit_this_turn = False
        self.current_target: Worm = None

    def pick_target(self):
        self.hit_this_turn = False
        worms = []
        for w in GameVariables().get_worms():
            if w in TeamManager().current_team.worms:
                continue
            worms.append(w)
        if len(worms) == 0:
            self.current_target = None
            return
        
        self.current_target = choice(worms)
        wormComment = {'text': self.current_target.name_str, 'color': self.current_target.team.color}
        comments = [
            [wormComment, {'text': ' is marked for death'}],
            [{'text': 'kill '}, wormComment],
            [wormComment, {'text': ' is the weakest link'}],
            [{'text': 'your target: '}, wormComment],
        ]
        GameEvents().post(EventComment(choice(comments)))

    def draw(self, win: pygame.Surface):
        draw_target(win, self.current_target.pos)
        draw_dir_indicator(win, self.current_target.pos)

    def on_game_init(self):
        self.pick_target()

    def on_cycle(self):
        pass

class DarknessGamePlay(GamePlayMode):
    pass
