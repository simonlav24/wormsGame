
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import pygame

from rooms.room import Room, Rooms, SwitchRoom
from gui.menu_gui_new import (
    Gui, StackPanel, Text, Button, HORIZONTAL, LoadBar
)

from common import GameGlobals
from common.vector import Vector

@dataclass
class PauseRoomInfo:
    teams_score: Tuple[Dict[str, Any]] = ()
    round_count: int = -1
    

class PauseRoom(Room):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = Gui()

        self.info: PauseRoomInfo = kwargs.get('input', None)
        pause_menu = self.initialize_pause_menu()
        self.gui.insert(pause_menu)

    def handle_pygame_event(self, event) -> None:
        ''' handle gui events '''
        super().handle_pygame_event(event)
        self.gui.handle_pygame_event(event)

    def step(self) -> None:
        super().step()
        self.gui.step()

        gui_event, gui_values = self.gui.listen()
        if gui_event is not None:
            self.handle_gui_events(gui_event, gui_values)
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        self.gui.draw(win)

    def handle_gui_events(self, event, values):
        if event is None:
            return
        if event == 'resume':
            self.switch = SwitchRoom(Rooms.GAME_ROOM, False, None)
        if event == 'to_main_menu':
            self.switch = SwitchRoom(Rooms.MAIN_MENU, True, None)

    def initialize_pause_menu(self) -> StackPanel:
        ''' create pause layout '''
        pauseMenu = StackPanel(name="endMenu", pos=[GameGlobals().win_width//2  - GameGlobals().win_width//4, 40], size=[GameGlobals().win_width // 2, 160])
        pauseMenu.insert(Text(text="Game paused"))
        pauseMenu.insert(Text(text=f"Round {self.info.round_count}", custom_size=15))

        if len(self.info.teams_score) > 0:
            max_score = max(team['score'] for team in self.info.teams_score)
            if max_score == 0:
                max_score = 1
            for team in self.info.teams_score:
                teamScore = StackPanel(orientation=HORIZONTAL, custom_size=15)
                teamScore.insert(Text(text=team['name'], custom_size=50))
                teamScore.insert(LoadBar(value=team['score'], color=team['color'], max_value=max_score))
                pauseMenu.add_element(teamScore)

        # if "missions" in args.keys():
        # 	pauseMenu.insert(MENU_TEXT, text="- missions -")
        # 	for mission in args["missions"]:
        # 		pauseMenu.insert(MENU_TEXT, text=mission)

        pauseMenu.insert(Button(key="resume", text="resume"))
        pauseMenu.insert(Button(key="to_main_menu", text="back to main menu"))
        pauseMenu.pos = Vector(GameGlobals().win_width//2 - pauseMenu.size[0]//2, GameGlobals().win_height//2 - pauseMenu.size[1]//2)

        return pauseMenu
