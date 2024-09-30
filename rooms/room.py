
from typing import Any
from enum import Enum
from dataclasses import dataclass

import pygame

class Rooms(Enum):
    MAIN_MENU = 'main_menu'
    GAME_ROOM = 'game_room'
    WEAPON_SETTINGS = 'weapon_settings'
    PAUSE_MENU = 'pause_menu'
    WIN_MENU = 'win_menu'
    EXIT = 'exit'


@dataclass
class SwitchRoom:
    next_room: Rooms
    craete_new_room: bool
    room_input: Any


class Room:
    def __init__(self, *args, **kwargs) -> None:
        self.switch: SwitchRoom = None

    def handle_pygame_event(self, event) -> None:
        ...

    def step(self) -> None:
        ...

    def draw(self, win: pygame.Surface) -> None:
        ...

    def is_ready_to_switch(self) -> bool:
        return self.switch is not None
