
from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Tuple
from random import uniform

import pygame

from common.game_config import GameConfig
from common import SingletonMeta, GameGlobals, ColorType, Entity, EntityPhysical, EntityWorm, AutonomousEntity, GamePlayMode, IComment, EntityPlant, CycleObserver, EntityLightSource, InterfaceEventHandler, EntityElectrocuted, IHud, calc_water_color, FireObserver, IStateMachine, IStats, GameRecord
from common.constants import WHITE, GameState, RIGHT, feels

from common.vector import Vector
from game.sfx import Sfx, SfxIndex

class WorldPhysics:
    ''' holds physics related data '''
    def __init__(self) -> None:
        self.global_gravity: float = 0.2
        self.wind: float = uniform(-1.0, 1.0)


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
        self.exploding_props: List[EntityPhysical] = []
        self.obscuring_objects: List[EntityPhysical] = []
        self.autonomous_objects: List[AutonomousEntity] = []
        self.targets: List[EntityPhysical] = []
        self.plants: List[EntityPlant] = []
        self.cycle_observers: List[CycleObserver] = []
        self.fire_observers: List[FireObserver] = []
        self.light_sources: List[EntityLightSource] = []
        self.pygame_event_listeners: List[InterfaceEventHandler] = []
        self.elecrocuted: List[EntityElectrocuted] = []
        self.fire_particles: List[EntityPhysical] = []


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
        self.dt = 1.0

        self.cam_pos: Vector = Vector(0,0)
        self.cam_track: EntityPhysical = None

        self.water_level = self.initial_variables.water_level
        self.water_rise_amount = 0
        self.water_color = (255, 255, 255)

        self.mega_weapon_trigger = False
        self.fuse_time = 2 * self.fps

        self.database = DataBase()
        self.stats: IStats = None

        self.game_stable = False
        self.game_turn_count = 0
        self.game_round_count = 0
        self.turns_in_round = 0
        self.num_of_teams = 0

        self.state_machine: IStateMachine = None
        self.game_state = GameState.RESET
        self.is_sudden_death = False
        self.player_can_move = True

        self.game_mode: GamePlayMode = None
        self.commentator: IComment = None
        self.hud: IHud = None

        self.continuous_fire = False
        self.weapon_hold: pygame.Surface = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.point_target: Vector = Vector(-100, -100)
        self.girder_size: int = 50
        self.girder_angle: int = 0
        self.airstrike_direction = RIGHT
        self.aim_aid = False

        self._player: EntityWorm = None

        # refactor later
        self.extra = []
        # those are for laser only
        self.layers_circles = []
        self.layers_lines = []

        self.game_end = False
        self.game_record: GameRecord = None

    @property
    def fps(self):
        return GameGlobals().fps

    @property
    def player(self):
        return self._player
    
    @player.setter
    def player(self, value):
        self._player = value
    
    def set_config(self, config: GameConfig) -> None:
        self.config = config
        self.water_color = calc_water_color(feels[config.feel_index])

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
        for entity in self.database.physicals:
            entity.step()
            if not entity.stable:
                self.game_distable()
        
        try:
            for entity in self.database.physicals_remove:
                self.database.physicals.remove(entity)
        except Exception as e:
            print(e)
        self.database.physicals_remove.clear()

    def step_non_physicals(self) -> None:
        try:
            for entity in self.database.non_physicals_remove:
                self.database.non_physicals.remove(entity)
        except Exception as e:
            print(e)
        self.database.non_physicals_remove.clear()

        for entity in self.database.non_physicals:
            entity.step()
    
    def step(self):
        if self.water_rise_amount > 0:
            self.game_distable()
            self.water_level += 1
            self.water_rise_amount -= 1

    def draw_non_physicals(self, win: pygame.Surface) -> None:
        for entity in self.database.non_physicals:
            entity.draw(win)
    
    def get_physicals(self) -> List[EntityPhysical]:
        return self.database.physicals

    def get_worms(self) -> List[EntityWorm]:
        return self.database.worms

    def get_debries(self) -> List[EntityPhysical]:
        return self.database.debries

    def get_targets(self) -> List[EntityPhysical]:
        return self.database.targets

    def get_exploding_props(self) -> List[EntityPhysical]:
        return self.database.exploding_props

    def get_obscuring_objects(self) -> List[EntityPhysical]:
        return self.database.obscuring_objects

    def get_plants(self) -> List[EntityPlant]:
        return self.database.plants

    def game_distable(self) -> None:
        self.game_stable = False
        self.state_machine.distable()

    def register_autonomous(self, object: AutonomousEntity) -> None:
        self.database.autonomous_objects.append(object)

    def unregister_autonomous(self, object: AutonomousEntity) -> None:
        self.database.autonomous_objects.remove(object)

    def engage_autonomous(self) -> bool:
        ''' engages autonomous objects, if any engages return true '''
        any_engaged = False
        for obj in self.database.autonomous_objects:
            if obj.can_engage():
                any_engaged |= obj.engage()
                self.cam_track = obj
        return any_engaged

    def get_event_handlers(self) -> List[InterfaceEventHandler]:
        return self.database.pygame_event_listeners

    def handle_event(self, event) -> None:
        for handler in self.get_event_handlers():
            handler.handle_event(event)

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

    def on_turn_begin(self):
        for observer in self.database.cycle_observers:
            observer.on_turn_begin()
    
    def on_turn_end(self):
        for observer in self.database.cycle_observers:
            observer.on_turn_end()
    
    def register_cycle_observer(self, obj: CycleObserver):
        self.database.cycle_observers.append(obj)
    
    def unregister_cycle_observer(self, obj: CycleObserver):
        self.database.cycle_observers.remove(obj)
    
    def register_fire_observer(self, obj: FireObserver):
        self.database.fire_observers.append(obj)
    
    def unregister_fire_observer(self, obj: FireObserver):
        self.database.fire_observers.remove(obj)

    def get_light_sources(self) -> List[EntityLightSource]:
        return self.database.light_sources

    def get_electrocuted(self) -> List[EntityElectrocuted]:
        return self.database.elecrocuted

    def debug_print(self) -> None:
        output = '# non_physicals:\n'
        for i in self.database.non_physicals:
            output += f'\t{i}\n'
        
        output += '\n# physicals:\n'
        for i in self.database.physicals:
            output += f'\t{i} (stable={i.stable})\n'

        output += self.game_mode.debug_print()

        output += f'{self.game_state=}\n'


        with open('debug.txt', 'w+') as file:
            file.write(output)
        
    def can_player_shoot(self) -> bool:
        ''' is player's state '''
        return self.game_state == GameState.PLAYER_PLAY
    
    def is_player_in_control(self) -> bool:
        return self.game_state in [GameState.PLAYER_PLAY, GameState.PLAYER_RETREAT]

    def rise_water(self, amount: int) -> None:
        self.water_rise_amount = amount
    
    def on_fire(self, **kwargs) -> bool:
        result = False
        for observer in self.database.fire_observers:
            result |= observer.on_fire(**kwargs)
        return result
    
    def update_state(self, state: GameState = None) -> None:
        self.state_machine.update(state)

    def register_fire_particle(self, particle: EntityPhysical) -> None:
        self.database.fire_particles.append(particle)
        Sfx().loop(SfxIndex.FIRE_LOOP)

    def unregister_fire_particle(self, particle: EntityPhysical) -> None:
        self.database.fire_particles.remove(particle)
        if not self.database.fire_particles:
            Sfx().stop(SfxIndex.FIRE_LOOP, 1000)

def point2world(point) -> Tuple[int, int]:
	''' point in vector space to point in world map space '''
	return (int(point[0]) - int(GameVariables().cam_pos[0]), int(point[1]) - int(GameVariables().cam_pos[1]))

def mouse_pos_in_world() -> Vector:
    mouse_pos = pygame.mouse.get_pos()
    return Vector(mouse_pos[0] / GameGlobals().scale_factor + GameVariables().cam_pos[0],
                   mouse_pos[1] / GameGlobals().scale_factor + GameVariables().cam_pos[1])

if __name__ == '__main__':
    g = GameVariables()
    print(g.config)