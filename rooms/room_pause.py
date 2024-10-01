

import pygame

from rooms.room import Room, Rooms, SwitchRoom
from gui.menu_gui_new import (
    Gui, StackPanel, MenuElementText, MenuElementButton,
)

from common import GameVariables
from common.vector import Vector

class PauseRoom(Room):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = Gui()

        pause_menu = self.initialize_pause_menu()
        self.gui.menus.append(pause_menu)

    def handle_pygame_event(self, event) -> None:
        ''' handle gui events '''
        super().handle_pygame_event(event)
        self.gui.handle_pygame_event(event)

    def step(self) -> None:
        super().step()
        self.gui.step()

        gui_event, gui_values = self.gui.get_event_values()
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
        pauseMenu = StackPanel(name="endMenu", pos=[GameVariables().win_width//2  - GameVariables().win_width//4, 40], size=[GameVariables().win_width // 2, 160])
        pauseMenu.insert(MenuElementText(text="Game paused"))

        # if "showPoints" in args.keys() and args["showPoints"]:
        # 	maxPoints = max([team.points for team in args["teams"]])
        # 	if maxPoints == 0:
        # 		maxPoints = 1
        # 	for team in args["teams"]:
        # 		teamScore = Menu(orientation=HORIZONTAL, customSize=15)
        # 		teamScore.insert(MENU_TEXT, text=team.name, customSize=50)
        # 		teamScore.insert(MENU_LOADBAR, value = team.points, color=team.color, maxValue=maxPoints)
        # 		pauseMenu.addElement(teamScore)

        # if "missions" in args.keys():
        # 	pauseMenu.insert(MENU_TEXT, text="- missions -")
        # 	for mission in args["missions"]:
        # 		pauseMenu.insert(MENU_TEXT, text=mission)

        pauseMenu.insert(MenuElementButton(key="resume", text="resume"))
        pauseMenu.insert(MenuElementButton(key="to_main_menu", text="back to main menu"))
        pauseMenu.pos = Vector(GameVariables().win_width//2 - pauseMenu.size[0]//2, GameVariables().win_height//2 - pauseMenu.size[1]//2)

        return pauseMenu
