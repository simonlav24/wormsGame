
import pygame
from typing import Dict, Tuple
from math import sin, pi
from random import uniform

from common import GameVariables, sprites, point2world, GameGlobals
from common.vector import *

from game.visual_effects import EffectManager

# drawing utilities

weapon_name_to_index: Dict[str, int] = None


def blit_weapon_sprite(dest: pygame.Surface, pos: Tuple[int, int], weapon_name: str):
    ''' blits weapons sprite of name onto dest surface '''
    weapon_index = weapon_name_to_index[weapon_name]
    x = weapon_index % 8
    y = 9 + weapon_index // 8
    rect = (x * 16, y * 16, 16, 16)
    dest.blit(sprites.sprite_atlas, pos, rect)


def draw_target(win: pygame.Surface, pos: Vector):
    ''' draw target on pos '''
    offset = sin(GameVariables().time_overall / 5) * 4 + 3
    triangle = [Vector(5 + offset,0), Vector(10 + offset,-2), Vector(10 + offset,2)]
    for i in range(4):
        angle = i * pi / 2
        triangle = [triangle[0].rotate(angle), triangle[1].rotate(angle), triangle[2].rotate(angle)]
        pygame.draw.polygon(win, (255,0,0), [point2world(pos + j) for j in triangle])


def draw_girder_hint(win: pygame.Surface):
	''' draw girder hint at mouse position '''
	surf = pygame.Surface((GameVariables().girder_size, 10)).convert_alpha()
	for i in range(GameVariables().girder_size // 16 + 1):
		surf.blit(sprites.sprite_atlas, (i * 16, 0), (64,80,16,16))
	surf.set_alpha(100)
	surf = pygame.transform.rotate(surf, GameVariables().girder_angle)
	pos = pygame.mouse.get_pos()
	pos = Vector(pos[0] / GameGlobals().scale_factor , pos[1] / GameGlobals().scale_factor)
	win.blit(surf, (int(pos[0] - surf.get_width()/2), int(pos[1] - surf.get_height()/2)))


def draw_lightning(win: pygame.Surface, start: Vector, end: Vector, color = (153, 255, 255)):
	''' draw lightning bolt between start and end '''
	radius = 2
	halves = int(dist(end, start) / 8)
	if halves == 0:
		halves = 1
	direction = (end - start)
	direction.setMag(dist(start, end)/halves)
	points = []
	lightings = []
	for t in range(halves):
		if t == 0 or t == halves - 1:
			point = (start + direction * t).vec2tupint()
		else:
			point = ((start + direction * t) + vectorUnitRandom() * uniform(-10,10)).vec2tupint()
		lightings.append(point)
		points.append(point2world(point))

	for i in lightings:
		EffectManager().add_light(vectorCopy(i), 50, [color[0], color[1], color[2], 100])
	if len(points) > 1:
		points.append(point2world(end))
		for i, point in enumerate(points):
			width = int((1 - (i / (len(points) - 1))) * 4) + 1
			if i == len(points) - 1:
				break
			pygame.draw.line(win, color, points[i], points[i+1], width)
	else:
		pygame.draw.lines(win, color, False, [point2world(start), point2world(end)], 2)
	pygame.draw.circle(win, color, point2world(end), int(radius) + 3)


def draw_dir_indicator(win: pygame.Surface, pos: Vector):
	''' draw direction indicator to pos at edge of screen '''
	border = 20
	if not (pos[0] < GameVariables().cam_pos[0] - border / 4 or pos[0] > (Vector(GameGlobals().win_width, GameGlobals().win_height) + GameVariables().cam_pos)[0] + border/4 or pos[1] < GameVariables().cam_pos[1] - border/4 or pos[1] > (Vector(GameGlobals().win_width, GameGlobals().win_height) + GameVariables().cam_pos)[1] + border/4):
		return

	cam = GameVariables().cam_pos + Vector(GameGlobals().win_width//2, GameGlobals().win_height//2)
	direction = pos - cam
	
	intersection = tup2vec(point2world((GameGlobals().win_width, GameGlobals().win_height))) + pos -  Vector(GameGlobals().win_width, GameGlobals().win_height)
	
	intersection[0] = min(max(intersection[0], border), GameGlobals().win_width - border)
	intersection[1] = min(max(intersection[1], border), GameGlobals().win_height - border)
	
	points = [Vector(0,2), Vector(0,-2), Vector(5,0)]
	angle = direction.getAngle()
	
	for point in points:
		point.rotate(angle)
	
	pygame.draw.polygon(win, (255,0,0), [intersection + i + normalize(direction) * 4 * sin(GameVariables().time_overall / 5) for i in points])

