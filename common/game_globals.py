
import pygame
from common import SingletonMeta

class GameGlobals(metaclass=SingletonMeta):
    def __init__(self):
        
        self.win: pygame.Surface = None
        self.win_width = 0
        self.win_height = 0

        self.screen_width = 1280
        self.screen_height = 720

        self.scale_factor = 3
        self.scale_range = (1, 3)

        self.fps = 30

    def update_win(self, win: pygame.Surface):
        pass