

from enum import Enum
from dataclasses import dataclass
from typing import Tuple

import pygame

# --- no game related imports ---

ColorType = Tuple[int, int, int] | Tuple[int, int, int, int]

__version__ = '1.5.0'

class GameState(Enum):
    RESET = 0
    PLAYER_PLAY = 1
    PLAYER_RETREAT = 2
    OBJECTS_PLAY = 3
    WAIT_STABLE = 4
    WIN = 5

RIGHT = 1
LEFT = -1
RED = (255,0,0)
YELLOW = (255,255,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
BLACK = (0,0,0)
WHITE = (255,255,255)
GREY = (100,100,100)
DARK_COLOR = (30,30,30)
DOWN = 1
UP = -1

HEALTH_PACK = 0
UTILITY_PACK = 1
WEAPON_PACK = 2
FLAG_DEPLOY = 3

MJOLNIR = 0
PLANT_MASTER = 1
AVATAR = 2
MINECRAFT = 3

EDGE_BORDER = 65
MAP_SCROLL_SPEED = 35

SHOCK_RADIUS = 1.5
LIGHT_RADIUS = 70
CRITICAL_FALL_VELOCITY = 5
JUMP_VELOCITY = 3
WATER_AMP = 2

# color feel 0:up 1:down 2:mountfar 3:mountclose
feels = [
		((238, 217, 97), (251, 236, 187), (222, 171, 51), (253, 215, 109)),
		((122, 196, 233), (199, 233, 251), (116, 208, 186), (100, 173, 133)),
		((110, 109, 166), (174, 95, 124), (68, 55, 101), (121, 93, 142)),
		((35, 150, 197), (248, 182, 130), (165, 97, 62), (227, 150, 104)),
		((121, 135, 174), (195, 190, 186), (101, 136, 174), (72, 113, 133)),
		((68, 19, 136), (160, 100, 170), (63, 49, 124), (45, 29, 78)),
		((40,40,30), (62, 19, 8), (20,20,26), (56, 41, 28)),
		((0,38,95), (23, 199, 248), (2,113,194), (0, 66, 153)),
		((252,255,186), (248, 243, 237), (165,176,194), (64, 97, 138)),
		((37,145,184), (232, 213, 155), (85,179,191), (16, 160, 187)),
		((246,153,121), (255, 205, 187), (252,117,92), (196, 78, 63))
	]

comments_damage = [
	("", " is no more"),
	("", " is an ex-worm"),
	("", " bit the dust"),
	("", " has been terminated"),
	("poor ", ""),
	("so long ", ""),
	("", " will see you on the other side"), 
	("", " diededed"),
	("", " smells the flower from bellow")
]

comments_flew = [
	(""," is swimming with the fishes"),
	("there goes ", " again"),
	("its bye bye for ", ""),
	("", " has drowed"),
	("", " swam like a brick"),
	("", " has gone to marry a mermaid"),
	("", " has divided by zero")
]

# sprites

@dataclass
class Sprites:
    blood: pygame.Surface = None
    hole: pygame.Surface = None
    sprite_atlas: pygame.Surface = None
    air_strike_indicator: pygame.Surface = None
    bee: pygame.Surface = None

sprites = Sprites()

class HaloFont:
    def __init__(self, font):
        self.font: pygame.font.Font = font

    def render(self, text, aa, color, halo=(0,0,0)) -> pygame.Surface:
        halo_surf = self.font.render(text, aa, halo)
        text_surf = self.font.render(text, aa, color)
        
        surf = pygame.Surface((text_surf.get_width() + 2, text_surf.get_height() + 2), pygame.SRCALPHA)
        for i in [(0,1), (1,0), (1,2), (2,1)]:
            surf.blit(halo_surf, i)

        surf.blit(text_surf, (1,1))
        return surf

# fonts
@dataclass
class Fonts:
    pixel5: pygame.font.Font = None
    pixel5_halo: pygame.font.Font = None
    pixel10: pygame.font.Font = None

sprites = Sprites()
fonts = Fonts()

def initialize() -> None:
    ''' initialize constants '''
    global sprites, fonts
    sprites.blood = pygame.image.load("assets/blood.png").convert_alpha()
    sprites.hole = pygame.image.load("assets/hole.png").convert_alpha()
    sprites.sprite_atlas = pygame.image.load("assets/sprites.png").convert_alpha()
    
    fonts.pixel5 = pygame.font.Font("fonts\pixelFont.ttf", 5)
    fonts.pixel10 = pygame.font.Font("fonts\pixelFont.ttf", 10)
    fonts.pixel5_halo = HaloFont(fonts.pixel5)

    sprites.air_strike_indicator = fonts.pixel10.render(">>>", False, BLACK)

    sprites.bee = pygame.Surface((4,4), pygame.SRCALPHA)
    sprites.bee.fill((255,255,0), ((1,2), (1,3)))
    sprites.bee.fill((0,0,0), ((2,2), (2,3)))
    sprites.bee.fill((255,255,0), ((3,2), (3,3)))
    sprites.bee.fill((143,234,217,100), ((1,0), (2,2)))


