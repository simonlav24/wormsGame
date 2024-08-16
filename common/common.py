
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Protocol
import pygame
from math import sin, pi

from common.vector import *
from common.constants import ColorType, sprites

# paths
PATH_ASSETS = r'./assets'

class SingletonMeta(type):
    ''' singleton metaclass '''
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Entity(Protocol):
    ''' an object that has step and draw '''
	
    def step(self) -> None:
        pass
    
    def draw(self, win: pygame.Surface) -> None:
        pass


class EntityOnMap(Protocol):
    ''' a object with position  '''
    pos: Vector

# color utilities

def grayen(color: ColorType) -> ColorType:
	''' grays color '''
	return tuple(i//5 + 167 for i in color)

def desaturate(color: ColorType, value: float=0.5) -> ColorType:
	''' desaturates color by value '''
	grey = color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.144
	return tuple(grey * value + i * (1 - value) for i in color)

def darken(color: ColorType) -> ColorType:
	''' darkens color '''
	return tuple(max(i - 30,0) for i in color)

# drawing utilities

weapon_name_to_index: Dict[str, int] = None

def blit_weapon_sprite(dest: pygame.Surface, pos: Tuple[int, int], weapon_name: str):
    weapon_index = weapon_name_to_index[weapon_name]
    x = weapon_index % 8
    y = 9 + weapon_index // 8
    rect = (x * 16, y * 16, 16, 16)
    dest.blit(sprites.sprite_atlas, pos, rect)

# math utilities

def clamp(value, upper, lower):
	if value > upper:
		value = upper
	if value < lower:
		value = lower
	return value

