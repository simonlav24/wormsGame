
import pygame
from typing import Dict, Tuple
from math import sin, pi

from common import GameVariables, sprites, point2world
from common.vector import Vector

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
        pos = Vector(pos[0] / GameVariables().scale_factor , pos[1] / GameVariables().scale_factor)
        win.blit(surf, (int(pos[0] - surf.get_width()/2), int(pos[1] - surf.get_height()/2)))