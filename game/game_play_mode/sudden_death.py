
from typing import Set
from random import choice

import pygame

from common import GameVariables, SuddenDeathMode
from game.game_play_mode.game_play_mode import GamePlayMode


class SuddenDeathGamePlay(GamePlayMode):
    def __init__(self):
        super().__init__()
        self.modes: Set[SuddenDeathMode] = set()

        if GameVariables().config.sudden_death_style == SuddenDeathMode.ALL:
            self.modes.add(SuddenDeathMode.FLOOD)
            self.modes.add(SuddenDeathMode.PLAGUE)
        else:
            self.modes.add(GameVariables().config.sudden_death_style)

        # sicken worms
        if SuddenDeathMode.PLAGUE in self.modes:
            for worm in GameVariables().get_worms():
                worm.sicken()
    
    def on_turn_end(self):
        if SuddenDeathMode.FLOOD in self.modes:
            GameVariables().rise_water(20)