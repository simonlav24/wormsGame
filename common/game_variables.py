
from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Tuple

import pygame

from common.game_config import GameConfig
from common import SingletonMeta, ColorType, Entity, EntityPhysical, EntityWorm
from common.constants import WHITE, GameState, RIGHT

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


class DataBase:
    def __init__(self) -> None:
        # updating lists
        self.non_physicals: List[Entity] = []
        self.non_physicals_remove: List[Entity] = []

        self.physicals: List[EntityPhysical] = []
        self.physicals_remove: List[EntityPhysical] = []

        # functional lists
        self.worms: List[EntityWorm] = []
        self.debries: List[EntityPhysical] = []


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
        self.cam_track: EntityPhysical = None
        self.scale_factor = 3
        self.scale_range = (1,3)

        self.win_width = 0
        self.win_height = 0

        self.water_level = self.initial_variables.water_level
        self.water_color = (255,255,255)

        self.mega_weapon_trigger = False
        self.fuse_time = 2 * self.fps

        self.database = DataBase()

        self.game_stable = False
        self.game_stable_counter = 0
        self.game_turn_count = 0

        self.game_state = GameState.RESET
        self.game_next_state = GameState.RESET
        self.player_in_control = False
        self.player_can_move = True
        self.player_can_shoot = False

        self.continuous_fire = False
        self.weapon_hold: pygame.Surface = pygame.Surface((16,16), pygame.SRCALPHA)
        self.point_target: Vector = Vector(-100, -100)
        self.girder_size: int = 50
        self.girder_angle: int = 0
        self.airstrike_direction = RIGHT

        # refactor later
        self.extra = []
        # those are for laser only
        self.layers_circles = []
        self.layers_lines = []

    
    def register_non_physical(self, entity: Entity) -> None:
        self.database.non_physicals.append(entity)

    def unregister_non_physical(self, entity: Entity) -> None:
        self.database.non_physicals_remove.append(entity)

    def register_physical(self, entity: EntityPhysical) -> None:
        self.database.physicals.append(entity)

    def unregister_physical(self, entity: EntityPhysical) -> None:
        self.database.physicals_remove.append(entity)

    def move_to_back_physical(self, entity: EntityPhysical) -> None:
        self.database.physicals.remove(entity)
        self.database.physicals.insert(0, entity)

    def step_physicals(self) -> None:
        try:
            for entity in self.database.physicals_remove:
                self.database.physicals.remove(entity)
        except Exception as e:
            print(e)
        self.database.physicals_remove.clear()

        for entity in self.database.physicals:
            entity.step()
            if not entity.stable:
                self.game_distable()

    def step_non_physicals(self) -> None:
        try:
            for entity in self.database.non_physicals_remove:
                self.database.non_physicals.remove(entity)
        except Exception as e:
            print(e)
        self.database.non_physicals_remove.clear()

        for entity in self.database.non_physicals:
            entity.step()
    
    def draw_non_physicals(self, win: pygame.Surface) -> None:
        for entity in self.database.non_physicals:
            entity.draw(win)
    
    def get_physicals(self) -> List[EntityPhysical]:
        return self.database.physicals

    def get_worms(self) -> List[EntityWorm]:
        return self.database.worms

    def get_debries(self) -> List[EntityPhysical]:
        return self.database.debries

    def game_distable(self):
        self.game_stable = False
        self.game_stable_counter = 0

    # refactor later
    def add_extra(self, pos, color = (255,255,255), delay = 5, absolute = False):
        self.extra.append((pos[0], pos[1], color, delay, absolute))

    def draw_extra(self, win):
        extraNext = []
        for i in self.extra:
            if not i[4]:
                win.fill(i[2], (point2world((i[0], i[1])),(1,1)))
            else:
                win.fill(i[2], ((i[0], i[1]),(1,1)))
            if i[3] > 0:
                extraNext.append((i[0], i[1], i[2], i[3]-1, i[4]))
        self.extra = extraNext
    
    def draw_layers(self, win):
        layersLinesNext = []

        for i in self.layers_lines:
            pygame.draw.line(win, i[0], point2world(i[1]), point2world(i[2]), i[3])
            if i[4]:
                layersLinesNext.append((i[0], i[1], i[2], i[3], i[4]-1))
        self.layers_lines = layersLinesNext

        for j in self.layers_circles:
            for i in j:
                pygame.draw.circle(win, i[0], point2world(i[1]), int(i[2]))
        self.layers_circles = [[],[],[]]

    


def point2world(point) -> Tuple[int, int]:
	''' point in vector space to point in world map space '''
	return (int(point[0]) - int(GameVariables().cam_pos[0]), int(point[1]) - int(GameVariables().cam_pos[1]))

def mouse_pos_in_world() -> Vector:
    mouse_pos = pygame.mouse.get_pos()
    return Vector(mouse_pos[0] / GameVariables().scale_factor + GameVariables().cam_pos[0],
                   mouse_pos[1] / GameVariables().scale_factor + GameVariables().cam_pos[1])

if __name__ == '__main__':
    g = GameVariables()
    print(g.config)