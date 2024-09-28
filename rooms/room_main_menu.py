
import os
from random import choice, randint

import pygame

from rooms.room import Room, Rooms, SwitchRoom
from gui.menu_gui_new import (
    Gui, MenuAnimator, HORIZONTAL, VERTICAL,
    StackPanel, MenuElementText, MenuElementButton,
    MenuElementComboSwitch, MenuElementToggle, MenuElementUpDown,
    MenuElementDragImage, MenuElementInput
)

from common import GameVariables, fonts
from common.constants import feels
from common.game_config import GameMode, RandomMode, SuddenDeathMode, GameConfig

from game.background import BackGround
from game.map_manager import grab_maps

class MainMenuRoom(Room):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.background = BackGround(feels[0])
        self.gui = Gui()

        main_menu = self.initialize_main_menu()
        self.gui.menus.append(main_menu)

    def handle_pygame_event(self, event) -> None:
        ''' handle gui events '''
        super().handle_pygame_event(event)
        self.gui.handle_pygame_event(event)

    def step(self) -> None:
        super().step()
        self.background.step()
        self.gui.step()

        gui_event, gui_values = self.gui.get_event_values()
        self.handle_gui_events(gui_event, gui_values)
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        self.background.draw(win)
        self.gui.draw(win)

    def handle_gui_events(self, event, values):
        if event is None:
            return
        if event == 'play':
            self.on_play(values)

    def on_play(self, values):
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
            is_recolor=values['is_recolor']
        )
        self.switch = SwitchRoom(Rooms.GAME_ROOM, True, config)
        

    def initialize_main_menu(self) -> StackPanel:
        ''' create menu layout '''
        mainMenu = StackPanel(name="menu", pos=[40, (GameVariables().win_height - 196) // 2], size=[GameVariables().win_width - 80, 196], register=True)
        mainMenu.insert(MenuElementButton(key="play", text="play", customSize=16))

        optionsAndPictureMenu = StackPanel(name="options and picture", orientation=HORIZONTAL)

        # options vertical sub menu
        optionsMenu = StackPanel(name="options")

        subMode = StackPanel(orientation=HORIZONTAL, customSize=15)
        subMode.insert(MenuElementText(text="game mode"))
        subMode.insert(MenuElementComboSwitch(key="game_mode", text=list(GameMode)[0].value, items=[mode.value for mode in GameMode]))
        optionsMenu.addElement(subMode)

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
            subOpt = StackPanel(orientation = HORIZONTAL, customSize = 15)
            subOpt.insert(MenuElementToggle(key=first[1], text=first[0], value=first[2]))
            subOpt.insert(MenuElementToggle(key=second[1], text=second[0], value=second[2]))
            optionsMenu.addElement(subOpt)

        # counters
        counters = [
            {'text': 'worms per team', 'key': 'worms_per_team', 'value': 8, 'limMin': 1, 'limMax': 8, 'stepSize': 1},
            {'text': 'worm health', 'key': 'worm_initial_health', 'value': 100, 'limMin': 0, 'limMax': 1000, 'stepSize': 50},
            {'text': 'packs', 'key': 'deployed_packs', 'value': 1, 'limMin': 0, 'limMax': 10, 'stepSize': 1},
        ]

        for counter in counters:
            subOpt = StackPanel(orientation=HORIZONTAL)
            subOpt.insert(MenuElementText(text=counter['text']))
            subOpt.insert(MenuElementUpDown(
                key=counter['key'], 
                text=counter['text'], 
                value=counter['value'], 
                limitMax=True,
                limitMin=True, 
                limMin=counter['limMin'], 
                limMax=counter['limMax'],
                stepSize=counter['stepSize']
            ))
            optionsMenu.addElement(subOpt)

        # random turns
        subMode = StackPanel(orientation=HORIZONTAL)
        subMode.insert(MenuElementText(text="random turns"))
        subMode.insert(MenuElementComboSwitch(key="random_mode", items=[mode.value for mode in RandomMode]))
        optionsMenu.addElement(subMode)

        # sudden death
        subMode = StackPanel(orientation=HORIZONTAL)
        subMode.insert(MenuElementText(text="sudden death"))
        subMode.insert(MenuElementUpDown(key="rounds_for_sudden_death", value=16, text="16", limitMin=True, limMin=0, customSize=19))
        subMode.insert(MenuElementComboSwitch(key="sudden_death_style", items=[style.value for style in SuddenDeathMode]))
        optionsMenu.addElement(subMode)

        optionsAndPictureMenu.addElement(optionsMenu)

        # map options vertical sub menu
        mapMenu = StackPanel(name="map menu", orientation=VERTICAL)
        mapMenu.insert(MenuElementDragImage(key="map_path", image=choice(grab_maps(['assets/worms_maps', 'assets/more_maps']))))

        # map buttons
        subMap = StackPanel(orientation = HORIZONTAL, customSize=15)
        subMap.insert(MenuElementButton(key="random_image", text="random"))
        subMap.insert(MenuElementButton(key="browse", text="browse"))
        subMap.insert(MenuElementButton(key="generate", text="generate"))

        mapMenu.addElement(subMap)

        # recolor & ratio
        subMap = StackPanel(orientation = HORIZONTAL, customSize = 15)
        subMap.insert(MenuElementToggle(key="is_recolor", text="recolor", value=False))
        subMap.insert(MenuElementText(text="ratio"))
        subMap.insert(MenuElementInput(key="map_ratio", text="enter ratio", evaluatedType='int'))

        mapMenu.addElement(subMap)
        optionsAndPictureMenu.addElement(mapMenu)
        mainMenu.addElement(optionsAndPictureMenu)

        # weapons setup
        subweapons = StackPanel(orientation=HORIZONTAL, customSize=14)
        subweapons.insert(MenuElementButton(key="weapons setup", text="weapons setup"))
        weaponsSets = ['default']

        if os.path.exists("./assets/weaponsSets"):
            for file in os.listdir("./assets/weaponsSets"):
                weaponsSets.append(file.split(".")[0])

        subweapons.insert(MenuElementText(text="weapons set:"))
        subweapons.insert(MenuElementComboSwitch(name="weapon_combo", key="weapon_set", items=weaponsSets))
        mainMenu.addElement(subweapons)

        subMore = StackPanel(orientation=HORIZONTAL, customSize=14)
        subMore.insert(MenuElementButton(key="scoreboard", text="score board"))
        mainMenu.addElement(subMore)
        
        subMore = StackPanel(orientation=HORIZONTAL, customSize=14)
        subMore.insert(MenuElementButton(key="exit", text="exit"))
        mainMenu.addElement(subMore)

        # background feel menu
        feelIndex = randint(0, len(feels) - 1)
        bgMenu = StackPanel(pos=[GameVariables().win_width - 20, GameVariables().win_height - 20], size=[20, 20], register=True)
        bgMenu.insert(MenuElementUpDown(text="bg", key="feel_index", value=feelIndex, values=[i for i in range(len(feels))], showValue=False))

        return mainMenu