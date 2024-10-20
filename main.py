''' main entry point '''

from math import pi, cos, sin
from random import randint, uniform, choice
import traceback

import pygame
import pygame.gfxdraw

from common import *
from common.vector import Vector
from common.game_config import GameMode, RandomMode

from rooms.room import Room, Rooms, SwitchRoom
from rooms.room_main_menu import MainMenuRoom
from rooms.room_pause import PauseRoom, PauseRoomInfo
from rooms.splash_screen import SplashScreenRoom

from game.game_play_mode import (
    GamePlayCompound, 
    TerminatorGamePlay,
    PointsGamePlay,
    TargetsGamePlay,
    DVGGamePlay, 
    CTFGamePlay,
    ArenaGamePlay,
    ArtifactsGamePlay,
    DarknessGamePlay,
	StatsGamePlay,
	MissionsGamePlay
)

from game.state_machine import StateMachine, sudden_death
from game.time_manager import TimeManager
from game.map_manager import MapManager, SKY
from game.background import BackGround
from game.visual_effects import FloatingText
from game.team_manager import TeamManager

from game.world_effects import boom, Earthquake

from game.hud import Commentator, Hud
from gui.radial_menu import RadialMenu, RadialButton

from entities.props import PetrolCan
from entities.deployables import HealthPack, WeaponPack, UtilityPack
from entities.worm import Worm

from weapons.weapon_manager import WeaponManager
from weapons.weapon import weapon_bg_color, WeaponCategory, WeaponStyle
from weapons.missiles import DrillMissile
from weapons.long_bow import LongBow
from weapons.plants import PlantSeed
from weapons.mine import Mine

from weapons.misc.springs import MasterOfPuppets
from weapons.misc.armageddon import Armageddon


class Game:
	def __init__(self, game_config: GameConfig=None):
		self.reset()
		GameVariables().set_config(game_config)
		GameVariables().commentator = Commentator()
		GameVariables().hud = Hud()
		GameVariables().state_machine = StateMachine(self)

		self.evaluate_config(game_config)
		
		WeaponManager()

		self.background = BackGround(feels[GameVariables().config.feel_index], GameVariables().config.option_darkness)
		self.background.set_closed(GameVariables().config.option_closed_map)

		self.cheatCode = "" # cheat code

		self.lstep = 0
		self.lstepmax = GameVariables().config.worms_per_team * 4
		self.loadingSurf = fonts.pixel10.render("Simon's Worms Loading", False, WHITE)

		self.endGameDict = None

		self.imageMjolnir = pygame.Surface((24,31), pygame.SRCALPHA)
		self.imageMjolnir.blit(sprites.sprite_atlas, (0,0), (100, 32, 24, 31))

		self.radial_weapon_menu: RadialMenu = None
		GameVariables().state_machine.update()
	
	def reset(self):
		''' reset all game singletons '''
		GameVariables.reset()
		MapManager.reset()
		TeamManager.reset()
		TimeManager.reset()
		EffectManager.reset()
		WeaponManager.reset()

	def create_new_game(self) -> None:
		''' initialize new game '''

		# create map
		self.create_map()
			
		# check for sky opening for airstrikes
		closed_sky_counter = 0
		for i in range(100):
			if MapManager().is_ground_at((randint(0, MapManager().game_map.get_width()-1), randint(0, 10))):
				closed_sky_counter += 1
		if closed_sky_counter > 50:
			GameVariables().initial_variables.allow_air_strikes = False
			for team in TeamManager().teams:
				for i, _ in enumerate(team.weapon_set):
					if WeaponManager().weapons[i].category == WeaponCategory.AIRSTRIKE:
						team.weapon_set[i] = 0

		# select current team
		TeamManager().current_team = TeamManager().teams[0]
		TeamManager().team_choser = TeamManager().teams.index(TeamManager().current_team)

		# place worms
		self.place_worms_random()
		
		# give random legendary starting weapons:
		WeaponManager().give_extra_starting_weapons()

		# place objects
		if not self.game_config.option_digging:
			amount = randint(2,4)
			for _ in range(amount):
				mine = MapManager().place_object(Mine, None, True)
				mine.damp = 0.1

		amount = randint(2,4)
		for _ in range(amount):
			MapManager().place_object(PetrolCan, None, False)

		if not self.game_config.option_digging:
			amount = randint(0, 2)
			for _ in range(amount):
				MapManager().place_object(PlantSeed, ((0,0), (0,0), 0, PlantMode.VENUS), False)

		# choose starting worm
		starting_worm = TeamManager().current_team.worms.pop(0)
		TeamManager().current_team.worms.append(starting_worm)

		if self.game_config.random_mode != RandomMode.NONE:
			starting_worm = choice(TeamManager().current_team.worms)
		
		GameVariables().player = starting_worm
		GameVariables().cam_track = starting_worm

		# reset time
		TimeManager().time_reset()
		WeaponManager().switch_weapon(WeaponManager().current_weapon)

		# randomize wind
		GameVariables().physics.wind = uniform(-1, 1)

		# handle game mode
		self.init_handle_game_mode()

	def place_worms_random(self) -> None:
		''' create worms and place them randomly '''
		for i in range(self.game_config.worms_per_team * len(TeamManager().teams)):
			if self.game_config.option_forts:
				place = MapManager().get_good_place(div=i)
			else:
				place = MapManager().get_good_place()
			if self.game_config.option_digging:
				pygame.draw.circle(MapManager().game_map, SKY, place, 35)
				pygame.draw.circle(MapManager().ground_map, SKY, place, 35)
				pygame.draw.circle(MapManager().ground_secondary, SKY, place, 30)
			current_team = TeamManager().teams[TeamManager().team_choser]
			new_worm_name = current_team.get_new_worm_name()
			current_team.worms.append(Worm(place, new_worm_name, current_team))
			TeamManager().team_choser = (TeamManager().team_choser + 1) % GameVariables().num_of_teams
			self.lstepper()

	def init_handle_game_mode(self) -> None:
		''' on init, handle game mode parameter and variables '''
		# digging match
		if GameVariables().config.option_digging:
			for _ in range(80):
				mine = MapManager().place_object(Mine, None)
				mine.damp = 0.1
			# more digging
			for team in TeamManager().teams:
				team.ammo(WeaponManager()["minigun"], 5)
				team.ammo(WeaponManager()["drill missile"], 3)
				team.ammo(WeaponManager()["laser gun"], 3)
			GameVariables().config.option_closed_map = True

		GameVariables().game_mode.on_game_init()
	
	def create_map(self) -> None:
		''' create game map '''
		custom_height = 512
		if self.game_config.map_ratio != -1:
			custom_height = self.game_config.map_ratio

		if self.game_config.option_digging:
			MapManager().create_map_digging(custom_height)
		elif 'noise' in self.game_config.map_path:
			MapManager().create_map_image(self.game_config.map_path, custom_height, True)
		else:
			MapManager().create_map_image(self.game_config.map_path, custom_height, self.game_config.is_recolor)
		
	def evaluate_config(self, game_config: GameConfig):
		self.game_config: GameConfig = game_config

		if self.game_config.feel_index == -1:
			self.game_config.feel_index = randint(0, len(feels) - 1)

		GameVariables().game_mode = GamePlayCompound()
		GameVariables().stats = StatsGamePlay()
		GameVariables().game_mode.add_mode(GameVariables().stats)

		game_mode_map = {
			GameMode.TERMINATOR: TerminatorGamePlay(),
			GameMode.POINTS: PointsGamePlay(),
			GameMode.TARGETS: TargetsGamePlay(),
			GameMode.DAVID_AND_GOLIATH: DVGGamePlay(),
			GameMode.CAPTURE_THE_FLAG: CTFGamePlay(),
			GameMode.ARENA: ArenaGamePlay(),
			GameMode.MISSIONS: MissionsGamePlay(GameVariables().stats),
		}

		GameVariables().game_mode.add_mode(game_mode_map.get(self.game_config.game_mode))

		if self.game_config.option_artifacts:
			GameVariables().game_mode.add_mode(ArtifactsGamePlay())
		if self.game_config.option_darkness:
			GameVariables().game_mode.add_mode(DarknessGamePlay())

	def handle_event(self, event) -> bool:
		''' handle pygame event, return true if event handled '''

		if self.radial_weapon_menu:
			self.radial_weapon_menu.handle_event(event)
			menu_event = self.radial_weapon_menu.get_event()
			if menu_event:
				WeaponManager().switch_weapon(menu_event)
				self.radial_weapon_menu = None
				return True
		
		is_handled = WeaponManager().handle_event(event)
		
		return is_handled

	def step(self):
		pass
	
	def lstepper(self):
		...
		# self.lstep += 1
		# pos = (GameGlobals().win_width/2 - self.loadingSurf.get_width()/2, GameGlobals().win_height/2 - self.loadingSurf.get_height()/2)
		# width = self.loadingSurf.get_width()
		# height = self.loadingSurf.get_height()
		# pygame.draw.rect(GameGlobals().win, (255,255,255), ((pos[0], pos[1] + 20), ((self.lstep / self.lstepmax)*width, height)))
		# screen.blit(pygame.transform.scale(GameGlobals().win, screen.get_rect().size), (0,0))
		# pygame.display.update()

	def weapon_menu_init(self):
		current_team = TeamManager().current_team
		
		layout = []

		for category in reversed(list(WeaponCategory)):
			weapons_in_category = WeaponManager().get_weapons_list_of_category(category)
			weapons_in_category = [weapon for weapon in weapons_in_category if current_team.ammo(weapon.index) != 0]
			if len(weapons_in_category) == 0:
				continue
			get_amount = lambda x: str(current_team.ammo(x.index)) if current_team.ammo(x.index) > 0 else ''
			
			sub_layout: List[RadialButton] = []
			for weapon in reversed(weapons_in_category):
				surf_portion = WeaponManager().get_surface_portion(weapon)
				is_enabled = WeaponManager().is_weapon_enabled(weapon)
				button = RadialButton(weapon, weapon.name, get_amount(weapon), weapon_bg_color[category], surf_portion, is_enabled=is_enabled)
				sub_layout.append(button)

			is_enabled = not all(not button.is_enabled for button in sub_layout)
			main_button = RadialButton(weapons_in_category[0], '', '', weapon_bg_color[category], WeaponManager().get_surface_portion(weapons_in_category[0]), sub_layout, is_enabled=is_enabled)
			layout.append(main_button)

		self.radial_weapon_menu = RadialMenu(layout, Vector(GameGlobals().win_width // 2, GameGlobals().win_height // 2))

	def cheat_activate(self, code: str):
		code = code[:-1].lower()
		mouse_pos = mouse_pos_in_world()

		if code == "gibguns":
			for team in TeamManager().teams:
				for i, _ in enumerate(team.weapon_set):
					team.weapon_set[i] = 100
			for weapon in WeaponManager().weapons:
				weapon.round_delay = 0
			GameVariables().config.option_cool_down = False
		elif code == "gibguns1":
			for team in TeamManager().teams:
				for i, _ in enumerate(team.weapon_set):
					team.weapon_set[i] = 1
		elif code == "suddendeath":
			sudden_death()
		elif code == "wind":
			GameVariables().physics.wind = uniform(-1, 1)
		elif code == "goodbyecruelworld":
			boom(GameVariables().player.pos, 100)
		elif code == "armageddon":
			Armageddon()
		elif code[0:5] == "gunme" and len(code) == 6:
			amount = int(code[5])
			for i in range(amount):
				WeaponPack(mouse_pos)
		elif code[0:9] == "utilizeme" and len(code) == 10:
			amount = int(code[9])
			for i in range(amount):
				UtilityPack(mouse_pos)
		elif code == "aspirin":
			HealthPack(mouse_pos)
		elif code == "globalshift":
			for worm in GameVariables().get_worms():
				# if worm in TeamManager().current_team.worms:
					# continue
				worm.gravity = worm.gravity * -1
		elif code == "petrolcan":
			PetrolCan(mouse_pos)
		elif code == "megaboom":
			GameVariables().mega_weapon_trigger = True
		elif code == "comeflywithme":
			TeamManager().current_team.ammo(WeaponManager()["jet pack"], 6)
			TeamManager().current_team.ammo(WeaponManager()["rope"], 6)
			TeamManager().current_team.ammo(WeaponManager()["ender pearl"], 6)
		elif code == "masterofpuppets":
			MasterOfPuppets()
		elif code == "deathtouch":
			pos = Vector(mouse_pos)
			closest = None
			closestDist = 100000
			for worm in GameVariables().get_worms():
				if dist(worm.pos, pos) < closestDist:
					closestDist = dist(worm.pos, pos)
					closest = worm
			if closest:
				closest.damage(1000)


################################################################################ Key bindings
def on_key_press_right():
	GameVariables().player.turn(RIGHT)

def on_key_press_left():
	GameVariables().player.turn(LEFT)

def on_key_press_space():
	# release worm_tool
	if GameVariables().game_state == GameState.PLAYER_RETREAT:
		worm_tool = GameVariables().player.get_tool()
		if worm_tool is not None:
			worm_tool.release()

def on_key_press_tab():
	if WeaponManager().current_weapon.name == "drill missile":
		DrillMissile.mode = not DrillMissile.mode
		if DrillMissile.mode:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "drill mode", (20,20,20))
		else:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "rocket mode", (20,20,20))
		WeaponManager().render_weapon_count()
	elif WeaponManager().current_weapon.name == "long bow":
		LongBow._sleep = not LongBow._sleep
		if LongBow._sleep:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "sleeping", (20,20,20))
		else:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "regular", (20,20,20))
	elif WeaponManager().current_weapon.name == "girder":
		GameVariables().girder_angle += 45
		if GameVariables().girder_angle == 180:
			GameVariables().girder_size = 100
		if GameVariables().girder_angle == 360:
			GameVariables().girder_size = 50
			GameVariables().girder_angle = 0
	elif WeaponManager().current_weapon.is_fused:
		GameVariables().fuse_time += GameVariables().fps
		if GameVariables().fuse_time > GameVariables().fps * 4:
			GameVariables().fuse_time = GameVariables().fps
		string = "delay " + str(GameVariables().fuse_time // GameVariables().fps) + " sec"
		FloatingText(GameVariables().player.pos + Vector(0, -5), string, (20, 20, 20))
		WeaponManager().render_weapon_count()
	elif WeaponManager().current_weapon.category == WeaponCategory.AIRSTRIKE:
		GameVariables().airstrike_direction *= -1
 
def on_key_press_test():
	''' test '''
	GameVariables().debug_print()
	# print(WeaponManager().weapon_director.actors)

def on_key_press_enter():
	# jump
	if GameVariables().player.stable and GameVariables().player.health > 0:
		GameVariables().player.vel += GameVariables().player.get_shooting_direction() * JUMP_VELOCITY
		GameVariables().player.stable = False

################################################################################ Main

class GameRoom(Room):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		config = kwargs.get('input')
		self.game_manager = Game(config)

		# refactor these
		damage_this_turn = GameVariables().stats.get_stats()['damage_this_turn']
		self.damageText = (damage_this_turn, fonts.pixel5_halo.render(str(int(damage_this_turn)), False, GameVariables().initial_variables.hud_color))
	
	def handle_pygame_event(self, event) -> None:
		''' handle pygame events in game '''
		super().handle_pygame_event(event)
		is_handled = self.game_manager.handle_event(event)
		if is_handled:
			return
		GameVariables().handle_event(event)
		if event.type == pygame.QUIT:
			self.switch = SwitchRoom(Rooms.EXIT, False, None)
			return
		# mouse click event
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # left click (main)
			pass

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)
			pass
		
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
			if GameVariables().game_state == GameState.PLAYER_PLAY:
				if self.game_manager.radial_weapon_menu is None:
					if WeaponManager().can_switch_weapon():
						self.game_manager.weapon_menu_init()
				else:
					self.game_manager.radial_weapon_menu = None
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll down
			if not self.game_manager.radial_weapon_menu:
				GameGlobals().scale_factor *= 1.1
				GameGlobals().scale_factor = GameGlobals().scale_factor
				if GameGlobals().scale_factor >= GameGlobals().scale_range[1]:
					GameGlobals().scale_factor = GameGlobals().scale_range[1]
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll up
			if not self.game_manager.radial_weapon_menu:
				GameGlobals().scale_factor *= 0.9
				GameGlobals().scale_factor = GameGlobals().scale_factor
				if GameGlobals().scale_factor <= GameGlobals().scale_range[0]:
					GameGlobals().scale_factor = GameGlobals().scale_range[0]

		# key press
		if event.type == pygame.KEYDOWN:
			# controll worm, jump and facing
				if GameVariables().player is not None and GameVariables().is_player_in_control():
					if event.key == pygame.K_RETURN:
						on_key_press_enter()
					if event.key == pygame.K_RIGHT:
						on_key_press_right()
					if event.key == pygame.K_LEFT:
						on_key_press_left()
				# fire on key press
				if event.key == pygame.K_SPACE:
					on_key_press_space()
				# weapon change by keyboard
				# misc
				if event.key == pygame.K_ESCAPE:
					# switch to pause menu
					pause_info = PauseRoomInfo(
						teams_score=TeamManager().get_info(),
						round_count=GameVariables().game_round_count
						)
					self.switch = SwitchRoom(Rooms.PAUSE_MENU, True, pause_info)
				if event.key == pygame.K_TAB:
					on_key_press_tab()
				if event.key == pygame.K_t:
					on_key_press_test()
				if event.key == pygame.K_F2:
					Worm.healthMode = (Worm.healthMode + 1) % 2
					if Worm.healthMode == 1:
						for worm in GameVariables().get_worms():
							worm.healthStr = fonts.pixel5.render(str(worm.health), False, worm.team.color)
				if event.key == pygame.K_F3:
					MapManager().draw_ground_secondary = not MapManager().draw_ground_secondary
				if event.key == pygame.K_m:
					pass
					# TimeSlow()
				if event.key in [pygame.K_RCTRL, pygame.K_LCTRL]:
					GameGlobals().scale_factor = GameGlobals().scale_range[1]
					if GameVariables().cam_track is None:
						GameVariables().cam_track = GameVariables().player

				self.game_manager.cheatCode += event.unicode
				if event.key == pygame.K_EQUALS:
					self.game_manager.cheat_activate(self.game_manager.cheatCode)
					self.game_manager.cheatCode = ""

	def step(self):
		''' game step '''

		GameVariables().state_machine.step()
		if GameVariables().game_end:
			self.switch = SwitchRoom(Rooms.MAIN_MENU, False, GameVariables().game_record)
			return

		if GameVariables().game_state in [GameState.RESET]:
			return

		# edge map scroll
		if pygame.mouse.get_focused():
			mouse_pos = pygame.mouse.get_pos()
			scroll = Vector()
			if mouse_pos[0] < EDGE_BORDER:
				scroll.x -= MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if mouse_pos[0] > GameGlobals().screen_width - EDGE_BORDER:
				scroll.x += MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if mouse_pos[1] < EDGE_BORDER:
				scroll.y -= MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if mouse_pos[1] > GameGlobals().screen_height - EDGE_BORDER:
				scroll.y += MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if scroll != Vector():
				GameVariables().cam_track = Camera(GameVariables().cam_pos + Vector(GameGlobals().win_width, GameGlobals().win_height)/2 + scroll)
		
		# handle scale:
		oldSize = (GameGlobals().win_width, GameGlobals().win_height)
		GameGlobals().win_width += (GameGlobals().screen_width / GameGlobals().scale_factor - GameGlobals().win_width) * 0.2
		GameGlobals().win_height += (GameGlobals().screen_height / GameGlobals().scale_factor - GameGlobals().win_height) * 0.2
		GameGlobals().win_width = int(GameGlobals().win_width)
		GameGlobals().win_height = int(GameGlobals().win_height)

		if oldSize != (GameGlobals().win_width, GameGlobals().win_height):
			GameGlobals().win = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height))
		
		# handle position:
		if GameVariables().cam_track:
			GameVariables().cam_pos += (
				(
					GameVariables().cam_track.pos - Vector(int(GameGlobals().screen_width / GameGlobals().scale_factor),
					int(GameGlobals().screen_height / GameGlobals().scale_factor)) / 2
				) - GameVariables().cam_pos
			) * 0.2

		# constraints:
		if GameVariables().cam_pos[1] < 0:
			GameVariables().cam_pos[1] = 0
		if GameVariables().cam_pos[1] >= MapManager().game_map.get_height() - GameGlobals().win_height:
			GameVariables().cam_pos[1] = MapManager().game_map.get_height() - GameGlobals().win_height


		if Earthquake.earthquake > 0:
			GameVariables().cam_pos[0] += Earthquake.earthquake * 25 * sin(GameVariables().time_overall)
			GameVariables().cam_pos[1] += Earthquake.earthquake * 15 * sin(GameVariables().time_overall * 1.8)
		
		self.game_manager.step()
		GameVariables().game_stable = True

		GameVariables().step_physicals()
		GameVariables().step_non_physicals()
		GameVariables().step()

		# step effects
		EffectManager().step()
		
		# step weapon manager
		WeaponManager().step()

		# step time manager
		TimeManager().step()
		GameVariables().hud.step()
		TeamManager().step()

		# step background
		self.game_manager.background.step()
		
		# step game mode
		GameVariables().game_mode.step()

		# camera for wait to stable:
		if GameVariables().game_state == GameState.WAIT_STABLE and GameVariables().time_overall % 20 == 0:
			for worm in GameVariables().get_worms():
				if worm.stable:
					continue
				GameVariables().cam_track = worm
				break
				
		# menu step
		if self.game_manager.radial_weapon_menu:
			self.game_manager.radial_weapon_menu.step()

		GameVariables().commentator.step()
	
	def draw(self, win: pygame.Surface) -> None:
		''' draw game '''
		super().draw(win)

		if GameVariables().game_state == GameState.RESET:
			return

		# draw background
		self.game_manager.background.draw(win)

		# draw map
		MapManager().draw_land(win)

		# draw objects
		for p in GameVariables().get_physicals(): 
			p.draw(win)
		
		GameVariables().draw_non_physicals(win)

		# draw effects
		EffectManager().draw(win)

		# draw top layer of background
		self.game_manager.background.draw_secondary(win)
		
		# draw shooting indicator
		if GameVariables().player is not None and GameVariables().game_state in [GameState.PLAYER_PLAY, GameState.PLAYER_RETREAT] and GameVariables().player.health > 0:
			GameVariables().player.draw_cursor(win)
			# draw aim aid
			if GameVariables().aim_aid and WeaponManager().current_weapon.style == WeaponStyle.GUN:
				p1 = vectorCopy(GameVariables().player.pos)
				p2 = p1 + GameVariables().player.get_shooting_direction() * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))

		# draw weapon indicators
		WeaponManager().draw_weapon_hint(win)

		# draw extra
		GameVariables().draw_extra(win)
		GameVariables().draw_layers(win)
		
		# draw game play mode
		GameVariables().game_mode.draw(win)

		# draw HUD
		GameVariables().hud.draw(win)
		TimeManager().draw(win)
		GameVariables().commentator.draw(win)
		WeaponManager().draw(win)
		
		# draw health bar
		TeamManager().draw(win)
		
		# weapon menu:
		if self.game_manager.radial_weapon_menu:
			self.game_manager.radial_weapon_menu.draw(win)
		
		# debug:
		damage_this_turn = GameVariables().stats.get_stats()['damage_this_turn']
		if self.damageText[0] != damage_this_turn:
			self.damageText = (damage_this_turn, fonts.pixel5_halo.render(str(int(damage_this_turn)), False, GameVariables().initial_variables.hud_color))
		win.blit(self.damageText[1], ((int(5), int(GameGlobals().win_height -5 -self.damageText[1].get_height()))))

wip = '''
	still in progress:
		loading screen
		holding mjolnir
		better portals
		refactor bubble
		team creation screen 
	'''


def main():
	print(wip)
	pygame.init()
	fps_clock = pygame.time.Clock()
	GameGlobals().win_width = int(GameGlobals().screen_width / GameGlobals().scale_factor)
	GameGlobals().win_height = int(GameGlobals().screen_height / GameGlobals().scale_factor)

	GameGlobals().win = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height))

	pygame.display.set_caption("Simon's Worms")
	screen = pygame.display.set_mode((GameGlobals().screen_width, GameGlobals().screen_height), pygame.DOUBLEBUF)

	constants.initialize()

	# room enum to room class converter
	rooms_creation_dict = {
		Rooms.MAIN_MENU: MainMenuRoom,
		Rooms.GAME_ROOM: GameRoom,
		Rooms.PAUSE_MENU: PauseRoom,
	}

	# current active rooms
	rooms_dict: Dict[Rooms, Room] = {}

	current_room = SplashScreenRoom()
	rooms_dict[Rooms.MAIN_MENU] = current_room

	done = False
	while not done:
		try:
			# handle events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					done = True
				current_room.handle_pygame_event(event)
		
			# step
			current_room.step()

			# draw
			current_room.draw(GameGlobals().win)

			if current_room.is_ready_to_switch():
				# switch room
				switch = current_room.switch
				current_room.switch = None
				if switch.craete_new_room:
					new_room = rooms_creation_dict[switch.next_room](input=switch.room_input)
					rooms_dict[switch.next_room] = new_room
					current_room = new_room
				else:
					if switch.next_room == Rooms.EXIT:
						done = True
						break
					existing_room = rooms_dict[switch.next_room]
					current_room = existing_room
					current_room.on_resume(input=switch.room_input)
				
		except Exception:
			print(traceback.format_exc())

		pygame.transform.scale(GameGlobals().win, screen.get_rect().size, screen)
		pygame.display.update()

		fps_clock.tick(GameGlobals().fps)

	pygame.quit()


if __name__ == "__main__":
	main()
	
