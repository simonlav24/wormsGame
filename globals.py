
import pygame
from common.vector import Vector

from common.game_variables import GameVariables
import common.constants

class HaloFont:
    def __init__(self, font):
        self.fontObject = font
    def render(self, text, antialiasing, color, halo=(0,0,0)):
        haloSurf = self.fontObject.render(text, antialiasing, halo)
        textSurf = self.fontObject.render(text, antialiasing, color)
        surf = pygame.Surface((textSurf.get_width() + 2, textSurf.get_height() + 2), pygame.SRCALPHA)
        surf.blit(haloSurf, (0,1))
        surf.blit(haloSurf, (1,0))
        surf.blit(haloSurf, (1,2))
        surf.blit(haloSurf, (2,1))
        surf.blit(textSurf, (1,1))
        return surf

def mouse_pos_in_world():
    mouse_pos = pygame.mouse.get_pos()
    return Vector(mouse_pos[0] / GameVariables().scale_factor + GameVariables().cam_pos[0],
                   mouse_pos[1] / GameVariables().scale_factor + GameVariables().cam_pos[1])

def globalsInit():
    global fpsClock, screenWidth, screenHeight, win, screen

    pygame.init()

    fpsClock = pygame.time.Clock()

    screenWidth = 1280
    screenHeight = 720
    
    GameVariables().win_width = int(screenWidth / GameVariables().scale_factor)
    GameVariables().win_height = int(screenHeight / GameVariables().scale_factor)

    win = pygame.Surface((GameVariables().win_width, GameVariables().win_height))
    
    pygame.display.set_caption("Simon's Worms")
    # screen = pygame.display.set_mode((screenWidth,screenHeight), pygame.DOUBLEBUF | pygame.NOFRAME)
    screen = pygame.display.set_mode((screenWidth,screenHeight), pygame.DOUBLEBUF)

    common.constants.initialize()

win = None

game_manager = None
time_manager = None
team_manager = None
weapon_manager = None

def exitGame():
    pygame.quit()
    quit(0)