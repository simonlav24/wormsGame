
from typing import Any
from pydantic import BaseModel
from Constants import *
from enum import Enum

class GameMode(Enum):
    BATTLE = 'battle'
    POINTS = 'points'
    TERMINATOR = 'terminator'
    TARGETS = 'targets'
    DAVID_AND_GOLIATH = 'david vs goliath'
    CAPTURE_THE_FLAG = 'ctf'
    ARENA = 'arena'
    MISSIONS = 'missions'

class RandomMode(Enum):
    NONE = 0
    IN_TEAM = 1
    COMPLETE = 2

class SuddenDeathMode(Enum):
    ALL = 0
    FLOOD = 1
    PLAGUE = 2

class GameConfig(BaseModel):
    ''' game parameters and configuration '''
    game_mode: GameMode = GameMode.BATTLE
    random_mode: RandomMode = RandomMode.NONE

    option_cool_down: bool = False
    option_artifacts: bool = False
    option_closed_map: bool = False
    option_forts: bool = False
    option_digging: bool = False
    option_darkness: bool = False

    worms_per_team: int = 8
    worm_initial_health: int = 100
    deployed_packs: int = 1

    rounds_for_sudden_death: int = 16

    map_path: str = None
    map_ratio: int = 512
    is_recolor: bool = False
    sudden_death_style: SuddenDeathMode = SuddenDeathMode.ALL
    weapon_set: str = None

    feel_index: int = -1
    