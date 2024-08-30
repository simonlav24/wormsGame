

from math import pi, cos, sin, atan2, degrees
from random import randint, uniform, choice
import os
from typing import Any

import pygame
import pygame.gfxdraw

from common import *
from common.vector import *
from common.game_config import *
from common.game_event import EventComment
from common.game_play_mode import GamePlay, TerminatorGamePlay, DarknessGamePlay

from mainMenus import mainMenu, pauseMenu, initGui, updateWin

from game.time_manager import TimeManager
from game.map_manager import *
from game.background import BackGround
from game.visual_effects import *

from entities.physical_entity import PhysObj
from entities.debrie import Debrie
from game.world_effects import *

from game.hud import *
from gui.radial_menu import *
from game.team_manager import TeamManager

from entities.worm_tools import *
from entities.props import *
from entities.worm import Worm
from entities.shooting_target import ShootingTarget
from entities.deployables import *

from weapons.weapon_manager import *
from weapons.missiles import *
from weapons.grenades import *
from weapons.cluster_grenade import ClusterGrenade
from weapons.bombs import *
from weapons.fire_weapons import *
from weapons.artillery import Artillery
from weapons.guided_missile import GuidedMissile
from weapons.tools import *
from weapons.bubble import Bubble
from weapons.aerial import *
from weapons.shoot_gun import *
from weapons.guns import *
from weapons.long_bow import LongBow
from weapons.mine import *
from weapons.plants import *
from weapons.bee_hive import BeeHive
from weapons.vortex import VortexGrenade
from weapons.pokeball import PokeBall
from weapons.snail import SnailShell
from weapons.portal import Portal, firePortal
from weapons.green_shell import GreenShell
from weapons.ender_pearl import EndPearl
from weapons.raon import Raon
from weapons.acid import AcidBottle
from weapons.sentry_gun import SentryGun
from weapons.electric import ElectricGrenade, ElectroBoom
from weapons.fireworks import fireFireWork
from weapons.covid import Covid19

import globals


def getGlobals():
	global fpsClock, fps, screenWidth, screenHeight, win, screen
	fpsClock = globals.fpsClock
	fps = GameVariables().fps
	screenWidth = globals.screenWidth
	screenHeight = globals.screenHeight
	win = globals.win
	screen = globals.screen

globals.globalsInit()
initGui()
getGlobals()



class Game:
	_game = None
	def __init__(self, game_config: GameConfig=None):
		Game._game = self
		globals.game_manager = self

		self.game_play = GamePlay()
		self.evaluate_config(game_config)
		GameVariables().config = game_config
		
		self.map_manager = MapManager()
		self.background = BackGround(feels[GameVariables().config.feel_index], GameVariables().config.option_darkness)

		self.clearLists()
		
		self.initiateGameVariables()
		self.game_vars = GameVariables()

		self.damageThisTurn = 0
		self.mostDamage = (0, None)

		self.killList = []
		self.lstep = 0
		self.lstepmax = 1

		self.loadingSurf = fonts.pixel10.render("Simon's Worms Loading", False, WHITE)

		self.endGameDict = None

		self.imageMjolnir = pygame.Surface((24,31), pygame.SRCALPHA)
		self.imageMjolnir.blit(sprites.sprite_atlas, (0,0), (100, 32, 24, 31))

		self.radial_weapon_menu: RadialMenu = None

	@property
	def player(self):
		return Worm.player
	
	@player.setter
	def player(self, value: Worm):
		Worm.player = value

	@property
	def win(self) -> pygame.Surface:
		return globals.win

	@property
	def gameMode(self) -> GameMode:
		return self.game_config.game_mode
		
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
		random_placing()
		
		# place objects
		if not self.game_config.option_digging:
			amount = randint(2,4)
			for _ in range(amount):
				mine = place_object(Mine, None, True)
				mine.damp = 0.1

		amount = randint(2,4)
		for _ in range(amount):
			place_object(PetrolCan, None, False)

		if not self.game_config.option_digging:
			amount = randint(0, 2)
			for _ in range(amount):
				place_object(PlantSeed, ((0,0), (0,0), 0, PlantMode.VENUS), False)

		# give random legendary starting weapons:
		give_random_legendary_weapon(1)

		# choose starting worm
		w = TeamManager().current_team.worms.pop(0)
		TeamManager().current_team.worms.append(w)
				
		if Game._game.game_config.random_mode != RandomMode.NONE:
			w = choice(TeamManager().current_team.worms)
		
		Worm.player = w
		GameVariables().cam_track = w

		# reset time
		TimeManager().time_reset()
		WeaponManager().switch_weapon(WeaponManager().current_weapon)

		# randomize wind
		GameVariables().physics.wind = uniform(-1, 1)

		# handle game mode
		self.init_handle_game_mode()

	def init_handle_game_mode(self) -> None:
		''' on init, handle game mode parameter and variables '''
		# targets:
		if Game._game.gameMode == GameMode.TARGETS:
			for i in range(ShootingTarget.numTargets):
				ShootingTarget()

		# digging match
		if Game._game.game_config.option_digging:
			for _ in range(80):
				mine = place_object(Mine, None)
				mine.damp = 0.1
			# more digging
			for team in TeamManager().teams:
				team.ammo(WeaponManager()["minigun"], 5)
				team.ammo(WeaponManager()["drill missile"], 3)
				team.ammo(WeaponManager()["laser gun"], 3)
			GameVariables().config.option_closed_map = True

		# david and goliath
		if Game._game.gameMode == GameMode.DAVID_AND_GOLIATH:
			for team in TeamManager().teams:
				length = len(team.worms)
				for i in range(length):
					if i == 0:
						team.worms[i].health = Game._game.game_config.worm_initial_health + (length - 1) * (Game._game.game_config.worm_initial_health//2)
						team.worms[i].healthStr = fonts.pixel5.render(str(team.worms[i].health), False, team.worms[i].team.color)
					else:
						team.worms[i].health = (Game._game.game_config.worm_initial_health//2)
						team.worms[i].healthStr = fonts.pixel5.render(str(team.worms[i].health), False, team.worms[i].team.color)
			Game._game.game_config.worm_initial_health = TeamManager().teams[0].worms[0].health
		
		# disable points in battle
		if Game._game.gameMode in [GameMode.BATTLE]:
			HealthBar.drawPoints = False

		# if Game._game.darkness:
		# 	WeaponManager().render_weapon_count()
		# 	for team in TeamManager().teams:
		# 		team.ammo(WeaponManager().weapon_dict['flare'], 3)

		GamePlay().on_game_init()

		if Game._game.gameMode == GameMode.CAPTURE_THE_FLAG:
			place_object(Flag, None)

		if Game._game.gameMode == GameMode.ARENA:
			ArenaManager()

		if Game._game.gameMode == GameMode.MISSIONS:
			MissionManager()
			globals.time_manager.turnTime += 10
			MissionManager._mm.cycle()

			
	def point_to_world(self, point):
		return (int(point[0]) - int(GameVariables().cam_pos[0]), int(point[1]) - int(GameVariables().cam_pos[1]))

	def clearLists(self):
		# clear lists
		PhysObj._mines.clear()
		Debrie._debries.clear()
		SentryGun._sentries.clear()
		Portal._reg.clear()
		Venus._reg.clear()
		GreenShell._shells.clear()
		Flare._flares.clear()
		Flag.flags.clear()
		ShootingTarget._reg.clear()
		Raon._raons.clear()
		Seagull._reg.clear()
		Chum._chums.clear()

		ArenaManager._arena = None
		MissionManager._mm = None
	
	def create_map(self) -> None:
		''' create game map '''
		custom_height = 512
		if self.game_config.map_ratio != -1:
			custom_height = self.game_config.map_ratio

		if self.game_config.option_digging:
			self.map_manager.create_map_digging(custom_height)
		elif 'PerlinMaps' in self.game_config.map_path:
			self.map_manager.create_map_image(self.game_config.map_path, custom_height, True)
		else:
			self.map_manager.create_map_image(self.game_config.map_path, custom_height, self.game_config.is_recolor)
		
	def dropArtifact(self, artifact, pos, comment=False):
		deploy = False
		if not pos:
			# find good position for artifact
			goodPlace = False
			count = 0
			deploy = False
			while not goodPlace:
				pos = Vector(randint(20, self.map_manager.game_map.get_width() - 20), -50)
				if not self.map_manager.is_ground_at((pos.x, 0)):
					goodPlace = True
				count += 1
				if count > 2000:
					break
			if not goodPlace:
				deploy = True
		
		if not deploy:
			m = artifact(pos)
		else:
			m = deploy_pack(artifact)
		
		if comment:
			m.commentCreation()
		GameVariables().cam_track = m

	def initiateGameVariables(self):
		self.waterRise = False # whether water rises at the end of each turn
		self.waterRising = False # water rises in current state
		self.raoning = False  # raons advancing in current state
		self.deploying = False # deploying pack in current state
		self.sentring = False # sentry guns active in current state
		self.deployingArtifact = False  # deploying artifacts in current state

		self.cheatCode = "" # cheat code
		self.holdArtifact = True # whether to hold artifact
		self.worldArtifacts = [MJOLNIR, PLANT_MASTER, AVATAR, MINECRAFT] # world artifacts
		self.worldArtifactsClasses = [Mjolnir, MagicLeaf, Avatar, PickAxeArtifact]
		self.trigerArtifact = False # whether to trigger artifact drop next turn
		self.shotCount = 0 # number of gun shots fired

		self.energising = False
		self.energyLevel = 0
		self.fireWeapon = False

		self.actionMove = False

		self.aimAid = False
		self.switchingWorms = False
		self.timeTravel = False
		
	def girder(self, pos):
		surf = pygame.Surface((GameVariables().girder_size, 10)).convert_alpha()
		for i in range(GameVariables().girder_size // 16 + 1):
			surf.blit(sprites.sprite_atlas, (i * 16, 0), (64,80,16,16))
		surfGround = pygame.transform.rotate(surf, GameVariables().girder_angle)
		self.map_manager.ground_map.blit(surfGround, (int(pos[0] - surfGround.get_width()/2), int(pos[1] - surfGround.get_height()/2)) )
		surf.fill(GRD)
		surfMap = pygame.transform.rotate(surf, GameVariables().girder_angle)
		self.map_manager.game_map.blit(surfMap, (int(pos[0] - surfMap.get_width()/2), int(pos[1] - surfMap.get_height()/2)) )
	
	def drawTrampolineHint(self):
		surf = pygame.Surface((24, 7), pygame.SRCALPHA)
		surf.blit(sprites.sprite_atlas, (0,0), (100, 117, 24, 7))
		position = self.player.pos + self.player.get_shooting_direction() * 20
		anchored = False
		for i in range(25):
			cpos = position.y + i
			if MapManager().is_ground_at(Vector(position.x, cpos)):
				anchored = True
				break
		if anchored:
			surf.set_alpha(200)
		else:
			surf.set_alpha(100)
		
		win.blit(surf, point2world(position - Vector(24,7) / 2))
	
	def evaluate_config(self, game_config: GameConfig):
		self.game_config: GameConfig = game_config

		if self.game_config.feel_index == -1:
			self.game_config.feel_index = randint(0, len(feels) - 1)

		game_mode_map = {
			GameMode.TERMINATOR: TerminatorGamePlay
		}
		self.game_play.add_mode(game_mode_map.get(self.game_config.game_mode, None))

		if self.game_config.option_darkness:
			self.game_play.modes.append(DarknessGamePlay())

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
	
	def addToScoreList(self, amount=1):
		"""add to score list if points, list entry: (surf, name, score)"""
		if len(self.killList) > 0 and self.killList[0][1] == self.player.name_str:
			amount += self.killList[0][2]
			self.killList.pop(0)
		string = self.player.name_str + ": " + str(amount)
		self.killList.insert(0, (fonts.pixel5_halo.render(string, False, GameVariables().initial_variables.hud_color), self.player.name_str, amount))

	def lstepper(self):
		self.lstep += 1
		pos = (GameVariables().win_width/2 - Game._game.loadingSurf.get_width()/2, GameVariables().win_height/2 - Game._game.loadingSurf.get_height()/2)
		width = Game._game.loadingSurf.get_width()
		height = Game._game.loadingSurf.get_height()
		pygame.draw.rect(win, (255,255,255), ((pos[0], pos[1] + 20), ((self.lstep / self.lstepmax)*width, height)))
		screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
		pygame.display.update()



# todo: determine where this belongs
def giveGoodPlace(div = 0, girderPlace = True):
	goodPlace = False
	counter = 0
	
	if Game._game.game_config.option_forts and not div == -1:
		half = MapManager().game_map.get_width() / TeamManager().num_of_teams
		Slice = div % TeamManager().num_of_teams
		
		left = half * Slice
		right = left + half
		if left <= 0: left += 6
		if right >= MapManager().game_map.get_width(): right -= 6
	else:
		left, right = 6, MapManager().game_map.get_width() - 6
	
	if Game._game.game_config.option_digging:
		while not goodPlace:
			place = Vector(randint(int(left), int(right)), randint(6, MapManager().game_map.get_height() - 50))
			goodPlace = True
			for worm in GameVariables().get_worms():
				if distus(worm.pos, place) < 5625:
					goodPlace = False
					break
				if  not goodPlace:
					continue
		return place
	
	while not goodPlace:
		# give rand place
		counter += 1
		goodPlace = True
		place = Vector(randint(int(left), int(right)), randint(6, MapManager().game_map.get_height() - 6))
		
		# if in MapManager().ground_map 
		if MapManager().is_ground_around(place):
			goodPlace = False
			continue
		
		if counter > 8000:
			# if too many iterations, girder place
			if not girderPlace:
				return None
			for worm in GameVariables().get_worms():
				if distus(worm.pos, place) < 2500:
					goodPlace = False
					break
			if  not goodPlace:
				continue
			Game._game.girder(place + Vector(0,20))
			return place
		
		# put place down
		y = place.y
		for i in range(MapManager().game_map.get_height()):
			if y + i >= MapManager().game_map.get_height():
				goodPlace = False
				break
			if MapManager().game_map.get_at((place.x, y + i)) == GRD or MapManager().worm_col_map.get_at((place.x, y + i)) != (0,0,0) or MapManager().objects_col_map.get_at((place.x, y + i)) != (0,0,0):
				y = y + i - 7
				break
		if  not goodPlace:
			continue
		place.y = y
		
		# check for nearby worms in radius 50
		for worm in GameVariables().get_worms():
			if distus(worm.pos, place) < 2500:
				goodPlace = False
				break
		if  not goodPlace:
			continue
		
		# check for nearby mines in radius 40
		for mine in PhysObj._mines:
			if distus(mine.pos, place) < 1600:
				goodPlace = False
				break
		if  not goodPlace:
			continue
		
		# check for nearby petrol cans in radius 30
		for can in PetrolCan._cans:
			if distus(can.pos, place) < 1600:
				goodPlace = False
				break
		if  not goodPlace:
			continue
		
		# if all conditions are met, make hole and place
		if MapManager().is_ground_around(place):
			pygame.draw.circle(MapManager().game_map, SKY, place.vec2tup(), 5)
			pygame.draw.circle(MapManager().ground_map, SKY, place.vec2tup(), 5)
	return place

def place_object(cls: Any, args, girder_place: bool=False) -> Any:
	''' create an instance of cls, return the last created'''
	place = giveGoodPlace(-1, girder_place)
	if place:
		if args is None:
			instance = cls()
		else:
			instance = cls(*args)
		instance.pos = Vector(place.x, place.y - 2)
	else:
		return None
	return instance


################################################################################ Objects


# refactor gas first
class GasGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		super().__init__(pos, direction, energy, "gas grenade")
		self.radius = 2
		self.color = (113,117,41)
		self.damp = 0.5
		self.state = "throw"

	def death_response(self):
		boom(self.pos, 20)
		for i in range(40):
			vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1,1.5)
			GasParticles._sp.addSmoke(self.pos, vel, color=(102, 255, 127))
	
	def secondaryStep(self):
		GameVariables().game_distable()
		self.angle -= self.vel.x * 4
		self.timer += 1
		if self.state == "throw":
			if self.timer >= GameVariables().fuse_time:
				self.state = "release"
		if self.state == "release":
			if self.timer % 3 == 0:
				GasParticles._sp.addSmoke(self.pos, vectorUnitRandom(), color=(102, 255, 127))
			if self.timer >= GameVariables().fuse_time + 5 * fps:
				self.dead = True

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
			fire(TimeTravel._tt.timeTravelList["weapon"])
			GameVariables().unregister_non_physical(self)
			TimeTravel._tt.timeTravelPositions = []
			TimeTravel._tt.timeTravelList = {}
			return
		self.pos = self.positions.pop(0)
		if len(self.positions) <= self.stepsForEnergy:
			self.energy += 0.05
			
		self.time_counter += 1
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, Worm.player.color, point2world(self.pos), 3+1)
		facing = self.facings.pop(0)
		win.blit(pygame.transform.flip(self.surf, facing == 1, False), point2world(tup2vec(self.pos) - tup2vec(self.surf.get_size()) / 2))
		win.blit(self.nameSurf , ((int(self.pos[0]) - int(GameVariables().cam_pos[0]) - int(self.nameSurf.get_size()[0]/2)), (int(self.pos[1]) - int(GameVariables().cam_pos[1]) - 21)))
		pygame.draw.rect(win, (220,220,220),(int(self.pos[0]) -10 -int(GameVariables().cam_pos[0]), int(self.pos[1]) -15 -int(GameVariables().cam_pos[1]), 20,3))
		value = 20 * self.health / Game._game.game_config.worm_initial_health
		if value < 1:
			value = 1
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
		self.timeTravelList["surf"] = Worm.player.surf
		self.timeTravelList["name"] = Worm.player.name
		self.timeTravelList["health"] = Worm.player.health
		self.timeTravelList["initial pos"] = vectorCopy(Worm.player.pos)
		self.timeTravelList["time_counter in turn"] = TimeManager().time_counter
	def timeTravelRecord(self):
		self.timeTravelPositions.append(Worm.player.pos.vec2tup())
		self.timeTravelFacings.append(Worm.player.facing)
	def timeTravelPlay(self):
		TimeManager().time_counter = self.timeTravelList["time_counter in turn"]
		Game._game.timeTravel = False
		self.timeTravelList["weapon"] = WeaponManager().current_weapon
		self.timeTravelList["weaponOrigin"] = vectorCopy(Worm.player.pos)
		self.timeTravelList["energy"] = Game._game.energyLevel
		self.timeTravelList["weaponDir"] = Worm.player.get_shooting_direction()
		Worm.player.health = self.timeTravelList["health"]
		if Worm.healthMode == 1:
			Worm.player.healthStr = fonts.pixel5.render(str(Worm.player.health), False, Worm.player.team.color)
		Worm.player.pos = self.timeTravelList["initial pos"]
		Worm.player.vel *= 0
		TimeAgent()
	def timeTravelReset(self):
		self.timeTravelFire = False
		self.timeTravelPositions = []
		self.timeTravelList = {}
	def step(self):
		self.timeTravelRecord()

class Armageddon:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.stable = False
		self.is_boom_affected = False
		self.timer = 700
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			GameVariables().unregister_non_physical(self)
			return
		if GameVariables().time_overall % 10 == 0:
			for i in range(randint(1,2)):
				x = randint(-100, MapManager().game_map.get_width() + 100)
				m = Missile((x, -10), Vector(randint(-10,10), 5).normalize(), 1)
				m.is_wind_affected = 0
				m.boomRadius = 40
	def draw(self, win: pygame.Surface):
		pass

class Flag(PhysObj):
	flags = []
	def __init__(self, pos=(0,0)):
		super().__init__(pos)
		Flag.flags.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.radius = 3.5
		self.color = (220,0,0)
		self.damp = 0.1
	def secondaryStep(self):
		if Worm.player:
			if not Worm.player in GameVariables().get_worms():
				return
			if dist(Worm.player.pos, self.pos) < self.radius + Worm.player.radius:
				# worm has flag
				Worm.player.flagHolder = True
				Worm.player.team.flagHolder = True
				self.remove_from_game()
				Flag.flags.remove(self)
				return
	def on_out_of_map(self):
		Flag.flags.remove(self)
		p = deploy_pack(Flag)
		GameVariables().cam_track = p
	def draw(self, win: pygame.Surface):
		pygame.draw.line(win, (51, 51, 0), point2world(self.pos + Vector(0, self.radius)), point2world(self.pos + Vector(0, -3 * self.radius)))
		pygame.draw.rect(win, self.color, (point2world(self.pos + Vector(1, -3 * self.radius)), (self.radius*2, self.radius*2)))








class MjolnirThrow(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		GameVariables().move_to_back_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.damp = 0.3
		self.rotating = True
		self.angle = 0
		self.stableCount = 0
		Game._game.holdArtifact = False
		self.worms = []

	def secondaryStep(self):
		if self.vel.getMag() > 1:
			self.rotating = True
		else:
			self.rotating = False
		if self.rotating:
			self.angle = -degrees(self.vel.getAngle()) - 90
		
		if self.stable:
			self.stableCount += 1
		else:
			self.stableCount = 0
		if self.stableCount > 20:
			self.remove_from_game()
			self.returnToWorm()
		
		# electrocute
		self.worms = []
		for worm in GameVariables().get_worms():
			if worm in TeamManager().current_team.worms:
				continue
			if distus(self.pos, worm.pos) < 10000:
				self.worms.append(worm)
		
		for worm in self.worms:
			if randint(1,100) < 5:
				worm.damage(randint(1,8))
				a = lambda x : 1 if x >= 0 else -1
				worm.vel -= Vector(a(self.pos.x - worm.pos.x)*uniform(1.2,2.2), uniform(1.2,3.2))
			if worm.health <= 0:
				self.worms.remove(worm)
		
		GameVariables().game_distable()
	def returnToWorm(self):
		MjolnirReturn(self.pos, self.angle)
	def on_collision(self, ppos):
		vel = self.vel.getMag()
		# print(vel, vel * 4)
		if vel > 4:
			boom(self.pos, max(20, 4 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	def on_out_of_map(self):
		self.returnToWorm()
	def draw(self, win: pygame.Surface):
		for worm in self.worms:
			draw_lightning(win, self.pos, worm.pos)
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirReturn:
	def __init__(self, pos, angle):
		GameVariables().register_non_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.acc = Vector()
		self.vel = Vector()
		self.angle = angle
		GameVariables().cam_track = self
		self.speedLimit = 8
	def step(self):
		self.acc = seek(self, Worm.player.pos, self.speedLimit, 1)
		
		self.vel += self.acc
		self.vel.limit(self.speedLimit)
		self.pos += self.vel
		
		self.angle += (0 - self.angle) * 0.1
		GameVariables().game_distable()
		if distus(self.pos, Worm.player.pos) < Worm.player.radius * Worm.player.radius * 2:
			GameVariables().unregister_non_physical(self)
			Game._game.holdArtifact = True
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Artifact(PhysObj):
	def __init__(self, pos):
		super().__init__(pos)
		self.pos = pos
		self.vel = Vector(randint(-2,2), 0)
		self.radius = 3
		self.damp = 0.2
		self.angle = 0
		GameVariables().cam_track = self
		self.artifact = self.getArtifact()
		self.setSurf()
	def getArtifact(self):
		pass
	def setSurf(self):
		pass
	def commentCreation(self):
		pass
	def commentPicked(self):
		pass
	def secondaryStep(self):
		# pick up
		if dist(Worm.player.pos, self.pos) < self.radius + Worm.player.radius + 5 and not Worm.player.health <= 0\
			and not len(Worm.player.team.artifacts) > 0: 
			self.remove_from_game()
			Game._game.worldArtifacts.remove(self.artifact)
			self.commentPicked()
			TeamManager().current_team.artifacts.append(self.artifact)
			# add artifacts moves:
			WeaponManager().addArtifactMoves(self.artifact)
			return
		self.trenaryStep()
	def remove_from_game(self):
		super().remove_from_game()
		Game._game.worldArtifacts.append(self.artifact)
	def trenaryStep(self):
		pass
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Mjolnir(Artifact):
	def getArtifact(self):
		return MJOLNIR
	
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0,112,16,16))
	
	def commentCreation(self):
		GameEvents().post(EventComment([{'text': "a gift from the gods"}]))
	
	def commentPicked(self):
		GameEvents().post(EventComment([{'text': Worm.player.name_str, 'color': TeamManager().current_team.color}, {'text': " is worthy to wield mjolnir!"}]))
	
	def trenaryStep(self):
		if self.vel.getMag() > 1:
			self.angle = -degrees(self.vel.getAngle()) - 90
	
	def on_collision(self, ppos):
		vel = self.vel.getMag()
		if vel > 4:
			boom(self.pos, max(20, 2 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	
class MjolnirFly(PhysObj):
	flying = False
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.damp = 0.3
		self.rotating = True
		self.angle = 0
		Game._game.holdArtifact = False
		MjolnirFly.flying = True
	def secondaryStep(self):
		if self.vel.getMag() > 1:
			self.rotating = True
		else:
			self.rotating = False
		if self.rotating:
			self.angle = -degrees(self.vel.getAngle()) - 90
			
		Worm.player.pos = vectorCopy(self.pos)
		Worm.player.vel = Vector()
	def on_collision(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() - GameVariables().water_level or testPos.x < 0:
				if GameVariables().config.option_closed_map:
					response += ppos - testPos
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if MapManager().game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		
		self.remove_from_game()
		response.normalize()
		pos = self.pos + response * (Worm.player.radius + 2)
		Worm.player.pos = pos
		
	def remove_from_game(self):
		GameVariables().unregister_physical(self)
		MjolnirFly.flying = False
		Game._game.holdArtifact = True
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirStrike:
	def __init__(self):
		self.pos = Worm.player.pos
		GameVariables().register_non_physical(self)
		Game._game.holdArtifact = False
		self.stage = 0
		self.timer = 0
		self.angle = 0
		self.worms = []
		self.facing = Worm.player.facing
		Worm.player.is_boom_affected = False
		self.radius = 0
	def step(self):
		self.pos = Worm.player.pos
		self.facing = Worm.player.facing
		if self.stage == 0:
			self.angle += 1
			if self.timer >= fps * 4:
				self.stage = 1
				self.timer = 0
			# electrocute:
			self.worms = []
			for worm in GameVariables().get_worms():
				if worm in TeamManager().current_team.worms:
					continue
				if self.pos.x - 60 < worm.pos.x and worm.pos.x < self.pos.x + 60 and worm.pos.y <= self.pos.y:
					self.worms.append(worm)
					
			for worm in self.worms:
				if randint(1,100) < 5:
					worm.damage(randint(1,8))
					a = lambda x : 1 if x >= 0 else -1
					worm.vel -= Vector(a(self.pos.x - worm.pos.x)*uniform(1.2,2.2), uniform(1.2,3.2))
				if worm.health <= 0:
					self.worms.remove(worm)
		elif self.stage == 1:
			self.angle += -30
			if self.timer >= fps * 0.25:
				boom(self.pos, 40)
				GameVariables().unregister_non_physical(self)
				Worm.player.is_boom_affected = True
		self.timer += 1
		GameVariables().game_distable()
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		surf = pygame.transform.flip(surf, self.facing == LEFT, False)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2 + Vector(0, -5)))
		draw_lightning(win, Vector(self.pos.x, 0), self.pos)
		for worm in self.worms:
			draw_lightning(win, Vector(self.pos.x, randint(0, int(self.pos.y))), worm.pos)

class MagicLeaf(Artifact):
	def getArtifact(self):
		return PLANT_MASTER
	
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (48, 64, 16,16))

		self.is_wind_affected = True
		self.turbulance = vectorUnitRandom()
	
	def commentCreation(self):
		GameEvents().post(EventComment([{'text': "a leaf of heavens tree"}]))
	
	def commentPicked(self):
		GameEvents().post(EventComment([{'text': Worm.player.name_str, 'color': TeamManager().current_team.color}, {'text': "  became master of plants"}]))
	
	def trenaryStep(self):
		self.angle += self.vel.x*4

		# aerodynamic drag
		self.turbulance.rotate(uniform(-1, 1))
		velocity = self.vel.getMag()
		force =  - 0.15 * 0.5 * velocity * velocity * normalize(self.vel)
		force += self.turbulance * 0.1
		self.acc += force
	
	def on_collision(self, ppos):
		self.turbulance *= 0.9







class PlantControl:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.timer = 5 * fps
		GameVariables().player_can_move = False
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			GameVariables().unregister_non_physical(self)
			GameVariables().player_can_move = True
		if pygame.key.get_pressed()[pygame.K_LEFT]:
			for plant in Venus._reg:
				plant.direction.rotate(-0.1)
		elif pygame.key.get_pressed()[pygame.K_RIGHT]:
			for plant in Venus._reg:
				plant.direction.rotate(0.1)
		GameVariables().game_distable()
	def draw(self, win: pygame.Surface):
		pass

class MasterOfPuppets:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.springs = []
		self.timer = 0
		for worm in GameVariables().get_worms():
			# point = Vector(worm.pos.x, 0)
			for t in range(200):
				posToCheck = worm.pos - Vector(0, t * 5)
				if MapManager().is_ground_at(posToCheck):
					break
				if posToCheck.y < 0:
					break
			rest = dist(posToCheck, worm.pos) / 2
			p = PointSpring(0.01, rest, worm, posToCheck)
			self.springs.append(p)
	def step(self):
		self.timer += 1
		if self.timer >= fps * 15:
			self.springs.clear()
			GameVariables().unregister_non_physical(self)
		for p in self.springs:
			p.step()
	def draw(self, win: pygame.Surface):
		for p in self.springs:
			p.draw(win)

class PointSpring:
	def __init__(self, k, rest, obj, point):
		self.k = k
		self.rest = rest
		self.obj = obj
		self.point = point
		self.alive = True
	def step(self):
		force = self.point - self.obj.pos
		x = force.getMag() - self.rest
		x = x * -1
		force.setMag(-1 * self.k * x)
		
		if distus(self.obj.pos, self.point) > self.rest * self.rest:
			self.obj.acc += force
		if not self.obj.alive:
			self.alive = False
	def draw(self, win: pygame.Surface):
		if not self.alive:
			return
		pygame.draw.line(win, (255, 220, 0), point2world(self.obj.pos), point2world(self.point))

class Tornado:
	def __init__(self):
		self.width = 30
		self.pos = Worm.player.pos + Vector(Worm.player.radius + self.width / 2, 0) * Worm.player.facing
		self.facing = Worm.player.facing
		GameVariables().register_non_physical(self)
		amount = MapManager().game_map.get_height() // 10
		self.points = [Vector(0, 10 * i) for i in range(amount)]
		self.swirles = []
		self.sizes = [self.width + randint(0,20) for i in self.points]
		for _ in self.points:
			xRadius = 0
			yRadius = 0
			theta = uniform(0, 2 * pi)
			self.swirles.append([xRadius, yRadius, theta])
		self.timer = 0
		self.speed = 2
		self.radius = 0
	def step(self):
		GameVariables().game_distable()
		if self.timer < 2 * fps:
			for i, swirl in enumerate(self.swirles):
				swirl[0] = min(self.timer, self.sizes[i])
				swirl[1] = min(self.timer / 3, 10)
		self.pos.x += self.speed * self.facing
		for swirl in self.swirles:
			swirl[2] += 0.1 * uniform(0.8, 1.2)
		rect = (Vector(self.pos.x - self.width / 2, 0), Vector(self.width, MapManager().game_map.get_height()))
		for obj in GameVariables().get_physicals():
			if obj.pos.x > rect[0][0] and obj.pos.x <= rect[0][0] + rect[1][0]:
				if obj.vel.y > -2:
					obj.acc.y += -0.5
				obj.acc.x += 0.5 * sin(self.timer/6)
		if self.timer >= fps * 10 and len(self.swirles) > 0:
			self.swirles.pop(-1)
			if len(self.swirles) == 0:
				GameVariables().unregister_non_physical(self)
		self.timer += 1
	def draw(self, win: pygame.Surface):
		for i, swirl in enumerate(self.swirles):
			five = [point2world(Vector(swirl[0] * cos(swirl[2] + t/5) + self.pos.x, 10 * i + swirl[1] * sin(swirl[2] + t/5))) for t in range(5)]
			pygame.draw.lines(win, (255,255,255), False, five)

class Avatar(Artifact):
	def getArtifact(self):
		return AVATAR
	
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0,112,16,16))
	
	def commentCreation(self):
		GameEvents().post(EventComment([{'text': "who is the next avatar?"}]))
	
	def commentPicked(self):
		GameEvents().post(EventComment([{'text': 'everything changed when the '}, {'text': TeamManager().current_team.name, 'color': TeamManager().current_team.color}, {'text': ' attacked'}]))
	
	def trenaryStep(self):
		self.angle -= self.vel.x*4

class PickAxe:
	_pa = None
	def __init__(self):
		PickAxe._pa = self
		GameVariables().register_non_physical(self)
		self.count = 6
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "pick axe")
		self.animating = 0
	def mine(self):
		worm = Worm.player
		position = worm.pos + vectorFromAngle(worm.shoot_angle, 20)
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

		colors = []
		for i in range(10):
			sample = (position + Vector(8,8) + vectorUnitRandom() * uniform(0,8)).vec2tupint()
			if MapManager().is_on_map(sample):
				color = MapManager().ground_map.get_at(sample)
				if not color == SKY:
					colors.append(color)
		if len(colors) == 0:
			colors = Blast._color

		for i in range(16):
			d = Debrie(position + Vector(8,8), 8, colors, 2, False)
			d.radius = choice([2,1])

		pygame.draw.rect(MapManager().game_map, SKY, (position, Vector(16,16)))
		pygame.draw.rect(MapManager().ground_map, SKY, (position, Vector(16,16)))

		self.animating = 90

		self.count -= 1
		if self.count == 0:
			return True
		return False
	def step(self):
		if self.count == 0:
			GameVariables().unregister_non_physical(self)
			PickAxe._pa = None
		if self.animating > 0:
			self.animating -= 5
			self.animating = max(self.animating, 0)
		if not Worm.player.alive:
			GameVariables().unregister_non_physical(self)
			PickAxe._pa = None
	def draw(self, win: pygame.Surface):
		worm = Worm.player
		position = worm.pos + vectorFromAngle(worm.shoot_angle, 20)
		# closest grid of 16
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)
		pygame.draw.rect(win, (255,255,255), (point2world(position), Vector(16,16)), 1)

		angle = - self.animating * worm.facing

		weaponSurf = pygame.transform.rotate(pygame.transform.flip(self.surf, worm.facing == LEFT, False), angle)
		win.blit(weaponSurf, point2world(worm.pos - tup2vec(weaponSurf.get_size())/2 + Vector(worm.facing * 9, -4)))

class MineBuild:
	_mb = None
	def __init__(self):
		MineBuild._mb = self
		GameVariables().register_non_physical(self)
		self.count = 6
		self.locations = []
	def build(self):
		worm = Worm.player
		position = worm.pos + vectorFromAngle(worm.shoot_angle, 20)
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

		pygame.draw.rect(MapManager().game_map, GRD, (position, Vector(16,16)))
		if position + Vector(0,16) in self.locations:
			blit_weapon_sprite(MapManager().ground_map, position, "build")
			MapManager().ground_map.blit(sprites.sprite_atlas, position + Vector(0,16), (80,112,16,16))
		elif position + Vector(0,-16) in self.locations:
			MapManager().ground_map.blit(sprites.sprite_atlas, position, (80,112,16,16))
		else:
			blit_weapon_sprite(MapManager().ground_map, position, "build")

		self.locations.append(position)
		
		self.count -= 1
		if self.count == 0:
			return True
		return False
	def step(self):
		if self.count == 0:
			GameVariables().unregister_non_physical(self)
			MineBuild._mb = None
			
		if not Worm.player.alive:
			GameVariables().unregister_non_physical(self)
			MineBuild._mb = None
	def draw(self, win: pygame.Surface):
		worm = Worm.player
		position = worm.pos + vectorFromAngle(worm.shoot_angle, 20)
		# closest grid of 16
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)
		pygame.draw.rect(win, (255,255,255), (point2world(position), Vector(16,16)), 1)

class PickAxeArtifact(Artifact):
	def getArtifact(self):
		return MINECRAFT
	
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "pick axe")
	
	def commentCreation(self):
		GameEvents().post(EventComment([{'text': "a game changer"}]))

	def commentPicked(self):
		GameEvents().post(EventComment([{'text': 'its mining time'}]))
	
	def trenaryStep(self):
		self.angle -= self.vel.x*4

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

def fire(weapon = None):
	global decrease
	if not weapon:
		weapon = WeaponManager().current_weapon
	decrease = True
	if Worm.player:
		weaponOrigin = vectorCopy(Worm.player.pos)
		weaponDir = Worm.player.get_shooting_direction()
		energy = Game._game.energyLevel
		
	if TimeTravel._tt.timeTravelFire:
		decrease = False
		weaponOrigin = TimeTravel._tt.timeTravelList["weaponOrigin"]
		energy = TimeTravel._tt.timeTravelList["energy"]
		weaponDir = TimeTravel._tt.timeTravelList["weaponDir"]
	
	gun_weapons_map = {
		'shotgun':       {'count': 3,  'func': fireShotgun, 'power': 15},
		'flame thrower': {'count': 70, 'func': fireFlameThrower, 'burst': True},
		'minigun':       {'count': 20, 'func': fireMiniGun, 'burst': True},
		'gamma gun':     {'count': 2,  'func': fireGammaGun},
		'long bow':      {'count': 3,  'func': fireLongBow},
		'portal gun':    {'count': 2,  'func': firePortal, 'end_turn': False},
		'laser gun':     {'count': 70, 'func': fireLaser, 'burst': True},
		'spear':         {'count': 2,  'func': fireSpear, 'power': energy},
		'bubble gun':    {'count': 10, 'func': fireBubbleGun, 'burst': True},
		'razor leaf':    {'count': 50, 'func': fireRazorLeaf, 'burst': True},
		'icicle':        {'count': 4,  'func': fireIcicle},
		'fire ball':     {'count': 3,  'func': fireFireBall},
		'fireworks':     {'count': 5,  'func': fireFireWork},
		'earth spike':   {'count': 2,  'func': fireEarthSpike},
	}

	avail = True
	w = None

	if weapon.name in gun_weapons_map.keys():
		# fire gun weapon
		if WeaponManager().current_gun is None:
			WeaponManager().current_gun = ShootGun(**gun_weapons_map[weapon.name])
		
		WeaponManager().current_gun.shoot()
		w = WeaponManager().current_gun.get_object()
		decrease = False
		GameVariables().game_next_state = GameState.PLAYER_PLAY

		if WeaponManager().current_gun.is_done():
			decrease = True
			if WeaponManager().current_gun.is_end_turn():
				GameVariables().game_next_state = GameState.PLAYER_RETREAT
			else:
				GameVariables().game_next_state = GameState.PLAYER_PLAY
			WeaponManager().current_gun.remove()
			WeaponManager().current_gun = None

	elif weapon.name == "missile":
		w = Missile(weaponOrigin, weaponDir, energy)
	elif weapon.name == "grenade":
		w = Grenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "cluster grenade":
		w = ClusterGrenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "petrol bomb":
		w = PetrolBomb(weaponOrigin, weaponDir, energy)
	elif weapon.name == "TNT":
		w = TNT(weaponOrigin)
		w.vel.x = Worm.player.facing * 0.5
		w.vel.y = -0.8
	elif weapon.name == "sticky bomb":
		w = StickyBomb(weaponOrigin, weaponDir, energy)
	elif weapon.name == "mine":
		w = Mine(weaponOrigin, fps * 2.5)
		w.vel.x = Worm.player.facing * 0.5
	elif weapon.name == "baseball":
		Baseball()
	elif weapon.name == "gas grenade":
		w = GasGrenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "gravity missile":
		w = GravityMissile(weaponOrigin, weaponDir, energy)
	elif weapon.name == "holy grenade":
		w = HolyGrenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "banana":
		w = Banana(weaponOrigin, weaponDir, energy)
	elif weapon.name == "earthquake":
		Earthquake()
	elif weapon.name == "gemino mine":
		w = Gemino(weaponOrigin, weaponDir, energy)
	elif weapon.name == "venus fly trap":
		w = PlantSeed(weaponOrigin, weaponDir, energy, PlantMode.VENUS)
	elif weapon.name == "sentry turret":
		w = SentryGun(weaponOrigin, TeamManager().current_team.color)
		w.pos.y -= Worm.player.radius + w.radius
	elif weapon.name == "bee hive":
		w = BeeHive(weaponOrigin, weaponDir, energy)
	elif weapon.name == "drill missile":
		w = DrillMissile(weaponOrigin, weaponDir, energy)
		avail = False
	elif weapon.name == "electric grenade":
		w = ElectricGrenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "homing missile":
		w = HomingMissile(weaponOrigin, weaponDir, energy)
	elif weapon.name == "vortex grenade":
		w = VortexGrenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "chilli pepper":
		w = ChilliPepper(weaponOrigin, weaponDir, energy)
	elif weapon.name == "covid 19":
		w = Covid19(weaponOrigin)
		for worm in Worm.player.team.worms:
			w.bitten.append(worm)
	elif weapon.name == "artillery assist":
		w = Artillery(weaponOrigin, weaponDir, energy)
	elif weapon.name == "sheep":
		w = Sheep(weaponOrigin + Vector(0,-5))
		w.facing = Worm.player.facing
	elif weapon.name == "rope":
		angle = weaponDir.getAngle()
		decrease = False
		if angle <= 0:
			Worm.player.worm_tool.set(Rope(Worm.player, weaponOrigin, weaponDir))

		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif weapon.name == "raging bull":
		w = Bull(weaponOrigin + Vector(0,-5))
		w.facing = Worm.player.facing
		w.ignore.append(Worm.player)
	elif weapon.name == "electro boom":
		w = ElectroBoom(weaponOrigin, weaponDir, energy)
	elif weapon.name == "parachute":
		if Worm.player.vel.y > 1:
			tool_set = Worm.player.worm_tool.set(Parachute(Worm.player))
			if not tool_set:
				decrease = False
		else:
			decrease = False

		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif weapon.name == "pokeball":
		w = PokeBall(weaponOrigin, weaponDir, energy)
	elif weapon.name == "green shell":
		w = GreenShell(weaponOrigin + Vector(0,-5))
		w.facing = Worm.player.facing
		w.ignore.append(Worm.player)
	elif weapon.name == "guided missile":
		w = GuidedMissile(weaponOrigin + Vector(0,-5))
		GameVariables().game_next_state = GameState.WAIT_STABLE
	elif weapon.name == "flare":
		w = Flare(weaponOrigin, weaponDir, energy)
		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif weapon.name == "ender pearl":
		w = EndPearl(weaponOrigin, weaponDir, energy)
		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif weapon.name == "raon launcher":
		w = Raon(weaponOrigin, weaponDir, energy * 0.95)
		w = Raon(weaponOrigin, weaponDir, energy * 1.05)
		if randint(0, 10) == 0 or GameVariables().mega_weapon_trigger:
			w = Raon(weaponOrigin, weaponDir, energy * 1.08)
			w = Raon(weaponOrigin, weaponDir, energy * 0.92)
	elif weapon.name == "snail":
		w = SnailShell(weaponOrigin, weaponDir, energy, Worm.player.facing)
	elif weapon.name == "acid bottle":
		w = AcidBottle(weaponOrigin, weaponDir, energy)
	elif weapon.name == "seeker":
		w = Seeker(weaponOrigin, weaponDir, energy)
	elif weapon.name == "chum bucket":
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 1)
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 2)
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 3)
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 1)
		w = Chum(weaponOrigin, weaponDir, energy)
	elif weapon.name == "trampoline":
		position = Worm.player.pos + Worm.player.get_shooting_direction() * 20
		anchored = False
		for i in range(25):
			if MapManager().is_ground_at(position + Vector(0, i)):
				anchored = True
				break
		if anchored:
			Trampoline(position)
		else:
			decrease = False
		GameVariables().game_next_state = GameState.PLAYER_PLAY

	# artifacts
	elif weapon.name == "mjolnir strike":
		MjolnirStrike()
	elif weapon.name == "mjolnir throw":
		w = MjolnirThrow(weaponOrigin, weaponDir, energy)
	elif weapon.name == "fly":
		if not MjolnirFly.flying:
			w = MjolnirFly(weaponOrigin, weaponDir, energy)
		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif weapon.name == "control plants":
		PlantControl()
	elif weapon.name == "magic bean":
		w = PlantSeed(weaponOrigin, weaponDir, energy, PlantSeed.bean)
		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif weapon.name == "mine plant":
		w = PlantSeed(weaponOrigin, weaponDir, energy, PlantSeed.mine)
	elif weapon.name == "air tornado":
		w = Tornado()
	elif weapon.name == "pick axe":
		if PickAxe._pa:
			decrease = PickAxe._pa.mine()
		else:
			PickAxe()
			decrease = False
		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif weapon.name == "build":
		if MineBuild._mb:
			decrease = MineBuild._mb.build()
		else:
			MineBuild()
			decrease = False
		GameVariables().game_next_state = GameState.PLAYER_PLAY

	if w and not TimeTravel._tt.timeTravelFire: GameVariables().cam_track = w	
	
	# position to available position
	if w and avail:
		availpos = MapManager().get_closest_pos_available(w.pos, w.radius)
		if availpos:
			w.pos = availpos
	
	if decrease:
		if TeamManager().current_team.ammo(weapon.index) != -1:
			TeamManager().current_team.ammo(weapon.index, -1)
		WeaponManager().render_weapon_count()

	Game._game.fireWeapon = False
	Game._game.energyLevel = 0
	Game._game.energising = False
	
	if TimeTravel._tt.timeTravelFire:
		TimeTravel._tt.timeTravelFire = False
		return
	
	GameVariables().game_state = GameVariables().game_next_state
	if GameVariables().game_state == GameState.PLAYER_RETREAT: TimeManager().time_remaining_etreat()
	
	# for uselist:
	if Game._game.game_config.option_cool_down and (GameVariables().game_state == GameState.PLAYER_RETREAT or GameVariables().game_state == GameState.WAIT_STABLE):
		WeaponManager().add_to_cool_down(WeaponManager().current_weapon)

def fireClickable():
	current_weapon = WeaponManager().current_weapon

	decrease = True
	if not Game._game.radial_weapon_menu is None:
		return
	if TeamManager().current_team.ammo(current_weapon.index) == 0:
		return
	mousePosition = mouse_pos_in_world()
	addToUsed = True
	
	if current_weapon.name == "girder":
		Game._game.girder(mousePosition)
	elif current_weapon.name == "teleport":
		Worm.player.pos = mousePosition
		addToUsed = False
	elif current_weapon.name == "airstrike":
		fireAirstrike(mousePosition)
	elif current_weapon.name == "mine strike":
		fireMineStrike(mousePosition)
	elif current_weapon.name == "napalm strike":
		fireNapalmStrike(mousePosition)

	if decrease and TeamManager().current_team.ammo(WeaponManager().current_weapon.index) != -1:
		TeamManager().current_team.ammo(WeaponManager().current_weapon.index, -1)
	
	if GameVariables().config.option_cool_down and GameVariables().game_next_state in [GameState.PLAYER_RETREAT, GameState.WAIT_STABLE] and addToUsed:
		WeaponManager().add_to_cool_down(WeaponManager().current_weapon)
	
	WeaponManager().render_weapon_count()
	TimeManager().time_remaining_etreat()
	GameVariables().game_state = GameVariables().game_next_state
  
def fireUtility(weapon = None):
	if not weapon:
		weapon = WeaponManager().current_weapon
	decrease = True
	if weapon.name == "moon gravity":
		GameVariables().physics.global_gravity = 0.1
		GameEvents().post(EventComment([{'text': "small step for wormanity"}]))

	elif weapon.name == "double damage":
		GameVariables().damage_mult *= 2
		GameVariables().boom_radius_mult *= 1.5
		comments = ["that's will hurt", "that'll leave a mark"]
		GameEvents().post(EventComment([{'text': choice(comments)}]))

	elif weapon.name == "aim aid":
		Game._game.aimAid = True
		GameEvents().post(EventComment([{'text': "snipe em'"}]))

	elif weapon.name == "teleport":
		WeaponManager().switch_weapon(weapon)
		decrease = False
	
	elif weapon.name == "switch worms":
		if Game._game.switchingWorms:
			decrease = False
		Game._game.switchingWorms = True
		GameEvents().post(EventComment([{'text': "the ol' switcheroo"}]))

	elif weapon.name == "time travel":
		if not Game._game.timeTravel:
			TimeTravel._tt.timeTravelInitiate()
		GameEvents().post(EventComment([{'text': "great scott"}]))

	elif weapon.name == "jet pack":
		tool_set = Worm.player.worm_tool.set(JetPack(Worm.player))
		if not tool_set:
			decrease = False
	
	elif weapon.name == "flare":
		WeaponManager().switch_weapon(weapon)
		decrease = False
	
	elif weapon.name == "control plants":
		PlantControl()
	
	if decrease:
		TeamManager().current_team.ammo(weapon.index, -1)


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
	end = False
	lastTeam = None
	count = 0
	pointsGame = False
	for team in TeamManager().teams:
		if len(team.worms) == 0:
			count += 1
	if count == TeamManager().num_of_teams - 1:
		# one team remains
		end = True
		for team in TeamManager().teams:
			if not len(team.worms) == 0:
				lastTeam = team
	if count == TeamManager().num_of_teams:
		# no team remains
		end = True
	
	if Game._game.gameMode == GameMode.TARGETS and len(ShootingTarget._reg) == 0 and ShootingTarget.numTargets <= 0:
		end = True
	
	if not end:
		return False
	# game end:
	dic = {}
	winningTeam = None
		
	# win bonuse:
	if Game._game.gameMode == GameMode.CAPTURE_THE_FLAG:
		dic["mode"] = "CTF"
		pointsGame = True
		for team in TeamManager().teams:
			if team.flagHolder:
				team.points += 1 + 3 # bonus points
				print("[ctf win, team", team.name, "got 3 bonus points]")
				break
		
	elif Game._game.gameMode == GameMode.POINTS:
		pointsGame = True
		if lastTeam:
			lastTeam.points += 150 # bonus points
			dic["mode"] = "points"
			print("[points win, team", lastTeam.name, "got 150 bonus points]")
			
	elif Game._game.gameMode == GameMode.TARGETS:
		pointsGame = True
		TeamManager().current_team.points += 3 # bonus points
		dic["mode"] = "targets"
		print("[targets win, team", TeamManager().current_team.name, "got 3 bonus points]")
		
	elif Game._game.gameMode == GameMode.ARENA:
		pointsGame = True
		if lastTeam:
			pass
		dic["mode"] = "arena"

	elif Game._game.gameMode == GameMode.MISSIONS:
		pointsGame = True
		if lastTeam:
			pass
		dic["mode"] = "missions"
	
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
		if Game._game.gameMode == GameMode.DAVID_AND_GOLIATH:
			dic["mode"] = "davidVsGoliath"
	
	if end:
		if winningTeam is not None:
			print("Team", winningTeam.name, "won!")
			dic["time"] = str(GameVariables().time_overall // fps)
			dic["winner"] = winningTeam.name
			if Game._game.mostDamage[1]:
				dic["mostDamage"] = str(int(Game._game.mostDamage[0]))
				dic["damager"] = Game._game.mostDamage[1]
			add_to_record(dic)
			if len(winningTeam.worms) > 0:
				GameVariables().cam_track = winningTeam.worms[0]
			GameEvents().post(EventComment([
				{'text': 'team '},
				{'text': winningTeam.name, 'color': winningTeam.color},
				{'text': ' Won!'}
			]))

		else:
			GameEvents().post(EventComment([{'text': 'its a tie!'}]))
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
	Game._game.aimAid = False
	if Game._game.timeTravel: TimeTravel._tt.timeTravelReset()

	Worm.player.worm_tool.release()

	Game._game.switchingWorms = False
	if Worm.roped:
		Worm.player.team.ammo(WeaponManager()["rope"], -1)
		Worm.roped = False
	
	# update damage:
	wormName = Worm.player.name_str
	wormColor = Worm.player.team.color
	if Game._game.damageThisTurn > Game._game.mostDamage[0]:
		Game._game.mostDamage = (Game._game.damageThisTurn, Worm.player.name_str)	
	if Game._game.damageThisTurn > int(Game._game.game_config.worm_initial_health * 2.5):
		if Game._game.damageThisTurn == 300:
			GameEvents().post(EventComment([{'text': "THIS IS "}, {'text': wormName, 'color': wormColor}]))
		else:
			comment = choice([
					[{'text': 'awesome shot '}, {'text': wormName, 'color': wormColor}, {'text': '!'}],
					[{'text': wormName, 'color': wormColor}, {'text': ' is on fire!'}],
					[{'text': wormName, 'color': wormColor}, {'text': ' shows no mercy'}],
				])
			GameEvents().post(EventComment(comment))

	elif Game._game.damageThisTurn > int(Game._game.game_config.worm_initial_health * 1.5):
		comment = choice([
					[{'text': 'good shot '}, {'text': wormName, 'color': wormColor}, {'text': '!'}],
					[{'text': 'nicely done '}, {'text': wormName, 'color': wormColor}],
				])
		GameEvents().post(EventComment(comment))
	
	TeamManager().current_team.damage += Game._game.damageThisTurn
	if Game._game.gameMode in [GameMode.POINTS, GameMode.BATTLE]:
		TeamManager().current_team.points = TeamManager().current_team.damage + 50 * TeamManager().current_team.kill_count
	Game._game.damageThisTurn = 0
	if check_winners():
		return
	GameVariables().game_turn_count += 1

	# shoot sentries:
	isThereTargets = False
	if len(SentryGun._sentries) > 0 and not Game._game.sentring:
		for sentry in SentryGun._sentries:
			sentry.engage()
			if sentry.target:
				isThereTargets = True
		if isThereTargets:
			# shoot
			for sentry in SentryGun._sentries:
				if sentry.target:
					sentry.fire()
					GameVariables().cam_track = sentry
			Game._game.sentring = True
			GameVariables().game_turn_count -= 1
			GameVariables().game_next_state = GameState.WAIT_STABLE
			return

	# controlling raons:
	isTherePointing = False
	if len(Raon._raons) > 0 and not Game._game.raoning:
		for raon in Raon._raons:
			if raon.state == Raon.pointing:
				isTherePointing = True
				break
		if isTherePointing:
			for raon in Raon._raons:
				moved = raon.advance()
				if moved:
					GameVariables().cam_track = raon
			Game._game.raoning = True
			GameVariables().game_turn_count -= 1
			GameVariables().game_next_state = GameState.WAIT_STABLE
			return
		
	# deploy pack:
	if GameVariables().game_turn_count % TeamManager().num_of_teams == 0 and not Game._game.deploying:
		Game._game.deploying = True
		GameVariables().game_turn_count -= 1
		GameVariables().game_next_state = GameState.WAIT_STABLE
		comments = [
			[{'text': 'a jewel from the heavens!'}],
			[{'text': 'its raining crates, halelujah!'}],
			[{'text': ' '}],
		]
		GameEvents().post(EventComment(choice(comments)))

		for i in range(Game._game.game_config.deployed_packs):
			w = deploy_pack(choice([HealthPack,UtilityPack, WeaponPack]))
			GameVariables().cam_track = w
		# if Game._game.darkness:
		# 	for team in TeamManager().teams:
		# 		team.ammo("flare", 1)
		# 		if team.ammo("flare") > 3:
		# 			team.ammo("flare", -1)
		return
	
	# rise water:
	if Game._game.waterRise and not Game._game.waterRising:
		Game._game.background.water_rise(20)
		GameVariables().game_next_state = GameState.WAIT_STABLE
		GameVariables().game_turn_count -= 1
		Game._game.waterRising = True
		return
	
	# throw artifact:
	if Game._game.game_config.option_artifacts:
		for team in TeamManager().teams:
			if PLANT_MASTER in team.artifacts:
				team.ammo(WeaponManager()["magic bean"], 1, True)
			elif MJOLNIR in team.artifacts:
				team.ammo(WeaponManager()["fly"], 3, True)
			elif MINECRAFT in team.artifacts:
				team.ammo(WeaponManager()["pick axe"], 1, True)
				team.ammo(WeaponManager()["build"], 1, True)
		
		if len(Game._game.worldArtifacts) > 0 and not Game._game.deployingArtifact:
			chance = randint(0,10)
			if chance == 0 or Game._game.trigerArtifact:
				Game._game.trigerArtifact = False
				Game._game.deployingArtifact = True
				artifact = choice(Game._game.worldArtifacts)
				Game._game.worldArtifacts.remove(artifact)
				Game._game.dropArtifact(Game._game.worldArtifactsClasses[artifact], None, comment=True)
				GameVariables().game_next_state = GameState.WAIT_STABLE
				GameVariables().game_turn_count -= 1
				return
	
	Game._game.waterRising = False
	Game._game.raoning = False
	Game._game.deploying = False
	Game._game.sentring = False
	Game._game.deployingArtifact = False
	
	if GameVariables().game_turn_count % TeamManager().num_of_teams == 0:
		Game._game.game_config.rounds_for_sudden_death -= 1
		if Game._game.game_config.rounds_for_sudden_death == 0:
			suddenDeath()
	
	if Game._game.gameMode == GameMode.CAPTURE_THE_FLAG:
		for team in TeamManager().teams:
			if team.flagHolder:
				team.points += 1
				break

	# update weapons delay (and targets)
	if GameVariables().game_turn_count % TeamManager().num_of_teams == 0:
		if Game._game.gameMode == GameMode.TARGETS:
			ShootingTarget.numTargets -= 1
			if ShootingTarget.numTargets == 0:
				GameEvents().post(EventComment([{'text': 'final targets round'}]))
	
	# update stuff
	Debrie._debries = []
	Bubble.cought = []
	
	# change wind:
	GameVariables().physics.wind = uniform(-1, 1)
	
	# flares reduction
	# if Game._game.darkness:
	# 	for flare in Flare._flares:
	# 		if not flare in GameVariables().get_physicals():
	# 			Flare._flares.remove(flare)
	# 		flare.lightRadius -= 10
	
	# sick:
	for worm in GameVariables().get_worms():
		if not worm.sick == 0 and worm.health > 5:
			worm.damage(min(int(5 / GameVariables().damage_mult) + 1, int((worm.health - 5) / GameVariables().damage_mult) + 1), 2)
		
	# select next team
	index = TeamManager().teams.index(TeamManager().current_team)
	index = (index + 1) % TeamManager().num_of_teams
	TeamManager().current_team = TeamManager().teams[index]
	while not len(TeamManager().current_team.worms) > 0:
		index = TeamManager().teams.index(TeamManager().current_team)
		index = (index + 1) % TeamManager().num_of_teams
		TeamManager().current_team = TeamManager().teams[index]
	
	GamePlay().on_cycle()

	Game._game.damageThisTurn = 0
	if GameVariables().game_next_state == GameState.PLAYER_PLAY:
	
		# sort worms by health for drawing purpuses
		GameVariables().get_physicals().sort(key = lambda worm: worm.health if worm.health else 0)
		
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
	
		Worm.player = w
		GameVariables().cam_track = Worm.player
		GameVariables().player_can_move = True

		WeaponManager().switch_weapon(WeaponManager().current_weapon)
		if Game._game.gameMode == GameMode.MISSIONS:
			MissionManager._mm.cycle()

def switch_worms():
	currentWorm = TeamManager().current_team.worms.index(Worm.player)
	totalWorms = len(TeamManager().current_team.worms)
	currentWorm = (currentWorm + 1) % totalWorms
	Worm.player = TeamManager().current_team.worms[currentWorm]
	GameVariables().cam_track = Worm.player
	if Game._game.gameMode == GameMode.MISSIONS:
		MissionManager._mm.cycle()



def random_placing():
	for i in range(Game._game.game_config.worms_per_team * len(TeamManager().teams)):
		if Game._game.game_config.option_forts:
			place = giveGoodPlace(i)
		else:
			place = giveGoodPlace()
		if Game._game.game_config.option_digging:
			pygame.draw.circle(MapManager().game_map, SKY, place, 35)
			pygame.draw.circle(MapManager().ground_map, SKY, place, 35)
			pygame.draw.circle(MapManager().ground_secondary, SKY, place, 30)
		current_team = TeamManager().teams[TeamManager().team_choser]
		new_worm_name = current_team.get_new_worm_name()
		current_team.worms.append(Worm(place, new_worm_name, current_team))
		TeamManager().team_choser = (TeamManager().team_choser + 1) % TeamManager().num_of_teams
		Game._game.lstepper()
	GameVariables().game_state = GameVariables().game_next_state


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
		sub_layout = [RadialButton(weapon, weapon.name, get_amount(weapon), weapon_bg_color[category], WeaponManager().get_surface_portion(weapon)) for weapon in reversed(weapons_in_category)]
		main_button = RadialButton(weapons_in_category[0], '', '', weapon_bg_color[category], WeaponManager().get_surface_portion(weapons_in_category[0]), sub_layout)
		layout.append(main_button)

	Game._game.radial_weapon_menu = RadialMenu(layout, Vector(GameVariables().win_width // 2, GameVariables().win_height // 2))

class Camera:
	def __init__(self, pos):
		self.pos = pos
		self.radius = 1

def toast_info():
	if Game._game.gameMode < GameMode.POINTS:
		return
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
	surf = pygame.Surface((toastWidth, (surfs[0][0].get_height() + 3) * TeamManager().num_of_teams), pygame.SRCALPHA)
	i = 0
	for s in surfs:
		surf.blit(s[0], (0, i))
		surf.blit(s[1], (toastWidth - s[1].get_width(), i))
		i += s[0].get_height() + 3
	Toast(surf)

class ArenaManager:
	_arena = None
	def __init__(self):
		ArenaManager._arena = self
		self.size = Vector(10 * 16, 10)
		self.pos = Vector(MapManager().game_map.get_width(), MapManager().game_map.get_height())//2 - self.size//2
	def step(self):
		pass
	def draw(self, win: pygame.Surface):
		pygame.draw.rect(MapManager().game_map, GRD,(self.pos, self.size))
		for i in range(10):
			MapManager().ground_map.blit(sprites.sprite_atlas, self.pos + Vector(i * 16, 0), (64,80,16,16))
	def wormsCheck(self):
		for worm in GameVariables().get_worms():
			checkPos = worm.pos + Vector(0, worm.radius * 2)
			if worm.pos.x > self.pos.x and worm.pos.x < self.pos.x + self.size.x and checkPos.y > self.pos.y and checkPos.y < self.pos.y + self.size.y:
				worm.team.points += 1

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
		for i in range(3):
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
				if mission.missionType == "hit _" or mission.missionType == "kill _":
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
		notFromTeam = Worm.player.team
		worms = []
		for worm in GameVariables().get_worms():
			if worm.team == notFromTeam:
				continue
			if not worm.alive:
				continue
			worms.append(worm)
		return worms

	def createMarker(self):
		return giveGoodPlace(-1, True)

	def chooseTarget(self):
		notFromTeam = Worm.player.team
		worms = self.getAliveWormsFromOtherTeams()
		return choice(worms)

	def chooseTeamTarget(self):
		notFromTeam = Worm.player.team
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
		if mission in self.wormMissionDict[Worm.player]:
			self.wormMissionDict[Worm.player].remove(mission)

		if Game._game.isPlayingState():
			self.assignMissions(Worm.player, mission)

	def notifyKill(self, worm):
		if worm == Worm.player:
			return
		self.killedThisTurn.append(worm)
		self.checkMissions(["kill a worm", "kill _", "double kill", "triple kill", "above 50 damage"])

	def notifyHit(self, worm):
		if worm in self.hitThisTurn or worm == Worm.player:
			self.checkMissions(["above 50 damage"])
			return
		self.hitThisTurn.append(worm)
		self.checkMissions(["hit a worm from _", "hit _", "hit 3 worms", "above 50 damage"])
		# check highest
		worms = []
		for w in GameVariables().get_worms():
			if w.alive and w.team != Worm.player.team:
				worms.append(w)
		
		highestWorm = min(worms, key=lambda w: w.pos.y)
		if worm == highestWorm:
			self.checkMissions(["hit highest worm"])
		# check distance
		if distus(worm.pos, Worm.player.pos) > 300 * 300:
			self.checkMissions(["hit distant worm"])

	def checkMissions(self, missionTypes):
		for mission in self.wormMissionDict[Worm.player]:
			if mission.missionType in missionTypes:
				mission.check()

	def notifySick(self, worm):
		pass

	def endTurn(self):
		pass

	def cycle(self):
		# start of turn, assign missions to current worm
		self.assignMissions(Worm.player)
		self.updateDisplay()
		self.killedThisTurn = []
		self.hitThisTurn = []
		self.sickThisTurn = []
		self.marker = None

		if "reach marker" in self.wormMissionDict[Worm.player]:
			self.createMarker()

	def updateDisplay(self):
		for mission in self.wormMissionDict[Worm.player]:
			mission.updateDisplay()

	def step(self):
		if Worm.player == None:
			return
		for mission in self.wormMissionDict[Worm.player]:
			mission.step()

	def draw(self, win: pygame.Surface):
		if Worm.player == None:
			return
		currentWorm = Worm.player
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
		self.timer = 3 * fps
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
			{'text': 'mission '}, {'text': string, 'color': Worm.player.team.color}, {'text': ' passed'}
		]

		GameEvents().post(EventComment(comment))
		Worm.player.team.points += self.reward
		Game._game.addToScoreList(self.reward)

		self.completed = True
		MissionManager._log += f"{Worm.player.name_str} completed mission {self.missionType} {str(self.reward)}\n"
		
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
			if Game._game.damageThisTurn >= 50:
				self.complete()

	def step(self):
		if self.marker:
			if distus(self.marker, Worm.player.pos) < 20 * 20:
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
		currentWorm = Worm.player
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
		amount = (1 - self.timer / (3 * fps)) * 4
		bColor = (0, min(255 * amount, 255), 0)

		self.surf.fill(bColor)
		self.surf.blit(self.textSurf, (1,1))

def give_random_legendary_weapon(amount: int):
	startingWeapons = ["holy grenade", "gemino mine", "bee hive", "electro boom", "pokeball", "green shell", "guided missile", "fireworks"]
	if GameVariables().initial_variables.allow_air_strikes:
		startingWeapons.append("mine strike")
	for _ in range(amount):
		for team in TeamManager().teams:
			chosen_weapon = WeaponManager().get_weapon(choice(startingWeapons)).index
			team.ammo(chosen_weapon, 1)
			if randint(0,2) >= 1:
				chosen_weapon = WeaponManager().get_weapon(choice(["moon gravity", "teleport", "jet pack", "aim aid", "switch worms"])).index
				team.ammo(chosen_weapon, 1)
			if randint(0,6) == 1:
				chosen_weapon = WeaponManager().get_weapon(choice(["portal gun", "trampoline", "ender pearl"])).index
				team.ammo(chosen_weapon, 3)

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
				team.weapon_set[i] = -1
		for _ in WeaponManager().weapons:
			# weapon [5] = 0 # todo
			pass
		Game._game.game_config.option_cool_down = False
	elif code == "suddendeath":
		suddenDeath()
	elif code == "wind":
		GameVariables().physics.wind = uniform(-1, 1)
	elif code == "goodbyecruelworld":
		boom(Worm.player.pos, 100)
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
	elif code == "gibpetrolcan":
		PetrolCan(mouse_pos)
	elif code == "megaboom":
		GameVariables().mega_weapon_trigger = True
	elif code == "tsunami":
		Game._game.waterRise = True
		GameEvents().post(EventComment([{'text': "water rising!"}]))
	elif code == "comeflywithme":
		TeamManager().current_team.ammo(WeaponManager()["jet pack"], 6)
		TeamManager().current_team.ammo(WeaponManager()["rope"], 6)
		TeamManager().current_team.ammo(WeaponManager()["ender pearl"], 6)
	elif code == "odinson":
		m = Mjolnir(mouse_pos)
		m.vel *= 0
	elif code == "bulbasaur":
		m = MagicLeaf(mouse_pos)
	elif code == "avatar":
		m = Avatar(mouse_pos)
	elif code == "masterofpuppets":
		MasterOfPuppets()
	elif code == "artifact":
		Game._game.trigerArtifact = True
		GameEvents().post(EventComment([{'text': 'next turn artifact drop'}]))
	elif code == "minecraft":
		PickAxeArtifact(mouse_pos)
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




class Anim:
	_a = None
	def __init__(self):
		Anim._a = self
		GameVariables().register_non_physical(self)
		num = -1
		for folder in os.listdir("./anims"):
			if not os.path.isdir("./anims/" + folder):
				continue
			try:
				folderNum = int(folder)
			except:
				continue
			num = max(num, folderNum)
		self.folder = "./anims/" + str(num + 1)
		# create folder
		if not os.path.isdir(self.folder):
			os.mkdir(self.folder)
		self.time = 0
		print("record Start")
	def step(self):
		pygame.image.save(win, self.folder + "/" + str(self.time).zfill(3) + ".png")
		self.time += 1
		if self.time == 5 * fps:
			Anim._a = None
			GameVariables().unregister_non_physical(self)
			print("record End")
	def draw(self, win: pygame.Surface):
		pass

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
	elif GameVariables().game_state == GameState.WAIT_STABLE:
		GameVariables().player_in_control = False #can play
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

		GameVariables().game_next_state = GameState.PLAYER_PLAY
	elif GameVariables().game_state == GameState.WIN:
		GameVariables().game_stable_counter += 1
		if GameVariables().game_stable_counter == 30 * 3:
			return 1
			# subprocess.Popen("wormsLauncher.py -popwin", shell=True)
	return 0

################################################################################ Key bindings
def onKeyPressRight():
	Worm.player.turn(RIGHT)

def onKeyPressLeft():
	Worm.player.turn(LEFT)

def onKeyPressSpace():
	if not WeaponManager().can_shoot():
		print('cant shoot')
		return

	if WeaponManager().current_weapon.style == WeaponStyle.CHARGABLE:
		Game._game.energising = True
		Game._game.energyLevel = 0
		Game._game.fireWeapon = False
		if WeaponManager().current_weapon in ["homing missile", "seeker"]:
			Game._game.energising = False

def onKeyHoldSpace():
	Game._game.energyLevel += 0.05
	if Game._game.energyLevel >= 1:
		if Game._game.timeTravel:
			TimeTravel._tt.timeTravelPlay()
			Game._game.energyLevel = 0
			Game._game.energising = False
		else:
			Game._game.energyLevel = 1
			Game._game.fireWeapon = True

def onKeyReleaseSpace():
	if WeaponManager().can_shoot():
		if Game._game.timeTravel:
			TimeTravel._tt.timeTravelPlay()
			Game._game.energyLevel = 0
		
		# chargeable
		elif WeaponManager().current_weapon.style == WeaponStyle.CHARGABLE and Game._game.energising:
			Game._game.fireWeapon = True
		
		# putable & guns
		elif (WeaponManager().current_weapon.style in [WeaponStyle.PUTABLE, WeaponStyle.GUN]):
			Game._game.fireWeapon = True
			GameVariables().player_can_shoot = False
		
		elif (WeaponManager().current_weapon.style in [WeaponStyle.UTILITY]):
			fireUtility()
			
		Game._game.energising = False
	elif Sheep.trigger == False:
		Sheep.trigger = True

def onKeyPressTab():
	if WeaponManager().current_weapon.name == "drill missile":
		DrillMissile.mode = not DrillMissile.mode
		if DrillMissile.mode:
			FloatingText(Worm.player.pos + Vector(0,-5), "drill mode", (20,20,20))
		else:
			FloatingText(Worm.player.pos + Vector(0,-5), "rocket mode", (20,20,20))
		WeaponManager().render_weapon_count()
	elif WeaponManager().current_weapon.name == "long bow":
		LongBow._sleep = not LongBow._sleep
		if LongBow._sleep:
			FloatingText(Worm.player.pos + Vector(0,-5), "sleeping", (20,20,20))
		else:
			FloatingText(Worm.player.pos + Vector(0,-5), "regular", (20,20,20))
	elif WeaponManager().current_weapon.name == "girder":
		GameVariables().girder_angle += 45
		if GameVariables().girder_angle == 180:
			GameVariables().girder_size = 100
		if GameVariables().girder_angle == 360:
			GameVariables().girder_size = 50
			GameVariables().girder_angle = 0
	elif WeaponManager().current_weapon.is_fused:
		GameVariables().fuse_time += fps
		if GameVariables().fuse_time > fps*4:
			GameVariables().fuse_time = fps
		string = "delay " + str(GameVariables().fuse_time//fps) + " sec"
		FloatingText(Worm.player.pos + Vector(0,-5), string, (20,20,20))
		WeaponManager().render_weapon_count()
	elif WeaponManager().current_weapon.category == WeaponCategory.AIRSTRIKE:
		GameVariables().airstrike_direction *= -1
	elif Game._game.switchingWorms:
		switch_worms()

def onKeyPressEnter():
	# jump
	if Worm.player.stable and Worm.player.health > 0:
		Worm.player.vel += Worm.player.get_shooting_direction() * JUMP_VELOCITY
		Worm.player.stable = False

################################################################################ Main

def gameMain(game_config: GameConfig=None):
	global win

	Game(game_config)
	WeaponManager()
	TeamManager()

	SmokeParticles()
	GasParticles()           
	
	damageText = (Game._game.damageThisTurn, fonts.pixel5_halo.render(str(int(Game._game.damageThisTurn)), False, GameVariables().initial_variables.hud_color))
	commentator = Commentator()
	TimeTravel()

	wind_flag = WindFlag()

	run = True
	pause = False
	while run:
				
		# events
		for event in pygame.event.get():
			is_handled = Game._game.handle_event(event)
			if is_handled:
				continue
			if event.type == pygame.QUIT:
				globals.exitGame()
			# mouse click event
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # left click (main)
				# mouse position:
				mousePos = pygame.mouse.get_pos()
				# CLICKABLE weapon check:
				if GameVariables().game_state == GameState.PLAYER_PLAY and WeaponManager().current_weapon.style == WeaponStyle.CLICKABLE:
					fireClickable()
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
					if Worm.player and GameVariables().player_in_control:
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
						pause = not pause
					if event.key == pygame.K_TAB:
						onKeyPressTab()
					if event.key == pygame.K_t:
						pass
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
							GameVariables().cam_track = Worm.player

					Game._game.cheatCode += event.unicode
					if event.key == pygame.K_EQUALS:
						cheat_activate(Game._game.cheatCode)
						Game._game.cheatCode = ""
			if event.type == pygame.KEYUP:
				# fire release
				if event.key == pygame.K_SPACE:
					onKeyReleaseSpace()
		
		#key hold:
		keys = pygame.key.get_pressed()
		if Worm.player and GameVariables().player_in_control and GameVariables().player_can_move:
			# fire hold
			if keys[pygame.K_SPACE] and GameVariables().player_can_shoot and WeaponManager().current_weapon.style == WeaponStyle.CHARGABLE and Game._game.energising:
				onKeyHoldSpace()
		
		if pause:
			result = [0]
			# todo here False V
			args = {"showPoints": False, "teams":TeamManager().teams}
			pauseMenu(args, result)
			pause = not pause
			if result[0] == 1:
				run = False
			continue
		
		result = stateMachine()
		if result == 1:
			run = False

		if GameVariables().game_state in [GameState.RESET]:
			continue

		# use edge map scroll
		if pygame.mouse.get_focused():
			mousePos = pygame.mouse.get_pos()
			scroll = Vector()
			if mousePos[0] < EDGE_BORDER:
				scroll.x -= MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if mousePos[0] > screenWidth - EDGE_BORDER:
				scroll.x += MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if mousePos[1] < EDGE_BORDER:
				scroll.y -= MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if mousePos[1] > screenHeight - EDGE_BORDER:
				scroll.y += MAP_SCROLL_SPEED * (2.5 - GameVariables().scale_factor / 2)
			if scroll != Vector():
				GameVariables().cam_track = Camera(GameVariables().cam_pos + Vector(GameVariables().win_width, GameVariables().win_height)/2 + scroll)
		
		# handle scale:
		oldSize = (GameVariables().win_width, GameVariables().win_height)
		GameVariables().win_width += (globals.screenWidth / GameVariables().scale_factor - GameVariables().win_width) * 0.2
		GameVariables().win_height += (globals.screenHeight / GameVariables().scale_factor - GameVariables().win_height) * 0.2
		GameVariables().win_width = int(GameVariables().win_width)
		GameVariables().win_height = int(GameVariables().win_height)
		
		if oldSize != (GameVariables().win_width, GameVariables().win_height):
			globals.win = pygame.Surface((GameVariables().win_width, GameVariables().win_height))
			win = globals.win
			globals.GameVariables().win_width = GameVariables().win_width
			globals.GameVariables().win_height = GameVariables().win_height
			updateWin(win, GameVariables().scale_factor)
		
		# handle position:
		if GameVariables().cam_track:
			# actual position target:
			### GameVariables().cam_pos = GameVariables().cam_track.pos - Vector(GameVariables().win_width, GameVariables().win_height)/2
			# with smooth transition:
			GameVariables().cam_pos += ((GameVariables().cam_track.pos - Vector(int(globals.screenWidth / GameVariables().scale_factor), int(globals.screenHeight / GameVariables().scale_factor))/2) - GameVariables().cam_pos) * 0.2
		
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
		
		# Fire
		if Game._game.fireWeapon and GameVariables().player_can_shoot: fire()
		
		# step:
		Game._game.step()
		GameVariables().game_stable = True

		GameVariables().step_physicals()
		GameVariables().step_non_physicals()

		# step effects
		EffectManager().step()
		
		for t in Toast._toasts:
			t.step()
		SmokeParticles._sp.step()
		GasParticles._sp.step()
		if Game._game.timeTravel: 
			TimeTravel._tt.step()
		
		GamePlay().step()

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
		
		if ArenaManager._arena:
			ArenaManager._arena.step()
		if MissionManager._mm:
			MissionManager._mm.step()
		
		# menu step
		if Game._game.radial_weapon_menu:
			Game._game.radial_weapon_menu.step()
		
		# reset actions
		Game._game.actionMove = False

		wind_flag.step()
		commentator.step()

		# draw:
		Game._game.background.draw(win)
		MapManager().draw_land(win)
		for p in GameVariables().get_physicals(): 
			p.draw(win)
		GameVariables().draw_non_physicals(win)
		if GameVariables().continuous_fire:
			GameVariables().continuous_fire = False
			fire()

		# draw effects
		EffectManager().draw(win)

		Game._game.background.drawSecondary(win)
		for t in Toast._toasts:
			t.draw(win)
		
		if ArenaManager._arena:
			ArenaManager._arena.draw(win)
		SmokeParticles._sp.draw(win)
		GasParticles._sp.draw(win)

		# if Game._game.darkness and MapManager().dark_mask: win.blit(MapManager().dark_mask, (-int(GameVariables().cam_pos[0]), -int(GameVariables().cam_pos[1])))
		# draw shooting indicator
		if Worm.player and GameVariables().game_state in [GameState.PLAYER_PLAY, GameState.PLAYER_RETREAT] and Worm.player.health > 0:
			Worm.player.drawCursor(win)
			if Game._game.aimAid and WeaponManager().current_weapon.style == WeaponStyle.GUN:
				p1 = vectorCopy(Worm.player.pos)
				p2 = p1 + Worm.player.get_shooting_direction() * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))
			i = 0
			while i < 20 * Game._game.energyLevel:
				cPos = vectorCopy(Worm.player.pos)
				pygame.draw.line(win, (0,0,0), point2world(cPos), point2world(cPos + Worm.player.get_shooting_direction() * i))
				i += 1
		
		GameVariables().draw_extra(win)
		GameVariables().draw_layers(win)
		
		# HUD
		wind_flag.draw(win)
		TimeManager().draw(win)
		if WeaponManager().surf:
			win.blit(WeaponManager().surf, (25, 5))
		commentator.draw(win)
		# draw weapon indicators
		WeaponManager().draw_weapon_hint(win)
		WeaponManager().draw(win)
		
		# draw health bar
		TeamManager().step()
		TeamManager().draw(win)
		
		GamePlay().draw(win)


		if Game._game.gameMode == GameMode.TARGETS and Worm.player:
			for target in ShootingTarget._reg:
				draw_dir_indicator(win, target.pos)
		if Game._game.gameMode == GameMode.MISSIONS:
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
		if damageText[0] != Game._game.damageThisTurn:
			damageText = (Game._game.damageThisTurn, fonts.pixel5_halo.render(str(int(Game._game.damageThisTurn)), False, GameVariables().initial_variables.hud_color))
		win.blit(damageText[1], ((int(5), int(GameVariables().win_height -5 -damageText[1].get_height()))))

		debug_text = fonts.pixel5_halo.render(str(GameVariables().game_state), False, GameVariables().initial_variables.hud_color)
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
		
		# screen manegement
		pygame.transform.scale(win, screen.get_rect().size, screen)
		pygame.display.update()
		fpsClock.tick(fps)

def splashScreen():
	splashImage = pygame.image.load("assets/simeGames.png")
	timer = 1 * fps // 2
	run = True
	while run:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				run = False
		
		timer -= 1
		if timer <= 0:
			break

		win.fill((11,126,193))
		win.blit(splashImage, ((GameVariables().win_width/2 - splashImage.get_width()/2, GameVariables().win_height/2 - splashImage.get_height()/2)))
		screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
		pygame.display.update()
		fpsClock.tick(fps)

if __name__ == "__main__":
	gameParameters = [None]
	splashScreen()

	wip = '''refactoring stage:
	still in wip:
		water rise
		loading screen
		health bar update
	'''
	print(wip)

	while True:
		mainMenu(Game._game.endGameDict if Game._game else None, gameParameters)
		gameMain(gameParameters[0])
