

from typing import List
import pygame

from gui.menu_gui_new import (
    Gui, HORIZONTAL, VERTICAL,
    StackPanel, Text, Button,
    UpDown, Input, ImageButton,
)
from common import GameGlobals, PATH_SPRITE_ATLAS
from common.vector import Vector, tup2vec
from weapons.weapon import Weapon, read_weapons, save_weapon_set


def sprite_index_to_rect(index):
	return (index % 8) * 16, (index // 8) * 16, 16, 16


class WeaponMenu:
    def __init__(self, gui: Gui):
        self.weapons_list: List[Weapon] = []
        self.weapon_up_downs: List[UpDown] = []
        self.gui = gui
        self.menu = None

    def get_menu(self) -> StackPanel:
        return self.menu

    def initialize_menu(self) -> StackPanel:
        
        self.weapons_list = read_weapons()
        self.weapon_up_downs: List[UpDown] = []

        size = Vector(GameGlobals().win_width - 30, GameGlobals().win_height - 30)
        pos = tup2vec(GameGlobals().win.get_size()) // 2 - size // 2
        menu = StackPanel(orientation=VERTICAL, name="weapons", size=size, pos=pos )
        
        weapon_sprites = pygame.image.load(PATH_SPRITE_ATLAS)
        index_offset = 72

        mapping = {-1: "inf"}

        weapon_index = 0
        done = False

        while not done:
            sub = StackPanel(orientation=HORIZONTAL, custom_size=16)
            for _ in range(6):
                weapon = self.weapons_list[weapon_index]
                if weapon.name == 'flare':
                    done = True
                    break
                weapon_index += 1
                pic = ImageButton(custom_size=16, tooltip=weapon.name)
                bg_color = weapon.get_bg_color()
                pic.set_image(weapon_sprites, sprite_index_to_rect(weapon.index + index_offset), background=bg_color)

                sub.insert(pic)
                combo = UpDown(key=weapon.name, lim_min=-1, lim_max=10, value=weapon.initial_amount, mapping=mapping)
                self.weapon_up_downs.append({'weapon': weapon, 'element': combo})
                sub.insert(combo)
                if weapon_index >= len(self.weapons_list):
                    break
            if not done:
                menu.insert(sub)

        sub = StackPanel(orientation=HORIZONTAL)
        sub.insert(Text(text="weapon set name:"))
        sub.insert(Input(key="file_name", text="enter name"))
        sub.insert(Button(key="save_weapons", text="save"))
        menu.insert(sub)

        sub = StackPanel(orientation=HORIZONTAL)
        sub.insert(Button(key="weapon_setup_to_main_menu", text="back"))
        sub.insert(Button(key="default_weapons", text="default"))
        sub.insert(Button(key="zero_weapons", text="zero"))
        menu.insert(sub)

        self.menu = menu
        return menu
    
    def handle_events(self, event, values) -> bool:
        if event is None:
            return False

        elif event == 'save_weapons':
            weapon_dict = {'name': values['file_name']}
            for element_dict in self.weapon_up_downs:
                weapon_dict[element_dict['weapon'].index] = element_dict['element'].value
            save_weapon_set(weapon_dict, values['file_name'])
            self.gui.toast(f'saved {values["file_name"]}')
        
        elif event == 'default_weapons':
            for element_dict in self.weapon_up_downs:
                initial_amount = element_dict['weapon'].initial_amount
                element_dict['element'].update_value(initial_amount)
        
        elif event == 'zero_weapons':
            for element_dict in self.weapon_up_downs:
                element_dict['element'].update_value(0)

        else:
            return False
        return True

