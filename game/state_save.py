
import json

from common import GameVariables, GameState


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

    # save to file
    with open(path, 'w') as file:
        json.dump(save_game_state, file, indent=4)

def load_game(path: str) -> None:
    '''load game state from a file'''

    with open(path, 'r') as file:
        save_game_state = json.load(file)

    # load game variables

    # load teams


    # load physicals
    for obj_data in save_game_state['objects']:
        class_name = obj_data.pop('class_name')
        class_ = globals()[class_name]
        obj = class_(**obj_data)
        obj.deserialize(obj_data)
        GameVariables().get_physicals().append(obj)

    # load non physicals


    # load map


