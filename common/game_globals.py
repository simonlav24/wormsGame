
import pygame
from common import SingletonMeta

class GameGlobals(metaclass=SingletonMeta):
    def __init__(self) -> None:
        
        self.screen: pygame.Surface = None
        self.win: pygame.Surface = None
        self.win_width = 0
        self.win_height = 0

        self.screen_width = 1920
        self.screen_height = 1080

        self.scale_factor = 3
        self.scale_range = (1, 3)

        self.fps = 30

    def reset_win_scale(self) -> None:
        ''' reset window size to initial scaled '''
        self.scale_factor = self.scale_range[1]
        self.win_width = int(self.screen_width / self.scale_factor)
        self.win_height = int(self.screen_height / self.scale_factor)
        GameGlobals().win = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height))

    def update_win(self, win: pygame.Surface):
        pass

    def full_screen(self):
        self.screen_width = 1920
        self.screen_height = 1080
        GameGlobals().win_width = int(GameGlobals().screen_width / GameGlobals().scale_factor)
        GameGlobals().win_height = int(GameGlobals().screen_height / GameGlobals().scale_factor)

        GameGlobals().win = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height))
        screen = pygame.display.set_mode((GameGlobals().screen_width, GameGlobals().screen_height), pygame.DOUBLEBUF | pygame.FULLSCREEN)
        GameGlobals().screen = screen


