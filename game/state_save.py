
import io
import json
import base64

import pygame

from common import GameVariables, GameState

from game.map_manager import MapManager


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

    save_game_state = {}

    # save game variables

    # save teams


    # save physicals
    objects = []
    for obj in GameVariables().get_physicals():
        class_name = obj.__class__.__name__
        obj_data = {'class_name': class_name}
        obj_data |= obj.serialize()
        objects.append(obj_data)

    save_game_state['objects'] = objects

    # save non physicals


    # save map
    # save_game_state['game_map'] = surface_to_base64(MapManager().game_map)
    save_game_state['ground_map'] = surface_to_base64(MapManager().ground_map)

    # save to file
    with open(path, 'w') as file:
        json.dump(save_game_state, file, indent=4)

def load_game(path: str) -> dict:
    '''load game state from a file'''

    with open(path, 'r') as file:
        save_game_state = json.load(file)

    save_game_state['ground_map'] = base64_to_surface(save_game_state['ground_map'])

    return save_game_state




