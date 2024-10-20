

from random import choice, randint
from typing import List
import pygame

from gui.menu_gui_new import (
    Gui, MenuAnimator, HORIZONTAL, VERTICAL,
    StackPanel, Text, Button,
    ComboSwitch, Toggle, UpDown,
    ImageDrag, Input, ImageButton,
    LoadBar, ElementAnimator
)
from common import PATH_MAPS, PATH_GENERATED_MAPS, GameGlobals, PATH_SPRITE_ATLAS, GameRecord
from common.vector import Vector, tup2vec, vectorCopy
from common.constants import feels
from common.game_config import GameMode, RandomMode, SuddenDeathMode, GameConfig



def sprite_index_to_rect(index):
	return (index % 8) * 16, (index // 8) * 16, 16, 16


class TeamsMenu:
    def __init__(self, gui: Gui):
        self.gui = gui
        self.menu = None

    def get_menu(self) -> StackPanel:
        return self.menu

    def initialize_menu(self) -> StackPanel:

        size = Vector(GameGlobals().win_width - 30, GameGlobals().win_height - 30)
        pos = tup2vec(GameGlobals().win.get_size()) // 2 - size // 2
        menu = StackPanel(orientation=VERTICAL, name="weapons", size=size, pos=pos )
        
        teams = ['-', 'reds', 'yellows', 'greens', 'blues']
        columns = StackPanel(orientation=HORIZONTAL)
        column_teams_selection = StackPanel(orientation=VERTICAL)
        column_teams_selection.insert(Text('teams in game'))
        for i in range(8):
            row = StackPanel(orientation=HORIZONTAL)
            row.insert(Toggle(text=' ', key=f'toggle_{i}', custom_size=16))
            row.insert(ComboSwitch(items=teams))
            row.insert(Button(key=f'edit_{i}', text='edit', custom_size=30))

            column_teams_selection.insert(row)
        columns.insert(column_teams_selection)
        
        columns.insert(Text(' ', custom_size=8))

        column_worms_edit = StackPanel(orientation=VERTICAL)
        column_worms_edit.insert(Text('edit worms'))
        for i in range(8):
            row = StackPanel(orientation=HORIZONTAL)
            row.insert(Text(f'{i + 1}.', custom_size=16))
            row.insert(Input(text='name', key=f'name_{i}'))
            column_worms_edit.insert(row)
        columns.insert(column_worms_edit)

        menu.insert(columns)
        menu.insert(Button(text='back', key='teams_to_main'))

        self.menu = menu
        return menu
    
    def handle_events(self, event, values) -> bool:
        if event is None:
            return False

        else:
            return False
        return True

