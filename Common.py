
from abc import ABC, abstractmethod
from typing import Tuple

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
