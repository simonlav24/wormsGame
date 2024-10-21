''' main menu game room. '''

import os
import datetime
from random import choice, randint
import tkinter
from tkinter.filedialog import askopenfile

import pygame

from rooms.room import Room, Rooms, SwitchRoom
from rooms.menu_weapon_setup import WeaponMenu
from gui.menu_gui_new import (
    Gui, MenuAnimator, HORIZONTAL, VERTICAL,
    StackPanel, Text, Button,
    ComboSwitch, Toggle, UpDown,
    ImageDrag, Input,
    LoadBar, ElementAnimator
)

from common import PATH_MAPS, PATH_GENERATED_MAPS, GameGlobals, GameRecord
from common.vector import Vector, vectorCopy
from common.constants import feels
from common.game_config import GameMode, RandomMode, SuddenDeathMode, GameConfig

from game.background import BackGround
from game.map_manager import grab_maps
from game.noise_gen import generate_noise

from weapons.weapon import read_weapon_sets

class MainMenuRoom(Room):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.feel_index = randint(0, len(feels) - 1)

        self.background = BackGround(feels[self.feel_index])
        self.gui = Gui()

        self.map_paths = grab_maps([PATH_MAPS])
        self.image_element: ImageDrag = None

        # self.weapon_sets_list = None
        self.weapon_set_combo: ComboSwitch = None
        self.update_weapon_sets()

        self.main_menu = self.initialize_main_menu()
        self.weapon_menu = WeaponMenu(self.gui)
        self.win_menu: StackPanel = None
        
        self.gui.insert(self.main_menu)

        self.menus_positions = {
            'main_menu': vectorCopy(self.main_menu.pos),
        }

        self.initial_menu_pos = self.main_menu.pos
        self.on_resume()

    def on_resume(self, *args, **kwargs):
        super().on_resume(*args, **kwargs)
        GameGlobals().reset_win_scale()

        record = kwargs.get('input', None)
        
        if record is not None:
            self.win_menu = self.initialize_win_menu(record)
            self.menus_positions['win_menu'] = vectorCopy(self.win_menu.pos)
            self.gui.insert(self.win_menu)
            animator = MenuAnimator(self.win_menu, self.menus_positions['win_menu'] + Vector(0, GameGlobals().win_height), self.menus_positions['win_menu'])
            self.gui.animators.append(animator)
            self.main_menu.pos = self.menus_positions['main_menu'] + Vector(0, GameGlobals().win_height)
            return

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

        elif event == 'weapon_setup_to_main_menu':
            main_menu_pos = self.menus_positions['main_menu']
            weapon_menu_pos = self.menus_positions['weapon_menu']

            main_menu_in = MenuAnimator(self.main_menu, main_menu_pos + Vector(GameGlobals().win_width, 0), main_menu_pos)
            weapon_out = MenuAnimator(self.weapon_menu.get_menu(), weapon_menu_pos, weapon_menu_pos - Vector(GameGlobals().win_width, 0))
            self.gui.animators.append(main_menu_in)
            self.gui.animators.append(weapon_out)
            self.update_weapon_sets()

        elif self.weapon_menu.handle_weapon_events(event, values):
            pass

        elif self.handle_win_events(event, values):
            pass
            
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
            feel_index=values['feel_index'],
            weapon_set=values['weapon_set'],
        )
        self.switch = SwitchRoom(Rooms.GAME_ROOM, True, config)

    def initialize_main_menu(self) -> StackPanel:
        ''' create menu layout '''
        main_menu = StackPanel(name="menu", pos=[40, (GameGlobals().win_height - 196) // 2], size=[GameGlobals().win_width - 80, 196] )
        main_menu.insert(Button(key="play", text="play", custom_size=16))

        options_and_picture_menu = StackPanel(name="options and picture", orientation=HORIZONTAL)

        # options vertical sub menu
        options_menu = StackPanel(name="options")

        sub_mode = StackPanel(orientation=HORIZONTAL, custom_size=15)
        sub_mode.insert(Text(text="game mode"))
        sub_mode.insert(ComboSwitch(key="game_mode", text=list(GameMode)[0].value, items=[mode.value for mode in GameMode]))
        options_menu.add_element(sub_mode)

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
            sub_opt = StackPanel(orientation = HORIZONTAL, custom_size = 15)
            sub_opt.insert(Toggle(key=first[1], text=first[0], value=first[2]))
            sub_opt.insert(Toggle(key=second[1], text=second[0], value=second[2]))
            options_menu.add_element(sub_opt)

        # counters
        counters = [
            {'text': 'worms per team', 'key': 'worms_per_team', 'value': 8, 'lim_min': 1, 'lim_max': 8, 'step_size': 1},
            {'text': 'worm health', 'key': 'worm_initial_health', 'value': 100, 'lim_min': 0, 'lim_max': 1000, 'step_size': 50},
            {'text': 'packs', 'key': 'deployed_packs', 'value': 1, 'lim_min': 0, 'lim_max': 10, 'step_size': 1},
        ]

        for counter in counters:
            sub_opt = StackPanel(orientation=HORIZONTAL)
            sub_opt.insert(Text(text=counter['text']))
            sub_opt.insert(UpDown(
                key=counter['key'], 
                value=counter['value'], 
                lim_min=counter['lim_min'], 
                lim_max=counter['lim_max'],
                step_size=counter['step_size']
            ))
            options_menu.add_element(sub_opt)

        # random turns
        sub_mode = StackPanel(orientation=HORIZONTAL)
        sub_mode.insert(Text(text="random turns"))
        sub_mode.insert(ComboSwitch(key="random_mode", items=[mode.value for mode in RandomMode]))
        options_menu.add_element(sub_mode)

        # sudden death
        sub_mode = StackPanel(orientation=HORIZONTAL)
        sub_mode.insert(Text(text="sudden death"))
        sub_mode.insert(UpDown(key="rounds_for_sudden_death", value=16, text="16", lim_min=0, custom_size=19))
        sub_mode.insert(ComboSwitch(key="sudden_death_style", items=[style.value for style in SuddenDeathMode]))
        options_menu.add_element(sub_mode)

        options_and_picture_menu.add_element(options_menu)

        # map options vertical sub menu
        map_menu = StackPanel(name="map menu", orientation=VERTICAL)
        self.image_element = ImageDrag(key="map_path", image=choice(self.map_paths))
        map_menu.insert(self.image_element)

        # map buttons
        sub_map = StackPanel(orientation = HORIZONTAL, custom_size=15)
        sub_map.insert(Button(key="random_image", text="random"))
        sub_map.insert(Button(key="browse", text="browse"))
        sub_map.insert(Button(key="generate", text="generate"))

        map_menu.add_element(sub_map)

        # recolor & ratio
        sub_map = StackPanel(orientation = HORIZONTAL, custom_size = 15)
        sub_map.insert(Toggle(key="is_recolor", text="recolor", value=False))
        sub_map.insert(Text(text="ratio"))
        sub_map.insert(Input(key="map_ratio", text="enter ratio", eval_type='int', default_value=512))

        map_menu.add_element(sub_map)
        options_and_picture_menu.add_element(map_menu)
        main_menu.add_element(options_and_picture_menu)

        # weapons setup
        sub_weapons = StackPanel(orientation=HORIZONTAL, custom_size=14)
        sub_weapons.insert(Button(key="weapons setup", text="weapons setup"))

        sub_weapons.insert(Text("weapons set:"))
        self.weapon_set_combo = ComboSwitch(name="weapon_combo", key="weapon_set")
        sub_weapons.insert(self.weapon_set_combo)
        self.update_weapon_sets()
        main_menu.add_element(sub_weapons)

        sub_more = StackPanel(orientation=HORIZONTAL, custom_size=14)
        sub_more.insert(Button(key="scoreboard", text="score board"))
        sub_more.insert(UpDown(text="background color", key="feel_index", value=self.feel_index, values=[i for i in range(len(feels))], show_value=False, generate_event=True))
        main_menu.add_element(sub_more)
        
        sub_more = StackPanel(orientation=HORIZONTAL, custom_size=14)
        sub_more.insert(Button(key="exit", text="exit"))
        main_menu.add_element(sub_more)

        return main_menu

    def update_weapon_sets(self) -> None:
        self.weapon_sets_list = read_weapon_sets()
        if self.weapon_set_combo is None:
            return
        
        weapon_sets_names = [dictionary['name'] for dictionary in self.weapon_sets_list]
        weapon_sets_names.insert(0, 'default')

        self.weapon_set_combo.update_items(weapon_sets_names)

    def on_weapon_setup(self):
        weapon_menu = self.weapon_menu.get_menu()
        if weapon_menu is None:
            self.weapon_menu.initialize_weapon_menu()

            self.menus_positions['weapon_menu'] = vectorCopy(self.weapon_menu.get_menu().pos)
            self.gui.insert(self.weapon_menu.get_menu())
        
        main_menu_pos = self.menus_positions['main_menu']
        weapon_menu_pos = self.menus_positions['weapon_menu']

        main_menu_out = MenuAnimator(self.main_menu, main_menu_pos, main_menu_pos + Vector(GameGlobals().win_width, 0))
        weapon_in = MenuAnimator(self.weapon_menu.get_menu(), weapon_menu_pos + Vector(-GameGlobals().win_width, 0), weapon_menu_pos)

        self.gui.animators.append(main_menu_out)
        self.gui.animators.append(weapon_in)



    def initialize_win_menu(self, record: GameRecord) -> StackPanel:
        end_menu = StackPanel(name="end_menu", pos=[GameGlobals().win_width // 2  - GameGlobals().win_width//4, (GameGlobals().win_height - 160)//2], size=[GameGlobals().win_width // 2, 160])
        end_menu.insert(Text(text="Game Over", custom_size=15))
        if record.winning_team != '':
            end_menu.insert(Text(text=f'team {record.winning_team} won the game!'))
        else:
            end_menu.insert(Text(text="its a tie!"))

        end_menu.insert(Text(text=f'most damage dealt: {record.most_damage} by {record.damager}', custom_size=15))
        
        if record.game_mode != GameMode.BATTLE.value:
            max_points = max([team[2] for team in record.points])
            for team_name, team_color, team_score in record.points:
                score_stack = StackPanel(orientation=HORIZONTAL, custom_size=15)
                score_stack.insert(Text(text=team_name, custom_size=50))
                bar = score_stack.insert(LoadBar(value = 0, color=team_color, max_value=max_points))
                end_menu.add_element(score_stack)
                bar_animator = ElementAnimator(bar, 0, team_score, duration = GameGlobals().fps, time_offset=1 * GameGlobals().fps)
                self.gui.animators.append(bar_animator)

        end_menu.insert(Button(key="win_menu_to_main_menu", text="continue"))

        return end_menu

    def handle_win_events(self, event, values) -> bool:
        if event == 'win_menu_to_main_menu':
            main_menu_pos = self.menus_positions['main_menu']
            win_menu_pos = self.menus_positions['win_menu']

            main_menu_in = MenuAnimator(self.main_menu, main_menu_pos + Vector(GameGlobals().win_width, 0), main_menu_pos)
            win_menu_out = MenuAnimator(self.win_menu, win_menu_pos, win_menu_pos - Vector(GameGlobals().win_width, 0))
            self.gui.animators.append(main_menu_in)
            self.gui.animators.append(win_menu_out)


def browse_file():
    root = tkinter.Tk()
    root.withdraw()
    file = askopenfile(mode ='r', filetypes =[('Image Files', '*.png')])
    if file is not None: 
        return file.name

def test_record() -> GameRecord:
    return GameRecord(
            winning_team='mo',
            game_mode=GameMode.BATTLE.value,
            time=1290,
            most_damage=156,
            damager='ron',
            points=[('row', (255,0,0), 10), ('your', (255,255,0), 11), ('boat', (255,0,255), 5)],
    )
