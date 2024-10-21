from random import uniform, randint
from math import cos, sin, atan2
from typing import Tuple

import pygame

from common.vector import Vector, distus, vectorUnitRandom
from common import sprites, GameVariables

from game.map_manager import MapManager, GRD, SKY, SKY_COL
from game.visual_effects import splash
from game.world_effects import boom
from entities.gun_shell import GunShell
from weapons.guns import fire_gun_generic


def fire_paint_ball(**kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	GunShell(pos + Vector(0, -4), direction=direction)
	for t in range(5, 500):
		test_pos = pos + direction * t
		GameVariables().add_extra(test_pos, (255, 250, 50), 3)
		
		if test_pos.y >= MapManager().game_map.get_height() - GameVariables().water_level:
			splash(test_pos, Vector(10, 0))
			break
		if test_pos.x >= MapManager().game_map.get_width() or test_pos.y >= MapManager().game_map.get_height() or test_pos.x < 0 or test_pos.y < 0:
			continue

		at = (int(test_pos.x), int(test_pos.y))
		if MapManager().game_map.get_at(at) == GRD or MapManager().worm_col_map.get_at(at) != SKY_COL or MapManager().objects_col_map.get_at(at) != SKY_COL:
			MapManager().stain(test_pos, sprites.blood, (80, 80), False)
			MapManager().stain(test_pos, sprites.blood, (80, 80), False)
			MapManager().stain(test_pos, sprites.blood, (80, 80), False)
			# if MapManager().worm_col_map.get_at(at) != SKY_COL:
			boom(test_pos, 5)
			break