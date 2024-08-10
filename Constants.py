from typing import Tuple, List

ColorType = Tuple[int, int, int] | Tuple[int, int, int, int]

__version__ = '1.5.0'

RESET = 0
PLAYER_CONTROL_1 = 1
PLAYER_CONTROL_2 = 2
WAIT_STABLE = 3
FIRE_MULTIPLE = 4
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