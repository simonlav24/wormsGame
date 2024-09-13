
from abc import ABC, abstractmethod
from typing import Protocol, List
from pydantic import BaseModel
import pygame

from common.vector import *
from common.constants import ColorType, Sickness

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


class TeamData(BaseModel):
	''' team data '''
	team_name: str
	color: ColorType
	names: List[str]
	hats: str


class Entity(Protocol):
    ''' an object that has step and draw '''
	
    def step(self) -> None:
        pass
    
    def draw(self, win: pygame.Surface) -> None:
        pass


class EntityPhysical(Entity):
	''' a physical entity '''
	pos: Vector
	vel: Vector
	acc: Vector
	stable: bool
	radius: float
	health: int
	damp: float
	is_fall_affected: bool

	def remove_from_game(self):
		...

	def damage(self, value, damageType=0):
		...

class EntityWorm(EntityPhysical):
	''' a object with position and velocity '''
	name_str: str
	is_boom_affected: bool
	facing: int
	alive: bool

	def dieded(self):
		...
	
	def get_team_data(self) -> TeamData:
		...
	
	def get_shooting_direction(self) -> Vector:
		...
	
	def drawCursor(self, win: pygame.Surface) -> None:
		...

	def get_shooting_angle(self) -> float:
		...
	
	def give_point(self, points: int) -> None:
		...
	
	def sicken(self, sickness: Sickness=Sickness.SICK):
		...


class AutonomousEntity(EntityPhysical):
	def engage(self) -> bool:
		...

	def done(self) -> None:
		...


class GamePlayMode:
	''' handles game mode '''
	def __init__(self):
		...

	def add_mode(self, mode: 'GamePlayMode'):
		...

	def on_game_init(self):
		...

	def on_cycle(self):
		...

	def step(self):
		...

	def draw(self, win: pygame.Surface):
		...

	def hud_draw(self, win: pygame.Surface):
		...

	def on_worm_damage(self, worm: EntityWorm, damage: int):
		...

	def on_worm_death(self, worm: EntityWorm):
		...

	def win_bonus(self):
		...


class IComment(Entity):
	def comment(self, text_dict):
		...


class EntityPlant(Entity):
	def rotate(self, angle: float):
		...

	def mutate(self):
		...

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

# math utilities

def clamp(value, upper, lower):
	if value > upper:
		value = upper
	if value < lower:
		value = lower
	return value

def seek(obj: EntityPhysical, target: Vector, max_speed: float, max_force: float ,arrival=False):
	''' calculate force to move towards object with velocity '''
	force = tup2vec(target) - obj.pos
	desiredSpeed = max_speed
	if arrival:
		slowRadius = 50
		distance = force.getMag()
		if (distance < slowRadius):
			force.setMag(desiredSpeed)
	force.setMag(desiredSpeed)
	force -= obj.vel
	force.limit(max_force)
	return force

def flee(obj: EntityPhysical, target: Vector, max_speed: float, max_force: float):
	return seek(obj, target, max_speed, max_force) * -1