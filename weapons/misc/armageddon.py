
from random import randint

import pygame

from common import GameVariables
from common.vector import Vector

from game.map_manager import MapManager
from weapons.missiles import Missile


class Armageddon:
    def __init__(self):
        GameVariables().register_non_physical(self)
        self.stable = False
        self.is_boom_affected = False
        self.timer = 700
    
    def step(self):
        self.timer -= 1
        if self.timer == 0:
            GameVariables().unregister_non_physical(self)
            return
        if GameVariables().time_overall % 10 == 0:
            for i in range(randint(1,2)):
                x = randint(-100, MapManager().game_map.get_width() + 100)
                m = Missile((x, -10), Vector(randint(-10,10), 5).normalize(), 1)
                m.is_wind_affected = 0
                m.boomRadius = 40
    
    def draw(self, win: pygame.Surface):
        pass