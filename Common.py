
from abc import ABC, abstractmethod
from typing import Tuple
import pygame
from math import sin, pi
from vector import *

import globals

# paths
PATH_ASSETS = r'./assets'

class Entity(ABC):
    ''' an object that has pos, step and draw '''
    def __init__(self, pos=(0,0)):
        self.pos = pos
    
    @abstractmethod
    def step(self) -> None:
        ...
    
    @abstractmethod
    def draw(self) -> None:
        ...

def clamp(value, upper, lower):
	if value > upper:
		value = upper
	if value < lower:
		value = lower
	return value

# color utilities

ColorType = Tuple[int, int, int]

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

def point2world(point):
	''' point in vector space to point in world map space '''
	return (int(point[0]) - int(globals.game_manager.camPos[0]), int(point[1]) - int(globals.game_manager.camPos[1]))

def drawTarget(pos):
	offset = sin(globals.time_manager.timeOverall / 5) * 4 + 3
	triangle = [Vector(5 + offset,0), Vector(10 + offset,-2), Vector(10 + offset,2)]
	for i in range(4):
		angle = i * pi / 2
		triangle = [triangle[0].rotate(angle), triangle[1].rotate(angle), triangle[2].rotate(angle)]
		pygame.draw.polygon(globals.game_manager.win, (255,0,0), [point2world(pos + j) for j in triangle])