
from typing import Any, Dict, List
from enum import Enum

from pydantic import BaseModel

from common.team_data import TeamData

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
    NONE = 'none'
    IN_TEAM = 'in team'
    COMPLETE = 'complete'

class SuddenDeathMode(Enum):
    ALL = 'all'
    FLOOD = 'flood'
    PLAGUE = 'plague'
    NONE = 'none'

class GameConfig(BaseModel):
    ''' game parameters and configuration '''
    game_mode: GameMode = GameMode.BATTLE
    random_mode: RandomMode = RandomMode.NONE

    game_load_state_path: str | None = None

    option_cool_down: bool = True
    option_artifacts: bool = True
    option_closed_map: bool = False
    option_forts: bool = False
    option_digging: bool = False
    option_darkness: bool = False

    teams: List[TeamData] = []
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
    