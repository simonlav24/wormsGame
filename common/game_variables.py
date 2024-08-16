
from pydantic import BaseModel
from typing import List, Dict
import pygame

from common.game_config import GameConfig
from common import SingletonMeta, ColorType, Entity, EntityOnMap
from common.constants import WHITE

from common.vector import Vector

class WorldPhysics:
    ''' holds physics related data '''
    def __init__(self) -> None:
        self.global_gravity: float = 0.2
        self.wind: float = 0.0


class InitialVariables(BaseModel):
    water_level: int = 50
    draw_health_bar: bool = True
    all_wind_affected: bool = False
    allow_air_strikes: bool = True

    hud_color: ColorType = WHITE


class GameVariables(metaclass=SingletonMeta):
    ''' holds common game variables to be globally accessed'''
    def __init__(self) -> None:
        self.initial_variables: InitialVariables = InitialVariables()
        self.physics: WorldPhysics = WorldPhysics()
        self.config: GameConfig = None

        # multipliers
        self.damage_mult = 0.8
        self.fall_damage_mult = 1.0
        self.boom_radius_mult = 1.0
        self.wind_mult = 1.5
        self.damp_mult = 1.5

        self.time_overall = 0
        self.fps = 30
        self.dt = 1.0

        self.cam_pos: Vector = Vector(0,0)
        self.cam_track: EntityOnMap = None

        self.win_width = 0
        self.win_height = 0

        self.water_level = self.initial_variables.water_level
        self.water_color = (255,255,255)

        self.mega_weapon_trigger = False
        self.fuse_time = 2 * self.fps

        self._non_pysicals: List[Entity] = []
        self._non_pysicals_to_remove: List[Entity] = []
    
    def register_non_physical(self, entity: Entity) -> None:
        self._non_pysicals.append(entity)

    def unregister_non_physical(self, entity: Entity) -> None:
        self._non_pysicals_to_remove.append(entity)

    def step_non_physicals(self) -> None:
        try:
            for entity in self._non_pysicals_to_remove:
                self._non_pysicals.remove(entity)
        except Exception as e:
            print(e)
        self._non_pysicals_to_remove.clear()

        for entity in self._non_pysicals:
            entity.step()
    
    def draw_non_physicals(self, win: pygame.Surface) -> None:
        for entity in self._non_pysicals:
            entity.draw(win)


def point2world(point):
	''' point in vector space to point in world map space '''
	return (int(point[0]) - int(GameVariables().cam_pos[0]), int(point[1]) - int(GameVariables().cam_pos[1]))


if __name__ == '__main__':
    g = GameVariables()
    print(g.config)