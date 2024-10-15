
import os
import datetime
from random import choice, randint
from typing import List
import tkinter
from tkinter.filedialog import askopenfile

import pygame

from rooms.room import Room, Rooms, SwitchRoom
from gui.menu_gui_new import (
    Gui, MenuAnimator, HORIZONTAL, VERTICAL,
    StackPanel, Text, Button,
    ComboSwitch, Toggle, UpDown,
    ImageDrag, Input, ImageButton
)

from common import PATH_MAPS, PATH_GENERATED_MAPS, GameGlobals, PATH_SPRITE_ATLAS
from common.vector import Vector, tup2vec, vectorCopy
from common.constants import feels
from common.game_config import GameMode, RandomMode, SuddenDeathMode, GameConfig

from game.background import BackGround
from game.map_manager import grab_maps
from game.noise_gen import generate_noise

from weapons.weapon import read_weapons, ArtifactType

class MainMenuRoom(Room):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.feel_index = randint(0, len(feels) - 1)

        self.background = BackGround(feels[self.feel_index])
        self.gui = Gui()

        self.map_paths = grab_maps([PATH_MAPS])
        self.image_element: ImageDrag = None

        self.main_menu = self.initialize_main_menu()
        self.weapon_menu: StackPanel = None
        self.gui.insert(self.main_menu)

        self.menus_positions = {
            'main_menu': vectorCopy(self.main_menu.pos),
        }

        self.initial_menu_pos = self.main_menu.pos
        animator = MenuAnimator(self.main_menu, self.initial_menu_pos + Vector(0, GameGlobals().win_height), self.initial_menu_pos)
        self.gui.animators.append(animator)

    def on_resume(self):
        super().on_resume()
        GameGlobals().reset_win_scale()
        animator = MenuAnimator(self.main_menu, self.initial_menu_pos + Vector(0, GameGlobals().win_height), self.initial_menu_pos)
        self.gui.animators.append(animator)

    def handle_pygame_event(self, event) -> None:
        ''' handle gui events '''
        super().handle_pygame_event(event)
        self.gui.handle_pygame_event(event)

    def step(self) -> None:
        super().step()
        self.background.step()
        self.gui.step()

        gui_event, gui_values = self.gui.listen()
        if gui_event is not None:
            self.handle_gui_events(gui_event, gui_values)
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        self.background.draw(win)
        self.background.draw_secondary(win)
        self.gui.draw(win)

    def handle_gui_events(self, event, values):
        if event is None:
            return
        
        elif event == 'play':
            self.gui.animators.append(
                MenuAnimator(
                    self.main_menu,
                    self.main_menu.pos,
                    self.main_menu.pos - Vector(0, GameGlobals().win_height),
                    trigger=self.on_play,
                    args=[values],
                )
            )
            # self.on_play(values)
        elif event == 'exit':
            self.switch = SwitchRoom(Rooms.EXIT, False, None)
        
        elif event == 'random_image':
            self.image_element.set_image(choice(self.map_paths))
        
        elif event == "generate":
            width, height = 800, 300
            noise = generate_noise(width, height)
            x = datetime.datetime.now()
            if not os.path.exists(PATH_GENERATED_MAPS):
                os.mkdir(PATH_GENERATED_MAPS)
            output_path = os.path.join(
                PATH_GENERATED_MAPS,
                f'noise{x.day}{x.month}{x.year % 100}{x.hour}{x.minute}.png'
            )
            pygame.image.save(noise, output_path)
            self.image_element.set_image(output_path)
        
        elif event == 'browse':
            filepath = browse_file()
            if filepath:
                self.image_element.set_image(filepath)
        
        elif event == 'feel_index':
            self.feel_index = values['feel_index']
            self.background.set_feel_color(feels[self.feel_index])
        
        elif event == 'weapons setup':
            self.on_weapon_setup()

        else:
            self.handle_weapon_events(event, values)
        

    def on_play(self, values):
        ''' on press play button '''
        config = GameConfig(
            option_artifacts=values['option_artifacts'],
            option_closed_map=values['option_closed_map'],
            option_cool_down=values['option_cool_down'],
            option_darkness=values['option_darkness'],
            option_digging=values['option_digging'],
            option_forts=values['option_forts'],
            game_mode=GameMode(values['game_mode']),
            worm_initial_health=values['worm_initial_health'],
            worms_per_team=values['worms_per_team'],
            deployed_packs=values['deployed_packs'],
            rounds_for_sudden_death=values['rounds_for_sudden_death'],
            sudden_death_style=SuddenDeathMode(values['sudden_death_style']),
            random_mode=RandomMode(values['random_mode']),
            map_path=values['map_path'],
            is_recolor=values['is_recolor'],
            map_ratio=values['map_ratio'],
            feel_index=values['feel_index']
        )
        self.switch = SwitchRoom(Rooms.GAME_ROOM, True, config)

    def initialize_main_menu(self) -> StackPanel:
        ''' create menu layout '''
        mainMenu = StackPanel(name="menu", pos=[40, (GameGlobals().win_height - 196) // 2], size=[GameGlobals().win_width - 80, 196] )
        mainMenu.insert(Button(key="play", text="play", custom_size=16))

        optionsAndPictureMenu = StackPanel(name="options and picture", orientation=HORIZONTAL)

        # options vertical sub menu
        optionsMenu = StackPanel(name="options")

        subMode = StackPanel(orientation=HORIZONTAL, custom_size=15)
        subMode.insert(Text(text="game mode"))
        subMode.insert(ComboSwitch(key="game_mode", text=list(GameMode)[0].value, items=[mode.value for mode in GameMode]))
        optionsMenu.add_element(subMode)

        config = GameConfig()

        # toggles
        toggles = [
            ('cool down', 'option_cool_down', config.option_cool_down),
            ('artifacts', 'option_artifacts', config.option_artifacts),
            ('closed map', 'option_closed_map', config.option_closed_map),
            ('forts', 'option_forts', config.option_forts),
            ('digging', 'option_digging', config.option_digging),
            ('darkness', 'option_darkness', config.option_darkness)
        ]
        
        for i in range(0, len(toggles) - 1, 2):
            first = toggles[i]
            second = toggles[i + 1]
            subOpt = StackPanel(orientation = HORIZONTAL, custom_size = 15)
            subOpt.insert(Toggle(key=first[1], text=first[0], value=first[2]))
            subOpt.insert(Toggle(key=second[1], text=second[0], value=second[2]))
            optionsMenu.add_element(subOpt)

        # counters
        counters = [
            {'text': 'worms per team', 'key': 'worms_per_team', 'value': 8, 'lim_min': 1, 'lim_max': 8, 'step_size': 1},
            {'text': 'worm health', 'key': 'worm_initial_health', 'value': 100, 'lim_min': 0, 'lim_max': 1000, 'step_size': 50},
            {'text': 'packs', 'key': 'deployed_packs', 'value': 1, 'lim_min': 0, 'lim_max': 10, 'step_size': 1},
        ]

        for counter in counters:
            subOpt = StackPanel(orientation=HORIZONTAL)
            subOpt.insert(Text(text=counter['text']))
            subOpt.insert(UpDown(
                key=counter['key'], 
                value=counter['value'], 
                limit_max=True,
                limit_min=True, 
                lim_min=counter['lim_min'], 
                lim_max=counter['lim_max'],
                step_size=counter['step_size']
            ))
            optionsMenu.add_element(subOpt)

        # random turns
        subMode = StackPanel(orientation=HORIZONTAL)
        subMode.insert(Text(text="random turns"))
        subMode.insert(ComboSwitch(key="random_mode", items=[mode.value for mode in RandomMode]))
        optionsMenu.add_element(subMode)

        # sudden death
        subMode = StackPanel(orientation=HORIZONTAL)
        subMode.insert(Text(text="sudden death"))
        subMode.insert(UpDown(key="rounds_for_sudden_death", value=16, text="16", limit_min=True, lim_min=0, custom_size=19))
        subMode.insert(ComboSwitch(key="sudden_death_style", items=[style.value for style in SuddenDeathMode]))
        optionsMenu.add_element(subMode)

        optionsAndPictureMenu.add_element(optionsMenu)

        # map options vertical sub menu
        mapMenu = StackPanel(name="map menu", orientation=VERTICAL)
        self.image_element = ImageDrag(key="map_path", image=choice(self.map_paths))
        mapMenu.insert(self.image_element)

        # map buttons
        subMap = StackPanel(orientation = HORIZONTAL, custom_size=15)
        subMap.insert(Button(key="random_image", text="random"))
        subMap.insert(Button(key="browse", text="browse"))
        subMap.insert(Button(key="generate", text="generate"))

        mapMenu.add_element(subMap)

        # recolor & ratio
        subMap = StackPanel(orientation = HORIZONTAL, custom_size = 15)
        subMap.insert(Toggle(key="is_recolor", text="recolor", value=False))
        subMap.insert(Text(text="ratio"))
        subMap.insert(Input(key="map_ratio", text="enter ratio", eval_type='int', default_value=512))

        mapMenu.add_element(subMap)
        optionsAndPictureMenu.add_element(mapMenu)
        mainMenu.add_element(optionsAndPictureMenu)

        # weapons setup
        subweapons = StackPanel(orientation=HORIZONTAL, custom_size=14)
        subweapons.insert(Button(key="weapons setup", text="weapons setup"))
        weaponsSets = ['default']

        if os.path.exists("./assets/weaponsSets"):
            for file in os.listdir("./assets/weaponsSets"):
                weaponsSets.append(file.split(".")[0])

        subweapons.insert(Text("weapons set:"))
        subweapons.insert(ComboSwitch(name="weapon_combo", key="weapon_set", items=weaponsSets))
        mainMenu.add_element(subweapons)

        subMore = StackPanel(orientation=HORIZONTAL, custom_size=14)
        subMore.insert(Button(key="scoreboard", text="score board"))
        subMore.insert(UpDown(text="background color", key="feel_index", value=self.feel_index, values=[i for i in range(len(feels))], show_value=False, generate_event=True))
        mainMenu.add_element(subMore)
        
        subMore = StackPanel(orientation=HORIZONTAL, custom_size=14)
        subMore.insert(Button(key="exit", text="exit"))
        mainMenu.add_element(subMore)

        return mainMenu

    def initialize_weapon_menu(self) -> StackPanel:

        self.weapons_list = read_weapons()
        self.weapon_up_downs: List[UpDown] = []

        size = Vector(GameGlobals().win_width - 30, GameGlobals().win_height - 30)
        pos = tup2vec(GameGlobals().win.get_size()) // 2 - size // 2
        weapon_menu = StackPanel(orientation=VERTICAL, name="weapons", size=size, pos=pos )
        
        weapon_sprites = pygame.image.load(PATH_SPRITE_ATLAS)
        index_offset = 72

        mapping = {-1: "inf"}

        weapon_index = 0
        done = False

        while not done:
            sub = StackPanel (orientation=HORIZONTAL, custom_size=16)
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
                combo = UpDown(key=weapon.name, limit_min=True, limit_max=True, lim_min=-1, lim_max=10, value=weapon.initial_amount, mapping=mapping)
                self.weapon_up_downs.append({'weapon': weapon, 'element': combo})
                sub.insert(combo)
                if weapon_index >= len(self.weapons_list):
                    break
            if not done:
                weapon_menu.insert(sub)

        sub = StackPanel(orientation=HORIZONTAL)
        sub.insert(Text(text="weapon set name:"))
        sub.insert(Input(key="filename", text="enter name"))
        sub.insert(Button(key="save_weapons", text="save"))
        weapon_menu.insert(sub)

        sub = StackPanel(orientation=HORIZONTAL)
        sub.insert(Button(key="weapon_setup_to_main_menu", text="back"))
        sub.insert(Button(key="default_weapons", text="default"))
        sub.insert(Button(key="zero_weapons", text="zero"))
        weapon_menu.insert(sub)

        return weapon_menu

    def on_weapon_setup(self):
        if self.weapon_menu is None:
            self.weapon_menu = self.initialize_weapon_menu()
            self.menus_positions['weapon_menu'] = vectorCopy(self.weapon_menu.pos)
            self.gui.insert(self.weapon_menu)
        
        main_menu_pos = self.menus_positions['main_menu']
        weapon_menu_pos = self.menus_positions['weapon_menu']

        main_menu_out = MenuAnimator(self.main_menu, main_menu_pos, main_menu_pos + Vector(GameGlobals().win_width, 0))
        weapon_in = MenuAnimator(self.weapon_menu, weapon_menu_pos + Vector(-GameGlobals().win_width, 0), weapon_menu_pos)

        self.gui.animators.append(main_menu_out)
        self.gui.animators.append(weapon_in)

    def handle_weapon_events(self, event, values):
        if event is None:
            return

        elif event == 'weapon_setup_to_main_menu':
            main_menu_pos = self.menus_positions['main_menu']
            weapon_menu_pos = self.menus_positions['weapon_menu']

            main_menu_in = MenuAnimator(self.main_menu, main_menu_pos + Vector(GameGlobals().win_width, 0), main_menu_pos)
            weapon_out = MenuAnimator(self.weapon_menu, weapon_menu_pos, weapon_menu_pos - Vector(GameGlobals().win_width, 0))
            self.gui.animators.append(main_menu_in)
            self.gui.animators.append(weapon_out)
        
        elif event == 'save_weapons':
            print('save weapons tbd')
        
        elif event == 'default_weapons':
            for element_dict in self.weapon_up_downs:
                initial_amount = element_dict['weapon'].initial_amount
                element_dict['element'].update_value(initial_amount)
        
        elif event == 'zero_weapons':
            for element_dict in self.weapon_up_downs:
                element_dict['element'].update_value(0)
        
        
        


def browse_file():
    root = tkinter.Tk()
    root.withdraw()
    file = askopenfile(mode ='r', filetypes =[('Image Files', '*.png')])
    if file is not None: 
        return file.name

def sprite_index_to_rect(index):
	return (index % 8) * 16, (index // 8) * 16, 16, 16