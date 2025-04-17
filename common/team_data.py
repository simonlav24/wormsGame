
from typing import List
import json

import pygame

from pydantic import BaseModel
from common.constants import ColorType, PATH_TEAMS_LIST, PATH_TEAMS_PLAY, sprites

class TeamData(BaseModel):
    ''' team data '''
    team_name: str
    color: ColorType
    names: List[str]
    hats: str


def read_teams() -> List[TeamData]:
    with open(PATH_TEAMS_LIST, 'r') as file:
        teams = json.load(file)
    data_list = [TeamData.model_validate(data) for data in teams]
    return data_list


def create_worm_surf(data: TeamData) -> pygame.Surface:
    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 206, 167), (8, 8), 4.5)
    surf.blit(sprites.sprite_atlas, (0,0), (0,0,16,16))
    return surf
