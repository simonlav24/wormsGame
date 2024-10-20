
import os
import json
from enum import Enum
from pydantic import BaseModel
from typing import Dict, Callable, Any, List

from common import ArtifactType, ColorType, PATH_WEAPON_LIST, PATH_WEAPON_SETS, PATH_WEAPON_SET

weapon_set_type = Dict[int, int]
weapon_func_type = Dict[str, Callable[[Any], Any]]

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
    can_fail: bool = False

    def get_bg_color(self) -> ColorType:
        ''' returns weapons background color '''
        return weapon_bg_color[self.category]


def read_weapons() -> List[Weapon]:
    ''' reads weapons from weapon-list file and returns list '''
    with open(PATH_WEAPON_LIST, 'r') as file:
        data = json.load(file)
        
    weapons: List[Weapon] = [Weapon.model_validate(weapon) for weapon in data]
    return weapons


def save_weapon_set(weapon_set: weapon_set_type, name: str) -> None:
    ''' save weapon set to file '''
    with open(os.path.join(PATH_WEAPON_SET.replace('__name__', name)), 'w+') as file: 
        json.dump(weapon_set, file)


def read_weapon_sets() -> List[weapon_set_type]:
    ''' read all saved weapon sets and returns a list '''
    output = []
    for weapon_set in os.listdir(PATH_WEAPON_SETS):
        if not weapon_set.endswith('json'):
            continue
        with open(os.path.join(PATH_WEAPON_SETS, weapon_set), 'r') as file:
            data = json.load(file)
            output.append(data)
    return output

def read_weapon_set(name: str) -> weapon_set_type:
    path = os.path.join(PATH_WEAPON_SET.replace('__name__', name))
    if not os.path.exists(path):
        return None
    with open(path, 'r') as file:
        data = json.load(file)
    return data
