

from random import choice, randint
from typing import List
import pygame

from gui.menu_gui_new import (
    Gui, MenuAnimator, HORIZONTAL, VERTICAL,
    StackPanel, Text, Button,
    ComboSwitch, Toggle, UpDown,
    ImageDrag, Input, ImageButton,
    LoadBar, ElementAnimator, SurfElement
)
from common import PATH_MAPS, PATH_GENERATED_MAPS, GameGlobals, PATH_SPRITE_ATLAS, GameRecord
from common.vector import Vector, tup2vec, vectorCopy
from common.constants import feels
from common.game_config import GameMode, RandomMode, SuddenDeathMode, GameConfig

from common.team_data import TeamData, read_teams, read_teams_play, create_worm_surf


def sprite_index_to_rect(index):
    return (index % 8) * 16, (index // 8) * 16, 16, 16


class TeamsMenu:
    def __init__(self, gui: Gui):
        self.gui = gui
        self.menu = None
        self.teams: List[TeamData] = []
        self.team_combos: List[ComboSwitch] = []
        self.name_inputs: List[Input] = []
        self.current_team_edit: TeamData = None

    def get_menu(self) -> StackPanel:
        return self.menu

    def initialize_menu(self) -> StackPanel:

        size = Vector(GameGlobals().win_width - 30, GameGlobals().win_height - 30)
        pos = tup2vec(GameGlobals().win.get_size()) // 2 - size // 2
        menu = StackPanel(orientation=VERTICAL, name="weapons", size=size, pos=pos )
        
        teams = read_teams()
        self.teams = {team.team_name: team for team in teams}
        teams_in_play = read_teams_play()
        names = [team.team_name for team in teams]

        columns = StackPanel(orientation=HORIZONTAL)
        column_teams_selection = StackPanel(orientation=VERTICAL)
        column_teams_selection.insert(Text('teams in game'))
        
        teams_in_order = teams_in_play.copy()
        for i in range(8):
            row = StackPanel(orientation=HORIZONTAL)

            is_playing = True
            team = None
            team_data = None
            if len(teams_in_order) == 0:
                is_playing = False
            else:
                team = teams_in_order.pop(0)
                team_data = self.teams[team]

            row.insert(Toggle(text=' ', key=f'toggle_{i}', value=is_playing, custom_size=16))
            combo = ComboSwitch(items=names, initial_item=team)
            self.team_combos.append(combo)
            row.insert(combo)
            row.insert(Button(key=f'edit_{i}', text='edit', custom_size=30))

            column_teams_selection.insert(row)
        columns.insert(column_teams_selection)
        
        columns.insert(Text(' ', custom_size=8))

        column_worms_edit = StackPanel(orientation=VERTICAL)
        column_worms_edit.insert(Text('edit worms'))

        team_name_row = StackPanel(orientation=HORIZONTAL)
        team_name_row.insert(Text('team name:'))
        team_name_row.insert(Input(text='new team', key=f'team_name_input'))
        column_worms_edit.insert(team_name_row)

        team_hat_row = StackPanel(orientation=HORIZONTAL)
        team_hat_row.insert(UpDown())

        for i in range(8):
            row = StackPanel(orientation=HORIZONTAL)
            row.insert(Text(f'{i + 1}.', custom_size=16))
            input_box = Input(text='name', key=f'name_{i}')
            self.name_inputs.append(input_box)
            row.insert(input_box)
            column_worms_edit.insert(row)
        columns.insert(column_worms_edit)

        menu.insert(columns)

        menu.insert(Button(text='save', key='save_team', custom_size=16))
        menu.insert(Button(text='create new team', key='create_new_team', custom_size=16))
        menu.insert(Button(text='back', key='teams_to_main', custom_size=16))

        self.menu = menu
        return menu
    
    def handle_events(self, event, values) -> bool:
        if event is None:
            return False

        elif event.startswith('edit_'):
            index = int(event.replace('edit_', ''))
            combo = self.team_combos[index]
            team_name = combo.get_value()
            self.current_team_edit = self.teams[team_name]
            self.refresh_edit_team()

        else:
            return False
        return True

    def save_team(self):
        pass

    def refresh_edit_team(self):
        for i in range(8):
            name = self.current_team_edit.names[i]
            self.name_inputs[i].set_value(name)
            