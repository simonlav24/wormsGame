

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

from common.constants import Sickness
from common.game_config import GameConfig

class GameModelBase(BaseModel):
    class_name: str | None = None
    pos: List[float]

class WormModel(GameModelBase):
    health: int
    alive: bool
    name_str: str
    team_name: str
    sick: Sickness
    shoot_angle: float
    facing: int

class PlantModel(GameModelBase):
    angle: float


class GameSaveStateModel(BaseModel):
    game_config: GameConfig

    current_team_name: str
    current_turn_worm: str

    ground_map: str

    objects: List[Union[PlantModel, WormModel, GameModelBase]]

    time_overall : int
    game_turn_count: int
    game_round_count: int
