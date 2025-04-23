
import io
import json
import base64

import pygame

from common import GameVariables, GameState, Serializable

from game.map_manager import MapManager
from game.team_manager import TeamManager
from game.models import GameSaveStateModel


def surface_to_base64(surface):
    byte_io = io.BytesIO()
    pygame.image.save(surface, byte_io, "PNG")
    return base64.b64encode(byte_io.getvalue()).decode('utf-8')

def base64_to_surface(b64_str):
    byte_io = io.BytesIO(base64.b64decode(b64_str))
    byte_io.seek(0)
    return pygame.image.load(byte_io).convert_alpha()


def save_game(path: str) -> None:
    '''save game state to a file'''

    if not GameVariables().game_state == GameState.PLAYER_PLAY:
        print("Game is not in playable state, cannot save.")
        return

    # save map
    surf = pygame.Surface((MapManager().ground_map.get_width(), MapManager().ground_map.get_height() - GameVariables().water_level), pygame.SRCALPHA)
    surf.blit(MapManager().ground_map, (0, 0))
    ground_map_str = surface_to_base64(surf)

    save_game_state = GameSaveStateModel(
        current_team_name=TeamManager().current_team.name,
        current_turn_worm=GameVariables().player.name_str,
        objects=[],
        ground_map=ground_map_str,
    )

    # save objects
    for obj in GameVariables().get_physicals() + GameVariables().database.non_physicals:
        if isinstance(obj, Serializable):
            model = obj.serialize()
            model.class_name = obj.__class__.__name__
            save_game_state.objects.append(model)

    # save to file
    with open(path, "w+") as file:
        file.write(save_game_state.model_dump_json(indent=2))
        print(f'saved game {path}')


def load_game(path: str) -> GameSaveStateModel:
    '''load game state from a file'''

    with open(path, 'r') as f:
        data = f.read()

    model = GameSaveStateModel.model_validate_json(data)

    return model




