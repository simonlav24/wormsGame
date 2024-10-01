

from math import pi, cos, sin
from random import randint, uniform, choice
import os
import time
import traceback

import pygame
import pygame.gfxdraw

from common import *
from common.vector import Vector
from common.game_config import GameMode, RandomMode, SuddenDeathMode

from rooms.room import Room, Rooms, SwitchRoom
from rooms.room_main_menu import MainMenuRoom
from rooms.room_pause import PauseRoom
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
	StatsGamePlay
)
from game.time_manager import TimeManager
from game.map_manager import MapManager, SKY
from game.background import BackGround
from game.visual_effects import FloatingText
from game.team_manager import TeamManager, Team

from game.world_effects import boom, Earthquake

from game.hud import Commentator, Toast, WindFlag
from gui.radial_menu import RadialMenu, RadialButton

from entities.props import PetrolCan
from entities.deployables import deploy_pack, HealthPack, WeaponPack, UtilityPack
from entities.worm import Worm

from weapons.weapon_manager import WeaponManager
from weapons.weapon import weapon_bg_color, WeaponCategory, WeaponStyle
from weapons.missiles import DrillMissile
from weapons.guns import Bubble # refactor
from weapons.long_bow import LongBow
from weapons.plants import PlantSeed
from weapons.mine import Mine

from weapons.misc.springs import MasterOfPuppets
from weapons.misc.armageddon import Armageddon


class Game:
	_game = None
	def __init__(self, game_config: GameConfig=None):
		Game._game = self

		self.evaluate_config(game_config)
		GameVariables().config = game_config
		
		self.map_manager = MapManager()
		self.background = BackGround(feels[GameVariables().config.feel_index], GameVariables().config.option_darkness)

		self.clearLists()
		
		self.initiateGameVariables()
		self.game_vars = GameVariables()
		GameVariables().commentator = Commentator()

		self.mostDamage = (0, None)

		self.killList = []
		self.lstep = 0
		self.lstepmax = GameVariables().config.worms_per_team * 4

		self.loadingSurf = fonts.pixel10.render("Simon's Worms Loading", False, WHITE)

		self.endGameDict = None

		self.imageMjolnir = pygame.Surface((24,31), pygame.SRCALPHA)
		self.imageMjolnir.blit(sprites.sprite_atlas, (0,0), (100, 32, 24, 31))

		self.radial_weapon_menu: RadialMenu = None
		
	def create_new_game(self):
		''' initialize new game '''

		# create map
		self.create_map()
			
		# check for sky opening for airstrikes
		closedSkyCounter = 0
		for i in range(100):
			if self.map_manager.is_ground_at((randint(0, self.map_manager.game_map.get_width()-1), randint(0, 10))):
				closedSkyCounter += 1
		if closedSkyCounter > 50:
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

		# give random legendary starting weapons:
		WeaponManager().give_extra_starting_weapons()

		# choose starting worm
		starting_worm = TeamManager().current_team.worms.pop(0)
		TeamManager().current_team.worms.append(starting_worm)

		if Game._game.game_config.random_mode != RandomMode.NONE:
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
		GameVariables().game_state = GameVariables().game_next_state


	def init_handle_game_mode(self) -> None:
		''' on init, handle game mode parameter and variables '''
		# digging match
		if Game._game.game_config.option_digging:
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

		if self.game_config.game_mode == GameMode.MISSIONS:
			MissionManager()
			TimeManager().turnTime += 10
			MissionManager._mm.cycle()

	def clearLists(self):
		# clear lists
		MissionManager._mm = None
	
	def create_map(self) -> None:
		''' create game map '''
		custom_height = 512
		if self.game_config.map_ratio != -1:
			custom_height = self.game_config.map_ratio

		if self.game_config.option_digging:
			self.map_manager.create_map_digging(custom_height)
		elif 'noise' in self.game_config.map_path:
			self.map_manager.create_map_image(self.game_config.map_path, custom_height, True)
		else:
			self.map_manager.create_map_image(self.game_config.map_path, custom_height, self.game_config.is_recolor)
		
	def initiateGameVariables(self):
		self.waterRise = False # whether water rises at the end of each turn
		self.waterRising = False # water rises in current state
		self.deployingArtifact = False  # deploying artifacts in current state

		self.cheatCode = "" # cheat code
		self.shotCount = 0 # number of gun shots fired

		self.actionMove = False

		self.timeTravel = False

	def evaluate_config(self, game_config: GameConfig):
		self.game_config: GameConfig = game_config

		if self.game_config.feel_index == -1:
			self.game_config.feel_index = randint(0, len(feels) - 1)

		GameVariables().game_mode = GamePlayCompound()
		self.game_stats = StatsGamePlay()
		GameVariables().game_mode.add_mode(self.game_stats)

		game_mode_map = {
			GameMode.TERMINATOR: TerminatorGamePlay(),
			GameMode.POINTS: PointsGamePlay(),
			GameMode.TARGETS: TargetsGamePlay(),
			GameMode.DAVID_AND_GOLIATH: DVGGamePlay(),
			GameMode.CAPTURE_THE_FLAG: CTFGamePlay(),
			GameMode.ARENA: ArenaGamePlay(),
		}

		GameVariables().game_mode.add_mode(game_mode_map.get(self.game_config.game_mode))

		if self.game_config.option_artifacts:
			GameVariables().game_mode.add_mode(ArtifactsGamePlay())
		if self.game_config.option_darkness:
			GameVariables().game_mode.add_mode(DarknessGamePlay())


	def handle_event(self, event) -> bool:
		''' handle pygame event, return true if event handled '''
		is_handled = False

		if self.radial_weapon_menu:
			self.radial_weapon_menu.handle_event(event)
			menu_event = self.radial_weapon_menu.get_event()
			if menu_event:
				WeaponManager().switch_weapon(menu_event)
				self.radial_weapon_menu = None
				is_handled = True
		
		is_handled |= WeaponManager().handle_event(event)
		
		return is_handled

	def step(self):
		pass
	
	def add_to_score_list(self, amount=1):
		"""add to score list if points, list entry: (surf, name, score)"""
		if len(self.killList) > 0 and self.killList[0][1] == GameVariables().player.name_str:
			amount += self.killList[0][2]
			self.killList.pop(0)
		string = GameVariables().player.name_str + ": " + str(amount)
		self.killList.insert(0, (fonts.pixel5_halo.render(string, False, GameVariables().initial_variables.hud_color), GameVariables().player.name_str, amount))

	def lstepper(self):
		...
		# self.lstep += 1
		# pos = (GameVariables().win_width/2 - Game._game.loadingSurf.get_width()/2, GameVariables().win_height/2 - Game._game.loadingSurf.get_height()/2)
		# width = Game._game.loadingSurf.get_width()
		# height = Game._game.loadingSurf.get_height()
		# pygame.draw.rect(GameVariables().win, (255,255,255), ((pos[0], pos[1] + 20), ((self.lstep / self.lstepmax)*width, height)))
		# screen.blit(pygame.transform.scale(GameVariables().win, screen.get_rect().size), (0,0))
		# pygame.display.update()





################################################################################ Objects




class TimeAgent:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.positions = TimeTravel._tt.timeTravelPositions
		self.facings = TimeTravel._tt.timeTravelFacings
		self.time_counter = 0
		self.pos = self.positions[0]
		self.surf = TimeTravel._tt.timeTravelList["surf"]
		self.health = TimeTravel._tt.timeTravelList["health"]
		self.nameSurf = TimeTravel._tt.timeTravelList["name"]
		self.weapon = TimeTravel._tt.timeTravelList["weapon"]
		
		self.energy = 0
		self.stepsForEnergy = int(TimeTravel._tt.timeTravelList["energy"]/0.05)
	
	def step(self):
		if len(self.positions) == 0:
			TimeTravel._tt.timeTravelFire = True
			WeaponManager().fire(TimeTravel._tt.timeTravelList["weapon"])
			GameVariables().unregister_non_physical(self)
			TimeTravel._tt.timeTravelPositions = []
			TimeTravel._tt.timeTravelList = {}
			return
		self.pos = self.positions.pop(0)
		if len(self.positions) <= self.stepsForEnergy:
			self.energy += 0.05
			
		self.time_counter += 1
	
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, GameVariables().player.color, point2world(self.pos), 3+1)
		facing = self.facings.pop(0)
		win.blit(pygame.transform.flip(self.surf, facing == 1, False), point2world(tup2vec(self.pos) - tup2vec(self.surf.get_size()) / 2))
		win.blit(self.nameSurf , ((int(self.pos[0]) - int(GameVariables().cam_pos[0]) - int(self.nameSurf.get_size()[0]/2)), (int(self.pos[1]) - int(GameVariables().cam_pos[1]) - 21)))
		pygame.draw.rect(win, (220,220,220),(int(self.pos[0]) -10 -int(GameVariables().cam_pos[0]), int(self.pos[1]) -15 -int(GameVariables().cam_pos[1]), 20,3))
		value = max(20 * self.health / Game._game.game_config.worm_initial_health, 1)
		pygame.draw.rect(win, (0,220,0),(int(self.pos[0]) -10 -int(GameVariables().cam_pos[0]), int(self.pos[1]) -15 -int(GameVariables().cam_pos[1]), int(value),3))
		
		i = 0
		while i < 20 * self.energy:
			cPos = vectorCopy(self.pos)
			angle = TimeTravel._tt.timeTravelList["weaponDir"].getAngle()
			pygame.draw.line(win, (0,0,0), (int(cPos[0] - GameVariables().cam_pos[0]), int(cPos[1] - GameVariables().cam_pos[1])), ((int(cPos[0] + cos(angle) * i - GameVariables().cam_pos[0]), int(cPos[1] + sin(angle) * i - GameVariables().cam_pos[1]))))
			i += 1

class TimeTravel:
	_tt = None
	def __init__(self):
		TimeTravel._tt = self
		self.timeTravelPositions = []
		self.timeTravelFacings = []
		self.timeTravelList = {}
		self.timeTravelFire = False
	def timeTravelInitiate(self):
		Game._game.timeTravel = True
		self.timeTravelList = {}
		self.timeTravelList["surf"] = GameVariables().player.surf
		self.timeTravelList["name"] = GameVariables().player.name
		self.timeTravelList["health"] = GameVariables().player.health
		self.timeTravelList["initial pos"] = vectorCopy(GameVariables().player.pos)
		self.timeTravelList["time_counter in turn"] = TimeManager().time_counter
	def timeTravelRecord(self):
		self.timeTravelPositions.append(GameVariables().player.pos.vec2tup())
		self.timeTravelFacings.append(GameVariables().player.facing)
	def timeTravelPlay(self):
		TimeManager().time_counter = self.timeTravelList["time_counter in turn"]
		Game._game.timeTravel = False
		self.timeTravelList["weapon"] = WeaponManager().current_weapon
		self.timeTravelList["weaponOrigin"] = vectorCopy(GameVariables().player.pos)
		self.timeTravelList["energy"] = WeaponManager().energy_level
		self.timeTravelList["weaponDir"] = GameVariables().player.get_shooting_direction()
		GameVariables().player.health = self.timeTravelList["health"]
		if Worm.healthMode == 1:
			GameVariables().player.healthStr = fonts.pixel5.render(str(GameVariables().player.health), False, GameVariables().player.team.color)
		GameVariables().player.pos = self.timeTravelList["initial pos"]
		GameVariables().player.vel *= 0
		TimeAgent()
	def timeTravelReset(self):
		self.timeTravelFire = False
		self.timeTravelPositions = []
		self.timeTravelList = {}
	def step(self):
		self.timeTravelRecord()


class TimeSlow:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.time = 0
		self.state = "slow"
	def step(self):
		self.time += 1
		if self.state == "slow":
			GameVariables().dt *= 0.9
			if GameVariables().dt < 0.1:
				self.state = "fast"
		elif self.state == "fast":
			GameVariables().dt *= 1.1
			if GameVariables().dt > 1:
				GameVariables().dt = 1
				GameVariables().unregister_non_physical(self)
	def draw(self, win: pygame.Surface):
		pass




################################################################################ Weapons setup







################################################################################ more functions

def add_to_record(dic):
	keys = ["time", "winner", "mostDamage", "damager", "mode", "points"]
	if not os.path.exists("wormsRecord.xml"):
		with open("wormsRecord.xml", "w+") as file:
			file.write("<data>\n")
			file.write("<game")
			for key in keys:
				if key in dic.keys():
					file.write(" " + key + '="' + str(dic[key]) + '"')
			file.write("/>\n</data>")
			return
	
	with open("wormsRecord.xml", "r") as file:
		contents = file.readlines()
		index = contents.index("</data>")
	
	string = "<game"
	for key in keys:
		if key in dic.keys():
			string += " " + key + '="' + str(dic[key]) + '"'
	string += "/>\n"
	contents.insert(index, string)
	
	with open("wormsRecord.xml", "w") as file:
		contents = "".join(contents)
		file.write(contents)

def check_winners() -> bool:
	game_over = False
	last_team: Team = None

	# check for last team standing
	teams = [team for team in TeamManager().teams if len(team.worms) > 0]
	if len(teams) == 1:
		game_over = True
		last_team = teams[0]
	if len(teams) == 0:
		game_over = True
	
	game_over |= GameVariables().game_mode.is_game_over()

	if not game_over:
		return False
	
	# game over
	winning_team: Team = None
	points_mode = GameVariables().game_mode.is_points_game()
	
	# determine winning team
	if not points_mode:
		winning_team = last_team
	else:
		if last_team is not None:
			last_team.points += GameVariables().game_mode.win_bonus()
		finals = sorted(TeamManager().teams, key = lambda x: x.points)
		winning_team = finals[-1]
	
	# declare winner
	if winning_team is not None:
		print("Team", winning_team.name, "won!")
		if len(winning_team.worms) > 0:
			GameVariables().cam_track = winning_team.worms[0]
		GameVariables().commentator.comment([
			{'text': 'team '},
			{'text': winning_team.name, 'color': winning_team.color},
			{'text': ' Won!'}
		])
	else:
		print("Tie!")
		GameVariables().commentator.comment([{'text': 'its a tie!'}])
	
	# todo: add to dict
	# todo: save win as image

	GameVariables().game_next_state = GameState.WIN
	return True

def _check_winners() -> bool:
	end = False
	lastTeam = None
	count = 0
	pointsGame = False
	for team in TeamManager().teams:
		if len(team.worms) == 0:
			count += 1
	if count == GameVariables().num_of_teams - 1:
		# one team remains
		end = True
		for team in TeamManager().teams:
			if not len(team.worms) == 0:
				lastTeam = team
	if count == GameVariables().num_of_teams:
		# no team remains
		end = True
		
	if not end:
		return False
	# game end:
	dic = {}
	winningTeam = None
	
	# if Game._game.game_config.game_mode == GameMode.MISSIONS:
	# 	pointsGame = True
	# 	if lastTeam:
	# 		pass
	# 	dic["mode"] = "missions"
	
	# win points:
	if pointsGame:
		for team in TeamManager().teams:
			print("[ |", team.name, "got", team.points, "points! | ]")
		teamsFinals = sorted(TeamManager().teams, key = lambda x: x.points)
		winningTeam = teamsFinals[-1]
		print("[most points to team", winningTeam.name, "]")
		dic["points"] = str(winningTeam.points)
	# regular win:
	else:
		winningTeam = lastTeam
		if winningTeam:
			print("[last team standing is", winningTeam.name, "]")
	
	if end:
		if winningTeam is not None:
			print("Team", winningTeam.name, "won!")
			dic["time"] = str(GameVariables().time_overall // GameVariables().fps)
			dic["winner"] = winningTeam.name
			if Game._game.mostDamage[1]:
				dic["mostDamage"] = str(int(Game._game.mostDamage[0]))
				dic["damager"] = Game._game.mostDamage[1]
			add_to_record(dic)
			if len(winningTeam.worms) > 0:
				GameVariables().cam_track = winningTeam.worms[0]
			GameVariables().commentator.comment([
				{'text': 'team '},
				{'text': winningTeam.name, 'color': winningTeam.color},
				{'text': ' Won!'}
			])

		else:
			GameVariables().commentator.comment([{'text': 'its a tie!'}])
			print("Tie!")
		
		# add teams to dic
		dic["teams"] = {}
		for team in TeamManager().teams:
			dic["teams"][team.name] = [team.color, team.points]

		Game._game.endGameDict = dic
		GameVariables().game_next_state = GameState.WIN
		
		GroundScreenShoot = pygame.Surface((MapManager().ground_map.get_width(), MapManager().ground_map.get_height() - GameVariables().water_level), pygame.SRCALPHA)
		GroundScreenShoot.blit(MapManager().ground_map, (0,0))
		pygame.image.save(GroundScreenShoot, "lastWormsGround.png")
	return end

def deploy_crate() -> None:
	# deploy crate if privious turn was last turn in round
	if ((GameVariables().game_turn_count) % (GameVariables().turns_in_round)) == (GameVariables().turns_in_round - 1):
		comments = [
			[{'text': 'a jewel from the heavens!'}],
			[{'text': 'its raining crates, halelujah!'}],
			[{'text': ' '}],
		]
		GameVariables().commentator.comment(choice(comments))

		for _ in range(Game._game.game_config.deployed_packs):
			w = deploy_pack(choice([HealthPack, UtilityPack, WeaponPack]))
			GameVariables().cam_track = w

def cycle_worms():
	''' switch to next worm and set up 
		reset special effect
		comments about damage
		check for winners
		make objects that are playing in between play
		deploy packs / artifacts
		handle water rise if flood
		update weapons delay (should be removed)
		flare reduction
		sick worms
		chose next worm
	
	'''

	# reset special effects:
	GameVariables().physics.global_gravity = 0.2
	GameVariables().damage_mult = 0.8
	GameVariables().boom_radius_mult = 1
	GameVariables().mega_weapon_trigger = False
	GameVariables().aim_aid = False
	if Game._game.timeTravel: TimeTravel._tt.timeTravelReset()

	# release worm tool
	worm_tool = GameVariables().player.get_tool()
	if worm_tool is not None:
		worm_tool.release()
	
	if check_winners():
		return

	new_round = False
	GameVariables().game_turn_count += 1
	if GameVariables().game_turn_count % GameVariables().turns_in_round == 0:
		GameVariables().game_round_count += 1
		new_round = True
	
	# rise water:
	if Game._game.waterRise and not Game._game.waterRising:
		Game._game.background.water_rise(20)
		GameVariables().game_next_state = GameState.WAIT_STABLE
		GameVariables().game_turn_count -= 1
		Game._game.waterRising = True
		return
		
	Game._game.waterRising = False
	Game._game.deployingArtifact = False
	
	if new_round:
		Game._game.game_config.rounds_for_sudden_death -= 1
		if Game._game.game_config.rounds_for_sudden_death == 0:
			suddenDeath()
	
	# update stuff
	GameVariables().get_debries().clear()
	Bubble.cought = []
	
	# change wind:
	GameVariables().physics.wind = uniform(-1, 1)
	
	# sick:
	for worm in GameVariables().get_worms():
		if worm.sick != Sickness.NONE and worm.health > 5:
			worm.damage(min(int(5 / GameVariables().damage_mult) + 1, int((worm.health - 5) / GameVariables().damage_mult) + 1), DamageType.SICK)
		
	# select next team
	index = TeamManager().teams.index(TeamManager().current_team)
	index = (index + 1) % GameVariables().num_of_teams
	TeamManager().current_team = TeamManager().teams[index]
	while not len(TeamManager().current_team.worms) > 0:
		index = TeamManager().teams.index(TeamManager().current_team)
		index = (index + 1) % GameVariables().num_of_teams
		TeamManager().current_team = TeamManager().teams[index]
		
	# sort worms by health for drawing purpuses
	GameVariables().get_physicals().sort(key = lambda worm: worm.health if worm.health else 0)
	
	GameVariables().on_turn_end()
	GameVariables().game_mode.on_turn_end()

	# actual worm switch:
	switched = False
	while not switched:
		w = TeamManager().current_team.worms.pop(0)
		TeamManager().current_team.worms.append(w)
		if w.sleep:
			w.sleep = False
			continue
		switched = True
		
	if Game._game.game_config.random_mode == RandomMode.COMPLETE: # complete random
		TeamManager().current_team = choice(TeamManager().teams)
		while not len(TeamManager().current_team.worms) > 0:
			TeamManager().current_team = choice(TeamManager().teams)
		w = choice(TeamManager().current_team.worms)
	if Game._game.game_config.random_mode == RandomMode.IN_TEAM: # random in the current team
		w = choice(TeamManager().current_team.worms)

	GameVariables().player = w
	GameVariables().cam_track = GameVariables().player
	GameVariables().player_can_move = True

	GameVariables().on_turn_begin()
	GameVariables().game_mode.on_turn_begin()

	WeaponManager().switch_weapon(WeaponManager().current_weapon)
	if Game._game.game_config.game_mode == GameMode.MISSIONS:
		MissionManager._mm.cycle()

################################################################################ Gui

def weapon_menu_init():
	# get categories

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

		is_enabled = not all([not button.is_enabled for button in sub_layout])
		main_button = RadialButton(weapons_in_category[0], '', '', weapon_bg_color[category], WeaponManager().get_surface_portion(weapons_in_category[0]), sub_layout, is_enabled=is_enabled)
		layout.append(main_button)

	Game._game.radial_weapon_menu = RadialMenu(layout, Vector(GameVariables().win_width // 2, GameVariables().win_height // 2))

class Camera:
	def __init__(self, pos):
		self.pos = pos
		self.radius = 1

def toast_info():
	if Toast.toastCount > 0:
		Toast._toasts[0].time = 0
		if Toast._toasts[0].state == 2:
			Toast._toasts[0].state = 0
		return
	toastWidth = 100
	surfs = []
	for team in TeamManager().teams:
		name = fonts.pixel5.render(team.name, False, team.color)
		points = fonts.pixel5.render(str(team.points), False, (0,0,0))
		surfs.append((name, points))
	surf = pygame.Surface((toastWidth, (surfs[0][0].get_height() + 3) * GameVariables().num_of_teams), pygame.SRCALPHA)
	i = 0
	for s in surfs:
		surf.blit(s[0], (0, i))
		surf.blit(s[1], (toastWidth - s[1].get_width(), i))
		i += s[0].get_height() + 3
	Toast(surf)


class MissionManager:
	_mm = None
	_log = None
	def __init__(self):
		MissionManager._mm = self
		MissionManager._log = ''
		self.availableMissions = {
			"kill a worm": 1,
			"kill _": 3,
			"hit a worm from _": 1,
			"hit _": 2,
			"reach marker": 1,
			"double kill": 3,
			"triple kill": 4,
			"hit highest worm": 1,
			"hit distant worm": 1,
			"hit 3 worms": 2, 
			"above 50 damage": 1,
		}
		self.wormMissionDict = {}
		self.killedThisTurn = []
		self.hitThisTurn = []
		self.sickThisTurn = []
		
	def assignMissions(self, worm, oldMission=None):
		# choose 3 missions from availableMissions
		if worm in self.wormMissionDict:
			self.evaluateMissions(worm, oldMission)
			return
		
		wormMissions = []
		self.wormMissionDict[worm] = wormMissions
		for _ in range(3):
			newMission = self.assignOneMission(worm)
			wormMissions.append(newMission)
			MissionManager._log += f"{worm.name_str} received mission {newMission.missionType}\n"

	def evaluateMissions(self, worm, oldMission=None):
		replaceMissions = []

		# check if any of the missions are completed and remove them
		for mission in self.wormMissionDict[worm]:
			if mission.completed and mission.readyToChange:
				replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))

		currentWormMissionsTypes = [i.missionType for i in self.wormMissionDict[worm]]

		# if missionType "hit _" or "kill _" or "hit a worm from _" and target is dead, remove mission
		if "hit _" in currentWormMissionsTypes or "kill _" in currentWormMissionsTypes:
			for mission in self.wormMissionDict[worm]:
				if mission.missionType in ["hit _", "kill _"]:
					if mission.target not in GameVariables().get_worms() or not mission.target.alive:
						replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))
		if "hit a worm from _" in currentWormMissionsTypes:
			for mission in self.wormMissionDict[worm]:
				if mission.missionType == "hit a worm from _":
					if len(mission.teamTarget) == 0:
						replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))

		# count alive worms from other teams
		aliveWorms = 0
		for w in GameVariables().get_worms():
			if w.alive and w.team != worm.team:
				aliveWorms += 1
		
		if aliveWorms < 5:
			for mission in self.wormMissionDict[worm]:
				if mission.missionType == "hit 3 worms":
					replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))
		if aliveWorms < 3:
			for mission in self.wormMissionDict[worm]:
				if mission.missionType == "triple kill":
					replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))
		if aliveWorms < 2:
			for mission in self.wormMissionDict[worm]:
				if mission.missionType == "double kill":
					replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))

		for mission in replaceMissions:
			if mission[0] in self.wormMissionDict[worm]:
				self.wormMissionDict[worm].remove(mission[0])
				newMission = self.assignOneMission(worm, oldMission)
				self.wormMissionDict[worm].insert(mission[1], newMission)
				# self.wormMissionDict[worm].append(newMission)
				MissionManager._log += f"{worm.name_str} received mission {newMission.missionType}\n"

		if len(self.wormMissionDict[worm]) < 3:
			for i in range(3 - len(self.wormMissionDict[worm])):
				newMission = self.assignOneMission(worm, oldMission)
				self.wormMissionDict[worm].append(newMission)
				# self.wormMissionDict[worm].append(newMission)
				MissionManager._log += f"{worm.name_str} received mission {newMission.missionType}\n"

		self.updateDisplay()

	def assignOneMission(self, worm, oldMission=None):
		# figure out which missions are available
		availableMissions = list(self.availableMissions.keys())
		for mission in self.wormMissionDict[worm]:
			availableMissions.remove(mission.missionType)
		
		if oldMission:
			availableMissions.remove(oldMission.missionType)

		# check if worms or teams exist
		if len(self.getAliveWormsFromOtherTeams()) == 0:
			for i in ["hit a worm from _", "kill _", "hit _"]:
				if i in availableMissions:
					availableMissions.remove(i)
		
		# choose a missionType and create it
		chosenMission = choice(availableMissions)
		newMission = Mission(chosenMission, self.availableMissions[chosenMission])
		if "_" in chosenMission:
			# targeted mission
			if "kill" in chosenMission:
				newMission.target = self.chooseTarget()
			elif "from" in chosenMission:
				newMission.teamTarget = self.chooseTeamTarget()
			elif "hit" in chosenMission:
				newMission.target = self.chooseTarget()
		
		if chosenMission == "reach marker":
			newMission.marker = self.createMarker()

		return newMission

	def getAliveWormsFromOtherTeams(self):
		notFromTeam = GameVariables().player.team
		worms = []
		for worm in GameVariables().get_worms():
			if worm.team == notFromTeam:
				continue
			if not worm.alive:
				continue
			worms.append(worm)
		return worms

	def createMarker(self) -> Vector:
		return MapManager().get_good_place()

	def chooseTarget(self):
		notFromTeam = GameVariables().player.team
		worms = self.getAliveWormsFromOtherTeams()
		return choice(worms)

	def chooseTeamTarget(self):
		notFromTeam = GameVariables().player.team
		teams = []
		for team in TeamManager().teams:
			if team == notFromTeam:
				continue
			if len(team.worms) == 0:
				continue
			teams.append(team)
		if len(teams) == 0:
			return None
		return choice(teams)

	def removeMission(self, mission):
		if mission in self.wormMissionDict[GameVariables().player]:
			self.wormMissionDict[GameVariables().player].remove(mission)

		if Game._game.isPlayingState():
			self.assignMissions(GameVariables().player, mission)

	def notifyKill(self, worm):
		if worm == GameVariables().player:
			return
		self.killedThisTurn.append(worm)
		self.checkMissions(["kill a worm", "kill _", "double kill", "triple kill", "above 50 damage"])

	def notifyHit(self, worm):
		if worm in self.hitThisTurn or worm == GameVariables().player:
			self.checkMissions(["above 50 damage"])
			return
		self.hitThisTurn.append(worm)
		self.checkMissions(["hit a worm from _", "hit _", "hit 3 worms", "above 50 damage"])
		# check highest
		worms = []
		for w in GameVariables().get_worms():
			if w.alive and w.team != GameVariables().player.team:
				worms.append(w)
		
		highestWorm = min(worms, key=lambda w: w.pos.y)
		if worm == highestWorm:
			self.checkMissions(["hit highest worm"])
		# check distance
		if distus(worm.pos, GameVariables().player.pos) > 300 * 300:
			self.checkMissions(["hit distant worm"])

	def checkMissions(self, missionTypes):
		for mission in self.wormMissionDict[GameVariables().player]:
			if mission.missionType in missionTypes:
				mission.check()

	def notifySick(self, worm):
		pass

	def endTurn(self):
		pass

	def cycle(self):
		# start of turn, assign missions to current worm
		self.assignMissions(GameVariables().player)
		self.updateDisplay()
		self.killedThisTurn = []
		self.hitThisTurn = []
		self.sickThisTurn = []
		self.marker = None

		if "reach marker" in self.wormMissionDict[GameVariables().player]:
			self.createMarker()

	def updateDisplay(self):
		for mission in self.wormMissionDict[GameVariables().player]:
			mission.updateDisplay()

	def step(self):
		if GameVariables().player == None:
			return
		for mission in self.wormMissionDict[GameVariables().player]:
			mission.step()

	def draw(self, win: pygame.Surface):
		if GameVariables().player == None:
			return
		currentWorm = GameVariables().player
		# draw missions gui in lower right of screen
		yOffset = 0
		for mission in self.wormMissionDict[currentWorm]:
			surf = mission.surf
			win.blit(surf, (GameVariables().win_width - surf.get_width() - 5, GameVariables().win_height - surf.get_height() - 5 - yOffset))
			yOffset += surf.get_height() + 2
		
		# draw mission indicators
		for mission in self.wormMissionDict[currentWorm]:
			mission.draw(win)

class Mission:
	def __init__(self, missionType, reward):
		self.missionType = missionType
		self.reward = reward
		self.target = None
		self.teamTarget = None
		self.marker = None
		self.completed = False
		self.readyToChange = False
		self.timer = 3 * GameVariables().fps
		self.textSurf = None
		self.surf = None

	def __str__(self):
		return self.missionType

	def __repr__(self):
		return self.missionType

	def missionToString(self):
		string = self.missionType
		if "_" in string:
			if "from" in string:
				string = string.replace("_", self.teamTarget.name)
			elif "kill" in string or "hit" in string:
				string = string.replace("_", self.target.name_str)

		string += " (" + str(self.reward) + ")"
		return string

	def complete(self, stringReplacement = None):
		string = self.missionType
		if "_" in string:
			string = string.replace("_", stringReplacement)
		comment = [
			{'text': 'mission '}, {'text': string, 'color': GameVariables().player.team.color}, {'text': ' passed'}
		]

		GameVariables().commentator.comment(comment)
		GameVariables().player.team.points += self.reward
		Game._game.add_to_score_list(self.reward)

		self.completed = True
		MissionManager._log += f"{GameVariables().player.name_str} completed mission {self.missionType} {str(self.reward)}\n"
		
	def check(self):
		# check complete
		if self.completed:
			return
		missionManager = MissionManager._mm
		if self.missionType == "kill a worm":
			if len(missionManager.killedThisTurn) > 0:
				self.complete()
		elif self.missionType == "reach marker":
			self.complete()
			self.marker = None
		elif self.missionType == "double kill":
			if len(missionManager.killedThisTurn) > 1:
				self.complete()
		elif self.missionType == "triple kill":
			if len(missionManager.killedThisTurn) > 2:
				self.complete()
		elif self.missionType == "hit highest worm":
			self.complete()
		elif self.missionType == "hit distant worm":
			self.complete()
		elif self.missionType == "hit 3 worms":
			if len(missionManager.hitThisTurn) > 2:
				self.complete()
		elif self.missionType == "kill _":
			if self.target in missionManager.killedThisTurn:
				self.complete(self.target.name_str)
		elif self.missionType == "hit a worm from _":
			team = self.teamTarget
			for worm in missionManager.hitThisTurn:
				if worm.team == team:
					self.complete(team.name)
		elif self.missionType == "hit _":
			if self.target in missionManager.hitThisTurn:
				self.complete(self.target.name_str)
		elif self.missionType == "above 50 damage":
			if 'condition':
				self.complete()

	def step(self):
		if self.marker:
			if distus(self.marker, GameVariables().player.pos) < 20 * 20:
				self.check()
		if self.completed:
			self.timer = max(0, self.timer - 1)
			self.updateDisplay()
			if self.timer == 0 and Game._game.isPlayingState():
				self.readyToChange = True
				MissionManager._mm.removeMission(self)

	def draw(self, win: pygame.Surface):
		# draw indicators
		# draw distance indicator
		currentWorm = GameVariables().player
		if self.missionType == "hit distant worm":
			radius = 300
			da = 2 * pi / 40
			time = da * int(GameVariables().time_overall / 2)
			timeAngles = [time + i * pi/2 for i in range(4)]
			for ta in timeAngles:
				for i in range(9):
					size = int(i / 3)
					pos = currentWorm.pos + vectorFromAngle(ta + i * da, radius)
					pygame.draw.circle(win, (255,0,0), point2world(pos), size)
		# draw marker
		elif self.marker:
			offset = sin(GameVariables().time_overall / 5) * 5
			pygame.draw.circle(win, (255,0,0), point2world(self.marker), 10 + offset, 1)
			draw_dir_indicator(win, self.marker)
		# draw indicators
		elif self.target:
			draw_dir_indicator(win, self.target.pos)
			draw_target(win, self.target.pos)

	def updateDisplay(self):
		if not self.textSurf:
			self.textSurf = fonts.pixel5.render(self.missionToString(), False, WHITE)
			self.surf = pygame.Surface((self.textSurf.get_width() + 2, self.textSurf.get_height() + 2))

		# interpolate from Black to Green base on timer [0, 3 * fps]
		amount = (1 - self.timer / (3 * GameVariables().fps)) * 4
		bColor = (0, min(255 * amount, 255), 0)

		self.surf.fill(bColor)
		self.surf.blit(self.textSurf, (1,1))


def suddenDeath():
	sudden_death_modes = [Game._game.game_config.sudden_death_style]
	if Game._game.game_config.sudden_death_style == SuddenDeathMode.ALL:
		for mode in SuddenDeathMode:
			sudden_death_modes.append(mode)

	if SuddenDeathMode.PLAGUE in sudden_death_modes:
		for worm in GameVariables().get_worms():
			worm.sicken()
			if not worm.health == 1:
				worm.health = worm.health // 2
	if SuddenDeathMode.FLOOD in sudden_death_modes:
		string += " water rise!"
		Game._game.waterRise = True
	text = fonts.pixel10.render("sudden death", False, (220,0,0))
	Toast(pygame.transform.scale(text, tup2vec(text.get_size()) * 2), Toast.middle)

def cheat_activate(code: str):
	code = code[:-1].lower()
	mouse_pos = mouse_pos_in_world()

	if code == "gibguns":
		for team in TeamManager().teams:
			for i, _ in enumerate(team.weapon_set):
				team.weapon_set[i] = 100
		for weapon in WeaponManager().weapons:
			weapon.round_delay = 0
		Game._game.game_config.option_cool_down = False
	elif code == "suddendeath":
		suddenDeath()
	elif code == "wind":
		GameVariables().physics.wind = uniform(-1, 1)
	elif code == "goodbyecruelworld":
		boom(GameVariables().player.pos, 100)
	elif code == "armageddon":
		Armageddon()
	elif code == "reset":
		GameVariables().game_state, GameVariables().game_next_state = GameState.RESET, GameState.RESET
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
	elif code == "tsunami":
		Game._game.waterRise = True
		GameVariables().commentator.comment([{'text': "water rising!"}])
	elif code == "comeflywithme":
		TeamManager().current_team.ammo(WeaponManager()["jet pack"], 6)
		TeamManager().current_team.ammo(WeaponManager()["rope"], 6)
		TeamManager().current_team.ammo(WeaponManager()["ender pearl"], 6)
	# elif code == "odinson":
	# 	# m = Mjolnir(mouse_pos)
	# 	m.vel *= 0
	# elif code == "bulbasaur":
	# 	m = MagicLeaf(mouse_pos)
	# elif code == "avatar":
	# 	m = Avatar(mouse_pos)
	elif code == "masterofpuppets":
		MasterOfPuppets()
	elif code == "artifact":
		Game._game.trigerArtifact = True
		GameVariables().commentator.comment([{'text': 'next turn artifact drop'}])
	# elif code == "minecraft":
	# 	PickAxeArtifact(mouse_pos)
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


################################################################################ State machine

def stateMachine():
	if GameVariables().game_state == GameState.RESET:
		GameVariables().game_stable = False
		GameVariables().game_stable_counter = False
		
		Game._game.create_new_game()
		GameVariables().game_next_state = GameState.PLAYER_PLAY
		GameVariables().game_state = GameVariables().game_next_state
	
	elif GameVariables().game_state == GameState.PLAYER_PLAY:
		GameVariables().player_in_control = True #can play
		GameVariables().player_can_shoot = True
		
		GameVariables().game_next_state = GameState.PLAYER_RETREAT
	
	elif GameVariables().game_state == GameState.PLAYER_RETREAT:
		GameVariables().player_in_control = True #can play
		GameVariables().player_can_shoot = False
		
		GameVariables().game_stable_counter = 0
		GameVariables().game_next_state = GameState.WAIT_STABLE
	
	elif GameVariables().game_state in [GameState.WAIT_STABLE, GameState.AUTONOMOUS_PLAY, GameState.DEPLOYEMENT]:
		GameVariables().player_in_control = False #can play
		GameVariables().player_can_shoot = False
		if GameVariables().game_stable:
			GameVariables().game_stable_counter += 1
			if GameVariables().game_stable_counter == 10:
				# next turn
				GameVariables().game_stable_counter = 0
				if GameVariables().game_state == GameState.WAIT_STABLE:
					# wait stable ended, engage autonomous
					GameVariables().engage_autonomous()
					GameVariables().game_next_state = GameState.AUTONOMOUS_PLAY
				
				elif GameVariables().game_state == GameState.AUTONOMOUS_PLAY:
					# autonomous turn ended, deploy crates
					deploy_crate()
					GameVariables().game_mode.on_deploy()
					GameVariables().game_next_state = GameState.DEPLOYEMENT

				elif GameVariables().game_state == GameState.DEPLOYEMENT:
					# deployed crates, cycle worms
					GameVariables().game_next_state = GameState.PLAYER_PLAY
					cycle_worms()
					TimeManager().time_reset()
					WeaponManager().render_weapon_count()
				
				GameVariables().game_state = GameVariables().game_next_state
	
	elif GameVariables().game_state == GameState.AUTONOMOUS_PLAY:
		GameVariables().game_next_state = GameState.PLAYER_PLAY
		GameVariables().player_in_control = False
		GameVariables().player_can_shoot = False
		if GameVariables().game_stable:
			GameVariables().game_stable_counter += 1
			if GameVariables().game_stable_counter == 10:
				# next turn
				GameVariables().game_stable_counter = 0
				TimeManager().time_reset()
				cycle_worms()
				WeaponManager().render_weapon_count()
				GameVariables().game_state = GameVariables().game_next_state
	
	elif GameVariables().game_state == GameState.WIN:
		GameVariables().game_stable_counter += 1
		if GameVariables().game_stable_counter == 30 * 3:
			return 1
	
	return 0

################################################################################ Key bindings
def onKeyPressRight():
	GameVariables().player.turn(RIGHT)

def onKeyPressLeft():
	GameVariables().player.turn(LEFT)

def onKeyPressSpace():
	if not WeaponManager().can_shoot():
		print('cant shoot')
		return
	# energize weapon
	if WeaponManager().current_weapon.style == WeaponStyle.CHARGABLE:
		WeaponManager().energising = True
		WeaponManager().energy_level = 0
		WeaponManager().fire_weapon = False

def onKeyHoldSpace():
	WeaponManager().energy_level += 0.05
	if WeaponManager().energy_level >= 1:
		if Game._game.timeTravel:
			TimeTravel._tt.timeTravelPlay()
			WeaponManager().energy_level = 0
			WeaponManager().energising = False
		else:
			WeaponManager().energy_level = 1
			WeaponManager().fire_weapon = True

def onKeyReleaseSpace():
	if WeaponManager().can_shoot():

		fire_weapon_conditions = [
			WeaponManager().current_weapon.style == WeaponStyle.CHARGABLE and WeaponManager().energising,
			WeaponManager().current_weapon.style in [WeaponStyle.UTILITY, WeaponStyle.WORM_TOOL, WeaponStyle.SPECIAL],
			WeaponManager().current_weapon.style in [WeaponStyle.PUTABLE, WeaponStyle.GUN],
		]

		if any(fire_weapon_conditions):
			WeaponManager().fire_weapon = True
		WeaponManager().energising = False

def onKeyPressTab():
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
 
def onKeyPressTest():
	GameVariables().debug_print()

def onKeyPressEnter():
	# jump
	if GameVariables().player.stable and GameVariables().player.health > 0:
		GameVariables().player.vel += GameVariables().player.get_shooting_direction() * JUMP_VELOCITY
		GameVariables().player.stable = False

################################################################################ Main

class GameRoom(Room):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		config = kwargs.get('input')
		Game(config)
		WeaponManager()

		# refactor these
		self.wind_flag = WindFlag()
		self.damageText = (Game._game.game_stats.damage_this_turn, fonts.pixel5_halo.render(str(int(Game._game.game_stats.damage_this_turn)), False, GameVariables().initial_variables.hud_color))
	
	def handle_pygame_event(self, event) -> None:
		''' handle pygame events in game '''
		super().handle_pygame_event(event)
		is_handled = Game._game.handle_event(event)
		if is_handled:
			return
		GameVariables().handle_event(event)
		if event.type == pygame.QUIT:
			self.switch = SwitchRoom(Rooms.EXIT, False, None)
			return
		# mouse click event
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # left click (main)
			# CLICKABLE weapon check:
			if GameVariables().game_state == GameState.PLAYER_PLAY and WeaponManager().current_weapon.style == WeaponStyle.CLICKABLE:
				# fireClickable()
				WeaponManager().fire_weapon = True
			if GameVariables().game_state == GameState.PLAYER_PLAY and WeaponManager().current_weapon.name in ["homing missile", "seeker"] and not Game._game.radial_weapon_menu:
				mouse_pos = mouse_pos_in_world()
				GameVariables().point_target = vectorCopy(mouse_pos)

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)
			pass
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
			# this is the next GameVariables().game_state after placing all worms
			if GameVariables().game_state == GameState.PLAYER_PLAY:
				if Game._game.radial_weapon_menu is None:
					if WeaponManager().can_open_menu():
						weapon_menu_init()
				else:
					Game._game.radial_weapon_menu = None
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll down
			if not Game._game.radial_weapon_menu:
				GameVariables().scale_factor *= 1.1
				GameVariables().scale_factor = GameVariables().scale_factor
				if GameVariables().scale_factor >= GameVariables().scale_range[1]:
					GameVariables().scale_factor = GameVariables().scale_range[1]
					GameVariables().scale_factor = GameVariables().scale_factor
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll up
			if not Game._game.radial_weapon_menu:
				GameVariables().scale_factor *= 0.9
				GameVariables().scale_factor = GameVariables().scale_factor
				if GameVariables().scale_factor <= GameVariables().scale_range[0]:
					GameVariables().scale_factor = GameVariables().scale_range[0]
					GameVariables().scale_factor = GameVariables().scale_factor

		# key press
		if event.type == pygame.KEYDOWN:
			# controll worm, jump and facing
				if GameVariables().player is not None and GameVariables().player_in_control:
					if event.key == pygame.K_RETURN:
						onKeyPressEnter()
					if event.key == pygame.K_RIGHT:
						onKeyPressRight()
					if event.key == pygame.K_LEFT:
						onKeyPressLeft()
				# fire on key press
				if event.key == pygame.K_SPACE:
					onKeyPressSpace()
				# weapon change by keyboard
				# misc
				if event.key == pygame.K_ESCAPE:
					# switch to pause menu
					self.switch = SwitchRoom(Rooms.PAUSE_MENU, True, None)
				if event.key == pygame.K_TAB:
					onKeyPressTab()
				if event.key == pygame.K_t:
					onKeyPressTest()
				if event.key == pygame.K_F1:
					toast_info()
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
					GameVariables().scale_factor = GameVariables().scale_range[1]
					if GameVariables().cam_track is None:
						GameVariables().cam_track = GameVariables().player

				Game._game.cheatCode += event.unicode
				if event.key == pygame.K_EQUALS:
					cheat_activate(Game._game.cheatCode)
					Game._game.cheatCode = ""
		if event.type == pygame.KEYUP:
			# fire release
			if event.key == pygame.K_SPACE:
				onKeyReleaseSpace()

	def step(self):
		''' game step '''
		
		# key hold:
		keys = pygame.key.get_pressed()
		if GameVariables().player is not None and GameVariables().player_in_control and GameVariables().player_can_move:
			# fire hold
			if keys[pygame.K_SPACE] and GameVariables().player_can_shoot and WeaponManager().current_weapon.style == WeaponStyle.CHARGABLE and WeaponManager().energising:
				onKeyHoldSpace()
				
		result = stateMachine()
		if result == 1:
			self.switch = SwitchRoom(Rooms.MAIN_MENU, False, None)
			return

		if GameVariables().game_state in [GameState.RESET]:
			return

		# use edge map scroll
		if pygame.mouse.get_focused():
			mousePos = pygame.mouse.get_pos()
			scroll = Vector()
			if mousePos[0] < EDGE_BORDER:
				scroll.x -= MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if mousePos[0] > GameVariables().screen_width - EDGE_BORDER:
				scroll.x += MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if mousePos[1] < EDGE_BORDER:
				scroll.y -= MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if mousePos[1] > GameVariables().screen_height - EDGE_BORDER:
				scroll.y += MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if scroll != Vector():
				GameVariables().cam_track = Camera(GameVariables().cam_pos + Vector(GameVariables().win_width, GameVariables().win_height)/2 + scroll)
		
		# handle scale:
		oldSize = (GameVariables().win_width, GameVariables().win_height)
		GameVariables().win_width += (GameVariables().screen_width / GameVariables().scale_factor - GameVariables().win_width) * 0.2
		GameVariables().win_height += (GameVariables().screen_height / GameVariables().scale_factor - GameVariables().win_height) * 0.2
		GameVariables().win_width = int(GameVariables().win_width)
		GameVariables().win_height = int(GameVariables().win_height)
		
		if oldSize != (GameVariables().win_width, GameVariables().win_height):
			GameVariables().win = pygame.Surface((GameVariables().win_width, GameVariables().win_height))
			GameVariables().win_width = GameVariables().win_width
			GameVariables().win_height = GameVariables().win_height
		
		# handle position:
		if GameVariables().cam_track:
			GameVariables().cam_pos += (
				(
					GameVariables().cam_track.pos - Vector(int(GameVariables().screen_width / GameVariables().scale_factor),
					int(GameVariables().screen_height / GameVariables().scale_factor)) / 2
				) - GameVariables().cam_pos
			) * 0.2
		
		# constraints:
		if GameVariables().cam_pos[1] < 0:
			GameVariables().cam_pos[1] = 0
		if GameVariables().cam_pos[1] >= MapManager().game_map.get_height() - GameVariables().win_height:
			GameVariables().cam_pos[1] = MapManager().game_map.get_height() - GameVariables().win_height
		# if GameVariables().config.option_closed_map or Game._game.darkness:
		# 	if GameVariables().cam_pos[0] < 0:
		# 		GameVariables().cam_pos[0] = 0
		# 	if GameVariables().cam_pos[0] >= MapManager().game_map.get_width() - GameVariables().win_width:
		# 		GameVariables().cam_pos[0] = MapManager().game_map.get_width() - GameVariables().win_width
		
		if Earthquake.earthquake > 0:
			GameVariables().cam_pos[0] += Earthquake.earthquake * 25 * sin(GameVariables().time_overall)
			GameVariables().cam_pos[1] += Earthquake.earthquake * 15 * sin(GameVariables().time_overall * 1.8)

		# ------- step -------
		Game._game.step()
		GameVariables().game_stable = True

		GameVariables().step_physicals()
		GameVariables().step_non_physicals()

		# step effects
		EffectManager().step()
		
		# step weapon manager
		WeaponManager().step()

		for t in Toast._toasts:
			t.step()

		if Game._game.timeTravel: 
			TimeTravel._tt.step()
		
		GameVariables().game_mode.step()

		# camera for wait to stable:
		if GameVariables().game_state == GameState.WAIT_STABLE and GameVariables().time_overall % 20 == 0:
			for worm in GameVariables().get_worms():
				if worm.stable:
					continue
				GameVariables().cam_track = worm
				break
		
		# advance timer
		TimeManager().step()
		Game._game.background.step()
		
		if MissionManager._mm:
			MissionManager._mm.step()
		
		# menu step
		if Game._game.radial_weapon_menu:
			Game._game.radial_weapon_menu.step()

		
		# reset actions
		Game._game.actionMove = False

		self.wind_flag.step()
		GameVariables().commentator.step()
	
	def draw(self, win: pygame.Surface) -> None:
		''' draw game '''
		super().draw(win)
		if GameVariables().game_state in [GameState.RESET]:
			return
		# ------- draw -------
		Game._game.background.draw(win)
		MapManager().draw_land(win)
		for p in GameVariables().get_physicals(): 
			p.draw(win)
		
		GameVariables().draw_non_physicals(win)

		# draw effects
		EffectManager().draw(win)

		Game._game.background.drawSecondary(win)
		for t in Toast._toasts:
			t.draw(win)
		
		
		# draw shooting indicator
		if GameVariables().player is not None and GameVariables().game_state in [GameState.PLAYER_PLAY, GameState.PLAYER_RETREAT] and GameVariables().player.health > 0:
			GameVariables().player.drawCursor(win)
			if GameVariables().aim_aid and WeaponManager().current_weapon.style == WeaponStyle.GUN:
				p1 = vectorCopy(GameVariables().player.pos)
				p2 = p1 + GameVariables().player.get_shooting_direction() * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))
			i = 0
			while i < 20 * WeaponManager().energy_level:
				cPos = vectorCopy(GameVariables().player.pos)
				pygame.draw.line(win, (0,0,0), point2world(cPos), point2world(cPos + GameVariables().player.get_shooting_direction() * i))
				i += 1
		
		GameVariables().draw_extra(win)
		GameVariables().draw_layers(win)
		
		# draw game play mode
		GameVariables().game_mode.draw(win)

		# HUD
		self.wind_flag.draw(win)
		TimeManager().draw(win)
		if WeaponManager().surf:
			win.blit(WeaponManager().surf, (25, 5))
		GameVariables().commentator.draw(win)
		# draw weapon indicators
		WeaponManager().draw_weapon_hint(win)
		WeaponManager().draw(win)
		
		# draw health bar
		TeamManager().step()
		TeamManager().draw(win)

		if Game._game.game_config.game_mode == GameMode.MISSIONS:
			if MissionManager._mm:
				MissionManager._mm.draw(win)
		
		
		# weapon menu:
		# move menus
		for t in Toast._toasts:
			if t.mode == Toast.bottom:
				t.updateWinPos((GameVariables().win_width/2, GameVariables().win_height))
			elif t.mode == Toast.middle:
				t.updateWinPos(Vector(GameVariables().win_width/2, GameVariables().win_height/2) - tup2vec(t.surf.get_size())/2)
		
		if Game._game.radial_weapon_menu:
			Game._game.radial_weapon_menu.draw(win)
		
		# debug:
		if self.damageText[0] != Game._game.game_stats.damage_this_turn:
			self.damageText = (Game._game.game_stats.damage_this_turn, fonts.pixel5_halo.render(str(int(Game._game.game_stats.damage_this_turn)), False, GameVariables().initial_variables.hud_color))
		win.blit(self.damageText[1], ((int(5), int(GameVariables().win_height -5 -self.damageText[1].get_height()))))

		weapon = None if WeaponManager().current_director is None else WeaponManager().current_director.weapon.name
		debug_string = f'director: {weapon}'
		debug_text = fonts.pixel5_halo.render(debug_string, False, GameVariables().initial_variables.hud_color)
		win.blit(debug_text, (win.get_width() - debug_text.get_width(), win.get_height() - debug_text.get_height()))
		
		# draw loading screen
		if GameVariables().game_state in [GameState.RESET]:
			win.fill((0,0,0))
			pos = (GameVariables().win_width/2 - Game._game.loadingSurf.get_width()/2, GameVariables().win_height/2 - Game._game.loadingSurf.get_height()/2)
			win.blit(Game._game.loadingSurf, pos)
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + 20), (pos[0] + Game._game.loadingSurf.get_width(), pos[1] + 20))
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + Game._game.loadingSurf.get_height() + 20), (pos[0] + Game._game.loadingSurf.get_width(), pos[1] + Game._game.loadingSurf.get_height() + 20))
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + 20), (pos[0], pos[1] + Game._game.loadingSurf.get_height() + 20))
			pygame.draw.line(win, (255,255,255), (pos[0] + Game._game.loadingSurf.get_width(), pos[1] + 20), (pos[0] + Game._game.loadingSurf.get_width(), pos[1] + Game._game.loadingSurf.get_height() + 20))
			pygame.draw.rect(win, (255,255,255), ((pos[0], pos[1] + 20), ((Game._game.lstep/Game._game.lstepmax)*Game._game.loadingSurf.get_width(), Game._game.loadingSurf.get_height())))


wip = '''refactoring stage:
	still in wip:
		major: reseting a game keeps every state of previous game
		collecting weapons create make the number float, not the nemae
		water rise
		loading screen
		optimize fire drawing for it is slowing
		optimize laser (?)
		holding mjolnir
		winning
		darkness outside area (either close or draw black)
		decrease rope count
		dont decrease parachute, trampoline if not opened
		icicle werid behaviour on hit
		minecraft weapons
	'''


def main():
	print(wip)
	pygame.init()
	fps_clock = pygame.time.Clock()
	GameVariables().win_width = int(GameVariables().screen_width / GameVariables().scale_factor)
	GameVariables().win_height = int(GameVariables().screen_height / GameVariables().scale_factor)

	GameVariables().win = pygame.Surface((GameVariables().win_width, GameVariables().win_height))

	pygame.display.set_caption("Simon's Worms")
	screen = pygame.display.set_mode((GameVariables().screen_width, GameVariables().screen_height), pygame.DOUBLEBUF)

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
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				done = True
			current_room.handle_pygame_event(event)
		
		try:
			# step
			current_room.step()
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

			# draw
			current_room.draw(GameVariables().win)
		except Exception:
			print(traceback.format_exc())

		pygame.transform.scale(GameVariables().win, screen.get_rect().size, screen)
		pygame.display.update()

		fps_clock.tick(GameVariables().fps)

	pygame.quit()


if __name__ == "__main__":
	main()
	
