

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

from common.constants import Sickness

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

    current_team_name: str
    current_turn_worm: str

    ground_map: str

    objects: List[Union[PlantModel, WormModel, GameModelBase]]
