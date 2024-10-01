
''' common interfaces, definitions and utilities '''

from typing import Protocol, List
from pydantic import BaseModel
import pygame

from common.vector import *
from common.constants import ColorType, Sickness, DamageType

# paths
PATH_ASSETS = r'./assets'
PATH_MAPS = r'./assets/worms_maps'
PATH_GENERATED_MAPS = r'./assets/worms_maps/generated_maps'

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

	def damage(self, value: int, damage_type: DamageType=DamageType.HURT, kill: bool=False) -> None:
		...


class EntityWormTool(Entity):
    def activate(self) -> None:
        ...
    
    def release(self) -> None:
        ...


class EntityWorm(EntityPhysical):
	''' a object with position and velocity '''
	name_str: str
	is_boom_affected: bool
	facing: int
	alive: bool

	def dieded(self, cause: DamageType=DamageType.HURT):
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
	
	def get_tool(self) -> EntityWormTool:
		...
	
	def set_tool(self, tool: EntityWormTool) -> None:
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

	def on_turn_begin(self):
		...
	
	def on_turn_end(self):
		...

	def on_deploy(self):
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

	def win_bonus(self) -> int:
		return 0
	
	def is_game_over(self) -> bool:
		...
	
	def is_game_over(self) -> bool:
		return False
	
	def is_points_game(self) -> bool:
		return False
	
	def debug_print(self) -> str:
		return ''


class CycleObserver(Protocol):
	def on_turn_end(self) -> None:
		...
	
	def on_turn_begin(self) -> None:
		...



class IComment(Entity):
	def comment(self, text_dict) -> None:
		...


class EntityPlant(Entity):
	def rotate(self, angle: float) -> None:
		...

	def mutate(self) -> None:
		...


class EntityLightSource(Entity):
	light_radius: int


class InterfaceEventHandler(Protocol):
	def handle_event(self, event):
		...


class EntityElectrocuted(EntityPhysical):
	def electrocute(self) -> None:
		...


class Camera:
	def __init__(self, pos):
		self.pos = pos
		self.radius = 1

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