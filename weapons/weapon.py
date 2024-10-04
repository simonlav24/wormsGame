
from enum import Enum
from pydantic import BaseModel

from common import ArtifactType, ColorType


class WeaponStyle(Enum):
    CHARGABLE = 0
    GUN = 1
    PUTABLE = 2
    CLICKABLE = 3
    UTILITY = 4
    WORM_TOOL = 5
    SPECIAL = 6


class WeaponCategory(Enum):
    MISSILES = 0
    GRENADES = 1
    GUNS = 2
    FIREY = 3
    BOMBS = 4
    TOOLS = 5
    AIRSTRIKE = 6
    LEGENDARY = 7
    UTILITIES = 8
    ARTIFACTS = 9


weapon_bg_color = {
    WeaponCategory.MISSILES : (255, 255, 255),
    WeaponCategory.GRENADES : (204, 255, 204),
    WeaponCategory.GUNS : (255, 204, 153),
    WeaponCategory.FIREY : (255, 204, 204),
    WeaponCategory.BOMBS : (200, 255, 200),
    WeaponCategory.TOOLS : (224, 224, 235),
    WeaponCategory.AIRSTRIKE : (204, 255, 255),
    WeaponCategory.LEGENDARY : (255, 255, 102),
    WeaponCategory.UTILITIES : (254, 254, 254),
    WeaponCategory.ARTIFACTS : (255, 255, 101),
}


class Weapon(BaseModel):
    ''' weapon base model '''
    index: int
    name: str
    style: WeaponStyle
    category: WeaponCategory
    initial_amount: int
    is_fused: bool = False
    round_delay: int = 0
    artifact: ArtifactType = ArtifactType.NONE
    draw_hint: bool = False
    shots: int = 1
    burst: bool = False
    turn_ending: bool = True
    decrease: bool = True
    worm_tool: bool = False
    decrease_on_turn_end: bool = False

    def get_bg_color(self) -> ColorType:
        ''' returns weapons background color '''
        return weapon_bg_color[self.category]