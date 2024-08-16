from math import pi, cos, sin, atan2, sqrt, degrees, radians, copysign, fabs
from random import shuffle ,randint, uniform, choice
import pygame
import pygame.gfxdraw
import os
from typing import Any, Callable

from common import *
from common.vector import *
from common.game_config import *
from common.game_event import *
from common.game_play_mode import *

from mainMenus import mainMenu, pauseMenu, initGui, updateWin

from game.map_manager import *
from game.background import BackGround
from game.visual_effects import *

from entities.physical_entity import PhysObj
from entities.debrie import Debrie
from entities.gun_shell import GunShell
from game.world_effects import *
from entities.fire import Fire

from game.hud import *
from gui.radial_menu import *
from game.team_manager import *

from entities.worm_tools import *
from entities.props import *

from weapons.weapon_manager import *
from weapons.missiles import *
from weapons.grenades import *
from weapons.cluster_grenade import ClusterGrenade
from weapons.bombs import *
from weapons.fire_weapons import *
from weapons.artillery import Artillery


import globals


def getGlobals():
	global fpsClock, fps, screenWidth, screenHeight, scalingFactor, win, screen
	fpsClock = globals.fpsClock
	fps = GameVariables().fps
	screenWidth = globals.screenWidth
	screenHeight = globals.screenHeight
	scalingFactor = globals.scalingFactor
	win = globals.win
	screen = globals.screen

globals.globalsInit()
initGui()
getGlobals()

def drawTarget(pos):
	offset = sin(GameVariables().time_overall / 5) * 4 + 3
	triangle = [Vector(5 + offset,0), Vector(10 + offset,-2), Vector(10 + offset,2)]
	for i in range(4):
		angle = i * pi / 2
		triangle = [triangle[0].rotate(angle), triangle[1].rotate(angle), triangle[2].rotate(angle)]
		pygame.draw.polygon(globals.game_manager.win, (255,0,0), [point2world(pos + j) for j in triangle])

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

		self.roundCounter = 0
		self.damageThisTurn = 0
		self.mostDamage = (0, None)

		

		self.extra = []
		self.layersCircles = [[], [], []]
		self.layersLines = [] #color, start, end, width, delay

		
		self.nonPhys = []
		self.nonPhysToRemove = []

		self.girderAngle = 0
		self.girderSize = 50

		self.airStrikeDir = RIGHT
		self.airStrikeSpr = fonts.pixel10.render(">>>", False, BLACK)

		self.killList = []
		self.lstep = 0
		self.lstepmax = 1

		self.state = RESET
		self.nextState = RESET
		self.loadingSurf = fonts.pixel10.render("Simon's Worms Loading", False, WHITE)
		self.gameStable = False
		self.playerControl = False
		self.playerMoveable = True
		self.playerShootAble = False
		self.gameStableCounter = 0

		self.endGameDict = None

		self.imageMjolnir = pygame.Surface((24,31), pygame.SRCALPHA)
		self.imageMjolnir.blit(sprites.sprite_atlas, (0,0), (100, 32, 24, 31))
		self.weaponHold = pygame.Surface((16,16), pygame.SRCALPHA)

		self.radial_weapon_menu: RadialMenu = None

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
			for team in globals.team_manager.teams:
				for i, _ in enumerate(team.weaponCounter):
					if WeaponManager._wm.weapons[i].category == WeaponCategory.AIRSTRIKE:
						team.weaponCounter[i] = 0

		# select current team
		globals.team_manager.currentTeam = globals.team_manager.teams[0]
		globals.team_manager.teamChoser = globals.team_manager.teams.index(globals.team_manager.currentTeam)

		# place worms
		randomPlacing()
		
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
				place_object(PlantBomb, ((0,0), (0,0), 0, PlantBomb.venus), False)

		# give random legendary starting weapons:
		randomStartingWeapons(1)

		# choose starting worm
		w = globals.team_manager.currentTeam.worms.pop(0)
		globals.team_manager.currentTeam.worms.append(w)
				
		if Game._game.game_config.random_mode != RandomMode.NONE:
			w = choice(globals.team_manager.currentTeam.worms)
		
		Game._game.player = w
		GameVariables().cam_track = w

		# reset time
		TimeManager._tm.timeReset()
		WeaponManager._wm.switchWeapon(WeaponManager._wm.currentWeapon)

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
			for team in globals.team_manager.teams:
				team.ammo("minigun", 5)
				team.ammo("drill missile", 3)
				team.ammo("laser gun", 3)
			GameVariables().config.option_closed_map = True

		# david and goliath
		if Game._game.gameMode == GameMode.DAVID_AND_GOLIATH:
			for team in globals.team_manager.teams:
				length = len(team.worms)
				for i in range(length):
					if i == 0:
						team.worms[i].health = Game._game.game_config.worm_initial_health + (length - 1) * (Game._game.game_config.worm_initial_health//2)
						team.worms[i].healthStr = fonts.pixel5.render(str(team.worms[i].health), False, team.worms[i].team.color)
					else:
						team.worms[i].health = (Game._game.game_config.worm_initial_health//2)
						team.worms[i].healthStr = fonts.pixel5.render(str(team.worms[i].health), False, team.worms[i].team.color)
			Game._game.game_config.worm_initial_health = globals.team_manager.teams[0].worms[0].health
		
		# disable points in battle
		if Game._game.gameMode in [GameMode.BATTLE]:
			HealthBar.drawPoints = False

		# if Game._game.darkness:
		# 	WeaponManager._wm.renderWeaponCount()
		# 	for team in globals.team_manager.teams:
		# 		team.ammo(WeaponManager._wm.weapon_dict['flare'], 3)

		self.game_play.on_game_init()

		if Game._game.gameMode == GameMode.CAPTURE_THE_FLAG:
			place_object(Flag, None)

		if Game._game.gameMode == GameMode.ARENA:
			ArenaManager()

		if Game._game.gameMode == GameMode.MISSIONS:
			MissionManager()
			globals.time_manager.turnTime += 10
			MissionManager._mm.cycle()
		
		if Game._game.gameMode == GameMode.TERMINATOR:
			pickVictim()
			
	def point_to_world(self, point):
		return (int(point[0]) - int(GameVariables().cam_pos[0]), int(point[1]) - int(GameVariables().cam_pos[1]))

	def get_worms(self):
		return PhysObj._worms

	def clearLists(self):
		# clear lists
		PhysObj._reg.clear()
		PhysObj._worms.clear()
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
			m = deployPack(artifact)
		
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

		self.victim = None # worm targeted for termination
		self.terminatorHit = False # whether terminator hit in current turn
		self.cheatCode = "" # cheat code
		self.holdArtifact = True # whether to hold artifact
		self.worldArtifacts = [MJOLNIR, PLANT_MASTER, AVATAR, MINECRAFT] # world artifacts
		self.worldArtifactsClasses = [Mjolnir, MagicLeaf, Avatar, PickAxeArtifact]
		self.trigerArtifact = False # whether to trigger artifact drop next turn
		self.shotCount = 0 # number of gun shots fired

		self.player = None # object under control
		self.energising = False
		self.energyLevel = 0
		self.fireWeapon = False

		self.actionMove = False

		self.aimAid = False
		self.switchingWorms = False
		self.timeTravel = False
	
	def addExtra(self, pos, color = (255,255,255), delay = 5, absolute = False):
		self.extra.append((pos[0], pos[1], color, delay, absolute))
	
	def drawExtra(self):
		extraNext = []
		for i in self.extra:
			if not i[4]:
				win.fill(i[2], (point2world((i[0], i[1])),(1,1)))
			else:
				win.fill(i[2], ((i[0], i[1]),(1,1)))
			if i[3] > 0:
				extraNext.append((i[0], i[1], i[2], i[3]-1, i[4]))
		self.extra = extraNext
	
	def drawLayers(self):
		layersLinesNext = []

		for i in self.layersLines:
			pygame.draw.line(win, i[0], point2world(i[1]), point2world(i[2]), i[3])
			if i[4]:
				layersLinesNext.append((i[0], i[1], i[2], i[3], i[4]-1))
		self.layersLines = layersLinesNext

		for j in self.layersCircles:
			for i in j:
				pygame.draw.circle(win, i[0], point2world(i[1]), int(i[2]))
		self.layersCircles = [[],[],[]]
	
	def girder(self, pos):
		surf = pygame.Surface((self.girderSize, 10)).convert_alpha()
		for i in range(self.girderSize // 16 + 1):
			surf.blit(sprites.sprite_atlas, (i * 16, 0), (64,80,16,16))
		surfGround = pygame.transform.rotate(surf, self.girderAngle)
		self.map_manager.ground_map.blit(surfGround, (int(pos[0] - surfGround.get_width()/2), int(pos[1] - surfGround.get_height()/2)) )
		surf.fill(GRD)
		surfMap = pygame.transform.rotate(surf, self.girderAngle)
		self.map_manager.game_map.blit(surfMap, (int(pos[0] - surfMap.get_width()/2), int(pos[1] - surfMap.get_height()/2)) )
	
	def drawGirderHint(self):
		surf = pygame.Surface((self.girderSize, 10)).convert_alpha()
		for i in range(self.girderSize // 16 + 1):
			surf.blit(sprites.sprite_atlas, (i * 16, 0), (64,80,16,16))
		surf.set_alpha(100)
		surf = pygame.transform.rotate(surf, self.girderAngle)
		pos = pygame.mouse.get_pos()
		pos = Vector(pos[0]/scalingFactor , pos[1]/scalingFactor )
		win.blit(surf, (int(pos[0] - surf.get_width()/2), int(pos[1] - surf.get_height()/2)))
	
	def drawTrampolineHint(self):
		surf = pygame.Surface((24, 7), pygame.SRCALPHA)
		surf.blit(sprites.sprite_atlas, (0,0), (100, 117, 24, 7))
		position = self.player.pos + vectorFromAngle(self.player.shootAngle, 20)
		anchored = False
		for i in range(25):
			cpos = position.y + i
			if Game._game.map_manager.is_ground_at(Vector(position.x, cpos)):
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
				globals.weapon_manager.switchWeapon(menu_event)
				self.radial_weapon_menu = None
				is_handled = True
		
		is_handled |= globals.weapon_manager.handle_event(event)
		
		return is_handled

	def step(self):
		pass
	
	def addToScoreList(self, amount=1):
		"""add to score list if points, list entry: (surf, name, score)"""
		if len(self.killList) > 0 and self.killList[0][1] == self.player.nameStr:
			amount += self.killList[0][2]
			self.killList.pop(0)
		string = self.player.nameStr + ": " + str(amount)
		self.killList.insert(0, (fonts.pixel5_halo.render(string, False, GameVariables().initial_variables.hud_color), self.player.nameStr, amount))

	def lstepper(self):
		self.lstep += 1
		pos = (GameVariables().win_width/2 - Game._game.loadingSurf.get_width()/2, GameVariables().win_height/2 - Game._game.loadingSurf.get_height()/2)
		width = Game._game.loadingSurf.get_width()
		height = Game._game.loadingSurf.get_height()
		pygame.draw.rect(win, (255,255,255), ((pos[0], pos[1] + 20), ((self.lstep / self.lstepmax)*width, height)))
		screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
		pygame.display.update()
	
	def isPlayingState(self):
		return self.state in [PLAYER_CONTROL_1, PLAYER_CONTROL_2]

def drawLand():
	if Game._game.map_manager.game_map.get_width() == 0:
		return
	if MapManager().draw_ground_secondary:
		win.blit(Game._game.map_manager.ground_secondary, point2world((0,0)))
	win.blit(Game._game.map_manager.ground_map, point2world((0,0)))
	
	Game._game.map_manager.worm_col_map.fill(SKY)
	Game._game.map_manager.objects_col_map.fill(SKY)

# todo: determine where this belongs
def giveGoodPlace(div = 0, girderPlace = True):
	goodPlace = False
	counter = 0
	
	if Game._game.game_config.option_forts and not div == -1:
		half = Game._game.map_manager.game_map.get_width() / globals.team_manager.totalTeams
		Slice = div % globals.team_manager.totalTeams
		
		left = half * Slice
		right = left + half
		if left <= 0: left += 6
		if right >= Game._game.map_manager.game_map.get_width(): right -= 6
	else:
		left, right = 6, Game._game.map_manager.game_map.get_width() - 6
	
	if Game._game.game_config.option_digging:
		while not goodPlace:
			place = Vector(randint(int(left), int(right)), randint(6, Game._game.map_manager.game_map.get_height() - 50))
			goodPlace = True
			for worm in PhysObj._worms:
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
		place = Vector(randint(int(left), int(right)), randint(6, Game._game.map_manager.game_map.get_height() - 6))
		
		# if in Game._game.map_manager.ground_map 
		if isGroundAround(place):
			goodPlace = False
			continue
		
		if counter > 8000:
			# if too many iterations, girder place
			if not girderPlace:
				return None
			for worm in PhysObj._worms:
				if distus(worm.pos, place) < 2500:
					goodPlace = False
					break
			if  not goodPlace:
				continue
			Game._game.girder(place + Vector(0,20))
			return place
		
		# put place down
		y = place.y
		for i in range(Game._game.map_manager.game_map.get_height()):
			if y + i >= Game._game.map_manager.game_map.get_height():
				goodPlace = False
				break
			if Game._game.map_manager.game_map.get_at((place.x, y + i)) == GRD or Game._game.map_manager.worm_col_map.get_at((place.x, y + i)) != (0,0,0) or Game._game.map_manager.objects_col_map.get_at((place.x, y + i)) != (0,0,0):
				y = y + i - 7
				break
		if  not goodPlace:
			continue
		place.y = y
		
		# check for nearby worms in radius 50
		for worm in PhysObj._worms:
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
		if isGroundAround(place):
			pygame.draw.circle(Game._game.map_manager.game_map, SKY, place.vec2tup(), 5)
			pygame.draw.circle(Game._game.map_manager.ground_map, SKY, place.vec2tup(), 5)
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
	
def move(obj):
	dir = obj.facing
	if MapManager().check_free_pos(obj.radius, obj.pos + Vector(dir, 0)):
		obj.pos += Vector(dir, 0) * GameVariables().dt
		return True
	else:
		for i in range(1,5):
			if MapManager().check_free_pos(obj.radius, obj.pos + Vector(dir, -i)):
				obj.pos += Vector(dir, -i) * GameVariables().dt
				return True
		for i in range(1,5):
			if MapManager().check_free_pos(obj.radius, obj.pos + Vector(dir, i)):
				obj.pos += Vector(dir, i) * GameVariables().dt
				return True
	return False

def moveFallProof(obj):
	dir = obj.facing
	if checkFreePosFallProof(obj, obj.pos + Vector(dir, 0)):
		obj.pos += Vector(dir, 0)
		return True
	else:
		for i in range(1,5):
			if checkFreePosFallProof(obj, obj.pos + Vector(dir, -i)):
				obj.pos += Vector(dir, -i)
				return True
		for i in range(1,5):
			if checkFreePosFallProof(obj, obj.pos + Vector(dir, i)):
				obj.pos += Vector(dir, i)
				return True
	return False

def checkFreePosFallProof(obj, pos):
	r = 0
	while r < 2 * pi:
		testPos = Vector((obj.radius) * cos(r) + pos.x, (obj.radius) * sin(r) + pos.y)
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - GameVariables().water_level or testPos.x < 0:
			if GameVariables().config.option_closed_map:
				return False
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			r += pi /8
			continue
			
		if not Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == (0,0,0):
			return False
		
		r += pi /8
	# check for falling
	groundUnder = False
	for i in range(int(obj.radius), 50):
		# extra.append((pos.x, pos.y + i, (255,255,255), 5))
		if Game._game.map_manager.game_map.get_at((int(pos.x), int(pos.y + i))) == GRD:
			groundUnder = True
			break
	return groundUnder

def getClosestPosAvail(pos: Vector, radius: int):
	r = 0
	found = None
	orgPos = vectorCopy(pos)
	t = 0
	while not found:
		checkPos = orgPos + t * vectorFromAngle(r)
		# addExtra(checkPos, (255,255,255), 100)
		if MapManager().check_free_pos(radius, checkPos, True):
			found = checkPos
			break
		# t += 1
		r += pi/8
		if r > 2*pi - 0.01 and r < 2*pi + 0.01:
			r = 0
			t += 1
			if t > 100:
				return None
	return checkPos

def getNormal(pos, vel, radius, wormCollision: bool, extraCollision: bool) -> Vector:
	''' returns collision with world response '''
	response = Vector(0,0)
	angle = atan2(vel.y, vel.x)
	r = angle - pi
	while r < angle + pi:
		testPos = Vector((radius) * cos(r) + pos.x, (radius) * sin(r) + pos.y)
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - GameVariables().water_level or testPos.x < 0:
			if GameVariables().config.option_closed_map:
				response += pos - testPos
				r += pi /8
				continue
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			r += pi /8
			continue
		
		if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
			response += pos - testPos
		if wormCollision and Game._game.map_manager.worm_col_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
			response += pos - testPos
		if extraCollision and Game._game.map_manager.objects_col_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
			response += pos - testPos
		
		r += pi /8
	return response

################################################################################ Objects

class TimeManager:
	''' manages time overall measuring, turn time counting '''
	_tm = None
	def __init__(self):
		TimeManager._tm = self
		globals.time_manager = self

		self.turnTime = 45
		self.retreatTime = 5
		self.wormDieTime = 3

		self.timeCounter: int = self.turnTime
		self.generateTimeSurf()
	def generateTimeSurf(self):
		self.timeSurf = (self.timeCounter, fonts.pixel5_halo.render(str(self.timeCounter), False, GameVariables().initial_variables.hud_color))
	def step(self):
		GameVariables().time_overall += 1
		if GameVariables().time_overall % fps == 0:
			self.timeStep()
	def timeStep(self):
		if self.timeCounter == 0:
			self.timeOnTimer()
		if not self.timeCounter <= 0:
			self.timeCounter -= 1
	def timeOnTimer(self):
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.state = WAIT_STABLE
			
		elif Game._game.state == PLAYER_CONTROL_2:
			Game._game.state = Game._game.nextState
			
	def draw(self, win: pygame.Surface):
		if self.timeSurf[0] != self.timeCounter:
			self.generateTimeSurf()
		win.blit(self.timeSurf[1] , ((5, 5)))
	def timeReset(self):
		self.timeCounter = self.turnTime
	def timeRemaining(self, amount):
		self.timeCounter = amount
	def timeRemainingRetreat(self):
		self.timeRemaining(self.retreatTime)
	def timeRemainingDie(self):
		self.timeRemaining(self.wormDieTime)





class Worm (PhysObj):
	healthMode = 0
	roped = False
	causeFlew = 0
	causeVenus = 1
	def __init__(self, pos, name=None, team=None):
		self._worms.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.color = (255, 206, 167)
		self.radius = 3.5
		self.damp = 0.2
		self.facing = RIGHT if self.pos.x < MapManager().game_map.get_width()/2 else LEFT
		self.shootAngle = 0 if self.pos.x < MapManager().game_map.get_width()/2 else pi
		self.shootAcc = 0
		self.shootVel = 0
		self.health = GameVariables().config.worm_initial_health
		self.alive = True
		self.team: Team = team
		self.sick = 0
		self.gravity = DOWN
		self.nameStr = name
		self.name = fonts.pixel5.render(self.nameStr, False, self.team.color)
		self.healthStr = fonts.pixel5.render(str(self.health), False, self.team.color)
		self.score = 0
		self.wormCollider = True
		self.flagHolder = False
		self.sleep = False
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0,0,16,16))
		self.surf.blit(self.team.hatSurf, (0,0))
		self.angle = 0
		self.stableCount = 0
		self.worm_tool = WormTool()
	
	def applyForce(self):
		# gravity:
		if self.gravity == DOWN:
			self.acc.y += GameVariables().physics.global_gravity			
			self.worm_tool.apply_force()

		else:# up
			self.acc.y -= GameVariables().physics.global_gravity
	
	def drawCursor(self):
		shootVec = self.pos + Vector((cos(self.shootAngle) * 20) ,sin(self.shootAngle) * 20)
		pygame.draw.circle(win, (255,255,255), (int(shootVec.x) - int(GameVariables().cam_pos[0]), int(shootVec.y) - int(GameVariables().cam_pos[1])), 2)
	
	def sicken(self, sickness = 1):
		self.sick = sickness
		self.surf.fill((0,0,0,0))
		self.surf.blit(sprites.sprite_atlas, (0,0), (16,0,16,16))
		self.surf.blit(self.team.hatSurf, (0,0))
		self.color = (128, 189,66)
		if MissionManager._mm: MissionManager._mm.notifySick(self)
	
	def heal(self, hp):
		self.health += hp
		if self.healthMode == 1:
			self.healthStr = fonts.pixel5.render(str(self.health), False, self.team.color)
		self.sick = 0
		self.color = (255, 206, 167)
		self.surf.fill((0,0,0,0))
		self.surf.blit(sprites.sprite_atlas, (0,0), (0,0,16,16))
		self.surf.blit(self.team.hatSurf, (0,0))
			
	def damage(self, value, damageType=0):
		if self.alive:
			dmg = int(value * GameVariables().damage_mult)
			if dmg < 1:
				dmg = 1
			if dmg > self.health:
				dmg = self.health
			
			if dmg != 0: FloatingText(self.pos.vec2tup(), str(dmg))
			self.health -= dmg
			if self.health < 0:
				self.health = 0
			if Worm.healthMode == 1:
				self.healthStr = fonts.pixel5.render(str(self.health), False, self.team.color)
			if not self == Game._game.player:
				if not Game._game.sentring and not Game._game.raoning and not Game._game.waterRising and not self in globals.team_manager.currentTeam.worms:
					Game._game.damageThisTurn += dmg
			Game._game.game_play.on_worm_damage(self)
			if Game._game.gameMode == GameMode.CAPTURE_THE_FLAG and damageType != 2:
				if self.flagHolder:
					self.team.flagHolder = False
					self.flagHolder = False
					Flag(self.pos)
			if Game._game.gameMode == GameMode.TERMINATOR and Game._game.victim == self and not Game._game.terminatorHit:
				globals.team_manager.currentTeam.points += 1
				Game._game.addToScoreList()
				Game._game.terminatorHit = True
			if Game._game.gameMode == GameMode.MISSIONS:
				MissionManager._mm.notifyHit(self)
	
	def draw(self, win: pygame.Surface):
		if not self is Game._game.player and self.alive:
			pygame.draw.circle(Game._game.map_manager.worm_col_map, GRD, self.pos.vec2tupint(), int(self.radius)+1)

		self.worm_tool.draw(win)

		if self.flagHolder:
			pygame.draw.line(win, (51, 51, 0), point2world(self.pos), point2world(self.pos + Vector(0, -3 * self.radius)))
			pygame.draw.rect(win, (220,0,0), (point2world(self.pos + Vector(1, -3 * self.radius)), (self.radius*2, self.radius*2)))
			
		# draw artifact
		if len(self.team.artifacts) > 0 and Game._game.holdArtifact:
			if self is Game._game.player and WeaponManager._wm.currentWeapon == WeaponCategory.ARTIFACTS:
				if WeaponManager._wm.currentArtifact() in self.team.artifacts:
					if WeaponManager._wm.currentArtifact() == MJOLNIR:
						win.blit(Game._game.imageMjolnir, point2world(self.pos + Vector(self.facing * 3, -5) - tup2vec(Game._game.imageMjolnir.get_size())/2))

		# draw worm sprite
		angle = 45 * int(self.angle / 45)
		fliped = pygame.transform.flip(self.surf, self.facing == RIGHT, False)
		rotated = pygame.transform.rotate(fliped, angle)
		if self.gravity == UP:
			rotated = pygame.transform.flip(rotated, False, True)
		pygame.draw.circle(win, self.color, point2world(self.pos), self.radius + 1)
		win.blit(rotated, point2world(self.pos - tup2vec(rotated.get_size())//2))
		
		# draw name
		nameHeight = -21
		namePos = Vector(self.pos.x - self.name.get_width()/2, max(self.pos.y + nameHeight, 10))
		win.blit(self.name , point2world(namePos))
		if self.alive and self.pos.y < 0:
			num = fonts.pixel5.render(str(int(-self.pos.y)), False, self.team.color)
			win.blit(num, point2world(namePos + Vector(self.name.get_width() + 2,0)))
		
		if self.alive and GameVariables().initial_variables.draw_health_bar:
			self.drawHealth()
		if self.sleep and self.alive:
			if GameVariables().time_overall % fps == 0:
				FloatingText(self.pos, "z", (0,0,0))
				
		# draw holding weapon
		if self is Game._game.player and Game._game.state in [PLAYER_CONTROL_1]:
			weaponSurf = pygame.transform.rotate(pygame.transform.flip(Game._game.weaponHold, False, self.facing == LEFT), -degrees(self.shootAngle))
			win.blit(weaponSurf, point2world(self.pos - tup2vec(weaponSurf.get_size())/2 + Vector(0, 5)))

	def __str__(self):
		return self.nameStr
	
	def __repr__(self):
		return str(self)
	
	def dieded(self, cause=-1):
		
		if Game._game.timeTravel:
			TimeTravel._tt.timeTravelPlay()
			return
		
		self.alive = False
		self.color = (167,167,167)
		self.surf.fill((0,0,0,0))
		self.surf.blit(sprites.sprite_atlas, (0,0), (32,0,16,16))
		self.name = fonts.pixel5.render(self.nameStr, False, grayen(self.team.color))

		# insert to kill list:
		if not Game._game.sentring and not Game._game.raoning and not Game._game.waterRising and not self in globals.team_manager.currentTeam.worms:
			Game._game.damageThisTurn += self.health
			globals.team_manager.currentTeam.killCount += 1
			if Game._game.gameMode == GameMode.POINTS:
				string = self.nameStr + " by " + Game._game.player.nameStr
				Game._game.killList.insert(0, (fonts.pixel5_halo.render(string, False, GameVariables().initial_variables.hud_color), 0))
		
		self.health = 0
		
		# if capture the flag:
		if self.flagHolder:
			self.flagHolder = False
			self.team.flagHolder = False
			if cause == Worm.causeFlew:
				p = deployPack(Flag)
				GameVariables().cam_track = p
			else:
				Flag(self.pos)
		
		# commentator:
		if cause == -1:
			EventComment.post_choice_event(comments_damage, self.nameStr, self.team.color)
			
		elif cause == Worm.causeFlew:
			comment = True
			if not self in globals.team_manager.currentTeam.worms and WeaponManager._wm.currentWeapon == "baseball" and Game._game.state in [PLAYER_CONTROL_2, WAIT_STABLE]:
				GameEvents().post(EventComment([{'text': self.nameStr, 'color': self.team.color}, {'text': 'home run'}]))
				comment = False
			if comment:
				EventComment.post_choice_event(comments_flew, self.nameStr, self.team.color)
		
		# remove from regs:
		if self in PhysObj._worms:
			PhysObj._worms.remove(self)
		if self in self.team.worms:
			self.team.worms.remove(self)
		if cause == Worm.causeFlew or cause == Worm.causeVenus:
			self.removeFromGame()
		
		# if under control 
		if Game._game.player == self:
			Game._game.nextState = PLAYER_CONTROL_2
			Game._game.state = Game._game.nextState
			TimeManager._tm.timeRemainingDie()
		if Game._game.gameMode == GameMode.TERMINATOR and self == Game._game.victim:
			globals.team_manager.currentTeam.points += 1
			Game._game.addToScoreList()
			if not Game._game.terminatorHit:
				globals.team_manager.currentTeam.points += 1
				Game._game.addToScoreList()
			if Game._game.state == PLAYER_CONTROL_1:
				pickVictim()
		
		# if team kill and artifacts
		if Game._game.game_config.option_artifacts and len(self.team.worms) == 0:
			if len(self.team.artifacts) > 0:
				for artifact in self.team.artifacts:
					Game._game.dropArtifact(WeaponManager._wm.artifactDict[artifact], self.pos)

		# if mission
		if Game._game.gameMode == GameMode.MISSIONS:
			MissionManager._mm.notifyKill(self)

	def drawHealth(self):
		healthHeight = -15
		if Worm.healthMode == 0:
			value = 20 * min(self.health / Game._game.game_config.worm_initial_health, 1)
			if value < 1:
				value = 1
			pygame.draw.rect(win, (220,220,220),(point2world(self.pos + Vector(-10, healthHeight)),(20,3)))
			pygame.draw.rect(win, (0,220,0),(point2world(self.pos + Vector(-10, healthHeight)), (int(value),3)))
		else:
			win.blit(self.healthStr , point2world(self.pos + Vector(-self.healthStr.get_width()/2, healthHeight)))
	
	def secondaryStep(self):
	
		if self.stable and self.alive:
			self.stableCount += 1
			if self.stableCount >= 30:
				
				self.angle *= 0.8
		else:
			self.stableCount = 0
			if not self is Game._game.player:
				self.angle -= self.vel.x * 4
				self.angle = self.angle % 360
		
		if Game._game.player == self and Game._game.playerControl and self.alive:
			keys = pygame.key.get_pressed()
			if keys[pygame.K_UP]:# or joystick.get_axis(1) < -0.5:
				self.shootAcc = -0.04
			elif keys[pygame.K_DOWN]:# or joystick.get_axis(1) > 0.5:
				self.shootAcc = 0.04
			else:
				self.shootAcc = 0
				self.shootVel = 0
		else:
			self.damp = 0.2
			self.shootAcc = 0
			self.shootVel = 0

		self.worm_tool.step()
		
		# virus
		if self.sick == 2 and self.health > 0 and not Game._game.state == WAIT_STABLE:
			if randint(1,200) == 1:
				GasParticles._sp.addSmoke(self.pos, color=(102, 255, 127))
		
		# shooting angle
		self.shootVel = clamp(self.shootVel + self.shootAcc, 0.1, -0.1)
		self.shootAngle += self.shootVel * self.facing
		if self.facing == RIGHT:
			self.shootAngle = clamp(self.shootAngle, pi/2, -pi/2)
		elif self.facing == LEFT:
			self.shootAngle = clamp(self.shootAngle, pi + pi/2, pi/2)
				
		# check if killed:
		if self.health <= 0 and self.alive:
			self.dieded()
		
		# check if on Game._game.map_manager.game_map:
		if self.pos.y > Game._game.map_manager.game_map.get_height() - GameVariables().water_level:
			splash(self.pos, self.vel)
			angle = self.vel.getAngle()
			if (angle > 2.7 and angle < 3.14) or (angle > 0 and angle < 0.4):
				if self.vel.getMag() > 7:
					self.pos.y = Game._game.map_manager.game_map.get_height() - GameVariables().water_level - 1
					self.vel.y *= -1
					self.vel.x *= 0.7
			else:
				self.dieded(Worm.causeFlew)
		if self.pos.y < 0:
			self.gravity = DOWN
		if Game._game.actionMove:
			if Game._game.player == self and self.health > 0 and not self.worm_tool.in_use():
				move(self)

		if not self.stable:
			velocity = self.vel.getMag()
			if velocity > 5:
				for worm in PhysObj._worms:
					if worm == self or not worm.stable:
						continue
					if distus(self.pos, worm.pos) < (self.radius + worm.radius) * (self.radius + worm.radius):
						worm.vel = vectorCopy(self.vel)

def fireShotgun(pos: Vector, direction: Vector, power: int=15):#6
	GunShell(pos + Vector(0, -4), direction=direction)
	for t in range(5,500):
		testPos = pos + direction * t
		Game._game.addExtra(testPos, (255, 204, 102), 3)
		
		if testPos.y >= MapManager().game_map.get_height() - GameVariables().water_level:
			splash(testPos, Vector(10,0))
			break
		if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue

		at = (int(testPos.x), int(testPos.y))
		if MapManager().game_map.get_at(at) == GRD or MapManager().worm_col_map.get_at(at) != (0,0,0) or MapManager().objects_col_map.get_at(at) != (0,0,0):
			if MapManager().worm_col_map.get_at(at) != (0,0,0):
				MapManager().stain(testPos, sprites.blood, sprites.blood.get_size(), False)
			boom(testPos, power)
			break

def fireFlameThrower(pos: Vector, direction: Vector, power: int=0):#8
	offset = uniform(1,2)
	f = Fire(pos + direction * 5)
	f.vel = direction * offset * 2.4

class ShootGun:
	def __init__(self, **kwargs) -> None:
		Game._game.nonPhys.append(self)
		self.ammo = kwargs.get('count')
		self.shoot_action = kwargs.get('func')
		self.power = kwargs.get('power', 0)
		self.end_turn = kwargs.get('end_turn', True)
		self.burst = kwargs.get('burst', False)

		self.shooted_object: EntityOnMap | None = None

	def step(self) -> None:
		if self.burst:
			fire()

	def draw(self, win: pygame.Surface) -> None:
		pass

	def shoot(self) -> None:
		if self.ammo == 0:
			return
		args = (
			vectorCopy(Game._game.player.pos),
			vectorFromAngle(Game._game.player.shootAngle),
			self.power
		)
		self.shooted_object = self.shoot_action(*args)
		self.ammo -= 1
	
	def get_object(self) -> EntityOnMap:
		result = self.shooted_object
		self.shooted_object = None
		return result

	def is_done(self) -> bool:
		return self.ammo == 0
	
	def is_end_turn(self) -> bool:
		return self.end_turn
	
	def remove(self) -> None:
		Game._game.nonPhysToRemove.append(self)
	


def fireMiniGun(pos: Vector, direction: Vector, power: int=0):#0
	angle = atan2(direction[1], direction[0])
	angle += uniform(-0.2, 0.2)
	direction[0], direction[1] = cos(angle), sin(angle)
	fireShotgun(pos, direction, randint(7,9))

class Mine(PhysObj):
	def __init__(self, pos=(0,0), delay=0):
		self.initialize()
		self._mines.append(self)
		self.pos = tup2vec(pos)
		self.radius = 2
		self.color = (52,66,71)
		self.damp = 0.35
		self.activated = False
		self.alive = delay == 0
		self.timer = delay
		self.exploseTime = randint(5, 100)
		self.windAffected = 0

	def secondaryStep(self):
		if not self.alive:
			self.timer -= 1
			if self.timer == 0:
				self.alive = True
				self.damp = 0.55
			return
		if not self.activated:
			for w in PhysObj._worms:
				if w.health <= 0:
					continue
				if distus(self.pos, w.pos) < 625:
					self.activated = True
		else:
			self.timer += 1
			self.stable = False
			if self.timer == self.exploseTime:
				self.dead = True
				
		if self.activated:
			EffectManager().add_light(vectorCopy(self.pos), 50, (100,0,0,100))

	def deathResponse(self):
		boom(self.pos, 30)

	def draw(self, win: pygame.Surface):
		if Game._game.game_config.option_digging:
			if self.activated:
				pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
				if self.timer % 2 == 0:
					pygame.draw.circle(win, (222,63,49), point2world(self.pos), 1)
			return

		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)		
		if not self.activated:
			pygame.draw.circle(win, (222,63,49), point2world(self.pos), 1)
		else:
			if self.timer % 2 == 0:
				pygame.draw.circle(win, (222,63,49), point2world(self.pos), 1)

class Baseball:
	def __init__(self):	
		self.direction = vectorFromAngle(Game._game.player.shootAngle)
		Game._game.nonPhys.append(self)
		self.timer = 0
		hitted = []
		for t in range(5, 25):
			testPositions = []
			testPos = Game._game.player.pos + self.direction * t
			testPositions.append(testPos)
			testPositions.append(testPos + normalize(self.direction).getNormal() * 3)
			testPositions.append(testPos - normalize(self.direction).getNormal() * 3)
			
			for worm in PhysObj._worms:
				for point in testPositions:
					if worm in hitted:
						continue
					if distus(point, worm.pos) < worm.radius * worm.radius:
						hitted.append(worm)
						worm.damage(randint(15,25))
						worm.vel += self.direction * 8
						GameVariables().cam_track = worm

	def step(self):
		self.timer += 1 * GameVariables().dt
		if self.timer >= 15:
			Game._game.nonPhysToRemove.append(self)

	def draw(self, win: pygame.Surface):
		weaponSurf = pygame.transform.rotate(pygame.transform.flip(Game._game.weaponHold, False, Game._game.player.facing == LEFT), -degrees(Game._game.player.shootAngle) + 180)
		win.blit(weaponSurf, point2world(Game._game.player.pos - tup2vec(weaponSurf.get_size())/2 + self.direction * 16))

class GasGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.color = (113,117,41)
		self.bounceBeforeDeath = -1
		self.damp = 0.5
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "gas grenade")
		self.angle = 0
		self.state = "throw"
	def deathResponse(self):
		boom(self.pos, 20)
		for i in range(40):
			vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1,1.5)
			GasParticles._sp.addSmoke(self.pos, vel, color=(102, 255, 127))
	def secondaryStep(self):
		gameDistable()
		self.angle -= self.vel.x*4
		self.timer += 1
		if self.state == "throw":
			if self.timer >= GameVariables().fuse_time:
				self.state = "release"
		if self.state == "release":
			if self.timer % 3 == 0:
				GasParticles._sp.addSmoke(self.pos, vectorUnitRandom(), color=(102, 255, 127))
			if self.timer >= GameVariables().fuse_time + 5 * fps:
				self.dead = True

class Deployable(ExplodingProp):
	def __init__(self, pos = (0,0)):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 5
		self.damp = 0.01
		self.health = 5
		self.fallAffected = False
		self.windAffected = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)

	def draw(self, win: pygame.Surface):
		win.blit(self.surf , point2world(self.pos - tup2vec(self.surf.get_size())/2))

	def secondaryStep(self):
		if distus(Game._game.player.pos, self.pos) < (self.radius + Game._game.player.radius + 5) * (self.radius + Game._game.player.radius + 5)\
			and not Game._game.player.health <= 0:
			self.effect(Game._game.player)
			self.removeFromGame()
			return
		if self.health <= 0:
			self.deathResponse()
			self.removeFromGame()

	def effect(self, worm):
		...

class HealthPack(Deployable):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		self.surf.blit(sprites.sprite_atlas, (0,0), (112, 96, 16, 16))

	def effect(self, worm: Worm):
		worm.heal(50)
		FloatingText(self.pos, "+50", (0,230,0))

class UtilityPack(Deployable):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		self.box = choice(["moon gravity", "double damage", "aim aid", "teleport", "switch worms", "time travel", "jet pack", "tool set", "travel kit"])
		self.surf.blit(sprites.sprite_atlas, (0,0), (96, 96, 16, 16))

	def effect(self, worm):
		FloatingText(self.pos, self.box, (0,200,200))
		weapon_dict = WeaponManager._wm.weapon_dict
		if self.box == "tool set":
			worm.team.ammo(weapon_dict["portal gun"], 1)
			worm.team.ammo(weapon_dict["ender pearl"], 5)
			worm.team.ammo(weapon_dict["trampoline"], 3)
			return
		elif self.box == "travel kit":
			worm.team.ammo(weapon_dict["rope"], 3)
			worm.team.ammo(weapon_dict["parachute"], 3)
			return
		worm.team.ammo(weapon_dict[self.box], 1)

class WeaponPack(Deployable):
	def __init__(self, pos = (0,0)):
		super().__init__(pos)
		weaponsInBox = ["banana", "holy grenade", "earthquake", "gemino mine", "sentry turret", "bee hive", "vortex grenade", "chilli pepper", "covid 19", "raging bull", "electro boom", "pokeball", "green shell", "guided missile", "fireworks"]
		if GameVariables().initial_variables.allow_air_strikes:
			weaponsInBox .append("mine strike")
		self.box = WeaponManager._wm.weapon_dict[choice(weaponsInBox)]
		self.surf.blit(sprites.sprite_atlas, (0,0), (80, 96, 16, 16))

	def effect(self, worm):
		FloatingText(self.pos, self.box.name, (0,200,200))
		worm.team.ammo(self.box, 1)

def deployPack(pack):
	x = 0
	ymin = 20
	goodPlace = False #1 has Game._game.map_manager.ground_map under. #2 not in Game._game.map_manager.ground_map. #3 not above worm 
	while not goodPlace:
		x = randint(10, Game._game.map_manager.game_map.get_width() - 10)
		y = randint(10, ymin)
		
		goodPlace = True
		# test1
		if isGroundAround(Vector(x,y), 10):
			goodPlace = False
			ymin += 10
			if ymin > 500:
				ymin = 20
			continue
		
		# test2
		for i in range(Game._game.map_manager.game_map.get_height()):
			if y + i >= Game._game.map_manager.game_map.get_height() - GameVariables().water_level:
				# no Game._game.map_manager.ground_map bellow
				goodPlace = False
				continue
			if Game._game.map_manager.game_map.get_at((x, y + i)) == GRD:
				goodPlace = True
				break
		# test3 (hopefully always possible)
		for worm in PhysObj._worms:
			if x > worm.pos.x-15 and x < worm.pos.x+15:
				goodPlace = False
				continue
	
	p = pack(Vector(x, y))
	return p

def fireAirstrike(pos):
	x = pos[0]
	y = 5
	for i in range(5):
		f = Missile((x - 40 + 20*i, y - i), (Game._game.airStrikeDir ,0), 0.1)
		f.megaBoom = False
		f.boomAffected = False
		f.radius = 1
		f.boomRadius = 19
		if i == 2:
			GameVariables().cam_track = f

def fireMineStrike(pos):
	megaBoom = False
	if randint(0,50) == 1 or GameVariables().mega_weapon_trigger:
		megaBoom = True
	x = pos[0]
	y = 5
	if megaBoom:
		for i in range(20):
			m = Mine((x - 40 + 4*i, y - i))
			m.vel.x = Game._game.airStrikeDir
			if i == 10:
				GameVariables().cam_track = m
	else:
		for i in range(5):
			m = Mine((x - 40 + 20*i, y - i))
			m.vel.x = Game._game.airStrikeDir
			if i == 2:
				GameVariables().cam_track = m

def fireNapalmStrike(pos):
	x = pos[0]
	y = 5
	for i in range(70):
		f = Fire((x - 35 + i, y ))
		f.vel = Vector(cos(uniform(pi, 2*pi)), sin(uniform(pi, 2*pi))) * 0.5
		if i == 2:
			GameVariables().cam_track = f



def fireGammaGun(pos: Vector, direction: Vector, power: int=15):
	hitted = []
	normal = Vector(-direction.y, direction.x).normalize()
	for t in range(5,500):
		testPos = pos + direction * t + normal * 1.5 * sin(t * 0.6) * (t + 1)/70
		Game._game.addExtra(testPos, (0,255,255), 10)
		
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue
		# if hits worm:
		for worm in PhysObj._worms:
			if distus(testPos, worm.pos) < worm.radius * worm.radius and not worm in hitted:
				worm.damage(int(10 / GameVariables().damage_mult) + 1)
				if randint(0,20) == 1:
					worm.sicken(2)
				else:
					worm.sicken()
				hitted.append(worm)
		# if hits plant:
		for plant in Venus._reg:
			if distus(testPos, plant.pos + plant.direction * 25) <= 625:
				plant.mutate()
		for target in ShootingTarget._reg:
			if distus(testPos, target.pos) < target.radius * target.radius:
				target.explode()


class Gemino(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (52,66,71)
		self.bounceBeforeDeath = 5
		self.damp = 0.6
	def collisionRespone(self, ppos):
		m = Mine(self.pos)
		# m = Gemino(self.pos, vectorUnitRandom(), uniform(0,2))
		m.vel = vectorUnitRandom() 
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(GameVariables().cam_pos[0]), int(self.pos.y) - int(GameVariables().cam_pos[1])), int(self.radius)+1)
		pygame.draw.circle(win, (222,63,49), (int(self.pos.x) - int(GameVariables().cam_pos[0]), int(self.pos.y) - int(GameVariables().cam_pos[1])), 1)

class Plant:
	def __init__(self, pos, radius = 5, angle = -1, mode = 0):
		Game._game.nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		if angle == -1:
			self.angle = uniform(0, 2*pi)
		else:
			self.angle = angle
		self.stable = False
		self.boomAffected = False
		self.radius = radius
		self.timeCounter = 0
		self.green = 135
		self.mode = mode
	def step(self):
		self.pos += vectorFromAngle(self.angle + uniform(-1,1))
		if randint(1,100) <= 2 and not self.mode == PlantBomb.venus:
			Plant(self.pos, self.radius, self.angle + choice([pi/3, -pi/3]), self.mode)
		self.timeCounter += 1
		if self.timeCounter % 10 == 0:
			self.radius -= 1
		self.green += randint(-5,5)
		if self.green > 255:
			self.green = 255
		if self.green < 0:
			self.green = 0
		pygame.draw.circle(Game._game.map_manager.game_map, GRD, (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		pygame.draw.circle(Game._game.map_manager.ground_map, (55,self.green,40), (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		if randint(0, 100) <= 10:
			leaf(self.pos, self.angle + 90, (55,self.green,40))
		if self.radius == 0:
			Game._game.nonPhysToRemove.append(self)
			if self.mode == PlantBomb.venus:
				pygame.draw.circle(Game._game.map_manager.game_map, GRD, (int(self.pos[0]), int(self.pos[1])), 3)
				pygame.draw.circle(Game._game.map_manager.ground_map, (55,self.green,40), (int(self.pos[0]), int(self.pos[1])), 3)
				Venus(self.pos, self.angle)
			if self.mode == PlantBomb.mine:
				Mine(self.pos, fps * 2)
	def draw(self, win: pygame.Surface):
		pass

class PlantBomb(PhysObj):
	bomb = 0
	venus = 1
	bean = 2
	mine = 3
	mode = 1
	def __init__(self, pos, direction, energy, mode=0):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (204, 204, 0)
		self.damp = 0.5
		self.mode = mode
		self.wormCollider = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "venus fly trap")
		self.angle = 0
	def secondaryStep(self):
		self.angle -= self.vel.x*4
	def collisionRespone(self, ppos):

		response = getNormal(ppos, self.vel, self.radius, False, True)
		
		self.removeFromGame()
		
		if self.mode == PlantBomb.bomb:
			for i in range(randint(4,5)):
				Plant(ppos)
		elif self.mode == PlantBomb.venus:
			Plant(ppos, 5, response.getAngle(), PlantBomb.venus)
		elif self.mode == PlantBomb.bean:
			w = MagicBeanGrow(ppos, normalize(response))
			GameVariables().cam_track = w
		elif self.mode == PlantBomb.mine:
			for i in range(randint(2,3)):
				Plant(ppos, 5, -1, PlantBomb.mine)
		
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class SentryGun(PhysObj):
	_sentries = []
	def __init__(self, pos, teamColor):
		self._sentries.append(self)
		self.initialize()
		self.pos = Vector(pos[0],pos[1])
		
		self.color = (0, 102, 0)
		self.boomAffected = True
		self.radius = 9
		self.health = 50
		self.teamColor = teamColor
		self.target = None
		self.damp = 0.1
		self.shots = 10
		self.firing = False
		self.timer = 20
		self.timesFired = randint(5,7)
		self.angle = 0
		self.angle2for = uniform(0, 2*pi)
		self.surf = pygame.Surface((17, 26), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (80, 32, 17, 26))
		self.electrified = False
		pygame.draw.circle(self.surf, self.teamColor, tup2vec(self.surf.get_size())//2, 2)
	def fire(self):
		self.firing = True
	def engage(self):
		close = []
		for worm in PhysObj._worms:
			if worm.team.color == self.teamColor:
				continue
			distance = distus(worm.pos, self.pos)
			if distance < 10000:
				close.append((worm, distance))
		if len(close) > 0:
			close.sort(key = lambda elem: elem[1])
			self.target = close[0][0]
		else:
			self.target = None
	def secondaryStep(self):
		if self.firing:
			if not self.target:
				return
			self.timer -= 1
			self.stable = False
			self.angle2for = (self.target.pos - self.pos).getAngle()
			if self.timer <= 0 and self.target:
				direction = self.target.pos - self.pos
				fireMiniGun(self.pos, direction)
				self.angle = direction.getAngle()
				self.shots -= 1
				if self.shots == 0:
					self.firing = False
					self.shots = 10
					self.timer = 20
					self.timesFired -= 1
					self.target = None
					if self.timesFired == 0:
						self.health = 0
		
		if self.electrified:
			if GameVariables().time_overall % 2 == 0:
				self.angle = uniform(0,2*pi)
				fireMiniGun(self.pos, vectorFromAngle(self.angle))
		
		self.angle += (self.angle2for - self.angle)*0.2
		if not self.target and GameVariables().time_overall % (fps*2) == 0:
			self.angle2for = uniform(0,2*pi)
		
		# extra "damp"
		if self.vel.x > 0.1:
			self.vel.x = 0.1
		if self.vel.x < -0.1:
			self.vel.x = -0.1
		if self.vel.y < 0.1:
			self.vel.y = 0.1
			
		if self.health <= 0:
			self.removeFromGame()
			self._sentries.remove(self)
			boom(self.pos, 20)
			
	def draw(self, win: pygame.Surface):
		size = Vector(4*2,10*2)
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))
		pygame.draw.line(win, self.teamColor, point2world(self.pos), point2world(self.pos + vectorFromAngle(self.angle) * 18))
	def damage(self, value, damageType=0):
		dmg = value
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0

class Bee:
	def __init__(self, pos, angle):
		PhysObj._reg.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.stable = False
		self.boomAffected = False
		self.radius = 1
		self.color = (230, 230, 0)
		self.angle = angle
		self.target = None
		self.lifespan = 330
		self.unreachable = []
		self.vel = Vector()
		self.surf = None
	def removeFromGame(self):
		PhysObj._toRemove.append(self)
	def step(self):
		self.lifespan -= 1
		gameDistable()
		if self.lifespan == 0:
			self.removeFromGame()
			return
		if self.target:
			self.angle = (self.target.pos - self.pos).getAngle()
		else:
			self.angle += uniform(-0.6,0.6)
		ppos = self.pos + vectorFromAngle(self.angle)
		if ppos.x >= Game._game.map_manager.game_map.get_width() or ppos.y >= Game._game.map_manager.game_map.get_height() or ppos.x < 0 or ppos.y < 0:
			ppos = self.pos + vectorFromAngle(self.angle) * -1
			self.angle += pi
		try:
			if Game._game.map_manager.game_map.get_at((ppos.vec2tupint())) == GRD:
				ppos = self.pos + vectorFromAngle(self.angle) * -1
				self.angle += pi
				if self.target:
					self.unreachable.append(self.target)
					self.target = None
		except IndexError:
			print("bee index error")
		self.pos = ppos
		
		if self.lifespan % 40 == 0:
			self.unreachable = []
		
		if self.lifespan < 300:
			closestDist = 100
			for worm in PhysObj._worms:
				if worm in self.unreachable:
					continue
				distance = dist(self.pos, worm.pos)
				if distance < 50 and distance < closestDist:
					self.target = worm
					closestDist = distance
			if self.target:
				if dist(self.pos, self.target.pos) > 50 or self.target.health <= 0:
					self.target = None
					return
				if dist(self.pos, self.target.pos) < self.target.radius:
					# sting
					self.target.vel.y -= 2
					if self.target.vel.y < -2:
						self.target.vel.y = 2
					if self.pos.x > self.target.pos.x:
						self.target.vel.x -= 1
					else:
						self.target.vel.x += 1
					self.removeFromGame()
					self.target.damage(uniform(1,8))
	def draw(self, win: pygame.Surface):
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())))

class BeeHive(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.color = (255, 204, 0)
		self.damp = 0.4
		self.unload = False
		self.beeCount = 50
		
		self.beeSurf = pygame.Surface((4,4), pygame.SRCALPHA)
		self.beeSurf.fill((255,255,0), ((1,2), (1,3)))
		self.beeSurf.fill((0,0,0), ((2,2), (2,3)))
		self.beeSurf.fill((255,255,0), ((3,2), (3,3)))
		self.beeSurf.fill((143,234,217,100), ((1,0), (2,2)))
		
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "bee hive")
		self.angle = 0
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		if self.beeCount <= 0:
			self.dead = True
	def deathResponse(self):
		# boom(self.pos, 15)
		pass
	def collisionRespone(self, ppos):
		out = randint(1,3)
		for i in range(out):
			b = Bee(self.pos, uniform(0,2*pi))
			b.surf = self.beeSurf
			self.beeCount -= 1
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

def drawLightning(start, end, color = (153, 255, 255)):
	radius = end.radius
	end = end.pos
	start = start.pos
	halves = int(dist(end, start) / 8)
	if halves == 0:
		halves = 1
	direction = (end - start)
	direction.setMag(dist(start, end)/halves)
	points = []
	lightings = []
	for t in range(halves):
		if t == 0 or t == halves - 1:
			point = (start + direction * t).vec2tupint()
		else:
			point = ((start + direction * t) + vectorUnitRandom() * uniform(-10,10)).vec2tupint()
		lightings.append(point)
		points.append(point2world(point))

	for i in lightings:
		EffectManager().add_light(vectorCopy(i), 50, [color[0], color[1], color[2], 100])
	if len(points) > 1:
		points.append(point2world(end))
		for i, point in enumerate(points):
			width = int((1-(i / (len(points)-1)))*4) + 1
			if i == len(points) - 1:
				break
			pygame.draw.line(win, color, points[i], points[i+1], width)
	else:
		pygame.draw.lines(win, color, False, [point2world(start), point2world(end)], 2)
	pygame.draw.circle(win, color, point2world(end), int(radius) + 3)

class ElectricGrenade(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0,self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.color = (120, 230, 230)
		self.damp = 0.525
		self.timer = 0
		self.worms = []
		self.raons = []
		self.shells = []
		self.sentries = []
		self.electrifying = False
		self.emptyCounter = 0
		self.lifespan = 300
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "electric grenade")
		self.angle = 0
	def deathResponse(self):
		rad = 20
		boom(self.pos, rad)
		for sentry in self.sentries:
			sentry.electrified = False
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		self.timer += 1
		if self.timer == GameVariables().fuse_time:
			self.electrifying = True
		if self.timer >= GameVariables().fuse_time + self.lifespan:
			self.dead = True
		if self.electrifying:
			self.stable = False
			self.worms = []
			self.raons = []
			self.shells = []
			for worm in PhysObj._worms:
				if distus(self.pos, worm.pos) < 10000:
					self.worms.append(worm)
			for raon in Raon._raons:
				if distus(self.pos, raon.pos) < 10000:
					self.raons.append(raon)
			for shell in GreenShell._shells:
				if distus(self.pos, shell.pos) < 10000:
					self.shells.append(shell)
			for sentry in SentryGun._sentries:
				if distus(self.pos, sentry.pos) < 10000:
					sentry.electrified = True
					if sentry not in self.sentries:
						self.sentries.append(sentry)
				else:
					sentry.electrified = False
			if len(self.worms) == 0 and len(self.raons) == 0:
				self.emptyCounter += 1
				if self.emptyCounter == fps:
					self.dead = True
			else:
				self.emptyCounter = 0
		for worm in self.worms:
			if randint(1,100) < 5:
				worm.damage(randint(1,8))
				a = lambda x : 1 if x >= 0 else -1
				worm.vel -= Vector(a(self.pos.x - worm.pos.x)*uniform(1.2,2.2), uniform(1.2,3.2))
			if worm.health <= 0:
				self.worms.remove(worm)
		for raon in self.raons:
			if randint(1,100) < 5:
				raon.electrified()
		for shell in self.shells:
			if randint(1,100) < 5:
				if shell.speed < 3:
					shell.facing = LEFT if self.pos.x > shell.pos.x else RIGHT
				shell.speed = 3
				shell.timer = 0
	def draw(self, win: pygame.Surface):
		# pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		for worm in self.worms:
			drawLightning(self, worm)
		for raon in self.raons:
			drawLightning(self, raon)
		for shell in self.shells:
			drawLightning(self, shell)
		for sentry in self.sentries:
			if sentry.electrified:
				drawLightning(self, sentry)

class Vortex():
	vortexRadius = 180
	def __init__(self, pos):
		Game._game.nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.rot = 0
		self.inhale = True
		self.boomAffected = False
	def step(self):
		gameDistable()
		if self.inhale:
			self.rot += 0.001
			if self.rot > 0.1:
				self.rot = 0.1
				self.inhale = False
		else:
			self.rot -= 0.001
		
		if self.inhale:
			for worm in PhysObj._reg:
				if distus(self.pos, worm.pos) < Vortex.vortexRadius * Vortex.vortexRadius:
					worm.acc += (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
					if randint(0,20) == 1:
						worm.vel.y -= 2
				if worm in PhysObj._worms and dist(self.pos, worm.pos) < Vortex.vortexRadius/2:
					if randint(0,20) == 1:
						worm.damage(randint(1,8))
		else:
			for worm in PhysObj._reg:
				if distus(self.pos, worm.pos) < Vortex.vortexRadius * Vortex.vortexRadius:
					worm.acc -= (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
			
		if not self.inhale and self.rot < 0:
			Game._game.nonPhysToRemove.append(self)
	def draw(self, win: pygame.Surface):
		width = 50
		arr = []
		halfwidth = width//2
		for x in range(int(self.pos.x) - halfwidth, int(self.pos.x) + halfwidth):
			for y in range(int(self.pos.y) - halfwidth, int(self.pos.y) + halfwidth):
				if distus(Vector(x,y), self.pos) > halfwidth * halfwidth:
					continue
				rot = (dist(Vector(x,y), self.pos) - halfwidth) * self.rot
				direction = Vector(x,y) - self.pos
				direction.rotate(rot)
				getAt = point2world(self.pos + direction)
				if getAt[0] < 0 or getAt[0] >= GameVariables().win_width or getAt[1] < 0 or getAt[1] >= GameVariables().win_height:
					arr.append((0,0,0))
				else:
					pixelColor = win.get_at(getAt)
					arr.append(pixelColor)
		for x in range(int(self.pos.x) - halfwidth, int(self.pos.x) + halfwidth):
			for y in range(int(self.pos.y) - halfwidth, int(self.pos.y) + halfwidth):
				if distus(Vector(x,y), self.pos) > halfwidth * halfwidth:
					continue
				
				win.set_at(point2world((x,y)), arr.pop(0))

class VortexGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 3
		self.color = (25, 102, 102)
		self.damp = 0.5
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "vortex grenade")
		self.angle = 0
	def deathResponse(self):
		Vortex(self.pos)

class TimeAgent:
	def __init__(self):
		Game._game.nonPhys.append(self)
		self.positions = TimeTravel._tt.timeTravelPositions
		self.facings = TimeTravel._tt.timeTravelFacings
		self.timeCounter = 0
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
			Game._game.nonPhys.remove(self)
			TimeTravel._tt.timeTravelPositions = []
			TimeTravel._tt.timeTravelList = {}
			return
		self.pos = self.positions.pop(0)
		if len(self.positions) <= self.stepsForEnergy:
			self.energy += 0.05
			
		self.timeCounter += 1
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, Game._game.player.color, point2world(self.pos), 3+1)
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
		self.timeTravelList["surf"] = Game._game.player.surf
		self.timeTravelList["name"] = Game._game.player.name
		self.timeTravelList["health"] = Game._game.player.health
		self.timeTravelList["initial pos"] = vectorCopy(Game._game.player.pos)
		self.timeTravelList["timeCounter in turn"] = TimeManager._tm.timeCounter
	def timeTravelRecord(self):
		self.timeTravelPositions.append(Game._game.player.pos.vec2tup())
		self.timeTravelFacings.append(Game._game.player.facing)
	def timeTravelPlay(self):
		TimeManager._tm.timeCounter = self.timeTravelList["timeCounter in turn"]
		Game._game.timeTravel = False
		self.timeTravelList["weapon"] = WeaponManager._wm.currentWeapon
		self.timeTravelList["weaponOrigin"] = vectorCopy(Game._game.player.pos)
		self.timeTravelList["energy"] = Game._game.energyLevel
		self.timeTravelList["weaponDir"] = Vector(cos(Game._game.player.shootAngle), sin(Game._game.player.shootAngle))
		Game._game.player.health = self.timeTravelList["health"]
		if Worm.healthMode == 1:
			Game._game.player.healthStr = fonts.pixel5.render(str(Game._game.player.health), False, Game._game.player.team.color)
		Game._game.player.pos = self.timeTravelList["initial pos"]
		Game._game.player.vel *= 0
		TimeAgent()
	def timeTravelReset(self):
		self.timeTravelFire = False
		self.timeTravelPositions = []
		self.timeTravelList = {}
	def step(self):
		self.timeTravelRecord()

class LongBow:
	_sleep = False #0-regular 1-sleep
	def __init__(self, pos, direction, sleep=False):
		Game._game.nonPhys.append(self)
		self.pos = vectorCopy(pos)
		self.direction = direction
		self.vel = direction.normalize() * 20
		self.stuck = None
		self.color = (112, 74, 37)
		self.ignore = None
		self.sleep = sleep
		self.radius = 1
		self.triangle = [Vector(0,3), Vector(6,0), Vector(0,-3)]
		for vec in self.triangle:
			vec.rotate(self.direction.getAngle())
		self.timer = 0
	def destroy(self):
		Game._game.nonPhysToRemove.append(self)
	def step(self):
		self.timer += 1
		if self.timer >= fps * 3:
			self.vel.y += GameVariables().physics.global_gravity
		if not self.stuck:
			ppos = self.pos + self.vel
			iterations = 15
			for t in range(iterations):
				value = t/iterations
				testPos = (self.pos * value) + (ppos * (1-value))
				# check cans collision:
				for can in PetrolCan._cans:
					if dist(testPos, can.pos) < can.radius + 1:
						can.damage(10)
						self.destroy()
						return
				# check worm collision
				for worm in PhysObj._worms:
					if worm == self.ignore:
						continue
					if dist(testPos, worm.pos) < worm.radius + 1:
						self.wormCollision(worm)
						return
				# check target collision:
				for target in ShootingTarget._reg:
					if dist(testPos, target.pos) < target.radius:
						target.explode()
						self.destroy()
						return
				# check Game._game.map_manager.game_map collision
				if MapManager().is_on_map(testPos.vec2tupint()):
					if Game._game.map_manager.is_ground_at(testPos.vec2tupint()):
						self.stuck = vectorCopy(testPos)
				if self.pos.y < 0:
					self.destroy()
					return
				if self.pos.y > Game._game.map_manager.game_map.get_height() - GameVariables().water_level:
					splash(self.pos, self.vel)
					self.destroy()
					return
			self.pos = ppos
		if self.stuck:
			self.stamp()
		self.secondaryStep()
	def wormCollision(self, worm):
		worm.vel += self.direction*4
		worm.vel.y -= 2
		worm.damage(randint(10,20) if self.sleep else randint(15,25))
		GameVariables().cam_track = worm
		if self.sleep: worm.sleep = True
		self.destroy()
		MapManager().stain(worm.pos, sprites.blood, sprites.blood.get_size(), False)
	def secondaryStep(self):
		pass
	def stamp(self):
		self.pos = self.stuck
			
		points = [(self.pos - self.direction * 10 + i).vec2tupint() for i in self.triangle]
		pygame.draw.polygon(Game._game.map_manager.ground_map, (230,235,240), points)
		pygame.draw.polygon(Game._game.map_manager.game_map, GRD, points)
		
		pygame.draw.line(Game._game.map_manager.game_map, GRD, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
		pygame.draw.line(Game._game.map_manager.ground_map, self.color, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
		
		self.destroy()
	def draw(self, win: pygame.Surface):
		points = [point2world(self.pos - self.direction * 10 + i) for i in self.triangle]
		pygame.draw.polygon(win, (230,235,240), points)
	
		pygame.draw.line(win, self.color, point2world(self.pos), point2world(self.pos - self.direction*8), 3)
		
		points = [point2world(self.pos + i) for i in self.triangle]
		pygame.draw.polygon(win, (230,235,240), points)

def fireLongBow(pos: Vector, direction: Vector, power: int=15):
	w = LongBow(pos + direction * 5, direction, LongBow._sleep)
	w.ignore = Game._game.player
	return w

def fireSpear(pos: Vector, direction: Vector, power: int=15):
	w = Spear(pos, direction, power * 0.95)
	return w

def fireBubbleGun(pos: Vector, direction: Vector, power: int=15):
	Bubble(getClosestPosAvail(pos, 3.5), direction, uniform(0.5, 0.9))

def fireRazorLeaf(pos: Vector, direction: Vector, power: int=15):
	RazorLeaf(pos + direction * 10, direction)

def fireIcicle(pos: Vector, direction: Vector, power: int=15):
	w = Icicle(pos + direction * 5, direction)
	w.ignore = Game._game.player
	return w

def fireFireBall(pos: Vector, direction: Vector, power: int=15):
	w = FireBall(pos + direction * 5, direction)
	w.ignore = Game._game.player
	return w

class Sheep(PhysObj):
	trigger = False
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(0,-3)
		self.radius = 6
		self.color = (250,240,240)
		self.damp = 0.2
		self.timer = 0
		self.facing = RIGHT
		self.windAffected = 0
	
	def secondaryStep(self):
		self.timer += 1
		self.stable = False
		moved = move(self)
		if self.timer % 3 == 0:
			moved = move(self)
		if not moved:
			if isGroundAround(self.pos, self.radius+1):
				self.facing *= -1
		if self.timer % (fps/2) == 0 and isGroundAround(self.pos, self.radius+1):
			self.vel.y -= 4.5
		if Sheep.trigger and self.timer > 5:
			self.dead = True
		else:
			Sheep.trigger = False
		if self.timer >= 300:
			self.dead = True
	
	def deathResponse(self):
		Sheep.trigger = False
		boom(self.pos, 35)
	
	def draw(self, win: pygame.Surface):
		rad = self.radius + 1
		wig = 0.4 * sin(0.5 * self.timer)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(pi/4 + wig), rad * sin(pi/4 + wig))), 2)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(3*pi/4 - wig), rad * sin(3*pi/4 - wig))), 2)
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(self.facing*self.radius,0)), 4)

class Armageddon:
	def __init__(self):
		Game._game.nonPhys.append(self)
		self.stable = False
		self.boomAffected = False
		self.timer = 700
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			Game._game.nonPhysToRemove.append(self)
			return
		if GameVariables().time_overall % 10 == 0:
			for i in range(randint(1,2)):
				x = randint(-100, Game._game.map_manager.game_map.get_width() + 100)
				m = Missile((x, -10), Vector(randint(-10,10), 5).normalize(), 1)
				m.windAffected = 0
				m.boomRadius = 40
	def draw(self, win: pygame.Surface):
		pass

class Bull(PhysObj):
	def __init__(self, pos):
		self.ignore = []
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(0,-3)
		self.radius = 6
		self.color = (165, 39, 40)
		self.damp = 0.2
		self.hits = 5
		self.timer = 0
		self.facing = RIGHT
		self.boomAffected = False
	def secondaryStep(self):
		self.stable = False
		self.timer += 1
		moved = move(self)
		moved = move(self)
		if not moved:
			if isGroundAround(self.pos, self.radius+1):
				self.hits -= 1
				boom(self.pos, 35)
				self.vel += Vector(-self.facing*3,-1)
		for worm in PhysObj._worms:
			if worm in self.ignore:
				continue
			if dist(worm.pos, self.pos) < self.radius:
				self.ignore.append(worm)
				self.hits -= 1
				boom(self.pos, 35)
				self.vel += Vector(-self.facing*3,-1)
		if self.timer % 10 == 0:
			self.ignore = []
		if self.hits == 0:
			self.dead = True
		if self.timer >= 300:
			boom(self.pos, 35)
			self.dead = True
	def draw(self, win: pygame.Surface):
		rad = self.radius + 1
		wig = 0.4*sin(0.5*self.timer)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(pi/4 + wig), rad * sin(pi/4 + wig))), 2)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(3*pi/4 - wig), rad * sin(3*pi/4 - wig))), 2)
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		pygame.draw.circle(win, self.color, point2world(self.pos + Vector(self.facing*(self.radius +1),-1)), 4)

class ElectroBoom(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0,self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.color = (120, 230, 230)
		self.damp = 0.6
		self.timer = 0
		self.worms = []
		self.network = []
		self.used = []
		self.electrifying = False
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "electro boom")
		self.angle = 0
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		self.timer += 1
		if self.timer == GameVariables().fuse_time:
			self.electrifying = True
			self.calculate()
		if self.timer == GameVariables().fuse_time + fps*2:
			for net in self.network:
				for worm in net[1]:
					boom(worm.pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
				boom(net[0].pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
			boom(self.pos + vectorUnitRandom() * uniform(1,5), randint(10,16))
			self.dead = True
	def calculate(self):
		for worm in PhysObj._worms:
			if worm in Game._game.player.team.worms:
				continue
			if dist(self.pos, worm.pos) < 150:
				self.worms.append(worm)
		for selfWorm in self.worms:
			net = []
			for worm in PhysObj._worms:
				if worm == selfWorm or worm in self.used or worm in self.worms or worm in Game._game.player.team.worms:
					continue
				if dist(selfWorm.pos, worm.pos) < 150 and not worm in self.worms:
					net.append(worm)
					self.used.append(worm)
			self.network.append((selfWorm, net))
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		for worm in self.worms:
			drawLightning(self, worm, (250, 250, 21))
		for net in self.network:
			for worm in net[1]:
				drawLightning(net[0], worm, (250, 250, 21))

def firePortal(pos: Vector, direction: Vector, power: int=15):
	steps = 500
	for t in range(5,steps):
		testPos = pos + direction * t
		Game._game.addExtra(testPos, (255,255,255), 3)
		
		# missed
		if t == steps - 1:
			if len(Portal._reg) % 2 == 1:
				p = Portal._reg.pop(-1)
				if p in PhysObj._reg:
					PhysObj._reg.remove(p)

		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue

		# if hits map:
		if Game._game.map_manager.game_map.get_at(testPos.vec2tupint()) == GRD:
			
			response = Vector(0,0)
			
			for i in range(12):
				ti = (i/12) * 2 * pi
				
				check = testPos + Vector(8 * cos(ti), 8 * sin(ti))
				
				if check.x >= Game._game.map_manager.game_map.get_width() or check.y >= Game._game.map_manager.game_map.get_height() or check.x < 0 or check.y < 0:
					continue
				if Game._game.map_manager.game_map.get_at(check.vec2tupint()) == GRD:
					# extra.append((check.x, check.y, (255,255,255), 100))
					response +=  Vector(8 * cos(ti), 8 * sin(ti))
			
			direction = response.normalize()
			
			p = Portal(testPos, direction)
			if len(Portal._reg) % 2 == 0:
				brother = Portal._reg[-2]
				p.brother = brother
				brother.brother = p
			break

class Portal:
	_reg = []
	radiusOfContact = 8
	radiusOfRelease = 10
	def __init__(self, pos, direction):
		Portal._reg.append(self)
		Game._game.nonPhys.append(self)
		self.direction = direction
		self.dirNeg = direction * -1
		self.pos = pos - direction * 5
		self.holdPos = pos
		self.brother = None
		width, height = 8,20
		
		s = pygame.Surface((width, height)).convert_alpha()
		s.fill((255,255,255,0))
		if len(Portal._reg) % 2 == 0:
			self.color = (255, 194, 63)
		else:
			self.color = (105, 255, 249)
			
		pygame.draw.ellipse(s, self.color, ((0,0), (width, height)))
		self.surf = pygame.transform.rotate(s, -degrees(self.direction.getAngle()))
		
		self.stable = True
		self.boomAffected = False
		self.health = 0
		
		self.posBro = Vector()
	def step(self):
		if not Game._game.map_manager.game_map.get_at(self.holdPos.vec2tupint()) == GRD:
			Game._game.nonPhysToRemove.append(self)
			Portal._reg.remove(self)
			
			if self.brother:
				Game._game.nonPhysToRemove.append(self.brother)
				Portal._reg.remove(self.brother)			
			return
			
		if Game._game.state == PLAYER_CONTROL_1 and not self.brother:
			Game._game.nonPhysToRemove.append(self)
			if self in Portal._reg:
				Portal._reg.remove(self)
			return
		
		if self.brother:
			Bro = (self.pos - Game._game.player.pos)
			angle = self.direction.getAngle() - (self.pos - Game._game.player.pos).getAngle()
			broAngle = self.brother.dirNeg.getAngle()
			finalAngle = broAngle + angle
			Bro.setAngle(finalAngle)
			self.posBro = self.brother.pos - Bro
			
		if self.brother:
			for worm in PhysObj._reg:
				if worm in Portal._reg:
					continue
				if distus(worm.pos, self.pos) <= Portal.radiusOfContact * Portal.radiusOfContact:
					Bro = (self.pos - worm.pos)
					angle = self.direction.getAngle() - (self.pos - worm.pos).getAngle()
					broAngle = self.brother.dirNeg.getAngle()
					finalAngle = broAngle + angle
					Bro.setAngle(finalAngle)
					worm.pos = self.brother.pos - Bro
					
					posT = self.brother.pos - worm.pos
					posT.normalize()
					worm.pos = self.brother.pos + posT * Portal.radiusOfRelease
					
					angle = self.direction.getAngle() - worm.vel.getAngle()
					finalAngle = broAngle + angle
					worm.vel.setAngle(finalAngle)
	def draw(self, win: pygame.Surface):
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))

class Venus:
	_reg = []
	grow = -1
	catch = 0
	idle = 1
	hold = 2
	release = 3
	def __init__(self, pos, angle = -1):
		Game._game.nonPhys.append(self)
		Venus._reg.append(self)
		self.pos = pos
		self.offset = Vector(25, 0)
		
		if angle == -1:
			self.direction = vectorUnitRandom()
		else:
			self.direction = vectorFromAngle(angle)
		self.angle = self.direction.getAngle()
		self.d1 = self.direction.normal()
		self.d2 = self.d1 * -1
		
		self.snap = 0
		self.gap = 0
		
		self.mode = Venus.grow
		self.timer = 0
		self.scale = 0
		self.explossive = False
		self.opening = -pi/2 + uniform(0, 0.8)
		self.mutant = False
		self.desired = None

		self.p1 = Vector()
		self.p2 = Vector()
		
		self.surf = pygame.Surface((48, 16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0, 64, 48, 16))
	def step(self):
		self.gap = 5*(self.snap + pi/2)/(pi/2)
		self.d1 = self.direction.normal()
		self.d2 = self.d1 * -1
		self.p1 = self.pos + self.d1 * self.gap
		self.p2 = self.pos + self.d2 * self.gap
		
		if self.mode == Venus.grow:
			# check if can eat a worm from here on first round:
			if Game._game.roundCounter == 0 and Game._game.state in [PLAYER_CONTROL_1] and self.scale == 0:
				pos = self.pos + self.direction * 25
				for worm in PhysObj._worms:
					if distus(worm.pos, pos) <= 625:
						Game._game.nonPhysToRemove.append(self)
						Venus._reg.remove(self)
						return
			
			self.scale += 0.1
			if self.scale >= 1:
					
				self.scale = 1
				self.mode = Venus.hold
				Game._game.map_manager.game_map.set_at(self.pos.vec2tupint(), GRD)
			gameDistable()
			return
		
		self.angle = self.direction.getAngle()
		self.timer += 1
		if self.desired:
			current = self.direction.getAngle()
					
			if self.desired - current > pi:
				self.desired -= 2*pi
			if current - self.desired > pi:
				self.desired += 2*pi
			
			current += (self.desired - current) * 0.2
			self.direction.setAngle(current)
		
		if self.mode == Venus.idle:
			pos = self.pos + self.direction * 25
						
			if self.mutant:
				maxDist = 640000
				closest = None
				for worm in PhysObj._worms:
					distance = distus(worm.pos, self.pos)
					if distance < maxDist and distance < 6400:
						maxDist = distance
						closest = worm
				if closest:
					self.desired = (closest.pos - self.pos).getAngle()
			listToCheck = PhysObj._reg + Seagull._reg
			for worm in listToCheck:
				if worm in Debrie._debries or worm in Flag.flags:
					continue
				if worm in PhysObj._worms and PLANT_MASTER in worm.team.artifacts:
					continue
				if distus(worm.pos, pos) <= 625:
					self.mode = Venus.catch
					if worm in PhysObj._worms:
						worm.dieded(Worm.causeVenus)
						name = worm.nameStr
						color = worm.team.color
						comments = [
							[{'text': 'yummy'}],
							[{'text': name, 'color': color}, {'text': ' was delicious'}],
							[{'text': name, 'color': color}, {'text': ' is good protein'}],
							[{'text': name, 'color': color}, {'text': ' is some serious gourmet s**t'}],
						]
						GameEvents().post(EventComment(choice(comments)))
					else:
						self.explossive = True
						worm.removeFromGame()
					break
		elif self.mode == Venus.catch:
			gameDistable()
			self.snap += 0.5
			if self.snap >= 0:
				self.snap = 0
				self.mode = Venus.hold
				self.timer = 0
		elif self.mode == Venus.hold:
			gameDistable()
			if self.timer == 1 * fps:
				self.mode = Venus.release
				if self.explossive:
					self.explossive = False
					for i in range(randint(6,14)):
						SmokeParticles._sp.addSmoke(self.pos + self.direction * 25 + vectorUnitRandom() * randint(3,10))
		elif self.mode == Venus.release:
			gameDistable()
			self.snap -= 0.1
			if self.snap <= self.opening:
				self.snap = self.opening
				self.mode = Venus.idle
		
		# check if self is destroyed
		if MapManager().is_on_map(self.pos.vec2tupint()):
			if not Game._game.map_manager.game_map.get_at(self.pos.vec2tupint()) == GRD:
				Game._game.nonPhysToRemove.append(self)
				Venus._reg.remove(self)
				
				gs = GunShell(vectorCopy(self.pos))
				gs.angle = self.angle - self.snap
				gs.surf = self.surf
				gs = GunShell(vectorCopy(self.pos))
				gs.angle = self.angle + self.snap
				gs.surf = self.surf
		else:
			Game._game.nonPhysToRemove.append(self)
			Venus._reg.remove(self)
		if self.pos.y >= Game._game.map_manager.game_map.get_height() - GameVariables().water_level:
			Game._game.nonPhysToRemove.append(self)
			Venus._reg.remove(self)
	def mutate(self):
		if self.mutant:
			return
		self.mutant = True
		self.surf.fill((0, 125, 255, 100), special_flags=pygame.BLEND_MULT)
	def draw(self, win: pygame.Surface):
		if self.scale < 1:
			if self.scale == 0:
				return
			image = pygame.transform.scale(self.surf, (tup2vec(self.surf.get_size()) * self.scale).vec2tupint())
		else: image = self.surf

		rotated_image = pygame.transform.rotate(image, -degrees(self.angle - self.snap))
		rotated_offset = rotateVector(self.offset, self.angle - self.snap)
		rect = rotated_image.get_rect(center=(self.p2 + rotated_offset).vec2tupint())
		win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))
		Game._game.map_manager.objects_col_map.blit(rotated_image, tup2vec(rect) + self.direction*-25*(1-self.scale))
		
		rotated_image = pygame.transform.rotate(pygame.transform.flip(image, False, True), -degrees(self.angle + self.snap))
		rotated_offset = rotateVector(self.offset, self.angle + self.snap)
		rect = rotated_image.get_rect(center=(self.p1 + rotated_offset).vec2tupint())
		win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))
		Game._game.map_manager.objects_col_map.blit(rotated_image, tup2vec(rect) + self.direction*-25*(1-self.scale))

class Ball0(PhysObj):# EXPERIMENTAL
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0],pos[1])
		
		self.radius = 5
		self.damp = 0.5
	def step(self):
		self.applyForce()
		
		# velocity
		self.vel += self.acc
		# position
		ppos = self.pos + self.vel
		
		# reset forces
		self.acc *= 0
		self.stable = False
		
		angle = atan2(self.vel.y, self.vel.x)
		response = Vector(0,0)
		collision = False
		
		# colission with world:
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0:
				if GameVariables().config.option_closed_map:
					response += ppos - testPos
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
				collision = True
			
			r += pi /8
		
		magVel = self.vel.getMag()
		
		if collision:
			self.collisionRespone(ppos)
			if self.vel.getMag() > 5 and self.fallAffected:
				self.damage(self.vel.getMag() * 1.5 * GameVariables().fall_damage_mult)
			self.stable = True
			
			response.normalize()
			
			fdot = self.vel.dot(response)
			if not self.bounceBeforeDeath == 1:
				self.vel = ((response * -2 * fdot) + self.vel) * self.damp
				if response.x > 0:
					self.vel.x += 0.5
				else:
					self.vel.x -= 0.5
			
			if self.bounceBeforeDeath > 0:
				self.bounceBeforeDeath -= 1
				self.dead = self.bounceBeforeDeath == 0
				
		else:
			self.pos = ppos
			# flew out Game._game.map_manager.game_map but not worms !
			if self.pos.y > Game._game.map_manager.game_map.get_height() and not self in self._worms:
				self.outOfMapResponse()
				self.removeFromGame()
				return
		
		if magVel < 0.1: # double jump problem
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self.removeFromGame()
			self.deathResponse()
	def collisionRespone(self, ppos):
		if self.vel.getMag() > 5:
			boom(ppos, 7)

def doCirclesOverlap(pos1, r1, pos2, r2):
	return fabs((pos1[0] - pos2[0])*(pos1[0] - pos2[0]) + (pos1[1] - pos2[1])*(pos1[1] - pos2[1])) <= (r1 + r2)*(r1 + r2)

def isPointInCircle(pos, radius, point):
	return fabs((pos[0] - point[0])*(pos[0] - point[0]) + (pos[1] - point[1])*(pos[1] - point[1])) <= radius * radius

class Ball(PhysObj):# EXPERIMENTAL
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0],pos[1])
		
		self.radius = 3
		self.damp = 0.3
		self.collidingBalls = []
		self.fakeballs = []
	def step(self):
		self.applyForce()
		
		# velocity
		self.vel += self.acc
		# position
		self.pos += self.vel
		
		# reset forces
		self.acc *= 0
		
		intppos = Vector(int(self.pos.x), int(self.pos.y))
		start = intppos + Vector(-self.radius - 2, -self.radius - 2)
		end = intppos + Vector(self.radius + 2, +self.radius + 2)
		self.fakeballs = []
		
		
		
		for y in range(start.y, end.y):
			for x in range(start.x, end.x):
				pos = Vector(x, y)
				if Game._game.map_manager.is_ground_at(pos):
					self.fakeballs.append(pos)
		
		shuffle(self.fakeballs)
		
		for ball in self.fakeballs:
			if self.colliding(ball):
				self.collidingBalls.append(ball)
			
		masterBall = Vector()
		for ball in self.collidingBalls:
			masterBall += ball
		masterBall = masterBall / len(self.collidingBalls)
		
		if self.colliding(masterBall):
			self.resolveCollision(masterBall)
		
	def colliding(self, ball):
		otherRadius = 0.5
	
		xd = self.pos.x - ball.x
		yd = self.pos.y - ball.y
		
		sumRadius = self.radius + otherRadius
		sqrRadius = sumRadius * sumRadius
		
		distsqr = (xd * xd) + (yd * yd)
		if distsqr <= sqrRadius:
			return True
		return False
		
	def resolveCollision(self, ball):
		otherRadius = 0.5
		selfMass = 1
		otherMass = 5
		otherVel = Vector()
		restitution = 0.5
	
		delta = self.pos - ball
		d = delta.getMag()
		
		mtd = delta * (((self.radius + otherRadius) - d) / d)
		
		im1 = 1 / selfMass
		im2 = 1 / otherMass
		
		self.pos = self.pos + (mtd * (im1 / (im1 + im2)))# + (mtd * (im2 / (im1 + im2)))
		# ballPos = ball - (mtd * (im2 / (im1 + im2)))
		
		v = self.vel - otherVel
		vn = dotProduct(self.vel, normalize(mtd))
		
		if vn > 0.0:
			return
		
		i = (-(1.0 + restitution) * vn) / (im1 + im2)
		impulse = normalize(mtd) * i
		
		self.vel = self.vel + impulse * im1
		
		
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		for i in self.collidingBalls:
			pygame.draw.circle(win, self.color, point2world(i), int(0.5)+1)
		self.collidingBalls = []

class PokeBall(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,0,200)
		self.damp = 0.4
		self.timer = 0
		self.hold = None
		self.health = 10
		self.name = None
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "pokeball")
		self.angle = 0
	def damage(self, value, damageType=0):
		if damageType == 1:
			return
		dmg = int(value * GameVariables().damage_mult)
		if dmg < 1:
			dmg = 1
		if dmg > self.health:
			dmg = self.health
		
		self.health -= dmg
		if self.health <= 0:
			self.health = 0
			self.dead = True
	def deathResponse(self):
		if self.hold:
			self.hold.pos = self.pos + Vector(0,- (self.radius + self.hold.radius))
			self.hold.vel = Vector(0,-1)
			PhysObj._reg.append(self.hold)
			PhysObj._worms.append(self.hold)
			self.hold.team.worms.append(self.hold)
		else:
			boom(self.pos, 20)
	def secondaryStep(self):
		self.timer += 1
		
		if self.timer >= GameVariables().fuse_time and self.timer <= GameVariables().fuse_time + fps*2 and not self.hold:
			self.stable = False
			closer = [None, 7000]
			for worm in PhysObj._worms:
				distance = dist(self.pos, worm.pos)
				if distance < closer[1]:
					closer = [worm, distance]
			if closer[1] < 50:
				self.hold = closer[0]
				
		if self.timer == GameVariables().fuse_time + fps*2:
			if self.hold:
				PhysObj._reg.remove(self.hold)
				PhysObj._worms.remove(self.hold)
				self.hold.team.worms.remove(self.hold)
				if self.hold.flagHolder:
					self.hold.flagHolder = False
					self.hold.team.flagHolder = False
					Flag(self.hold.pos)
				self.name = fonts.pixel5.render(self.hold.nameStr, False, self.hold.team.color)
				name = self.hold.nameStr
				color = self.hold.team.color
				comments = [
					[{'text': name, 'color': color}, {'text': ', i choose you'}],
					[{'text': "gotta catch 'em al"}],
					[{'text': name, 'color': color}, {'text': ' will help beat the next gym leader'}],
				]
				GameEvents().post(EventComment(choice(comments)))

			else:
				self.dead = True
		
		if self.timer <= GameVariables().fuse_time + fps*2 + fps/2:
			gameDistable()
		
		if self.vel.getMag() > 0.25:
			self.angle -= self.vel.x*4
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		if self.timer >= GameVariables().fuse_time and self.timer < GameVariables().fuse_time + fps*2 and self.hold:
			drawLightning(self, self.hold, (255, 255, 204))
		if self.name:
			win.blit(self.name , point2world(self.pos + Vector(-self.name.get_width()/2, -21)))

class GreenShell(PhysObj):
	_shells = []
	def __init__(self, pos):
		self.ignore = []
		GreenShell._shells.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(0,-0.5)
		self.radius = 6
		self.damp = 0.01
		self.timer = 0
		self.boomAffected = False
		self.facing = RIGHT
		self.ignore = []
		self.speed = 3
		self.wormCollider = True
	def outOfMapResponse(self):
		self.dead = True
		GreenShell._shells.remove(self)
	def secondaryStep(self):
		self.timer += 1
			
		if not self.speed == 0:
			self.wormCollider = True
			self.damp = 0.01
			self.boomAffected = False
			self.stable = False
			for i in range(self.speed):
				moved = move(self)
			
			if not moved:
				self.facing *= -1
				
			for worm in PhysObj._reg:
				if worm == self or worm in self.ignore:
					continue
				if distus(worm.pos, self.pos) < (self.radius + worm.radius) * (self.radius + worm.radius):
					self.ignore.append(worm)
					worm.vel = Vector(self.facing * randint(1,2),-randint(2,4))*0.8
					if worm in PhysObj._worms:
						worm.damage(randint(10,25))
		else:
			self.wormCollider = False
			self.damp = 0.5
			self.boomAffected = True
			self.stable = True
				
		if self.timer % 20 == 0:
			self.ignore = []
		
		if self.timer == 100:
			self.speed = 2
		if self.timer == 200:
			self.speed = 1
		if self.timer >= 300:
			if self.timer == 300:
				gameDistable()
			self.speed = 0
			if int(self.vel.x) >= 1:
				if self.vel.x >= 0:
					self.facing = RIGHT
				else:
					self.facing = LEFT
				if int(self.vel.x) >= 3:
					self.speed = 3
				else:
					self.speed = int(self.vel.x)
				
				self.timer = (3 - self.speed) * 100
	def draw(self, win: pygame.Surface):
		if not self.speed == 0:
			index = int((self.timer*(self.speed/3) % 12)/3)
		else:
			index = 0	
		win.blit(sprites.sprite_atlas, point2world(self.pos - Vector(16,16)/2), ((index*16, 48), (16,16)))

def fireLaser(pos: Vector, direction: Vector, power: int=15):
	hit = False
	color = (254, 153, 35)
	square = [Vector(1,5), Vector(1,-5), Vector(-10,-5), Vector(-10,5)]
	for i in square:
		i.rotate(direction.getAngle())
	
	for t in range(5,500):
		testPos = pos + direction * t
		# extra.append((testPos.x, testPos.y, (255,0,0), 3))
		
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			Game._game.layersCircles[0].append((color, pos, 5))
			Game._game.layersCircles[0].append((color, testPos, 5))
			Game._game.layersLines.append((color, pos, testPos, 10, 1))
			continue
			
		# if hits worm:
		for worm in PhysObj._worms:
			if worm == Game._game.player:
				continue
			if distus(testPos, worm.pos) < (worm.radius + 2) * (worm.radius + 2):
				if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
				Game._game.layersCircles[0].append((color, pos + direction * 5, 5))
				Game._game.layersCircles[0].append((color, testPos, 5))
				Game._game.layersLines.append((color, pos + direction * 5, testPos, 10, 1))
				
				boom(worm.pos + Vector(randint(-1,1),randint(-1,1)), 2, False, False, True)
				# worm.damage(randint(1,5))
				# worm.vel += direction*2 + vectorUnitRandom()
				hit = True
				break
		# if hits can:
		for can in PetrolCan._cans:
			if distus(testPos, can.pos) < (can.radius + 1) * (can.radius + 1):
				can.damage(10)
				# hit = True
				break
		if hit:
			break
		
		# if hits Game._game.map_manager.game_map:
		if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
			if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
			Game._game.layersCircles[0].append((color, pos + direction * 5, 5))
			Game._game.layersCircles[0].append((color, testPos, 5))
			Game._game.layersLines.append((color, pos + direction * 5, testPos, 10, 1))
			points = []
			for i in square:
				points.append((testPos + i).vec2tupint())
			
			pygame.draw.polygon(Game._game.map_manager.game_map, SKY, points)
			pygame.draw.polygon(Game._game.map_manager.ground_map, SKY, points)
			break

class GuidedMissile(PhysObj):
	def __init__(self, pos):
		self.initialize()
		self.pos = pos
		self.speed = 5.5
		self.vel = Vector(0, -self.speed)
		self.stable = False
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "guided missile")
		self.radius = 3
	def applyForce(self):
		pass
	def turn(self, direc):
		self.vel.rotate(direc * 0.1)
	def step(self):
		GameVariables().cam_track = self
		self.pos += self.vel
		if pygame.key.get_pressed()[pygame.K_LEFT]:
			self.vel.rotate(-0.3)
		elif pygame.key.get_pressed()[pygame.K_RIGHT]:
			self.vel.rotate(0.3)
		Blast(self.pos - self.vel * 1.5 + vectorUnitRandom() * 2 - 10 * normalize(self.vel), randint(5,8))
		
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi
		collision = False
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + self.pos.x, (self.radius) * sin(r) + self.pos.y)
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - GameVariables().water_level or testPos.x < 0:
				if GameVariables().config.option_closed_map:
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				collision = True
			
			r += pi /8
		
		if collision:
			boom(self.pos, 35)
			if randint(0,30) == 1 or GameVariables().mega_weapon_trigger:
				for i in range(80):
					s = Fire(self.pos, 5)
					s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,4)
			self.removeFromGame()
		if self.pos.y > Game._game.map_manager.game_map.get_height():
			self.removeFromGame()
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(self.surf, -90 -degrees(self.vel.getAngle()))
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Flare(PhysObj):
	_flares = []
	def __init__(self, pos, direction, energy):
		self.initialize()
		Flare._flares.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (128, 0, 0)
		self.damp = 0.4
		self.lightRadius = 50
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "flare")
		self.angle = 0
	def secondaryStep(self):
		if self.vel.getMag() > 0.25:
			self.angle -= self.vel.x*4
		if randint(0,10) == 1:
			Blast(self.pos, randint(self.radius,7), 150)
		if self.lightRadius < 0:
			self.removeFromGame()
			Flare._flares.remove(self)
			return
		
		EffectManager().add_light(vectorCopy(self.pos), self.lightRadius, (100,0,0,100))
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class EndPearl(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,0,150)
	def collisionRespone(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - GameVariables().water_level or testPos.x < 0:
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
			
			if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		self.removeFromGame()
		
		response.normalize()
		pos = self.pos + response * (Game._game.player.radius + 2)
		Game._game.player.pos = pos
	def draw(self, win: pygame.Surface):
		blit_weapon_sprite(win, point2world(self.pos - Vector(8,8)), "ender pearl")

class Flag(PhysObj):
	flags = []
	def __init__(self, pos=(0,0)):
		self.initialize()
		Flag.flags.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.radius = 3.5
		self.color = (220,0,0)
		self.damp = 0.1
	def secondaryStep(self):
		if Game._game.player:
			if not Game._game.player in PhysObj._worms:
				return
			if dist(Game._game.player.pos, self.pos) < self.radius + Game._game.player.radius:
				# worm has flag
				Game._game.player.flagHolder = True
				Game._game.player.team.flagHolder = True
				self.removeFromGame()
				Flag.flags.remove(self)
				return
	def outOfMapResponse(self):
		Flag.flags.remove(self)
		p = deployPack(Flag)
		GameVariables().cam_track = p
	def draw(self, win: pygame.Surface):
		pygame.draw.line(win, (51, 51, 0), point2world(self.pos + Vector(0, self.radius)), point2world(self.pos + Vector(0, -3 * self.radius)))
		pygame.draw.rect(win, self.color, (point2world(self.pos + Vector(1, -3 * self.radius)), (self.radius*2, self.radius*2)))

class ShootingTarget:
	numTargets = 10
	_reg = []
	def __init__(self):
		Game._game.nonPhys.append(self)
		ShootingTarget._reg.append(self)
		self.pos = Vector(randint(10, Game._game.map_manager.game_map.get_width() - 10), randint(10, Game._game.map_manager.game_map.get_height() - 50))
		self.radius = 10
		pygame.draw.circle(Game._game.map_manager.game_map, GRD, self.pos, self.radius)
		self.points = [self.pos + vectorFromAngle((i / 11) * 2 * pi) * (self.radius - 2) for i in range(10)]
	def step(self):
		for point in self.points:
			if Game._game.map_manager.game_map.get_at(point.vec2tupint()) != GRD:
				self.explode()
				return
	def explode(self):
		boom(self.pos, 15)
		Game._game.nonPhysToRemove.append(self)
		if self in ShootingTarget._reg:
			ShootingTarget._reg.remove(self)
		globals.team_manager.currentTeam.points += 1
		if len(ShootingTarget._reg) < ShootingTarget.numTargets:
			ShootingTarget()
		# add to kill list(surf, name, amount):
		Game._game.addToScoreList()
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius))
		pygame.draw.circle(win, RED, point2world(self.pos), int(self.radius - 4))
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius - 8))

class Raon(PhysObj):
	_raons = []
	searching = 0
	idle = 1
	pointing = 2
	advancing = 3
	wait = 4
	def __init__(self, pos, direction, energy):
		Raon._raons.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.color = (255, 204, 0)
		self.damp = 0.2
		self.target = None
		self.state = Raon.wait
		self.timer = 10
		self.facing = RIGHT
	def secondaryStep(self):
		if self.state == Raon.wait:
			self.timer -= 1
			if self.timer == 0:
				self.state = Raon.idle
			else:
				return
		if not self.state == Raon.advancing:
			self.search()
		if self.state == Raon.pointing:
			if distus(self.pos, self.target.pos) > 10000:
				self.state = Raon.idle
				self.target = None
			if self.proximity():
				self.dead = True
				Raon._raons.remove(self)
		if self.state == Raon.advancing:
			gameDistable()
			moved = move(self)
			self.timer -= 1
			if self.timer == 0:
				self.state = Raon.pointing
			if self.proximity():
				self.dead = True
				Raon._raons.remove(self)
	def deathResponse(self):
		boom(self.pos, 25)
	def proximity(self):
		if distus(self.target.pos, self.pos) < (self.radius + self.target.radius + 2) * (self.radius + self.target.radius + 2):
			return True
		return False
	def search(self):
		if len(PhysObj._worms) <= 0: return
		closest = [PhysObj._worms[0], dist(self.pos, PhysObj._worms[0].pos)]
		for worm in PhysObj._worms:
			distance = dist(worm.pos, self.pos)
			if distance < closest[1]:
				closest = [worm, distance]
		if closest[1] < 100:
			self.target = closest[0]
			self.state = Raon.pointing
			self.facing = RIGHT if self.target.pos.x > self.pos.x else LEFT
		else:
			self.state = Raon.idle
	def advance(self):
		self.facing = RIGHT if self.target.pos.x > self.pos.x else LEFT
		if not self.state == Raon.pointing:
			return False
		self.state = Raon.advancing
		self.timer = 20
		return True
	def electrified(self):
		self.dead = True
		Raon._raons.remove(self)
	def draw(self, win: pygame.Surface):
		pygame.draw.rect(win, self.color, (point2world(self.pos - Vector(self.radius, self.radius)), (self.radius * 2, self.radius * 2)))
		pygame.draw.line(win, (255,0,0), point2world(self.pos + Vector(self.radius-1, self.radius)), point2world(self.pos + Vector(-self.radius, self.radius)))
		pygame.draw.line(win, (0,0,0), point2world(self.pos + Vector(0, self.radius - 1)), point2world(self.pos + Vector(0, self.radius + 2)))
		pygame.draw.line(win, (0,0,0), point2world(self.pos + Vector(-2, self.radius - 1)), point2world(self.pos + Vector(-2, self.radius + 2)))
		pygame.draw.line(win, (0,0,0), point2world(self.pos + Vector(2, self.radius - 1)), point2world(self.pos + Vector(2, self.radius + 2)))
		if self.state == Raon.pointing or self.state == Raon.advancing:
			#pygame.draw.line(win, (255,0,0), point2world(self.pos), point2world(self.pos + (self.target.pos - self.pos)*0.5))
			pygame.draw.circle(win, (255,255,255), point2world(self.pos + Vector(self.facing * self.radius/2,0)), 2)
			win.set_at(point2world(self.pos + Vector(self.facing * (self.radius/2), -1)), (0,0,0))
		if self.state == Raon.idle or self.state == Raon.wait:
			pygame.draw.circle(win, (255,255,255), point2world(self.pos), 2)
			win.set_at(point2world(self.pos), (0,0,0))

class Spear(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0, self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.damp = 0.4
		self.stable = False
		self.bounceBeforeDeath = 1
		self.color = (204, 102, 0)
		self.triangle = [Vector(0,2), Vector(7,0), Vector(0,-2)]
		self.wormCollider = True
		self.worms = []
		self.ignore = [Game._game.player]
	def secondaryStep(self):
		for worm in PhysObj._worms:
			if worm in self.ignore:
				continue
			if distus(self.pos, worm.pos) < (worm.radius + 3) * (worm.radius + 3):
				self.worms.append(worm)
				worm.damage(20 + self.vel.getMag()*1.5)
				self.ignore.append(worm)
		for i, worm in enumerate(self.worms):
			worm.pos = vectorCopy(self.pos) - 5 * normalize(self.vel) * i
			worm.vel *= 0
		for target in ShootingTarget._reg:
			if dist(self.pos + normalize(self.vel) * 8, target.pos) < target.radius + 1:
				self.boomAffected = False
				target.explode()
				return
	def deathResponse(self):
		self.pos += self.vel
		point = self.pos - normalize(self.vel) * 30
		pygame.draw.line(Game._game.map_manager.game_map, GRD, self.pos, point, self.radius)
		pygame.draw.polygon(Game._game.map_manager.game_map, GRD, [self.pos + rotateVector(i, self.vel.getAngle()) for i in self.triangle])
		
		pygame.draw.line(Game._game.map_manager.ground_map, self.color, self.pos, point, self.radius)
		pygame.draw.polygon(Game._game.map_manager.ground_map, (230,235,240), [self.pos + rotateVector(i, self.vel.getAngle()) for i in self.triangle])
		
		if len(self.worms) > 0:
			MapManager().stain(self.pos, sprites.blood, sprites.blood.get_size(), False)
		if len(self.worms) > 1:
			name = Game._game.player.nameStr
			color = Game._game.player.team.color
			GameEvents().post(EventComment([{'text': name, 'color': color}, {'text': ' the impaler!'}]))

	def draw(self, win: pygame.Surface):
		point = self.pos - normalize(self.vel) * 30
		pygame.draw.line(win, self.color, point2world(self.pos), point2world(point), self.radius)
		pygame.draw.polygon(win, (230,235,240), [point2world(self.pos + rotateVector(i, self.vel.getAngle())) for i in self.triangle])
		
class Snail:
	around = [Vector(1,0), Vector(1,-1), Vector(0,-1), Vector(-1,-1), Vector(-1,0), Vector(-1,1), Vector(0,1), Vector(1,1)]
	def __init__(self, pos, anchor, clockwise=RIGHT):
		Game._game.nonPhys.append(self)
		self.pos = pos
		self.pos.integer()
		self.clockwise = clockwise
		self.anchor = anchor
		self.life = 0
		self.surf = pygame.Surface((6,6), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (70,48,6,6))
		if self.clockwise == LEFT:
			self.surf = pygame.transform.flip(self.surf, True, False)
		self.secondaryInit()
	def secondaryInit(self):
		pass
	def climb(self):
		steps = 0
		while True:
			steps += 1
			if steps > 20:
				break
			revolvment = self.pos - self.anchor
			index = Snail.around.index(revolvment)
			candidate = self.anchor + Snail.around[(index + self.clockwise * -1) % 8]
			if Game._game.map_manager.is_ground_at(candidate):
				self.anchor = candidate
			else:
				self.pos = candidate
				break
	def step(self):
		self.life += 1
		for i in range(3):
				self.climb()
		for worm in PhysObj._worms:
			if distus(self.pos, worm.pos) < (3 + worm.radius) * (3 + worm.radius):
				Game._game.nonPhysToRemove.append(self)
				boom(self.pos, 30)
				return
	def draw(self, win: pygame.Surface):
		normal = getNormal(self.pos, Vector(), 4, False, False)
		angle = round((-degrees(normal.getAngle()) - 90) / 22) * 22
		win.blit(pygame.transform.rotate(self.surf, angle) , point2world(self.pos - Vector(3,3)))

class SnailShell(PhysObj):
	def __init__(self, pos, direction, energy, obj=Snail):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 1
		self.bounceBeforeDeath = 1
		self.damp = 0.2
		self.wormCollider = True
		self.extraCollider = True
		self.clockwise = Game._game.player.facing
		self.timer = 0
		self.surf = pygame.Surface((6,6), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (64,48, 6,6))
		self.obj = obj
	def setSurf(self, surf):
		self.surf = surf
	def collisionRespone(self, ppos):
		finalPos = vectorCopy(self.pos)
		finalAnchor = None

		for t in range(50):
			testPos = self.pos + normalize(self.vel) * t
			testPos.integer()
			if Game._game.map_manager.is_ground_at(testPos):
				finalAnchor = testPos
				break
			else:
				finalPos = testPos

		if not finalAnchor:
			print("shell error")
			return

		GameVariables().cam_track = self.obj(finalPos, finalAnchor, self.clockwise)
	def draw(self, win: pygame.Surface):
		self.timer += 1
		win.blit(pygame.transform.rotate(self.surf, (self.timer % 4) * 90), point2world(self.pos - Vector(3,3)))

class Bubble:
	cought = []
	def __init__(self, pos, direction, energy):
		Game._game.nonPhys.append(self)
		self.pos = vectorCopy(pos)
		self.acc = Vector()
		self.vel = Vector(direction[0], direction[1]).rotate(uniform(-0.1, 0.1)) * energy * 5
		self.radius = 1
		self.grow = randint(7, 13)
		self.color = (220,220,220)
		self.catch = None
	def applyForce(self):
		self.acc.y -= GameVariables().physics.global_gravity * 0.3
		self.acc.x += GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * 0.5
	def step(self):
		gameDistable()
		self.applyForce()
		self.vel += self.acc * GameVariables().dt
		self.pos += self.vel * GameVariables().dt
		self.vel.x *= 0.99
		self.acc *= 0
		
		if self.radius <= self.grow and GameVariables().time_overall % 5 == 0:
			self.radius += 1 * GameVariables().dt
			
		if not self.catch:
			for worm in PhysObj._reg:
				if worm == Game._game.player or worm in Bubble.cought or worm in Debrie._debries:
					continue
				if dist(worm.pos, self.pos) < worm.radius + self.radius:
					self.catch = worm
					Bubble.cought.append(self.catch)
					GameVariables().cam_track = self
		else:
			self.catch.pos = self.pos
			self.catch.vel *= 0
		if GameVariables().config.option_closed_map and (self.pos.x - self.radius <= 0 or self.pos.x + self.radius >= Game._game.map_manager.game_map.get_width() - GameVariables().water_level):
			self.burst()
		if self.pos.y < 0 and (Game._game.map_manager.is_ground_at((int(self.pos.x + self.radius), 0)) or Game._game.map_manager.is_ground_at((int(self.pos.x - self.radius), 0))):
			self.burst()
		if self.pos.y < -50:
			self.burst()
		if self.pos.y - self.radius <= 0 and Game._game.map_manager.is_ground_at((int(self.pos.x), 0)):
			self.burst()
		if randint(0, 300) == 1:
			if not Game._game.map_manager.is_ground_at(self.pos.integer()):
				self.burst()
	def burst(self):
		if self.catch:
			self.catch.vel = self.vel * 0.6
			if self == GameVariables().cam_track:
				GameVariables().cam_track = self.catch
		self.catch = None
		pygame.draw.circle(Game._game.map_manager.game_map, SKY, self.pos, self.radius)
		pygame.draw.circle(Game._game.map_manager.ground_map, SKY, self.pos, self.radius)
		Game._game.nonPhysToRemove.append(self)
		for i in range(min(int(self.radius), 8)):
			d = DropLet(self.pos + vectorUnitRandom() * self.radius, vectorUnitRandom())
			d.vel += self.vel
			d.radius = 1
	def draw(self, win: pygame.Surface):
		pygame.gfxdraw.circle(win, *point2world(self.pos), int(self.radius), self.color)

class Acid(PhysObj):
	def __init__(self, pos, vel):
		self.initialize()
		self.pos = vectorCopy(pos)
		self.vel = vectorCopy(vel)
		self.life = randint(70, 170)
		self.radius = 2
		self.damp = 0
		self.windAffected = 0.5
		self.inGround = False
		self.wormCollider = True
		self.color = (200,255,200)
		self.damageCooldown = 0
	def collisionRespone(self, ppos):
		self.inGround = True
	def secondaryStep(self):
		if self.inGround:
			pygame.draw.circle(Game._game.map_manager.game_map, SKY, self.pos + Vector(0, 1), self.radius + 2)
			pygame.draw.circle(Game._game.map_manager.ground_map, SKY, self.pos + Vector(0, 1), self.radius + 2)
			self.pos.x += choice([LEFT, RIGHT])
		self.life -= 1
		if self.life == 50:
			self.radius -= 1
		if self.life <= 0:
			self.dead = True
			
		if self.damageCooldown != 0:
			self.damageCooldown -= 1
		else:
			for worm in PhysObj._worms:
				if squareCollision(self.pos, worm.pos, self.radius, worm.radius):
					worm.damage(randint(0,1))
					self.damageCooldown = 30
		self.inGround = False
		if randint(0,50) < 1:
			# Smoke(self.pos, color=(200,255,200))
			SmokeParticles._sp.addSmoke(self.pos, color=(200,255,200))
		gameDistable()
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, point2world(self.pos + Vector(0,1)), self.radius+1)

class AcidBottle(PetrolBomb):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (200,255,200)
		self.bounceBeforeDeath = 1
		self.damp = 0.5
		self.angle = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "acid bottle")
	def secondaryStep(self):
		self.angle -= self.vel.x*4
	def deathResponse(self):
		boom(self.pos, 10)
		for i in range(40):
			s = Acid(self.pos, Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2))
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Seeker:
	def __init__(self, pos, direction, energy):
		self.initialize(pos, direction, energy)
		self.timer = 15 * fps
		self.target = HomingMissile.Target
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "seeker")
	def initialize(self, pos, direction, energy):
		Game._game.nonPhys.append(self)
		self.pos = vectorCopy(pos)
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.acc = Vector()
		self.maxSpeed = 5
		self.maxForce = 1
		self.color = (255,100,0)
		self.avoid = []
		self.radius = 6
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			self.deathResponse()
		gameDistable()
		getForce = seek(self, self.target, self.maxSpeed, self.maxForce)
		avoidForce = Vector()
		distance = dist(self.pos, self.target)
		if distance > 30:
			self.avoid = []
			visibility = int(0.1 * distance + 10)
			for i in range(20):
				direction = vectorFromAngle((i / 20) * 2 * pi)
				for j in range(visibility):
					testPos = self.pos + direction * j
					if Game._game.map_manager.is_ground_at(testPos):
						self.avoid.append(testPos)
		else:
			if Game._game.map_manager.is_ground_at(self.pos):
				self.hitResponse()
				return
			
		if distance < 8:
			self.hitResponse()
			return
			
		for i in self.avoid:
			# if dist(self.pos, i) < 50:
			avoidForce += flee(self, i, self.maxSpeed, self.maxForce)
		
		force = avoidForce + getForce
		self.applyForce(force)
		
		self.vel += self.acc
		self.vel.limit(self.maxSpeed)
		
		ppos = self.pos + self.vel
		while Game._game.map_manager.is_ground_at(ppos):
			self.vel *= -1
			self.vel.rotate(uniform(-0.5,0.5))
			ppos = self.pos + self.vel
		
		self.pos = ppos
		self.secondaryStep()
	def hitResponse(self):
		self.deathResponse()
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), randint(5,8), 30, 3)
	def deathResponse(self):
		boom(self.pos, 30)
		Game._game.nonPhysToRemove.append(self)
		HomingMissile.showTarget = False
	def applyForce(self, force):
		force.limit(self.maxForce)
		self.acc = vectorCopy(force)
	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Seagull(Seeker):
	_reg = []
	def __init__(self, pos, direction, energy):
		self.initialize(pos, direction, energy)
		Seagull._reg.append(self)
		self.timer = 15 * fps
		self.target = Vector()
		self.chum = None
	def deathResponse(self):
		boom(self.pos, 30)
		self.removeFromGame()
	def removeFromGame(self):
		if self in Seagull._reg:
			Seagull._reg.remove(self)
		Game._game.nonPhysToRemove.append(self)
		self.chum.dead = True
	def secondaryStep(self):
		self.target = self.chum.pos
	def draw(self, win: pygame.Surface):
		dir = self.vel.x > 0
		width = 16
		height = 13
		frame = GameVariables().time_overall // 2 % 3
		surf = pygame.Surface((16,16), pygame.SRCALPHA)
		surf.blit(sprites.sprite_atlas, (0,0), (frame * 16,80, 16, 16))
		win.blit(pygame.transform.flip(surf, dir, False), point2world(self.pos - Vector(width//2, height//2)))

class Covid19(Seeker):
	def __init__(self, pos):
		self.initialize(pos, Vector(), 5)
		self.timer = 12 * fps
		self.target = Vector()
		self.wormTarget = None
		self.chum = None
		self.unreachable = []
		self.bitten = []
	def secondaryStep(self):
		# find target
		closest = 800
		for worm in PhysObj._worms:
			if worm in globals.team_manager.currentTeam.worms or worm in self.bitten or worm in self.unreachable:
				continue
			distance = dist(worm.pos, self.pos)
			if distance < closest:
				closest = distance
				self.target = worm.pos
				self.wormTarget = worm
	def hitResponse(self):
		self.bitten.append(self.wormTarget)
		self.target = Vector()
		# sting
		if not self.wormTarget:
			return
		self.wormTarget.vel.y -= 2
		if self.wormTarget.vel.y < -3:
			self.wormTarget.vel.y = 3
		if self.pos.x > self.wormTarget.pos.x:
			self.wormTarget.vel.x -= 2
		else:
			self.wormTarget.vel.x += 2
		self.wormTarget.damage(10)
		self.wormTarget.sicken(2)
		self.wormTarget = None
	def draw(self, win: pygame.Surface):
		width = 16
		height = 16
		frame = GameVariables().time_overall // 2 % 5
		win.blit(sprites.sprite_atlas, point2world(self.pos - Vector(8, 8)), ((frame * 16, 32), (16, 16)) )

class Chum(Grenade):
	_chums = []
	def __init__(self, pos, direction, energy, radius=0):
		Chum._chums.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = radius
		if radius == 0:
			self.radius = randint(1,3)
		self.color = (255, 102, 102)
		self.bounceBeforeDeath = -1
		self.damp = 0.5
		self.sticked = False
		self.stick = None
		self.timer = 0
		self.alarm = randint(0,3) * fps
		self.ticking = False
		self.summoned = False
		self.boomAffected = False
	def collisionRespone(self, ppos):
		if not self.summoned:
				self.ticking = True
				self.summoned = True
		if not self.sticked:
			self.sticked = True
			self.stick = vectorCopy((self.pos + ppos)/2)
			Game._game.map_manager.game_map.set_at(self.stick.integer(), GRD)
	def deathResponse(self):
		Chum._chums.remove(self)
		if self.stick:
			Game._game.map_manager.game_map.set_at(self.stick.integer(), SKY)
	def secondaryStep(self):
		# self.stable = False
		if self.ticking:
			if self.timer == self.alarm:
				s = Seagull(Vector(self.pos.x + randint(-100,100), -10), Vector(randint(-100,100), 0), 1)
				s.target = self.pos
				s.chum = self
			self.timer += 1
		if self.stick:
			self.pos = self.stick
			if not Game._game.map_manager.is_ground_at(self.stick):
				self.sticked = False
				self.stick = None
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)

class MjolnirThrow(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.damp = 0.3
		self.rotating = True
		self.angle = 0
		self.stableCount = 0
		Game._game.holdArtifact = False
		self.worms = []
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0,self)
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
			self.removeFromGame()
			self.returnToWorm()
		
		# electrocute
		self.worms = []
		for worm in PhysObj._worms:
			if worm in globals.team_manager.currentTeam.worms:
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
		
		gameDistable()
	def returnToWorm(self):
		MjolnirReturn(self.pos, self.angle)
	def collisionRespone(self, ppos):
		vel = self.vel.getMag()
		# print(vel, vel * 4)
		if vel > 4:
			boom(self.pos, max(20, 4 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	def outOfMapResponse(self):
		self.returnToWorm()
	def draw(self, win: pygame.Surface):
		for worm in self.worms:
			drawLightning(self, worm)
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirReturn:
	def __init__(self, pos, angle):
		Game._game.nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.acc = Vector()
		self.vel = Vector()
		self.angle = angle
		GameVariables().cam_track = self
		self.speedLimit = 8
	def step(self):
		self.acc = seek(self, Game._game.player.pos, self.speedLimit, 1)
		
		self.vel += self.acc
		self.vel.limit(self.speedLimit)
		self.pos += self.vel
		
		self.angle += (0 - self.angle) * 0.1
		gameDistable()
		if distus(self.pos, Game._game.player.pos) < Game._game.player.radius * Game._game.player.radius * 2:
			Game._game.nonPhysToRemove.append(self)
			Game._game.holdArtifact = True
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Artifact(PhysObj):
	def __init__(self, pos):
		self.initialize()
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
		if dist(Game._game.player.pos, self.pos) < self.radius + Game._game.player.radius + 5 and not Game._game.player.health <= 0\
			and not len(Game._game.player.team.artifacts) > 0: 
			self.removeFromGame()
			Game._game.worldArtifacts.remove(self.artifact)
			self.commentPicked()
			globals.team_manager.currentTeam.artifacts.append(self.artifact)
			# add artifacts moves:
			WeaponManager._wm.addArtifactMoves(self.artifact)
			return
		self.trenaryStep()
	def removeFromGame(self):
		super().removeFromGame()
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
		GameEvents().post(EventComment([{'text': Game._game.player.nameStr, 'color': globals.team_manager.currentTeam.color}, {'text': " is worthy to wield mjolnir!"}]))
	
	def trenaryStep(self):
		if self.vel.getMag() > 1:
			self.angle = -degrees(self.vel.getAngle()) - 90
	
	def collisionRespone(self, ppos):
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
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.damp = 0.3
		self.rotating = True
		self.angle = 0
		Game._game.holdArtifact = False
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0,self)
		MjolnirFly.flying = True
	def secondaryStep(self):
		if self.vel.getMag() > 1:
			self.rotating = True
		else:
			self.rotating = False
		if self.rotating:
			self.angle = -degrees(self.vel.getAngle()) - 90
			
		Game._game.player.pos = vectorCopy(self.pos)
		Game._game.player.vel = Vector()
	def collisionRespone(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - GameVariables().water_level or testPos.x < 0:
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
			
			if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		
		self.removeFromGame()
		response.normalize()
		pos = self.pos + response * (Game._game.player.radius + 2)
		Game._game.player.pos = pos
		
	def removeFromGame(self):
		PhysObj._toRemove.append(self)
		MjolnirFly.flying = False
		Game._game.holdArtifact = True
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirStrike:
	def __init__(self):
		self.pos = Game._game.player.pos
		Game._game.nonPhys.append(self)
		Game._game.holdArtifact = False
		self.stage = 0
		self.timer = 0
		self.angle = 0
		self.worms = []
		self.facing = Game._game.player.facing
		Game._game.player.boomAffected = False
		self.radius = 0
	def step(self):
		self.pos = Game._game.player.pos
		self.facing = Game._game.player.facing
		if self.stage == 0:
			self.angle += 1
			if self.timer >= fps * 4:
				self.stage = 1
				self.timer = 0
			# electrocute:
			self.worms = []
			for worm in PhysObj._worms:
				if worm in globals.team_manager.currentTeam.worms:
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
				Game._game.nonPhysToRemove.append(self)
				Game._game.player.boomAffected = True
		self.timer += 1
		gameDistable()
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		surf = pygame.transform.flip(surf, self.facing == LEFT, False)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2 + Vector(0, -5)))
		drawLightning(Camera(Vector(self.pos.x, 0)), self)
		for worm in self.worms:
			drawLightning(Camera(Vector(self.pos.x, randint(0, int(self.pos.y)))), worm)

class MagicLeaf(Artifact):
	def getArtifact(self):
		return PLANT_MASTER
	
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (48, 64, 16,16))

		self.windAffected = True
		self.turbulance = vectorUnitRandom()
	
	def commentCreation(self):
		GameEvents().post(EventComment([{'text': "a leaf of heavens tree"}]))
	
	def commentPicked(self):
		GameEvents().post(EventComment([{'text': Game._game.player.nameStr, 'color': globals.team_manager.currentTeam.color}, {'text': "  became master of plants"}]))
	
	def trenaryStep(self):
		self.angle += self.vel.x*4

		# aerodynamic drag
		self.turbulance.rotate(uniform(-1, 1))
		velocity = self.vel.getMag()
		force =  - 0.15 * 0.5 * velocity * velocity * normalize(self.vel)
		force += self.turbulance * 0.1
		self.acc += force
	
	def collisionRespone(self, ppos):
		self.turbulance *= 0.9

class MagicBeanGrow:
	def __init__(self, pos, vel):
		Game._game.nonPhys.append(self)
		if vel.getMag() < 0.1:
			vel = Vector(0, -1)
		self.vel = vel
		self.pos = pos
		self.p1 = pos
		self.p2 = pos
		self.p3 = pos
		self.timer = 0
		self.green1 = 135
		self.green2 = 135
		self.green3 = 135
		self.face = 0
		Game._game.playerMoveable = False
	def regreen(self, value):
		value += randint(-5,5)
		if value > 255:
			value = 255
		if value < 0:
			value = 0
		return value
	def step(self):
		self.timer += 1
		gameDistable()
		self.pos += 1.5 * self.vel
		if pygame.key.get_pressed()[pygame.K_LEFT]:
			self.vel.rotate(-0.1)
			self.face = RIGHT
		elif pygame.key.get_pressed()[pygame.K_RIGHT]:
			self.vel.rotate(0.1)
			self.face = LEFT

		self.vel.rotate(0.02 * copysign(1,(sin(0.05 * self.timer))))
		
		growRadius = -0.02 * self.timer + 4
		pygame.draw.circle(Game._game.map_manager.game_map, GRD, self.p1, growRadius)
		pygame.draw.circle(Game._game.map_manager.game_map, GRD, self.p2, growRadius)
		pygame.draw.circle(Game._game.map_manager.game_map, GRD, self.p3, growRadius)
		pygame.draw.circle(Game._game.map_manager.ground_map, (55,self.green1,40), self.p1, growRadius)
		pygame.draw.circle(Game._game.map_manager.ground_map, (55,self.green2,40), self.p2, growRadius)
		pygame.draw.circle(Game._game.map_manager.ground_map, (55,self.green3,40), self.p3, growRadius)

		self.green1 = self.regreen(self.green1)
		self.green2 = self.regreen(self.green2)
		self.green3 = self.regreen(self.green3)

		growRadius = -0.055 * self.timer + 9

		if randint(0, 100) < 10:
			leaf(self.p1, self.vel.getNormal().getAngle(), (55, self.green1, 40))

		self.p1 = self.pos + growRadius * sin(self.timer * 0.1) * self.vel.getNormal()
		self.p2 = self.pos + growRadius * sin(self.timer * 0.1 + 2*pi/3) * self.vel.getNormal()
		self.p3 = self.pos + growRadius * sin(self.timer * 0.1 + 4*pi/3) * self.vel.getNormal()

		if self.timer >= 5 * fps:
			Game._game.nonPhysToRemove.append(self)
			Game._game.playerMoveable = True
	def draw(self, win: pygame.Surface):
		pass

def leaf(pos, direction, color) -> None:
	# draw procedural leaf
	points = []
	width = max(0.3, uniform(0,1))
	length = 1 + uniform(0,1)
	for i in range(10):
		x = (i/10) * length
		y = 0.5 * width * sin(2 * (1/length) * pi * x)
		points.append(Vector(x, y))
	for i in range(10):
		x = (1 - (i/10)) * length
		y = - width * sqrt(1 - ((2/length) * (x - length/2))**2)
		points.append(Vector(x, y))
	if randint(0,1) == 0:
		points = [Vector(-i.x, i.y) for i in points]
	size = uniform(4, 7)
	points = [pos + i.rotate(direction) * size for i in points]
	pygame.draw.polygon(Game._game.map_manager.game_map, GRD, points)
	pygame.draw.polygon(Game._game.map_manager.ground_map, color, points)

class RazorLeaf(PhysObj):
	def __init__(self, pos, direction):
		self.initialize()
		self.radius = 2
		self.color = (55, randint(100, 200), 40)
		self.pos = pos
		self.direction = direction
		self.vel += vectorUnitRandom() * 1
		self.timer = 0
		
		points = []
		width = max(0.3, uniform(0,1))
		length = 1 + uniform(0,1)
		for i in range(10):
			x = (i/10) * length
			y = 0.5 * width * sin(2 * (1/length) * pi * x)
			points.append(Vector(x, y))
		for i in range(10):
			x = (1 - (i/10)) * length
			y = - width * sqrt(1 - ((2/length) * (x - length/2))**2)
			points.append(Vector(x, y))
		if randint(0,1) == 0:
			points = [Vector(-i.x, i.y) for i in points]
		size = uniform(4, 7)
		angle = uniform(0, 2*pi)
		self.points = [i.rotate(angle) * size for i in points]
	def limitVel(self):
		self.vel.limit(15)
	def secondaryStep(self):
		self.timer += 1
		if self.timer >= fps * 6:
			self.removeFromGame()
	def applyForce(self):
		self.acc = vectorCopy(self.direction) * 0.8
	def collisionRespone(self, ppos):
		boom(ppos, 7)
		self.removeFromGame()
	def draw(self, win: pygame.Surface):
		pygame.draw.polygon(win, self.color, [point2world(self.pos + i) for i in self.points])

class PlantControl:
	def __init__(self):
		Game._game.nonPhys.append(self)
		self.timer = 5 * fps
		Game._game.playerMoveable = False
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			Game._game.nonPhysToRemove.append(self)
			Game._game.playerMoveable = True
		if pygame.key.get_pressed()[pygame.K_LEFT]:
			for plant in Venus._reg:
				plant.direction.rotate(-0.1)
		elif pygame.key.get_pressed()[pygame.K_RIGHT]:
			for plant in Venus._reg:
				plant.direction.rotate(0.1)
		gameDistable()
	def draw(self, win: pygame.Surface):
		pass

class MasterOfPuppets:
	def __init__(self):
		Game._game.nonPhys.append(self)
		self.springs = []
		self.timer = 0
		for worm in PhysObj._worms:
			# point = Vector(worm.pos.x, 0)
			for t in range(200):
				posToCheck = worm.pos - Vector(0, t * 5)
				if Game._game.map_manager.is_ground_at(posToCheck):
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
			Game._game.nonPhysToRemove.append(self)
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

class Frost:
	def __init__(self, pos):
		self.pos = pos.integer()
		self.visited = []
		self.next = []
		self.timer = fps * randint(2, 6)
		if not Game._game.map_manager.is_ground_at(self.pos):
			return
		Game._game.nonPhys.append(self)
	def step(self):
		color = Game._game.map_manager.ground_map.get_at(self.pos)
		r = color[0] + (256 - color[0]) // 2
		g = color[1] + (256 - color[1]) // 2
		b = color[2] + int((256 - color[2]) * 0.8)
		newColor = (r, g, b)
		Game._game.map_manager.ground_map.set_at(self.pos, newColor)
		self.visited.append(vectorCopy(self.pos))
		directions = [Vector(1,0), Vector(0,1), Vector(-1,0), Vector(0,-1)]
		shuffle(directions)
		
		while len(directions) > 0:
			direction = directions.pop(0)
			checkPos = self.pos + direction
			if Game._game.map_manager.is_ground_at(checkPos) and not checkPos in self.visited:
				self.next.append(checkPos)
		if len(self.next) == 0:
			Game._game.nonPhysToRemove.append(self)
			return
		self.pos = choice(self.next)
		self.next.remove(self.pos)
		
		self.timer -= 1
		if self.timer <= 0:
			Game._game.nonPhysToRemove.append(self)
	def draw(self, win: pygame.Surface):
		pass

class Icicle(LongBow):
	def __init__(self, pos, direction):
		Game._game.nonPhys.append(self)
		self.pos = vectorCopy(pos)
		self.direction = direction
		self.vel = direction.normalize() * 20
		self.stuck = None
		self.color = (112, 74, 255)
		self.ignore = None
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "icicle")
		self.timer = 0
	def secondaryStep(self):
		if randint(0,5) == 0:
			Frost(self.pos + vectorUnitRandom() * 3)
	def destroy(self):
		Game._game.nonPhysToRemove.append(self)
		for _ in range(8):
			DropLet(self.pos, vectorUnitRandom())
	def stamp(self):
		self.pos = self.stuck
		Frost(self.stuck)
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		Game._game.map_manager.ground_map.blit(surf, self.pos - tup2vec(surf.get_size())//2)
		for y in range(self.surf.get_height()):
			for x in range(self.surf.get_width()):
				if not self.surf.get_at((x,y))[3] < 255:
					self.surf.set_at((x,y), GRD)
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		Game._game.map_manager.game_map.blit(surf, self.pos - tup2vec(surf.get_size())//2)
		
		self.destroy()
	def wormCollision(self, worm):
		for i in range(8):
			pos = worm.pos + vectorFromAngle(2 * pi * i / 8, worm.radius + 1)
			Frost(pos)
		worm.vel += self.direction*4
		worm.vel.y -= 2
		worm.damage(randint(20,30))
		GameVariables().cam_track = worm
		for i in range(8):
			DropLet(self.pos, vectorUnitRandom())
		self.destroy()
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())//2))

def calcEarthSpikePos():
	amount = (pi/2 - Game._game.player.shootAngle) * Game._game.player.facing / pi
	xFromWorm = Game._game.player.pos.x + Game._game.player.facing * amount * 70
	if Game._game.map_manager.is_ground_at(Vector(xFromWorm, Game._game.player.pos.y)):
		y = Game._game.player.pos.y
		while Game._game.map_manager.is_ground_at(Vector(xFromWorm, y)):
			y -= 2
			if y < 0:
				return None
	else:
		y = Game._game.player.pos.y
		while not Game._game.map_manager.is_ground_at(Vector(xFromWorm, y)):
			y += 2
			if y > Game._game.map_manager.game_map.get_height():
				return None
	return Vector(xFromWorm, y)

class EarthSpike:
	def __init__(self):
		self.squareSize = Vector(16,32)
		self.pos = calcEarthSpikePos()
		Game._game.nonPhys.append(self)
		self.timer = 0
		self.surf = pygame.Surface((32, 32), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), ((32, 96), (32, 32)))
		if randint(0, 1) == 0:
			self.surf = pygame.transform.flip(self.surf, True, False)
		self.colors = [(139, 140, 123), (91, 92, 75), (208, 195, 175), (48, 35, 34)]
	def step(self):
		if self.timer < 5:
			for i in range(randint(5,10)):
				d = Debrie(self.pos + Vector(randint(-8,8), -3), 10, self.colors, 1, False, True)
				d.vel = vectorUnitRandom()
				d.vel.y = uniform(-10, -8)
				d.radius = choice([2,1])
		if self.timer == 5:
			surf = pygame.transform.scale(self.surf, (32, 16))
			rectPos = self.pos + Vector(-surf.get_width() // 2, 3 - surf.get_height())
			win.blit(surf, point2world(rectPos))
			MapManager().stain(self.pos - Vector(0, 3), sprites.hole, (32,32), True)
			
		if self.timer == 6:
			rectPos = self.pos + Vector(-self.surf.get_width() // 2, 3 - self.surf.get_height())
			for obj in PhysObj._reg:
				if obj in Debrie._debries:
					continue
				if obj.pos.x > rectPos.x + 8 and obj.pos.x <= rectPos.x + self.surf.get_width() - 8 \
						and obj.pos.y > rectPos.y and obj.pos.y <= rectPos.y + self.surf.get_height():
					obj.pos += Vector(0, -self.surf.get_height())
					obj.vel.x = obj.pos.x - self.pos.x
					obj.vel.y -= randint(7,9)
					if obj in PhysObj._worms and not obj in globals.team_manager.currentTeam.worms:
						obj.damage(randint(25,35))
			
			Game._game.map_manager.ground_map.blit(self.surf, rectPos)
			surf = self.surf.copy()
			pixels = pygame.PixelArray(surf)
			for i in self.colors:
				pixels.replace(i, GRD)
			del pixels
			Game._game.map_manager.game_map.blit(surf, rectPos)
		self.timer += 1
	def draw(self, win: pygame.Surface):
		pass

class FireBall(LongBow):
	def __init__(self, pos, direction):
		Game._game.nonPhys.append(self)
		self.pos = vectorCopy(pos)
		self.direction = direction
		self.vel = direction.normalize() * 20
		self.stuck = None
		self.color = (112, 74, 255)
		self.ignore = None
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "fire ball")
		self.timer = 0
	def secondaryStep(self):
		if randint(0,2) == 0:
			Fire(self.pos)
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), randint(5,8), 30, 3)
	def destroy(self):
		if self.stuck:
			boomPos = self.stuck
		else:
			boomPos = self.pos
		boom(boomPos, 15)
		for i in range(40):
			s = Fire(boomPos, 5)
			s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2)
		Game._game.nonPhysToRemove.append(self)
	def stamp(self):
		self.destroy()
	def wormCollision(self, worm):
		self.stuck = worm.pos + vectorUnitRandom() * 2
		self.destroy()
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())//2))

class Tornado:
	def __init__(self):
		self.width = 30
		self.pos = Game._game.player.pos + Vector(Game._game.player.radius + self.width / 2, 0) * Game._game.player.facing
		self.facing = Game._game.player.facing
		Game._game.nonPhys.append(self)
		amount = Game._game.map_manager.game_map.get_height() // 10
		self.points = [Vector(0, 10 * i) for i in range(amount)]
		self.swirles = []
		self.sizes = [self.width + randint(0,20) for i in self.points]
		for point in self.points:
			xRadius = 0
			yRadius = 0
			theta = uniform(0, 2 * pi)
			self.swirles.append([xRadius, yRadius, theta])
		self.timer = 0
		self.speed = 2
		self.radius = 0
	def step(self):
		gameDistable()
		if self.timer < 2 * fps:
			for i, swirl in enumerate(self.swirles):
				swirl[0] = min(self.timer, self.sizes[i])
				swirl[1] = min(self.timer / 3, 10)
		self.pos.x += self.speed * self.facing
		for swirl in self.swirles:
			swirl[2] += 0.1 * uniform(0.8, 1.2)
		rect = (Vector(self.pos.x - self.width / 2, 0), Vector(self.width, Game._game.map_manager.game_map.get_height()))
		for obj in PhysObj._reg:
			if obj.pos.x > rect[0][0] and obj.pos.x <= rect[0][0] + rect[1][0]:
				if obj.vel.y > -2:
					obj.acc.y += -0.5
				obj.acc.x += 0.5 * sin(self.timer/6)
		if self.timer >= fps * 10 and len(self.swirles) > 0:
			self.swirles.pop(-1)
			if len(self.swirles) == 0:
				Game._game.nonPhysToRemove.append(self)
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
		GameEvents().post(EventComment([{'text': 'everything changed when the '}, {'text': globals.team_manager.currentTeam.name, 'color': globals.team_manager.currentTeam.color}, {'text': ' attacked'}]))
	
	def trenaryStep(self):
		self.angle -= self.vel.x*4

class PickAxe:
	_pa = None
	def __init__(self):
		PickAxe._pa = self
		Game._game.nonPhys.append(self)
		self.count = 6
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "pick axe")
		self.animating = 0
	def mine(self):
		worm = Game._game.player
		position = worm.pos + vectorFromAngle(worm.shootAngle, 20)
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

		colors = []
		for i in range(10):
			sample = (position + Vector(8,8) + vectorUnitRandom() * uniform(0,8)).vec2tupint()
			if MapManager().is_on_map(sample):
				color = Game._game.map_manager.ground_map.get_at(sample)
				if not color == SKY:
					colors.append(color)
		if len(colors) == 0:
			colors = Blast._color

		for i in range(16):
			d = Debrie(position + Vector(8,8), 8, colors, 2, False)
			d.radius = choice([2,1])

		pygame.draw.rect(Game._game.map_manager.game_map, SKY, (position, Vector(16,16)))
		pygame.draw.rect(Game._game.map_manager.ground_map, SKY, (position, Vector(16,16)))

		self.animating = 90

		self.count -= 1
		if self.count == 0:
			return True
		return False
	def step(self):
		if self.count == 0:
			Game._game.nonPhysToRemove.append(self)
			PickAxe._pa = None
		if self.animating > 0:
			self.animating -= 5
			if self.animating < 0:
				self.animating = 0
		if not Game._game.player.alive:
			Game._game.nonPhysToRemove.append(self)
			PickAxe._pa = None
	def draw(self, win: pygame.Surface):
		worm = Game._game.player
		position = worm.pos + vectorFromAngle(worm.shootAngle, 20)
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
		Game._game.nonPhys.append(self)
		self.count = 6
		self.locations = []
	def build(self):
		worm = Game._game.player
		position = worm.pos + vectorFromAngle(worm.shootAngle, 20)
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

		pygame.draw.rect(Game._game.map_manager.game_map, GRD, (position, Vector(16,16)))
		if position + Vector(0,16) in self.locations:
			blit_weapon_sprite(Game._game.map_manager.ground_map, position, "build")
			Game._game.map_manager.ground_map.blit(sprites.sprite_atlas, position + Vector(0,16), (80,112,16,16))
		elif position + Vector(0,-16) in self.locations:
			Game._game.map_manager.ground_map.blit(sprites.sprite_atlas, position, (80,112,16,16))
		else:
			blit_weapon_sprite(Game._game.map_manager.ground_map, position, "build")

		self.locations.append(position)
		
		self.count -= 1
		if self.count == 0:
			return True
		return False
	def step(self):
		if self.count == 0:
			Game._game.nonPhysToRemove.append(self)
			MineBuild._mb = None
			
		if not Game._game.player.alive:
			Game._game.nonPhysToRemove.append(self)
			MineBuild._mb = None
	def draw(self, win: pygame.Surface):
		worm = Game._game.player
		position = worm.pos + vectorFromAngle(worm.shootAngle, 20)
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
		Game._game.nonPhys.append(self)
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
				Game._game.nonPhysToRemove.append(self)
	def draw(self, win: pygame.Surface):
		pass

class FireWorkRockets:
	_fw = None
	def __init__(self):
		Game._game.nonPhys.append(self)
		FireWorkRockets._fw = self
		self.objects = []
		self.state = "tag"
		self.timer = 0
		self.picked = 0
	def step(self):
		if self.state == "thrusting":
			self.timer += 1
			if self.timer > 1.5 * fps:
				self.state = "exploding"
			for obj in self.objects:
				obj.acc += Vector(0, -0.34)
				Blast(obj.pos + Vector(0, obj.radius*1.5) + vectorUnitRandom()*2, randint(5,8), 80)
		elif self.state == "exploding":
			for obj in self.objects:
				FireWork(obj.pos, Game._game.player.team.color)
				boom(obj.pos, 22)
			self.done()
	def done(self):
		if self in Game._game.nonPhys:
			Game._game.nonPhysToRemove.append(self)
		FireWorkRockets._fw = None
	def fire(self):
		"""return true if fired"""
		if self.state == "tag":
			candidates = []
			for obj in PhysObj._reg:
				if obj == Game._game.player or obj in self.objects:
					continue
				if distus(obj.pos, Game._game.player.pos) < 15*15:
					candidates.append(obj)
			# take the closest
			if len(candidates) > 0:
				candidates.sort(key = lambda x: distus(x.pos, Game._game.player.pos))
				self.objects.append(candidates[0])
			self.picked += 1
			if self.picked >= 3:
				self.state = "ready"
		elif self.state == "ready":
			self.state = "thrusting"
			for obj in self.objects:
				obj.vel += Vector(randint(-3,3), -2)
			if len(self.objects) > 0:
				GameVariables().cam_track = choice(self.objects)
			return True
		return False
	def draw(self, win: pygame.Surface):
		if self.state in ["tag"]:
			for obj in PhysObj._reg:
				if obj == Game._game.player or obj in self.objects:
					continue
				if distus(obj.pos, Game._game.player.pos) < 15*15:
					drawTarget(obj.pos)
		
		for obj in self.objects:
			blit_weapon_sprite(win, point2world(obj.pos - Vector(8,8)), "fireworks")

class FireWork:
	_reg = []
	def __init__(self, pos, color):
		Game._game.nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.blasts = []
		
		self.timer = 0
		blastNum = 20
		for i in range(blastNum):
			self.blasts.append([vectorCopy(self.pos), vectorFromAngle(i * 2 * pi / blastNum, 7 + uniform(-1,1))])

		self.color = color
		self.state = "blow"
	def step(self):
		if self.state == "blow":
			for i in range(len(self.blasts)):
				vel = self.blasts[i][1]
				vel += Vector(0, 0.5 * GameVariables().physics.global_gravity)
				vel *= 0.9
				self.blasts[i][0] += vel
				Blast(self.blasts[i][0] + vectorUnitRandom(), randint(3,6), 150, color=self.color)
		
		self.timer += 1
		if self.timer > 0.9 * fps:
			if self in Game._game.nonPhys:
				Game._game.nonPhysToRemove.append(self)
	def draw(self, win: pygame.Surface):
		pass

class Trampoline:
	_reg = []
	_sprite = None
	def __init__(self, pos):
		Game._game.nonPhys.append(self)
		self.pos = vectorCopy(pos)
		self.directionalVel = 0
		self.offset = 0
		self.stable = False
		for i in range(25):
			if Game._game.map_manager.is_ground_at(self.pos + Vector(0, i)):
				self.anchor = self.pos + Vector(0, i)
				break
		Trampoline._reg.append(self)
		self.size = Vector(24, 8)
		if Trampoline._sprite == None:
			Trampoline._sprite = pygame.Surface((24, 7), pygame.SRCALPHA)
			Trampoline._sprite.blit(sprites.sprite_atlas, (0,0), (100, 117, 24, 7))
	def collide(self, pos):
		if pos.x > self.pos.x - self.size.x / 2 and pos.x < self.pos.x + self.size.x / 2 and pos.y > self.pos.y - self.size.y / 2 and pos.y < self.pos.y + self.size.y:
			return True
		return False
	def step(self):
		if not self.stable:
			acc = - 1 * self.offset
			self.directionalVel += acc
			self.directionalVel *= 0.8
			self.offset += self.directionalVel
			if abs(self.directionalVel) < 0.2 and abs(self.offset) < 0.2:
				self.directionalVel = 0
				self.offset = 0
				self.stable = True
		if not Game._game.map_manager.is_ground_at(self.anchor):
			Game._game.nonPhysToRemove.append(self)
			Trampoline._reg.remove(self)
			gs = GunShell(vectorCopy(self.pos))
			gs.surf = Trampoline._sprite
		for obj in PhysObj._reg:
			# trampoline
			if obj.vel.y > 0 and self.collide(obj.pos):
				self.spring(obj.vel.y)
				if abs(obj.vel.y) <= 10:
					obj.vel.y *= -1.2
				else:
					obj.vel.y *= -1.0
				if abs(obj.vel.y) < JUMP_VELOCITY:
					obj.vel.y = - JUMP_VELOCITY
				if Game._game.state == WAIT_STABLE:
					obj.vel.x += uniform(-0.5,0.5)
	def spring(self, amount):
		self.offset = -amount
		self.stable = False
	def draw(self, win: pygame.Surface):
		startPos = self.anchor.y
		endPos = self.pos.y + self.offset - 4
		i = startPos
		while i > endPos:
			win.blit(sprites.sprite_atlas, point2world((self.pos.x - 5, i)), (107, 124, 10, 4))
			i -= 4
		win.blit(Trampoline._sprite, point2world(self.pos + Vector(0, self.offset) - self.size / 2))

################################################################################ Weapons setup

def fire(weapon = None):
	global decrease
	if not weapon:
		weapon = WeaponManager._wm.currentWeapon
	decrease = True
	if Game._game.player:
		weaponOrigin = vectorCopy(Game._game.player.pos)
		weaponDir = vectorFromAngle(Game._game.player.shootAngle)
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
	}

	avail = True
	w = None

	if weapon.name in gun_weapons_map.keys():
		if WeaponManager._wm.current_gun is None:
			WeaponManager._wm.current_gun = ShootGun(**gun_weapons_map[weapon.name])
		
		WeaponManager._wm.current_gun.shoot()
		w = WeaponManager._wm.current_gun.get_object()
		decrease = False
		Game._game.nextState = PLAYER_CONTROL_1

		if WeaponManager._wm.current_gun.is_done():
			decrease = True
			if WeaponManager._wm.current_gun.is_end_turn():
				Game._game.nextState = PLAYER_CONTROL_2
			else:
				Game._game.nextState = PLAYER_CONTROL_1
			WeaponManager._wm.current_gun.remove()
			WeaponManager._wm.current_gun = None

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
		w.vel.x = Game._game.player.facing * 0.5
		w.vel.y = -0.8
	elif weapon.name == "sticky bomb":
		w = StickyBomb(weaponOrigin, weaponDir, energy)
	elif weapon.name == "mine":
		w = Mine(weaponOrigin, fps * 2.5)
		w.vel.x = Game._game.player.facing * 0.5
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
		w = PlantBomb(weaponOrigin, weaponDir, energy, PlantBomb.mode)
	elif weapon.name == "sentry turret":
		w = SentryGun(weaponOrigin, globals.team_manager.currentTeam.color)
		w.pos.y -= Game._game.player.radius + w.radius
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
		for worm in Game._game.player.team.worms:
			w.bitten.append(worm)
	elif weapon.name == "artillery assist":
		w = Artillery(weaponOrigin, weaponDir, energy)
	elif weapon.name == "sheep":
		w = Sheep(weaponOrigin + Vector(0,-5))
		w.facing = Game._game.player.facing
	elif weapon.name == "rope":
		angle = weaponDir.getAngle()
		decrease = False
		if angle <= 0:
			Game._game.player.worm_tool.set(Rope(Game._game.player, weaponOrigin, weaponDir))

		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "raging bull":
		w = Bull(weaponOrigin + Vector(0,-5))
		w.facing = Game._game.player.facing
		w.ignore.append(Game._game.player)
	elif weapon.name == "electro boom":
		w = ElectroBoom(weaponOrigin, weaponDir, energy)
	elif weapon.name == "parachute":
		if Game._game.player.vel.y > 1:
			tool_set = Game._game.player.worm_tool.set(Parachute(Game._game.player))
			if not tool_set:
				decrease = False
		else:
			decrease = False

		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "pokeball":
		w = PokeBall(weaponOrigin, weaponDir, energy)
	elif weapon.name == "green shell":
		w = GreenShell(weaponOrigin + Vector(0,-5))
		w.facing = Game._game.player.facing
		w.ignore.append(Game._game.player)
	elif weapon.name == "guided missile":
		w = GuidedMissile(weaponOrigin + Vector(0,-5))
		Game._game.nextState = WAIT_STABLE
	elif weapon.name == "flare":
		w = Flare(weaponOrigin, weaponDir, energy)
		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "ender pearl":
		w = EndPearl(weaponOrigin, weaponDir, energy)
		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "raon launcher":
		w = Raon(weaponOrigin, weaponDir, energy * 0.95)
		w = Raon(weaponOrigin, weaponDir, energy * 1.05)
		if randint(0, 10) == 0 or GameVariables().mega_weapon_trigger:
			w = Raon(weaponOrigin, weaponDir, energy * 1.08)
			w = Raon(weaponOrigin, weaponDir, energy * 0.92)
	elif weapon.name == "snail":
		w = SnailShell(weaponOrigin, weaponDir, energy)
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
	elif weapon.name == "fireworks":
		done = False
		decrease = False
		if FireWorkRockets._fw:
			done = FireWorkRockets._fw.fire()
			Game._game.nextState = FIRE_MULTIPLE
		else:
			FireWorkRockets()
			Game._game.nextState = FIRE_MULTIPLE
		if done:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
	elif weapon.name == "trampoline":
		position = Game._game.player.pos + vectorFromAngle(Game._game.player.shootAngle, 20)
		anchored = False
		for i in range(25):
			if Game._game.map_manager.is_ground_at(position + Vector(0, i)):
				anchored = True
				break
		if anchored:
			Trampoline(position)
		else:
			decrease = False
		Game._game.nextState = PLAYER_CONTROL_1

	# artifacts
	elif weapon.name == "mjolnir strike":
		MjolnirStrike()
	elif weapon.name == "mjolnir throw":
		w = MjolnirThrow(weaponOrigin, weaponDir, energy)
	elif weapon.name == "fly":
		if not MjolnirFly.flying:
			w = MjolnirFly(weaponOrigin, weaponDir, energy)
		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "control plants":
		PlantControl()
	elif weapon.name == "magic bean":
		w = PlantBomb(weaponOrigin, weaponDir, energy, PlantBomb.bean)
		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "mine plant":
		w = PlantBomb(weaponOrigin, weaponDir, energy, PlantBomb.mine)
	elif weapon.name == "earth spike":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 2
		if calcEarthSpikePos():
			EarthSpike()
			Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
	elif weapon.name == "air tornado":
		w = Tornado()
	elif weapon.name == "pick axe":
		if PickAxe._pa:
			decrease = PickAxe._pa.mine()
		else:
			PickAxe()
			decrease = False
		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "build":
		if MineBuild._mb:
			decrease = MineBuild._mb.build()
		else:
			MineBuild()
			decrease = False
		Game._game.nextState = PLAYER_CONTROL_1

	if w and not TimeTravel._tt.timeTravelFire: GameVariables().cam_track = w	
	
	# position to available position
	if w and avail:
		availpos = getClosestPosAvail(w.pos, w.radius)
		if availpos:
			w.pos = availpos
	
	if decrease:
		if globals.team_manager.currentTeam.ammo(weapon) != -1:
			globals.team_manager.currentTeam.ammo(weapon, -1)
		WeaponManager._wm.renderWeaponCount()

	Game._game.fireWeapon = False
	Game._game.energyLevel = 0
	Game._game.energising = False
	
	if TimeTravel._tt.timeTravelFire:
		TimeTravel._tt.timeTravelFire = False
		return
	
	Game._game.state = Game._game.nextState
	if Game._game.state == PLAYER_CONTROL_2: TimeManager._tm.timeRemainingRetreat()
	
	# for uselist:
	if Game._game.game_config.option_cool_down and (Game._game.state == PLAYER_CONTROL_2 or Game._game.state == WAIT_STABLE):
		globals.weapon_manager.add_to_cool_down(globals.weapon_manager.currentWeapon)

def fireClickable():
	current_weapon = WeaponManager._wm.currentWeapon

	decrease = True
	if not Game._game.radial_weapon_menu is None:
		return
	if globals.team_manager.currentTeam.ammo(current_weapon) == 0:
		return
	mousePosition = globals.mouse_pos_in_world()
	addToUsed = True
	
	if current_weapon.name == "girder":
		Game._game.girder(mousePosition)
	elif current_weapon.name == "teleport":
		Game._game.player.pos = mousePosition
		addToUsed = False
	elif current_weapon.name == "airstrike":
		fireAirstrike(mousePosition)
	elif current_weapon.name == "mine strike":
		fireMineStrike(mousePosition)
	elif current_weapon.name == "napalm strike":
		fireNapalmStrike(mousePosition)

	if decrease and globals.team_manager.currentTeam.ammo(WeaponManager._wm.currentWeapon) != -1:
		globals.team_manager.currentTeam.ammo(WeaponManager._wm.currentWeapon, -1)
	
	if Game._game.game_config.option_cool_down and (Game._game.nextState == PLAYER_CONTROL_2 or Game._game.nextState == WAIT_STABLE) and addToUsed:
		globals.weapon_manager.add_to_cool_down(globals.weapon_manager.currentWeapon)
	
	WeaponManager._wm.renderWeaponCount()
	TimeManager._tm.timeRemainingRetreat()
	Game._game.state = Game._game.nextState
  
def fireUtility(weapon = None):
	if not weapon:
		weapon = WeaponManager._wm.currentWeapon
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
		WeaponManager._wm.switchWeapon(weapon)
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
		tool_set = Game._game.player.worm_tool.set(JetPack(Game._game.player))
		if not tool_set:
			decrease = False
	
	elif weapon.name == "flare":
		WeaponManager._wm.switchWeapon(weapon)
		decrease = False
	
	elif weapon.name == "control plants":
		PlantControl()
	
	if decrease:
		globals.team_manager.currentTeam.ammo(weapon, -1)


################################################################################ more functions

def addToRecord(dic):
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

def checkWinners():
	end = False
	lastTeam = None
	count = 0
	pointsGame = False
	for team in globals.team_manager.teams:
		if len(team.worms) == 0:
			count += 1
	if count == globals.team_manager.totalTeams - 1:
		# one team remains
		end = True
		for team in globals.team_manager.teams:
			if not len(team.worms) == 0:
				lastTeam = team
	if count == globals.team_manager.totalTeams:
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
		for team in globals.team_manager.teams:
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
		globals.team_manager.currentTeam.points += 3 # bonus points
		dic["mode"] = "targets"
		print("[targets win, team", globals.team_manager.currentTeam.name, "got 3 bonus points]")
	
	elif Game._game.gameMode == GameMode.TERMINATOR:
		pointsGame = True
		if lastTeam:
			lastTeam.points += 3 # bonus points
			print("[team", lastTeam.name, "got 3 bonus points]")
		dic["mode"] = "terminator"
	
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
		for team in globals.team_manager.teams:
			print("[ |", team.name, "got", team.points, "points! | ]")
		teamsFinals = sorted(globals.team_manager.teams, key = lambda x: x.points)
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
		if winningTeam != None:
			print("Team", winningTeam.name, "won!")
			dic["time"] = str(GameVariables().time_overall // fps)
			dic["winner"] = winningTeam.name
			if Game._game.mostDamage[1]:
				dic["mostDamage"] = str(int(Game._game.mostDamage[0]))
				dic["damager"] = Game._game.mostDamage[1]
			addToRecord(dic)
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
		for team in globals.team_manager.teams:
			dic["teams"][team.name] = [team.color, team.points]

		Game._game.endGameDict = dic
		Game._game.nextState = WIN
		
		GroundScreenShoot = pygame.Surface((Game._game.map_manager.ground_map.get_width(), Game._game.map_manager.ground_map.get_height() - GameVariables().water_level), pygame.SRCALPHA)
		GroundScreenShoot.blit(Game._game.map_manager.ground_map, (0,0))
		pygame.image.save(GroundScreenShoot, "lastWormsGround.png")
	return end

def cycleWorms():
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

	Game._game.player.worm_tool.release()

	Game._game.switchingWorms = False
	if Worm.roped:
		Game._game.player.team.ammo("rope", -1)
		Worm.roped = False
	
	# update damage:
	wormName = Game._game.player.nameStr
	wormColor = Game._game.player.team.color
	if Game._game.damageThisTurn > Game._game.mostDamage[0]:
		Game._game.mostDamage = (Game._game.damageThisTurn, Game._game.player.nameStr)	
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
	
	globals.team_manager.currentTeam.damage += Game._game.damageThisTurn
	if Game._game.gameMode in [GameMode.POINTS, GameMode.BATTLE]:
		globals.team_manager.currentTeam.points = globals.team_manager.currentTeam.damage + 50 * globals.team_manager.currentTeam.killCount
	Game._game.damageThisTurn = 0
	if checkWinners():
		return
	Game._game.roundCounter += 1

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
			Game._game.roundCounter -= 1
			Game._game.nextState = WAIT_STABLE
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
			Game._game.roundCounter -= 1
			Game._game.nextState = WAIT_STABLE
			return
		
	# deploy pack:
	if Game._game.roundCounter % globals.team_manager.totalTeams == 0 and not Game._game.deploying:
		Game._game.deploying = True
		Game._game.roundCounter -= 1
		Game._game.nextState = WAIT_STABLE
		comments = [
			[{'text': 'a jewel from the heavens!'}],
			[{'text': 'its raining crates, halelujah!'}],
			[{'text': ' '}],
		]
		GameEvents().post(EventComment(choice(comments)))

		for i in range(Game._game.game_config.deployed_packs):
			w = deployPack(choice([HealthPack,UtilityPack, WeaponPack]))
			GameVariables().cam_track = w
		# if Game._game.darkness:
		# 	for team in globals.team_manager.teams:
		# 		team.ammo("flare", 1)
		# 		if team.ammo("flare") > 3:
		# 			team.ammo("flare", -1)
		return
	
	# rise water:
	if Game._game.waterRise and not Game._game.waterRising:
		Game._game.background.water_rise(20)
		Game._game.nextState = WAIT_STABLE
		Game._game.roundCounter -= 1
		Game._game.waterRising = True
		return
	
	# throw artifact:
	if Game._game.game_config.option_artifacts:
		for team in globals.team_manager.teams:
			if PLANT_MASTER in team.artifacts:
				team.ammo("magic bean", 1, True)
			elif MJOLNIR in team.artifacts:
				team.ammo("fly", 3, True)
			elif MINECRAFT in team.artifacts:
				team.ammo("pick axe", 1, True)
				team.ammo("build", 1, True)
		
		if len(Game._game.worldArtifacts) > 0 and not Game._game.deployingArtifact:
			chance = randint(0,10)
			if chance == 0 or Game._game.trigerArtifact:
				Game._game.trigerArtifact = False
				Game._game.deployingArtifact = True
				artifact = choice(Game._game.worldArtifacts)
				Game._game.worldArtifacts.remove(artifact)
				Game._game.dropArtifact(Game._game.worldArtifactsClasses[artifact], None, comment=True)
				Game._game.nextState = WAIT_STABLE
				Game._game.roundCounter -= 1
				return
	
	Game._game.waterRising = False
	Game._game.raoning = False
	Game._game.deploying = False
	Game._game.sentring = False
	Game._game.deployingArtifact = False
	
	if Game._game.roundCounter % globals.team_manager.totalTeams == 0:
		Game._game.game_config.rounds_for_sudden_death -= 1
		if Game._game.game_config.rounds_for_sudden_death == 0:
			suddenDeath()
	
	if Game._game.gameMode == GameMode.CAPTURE_THE_FLAG:
		for team in globals.team_manager.teams:
			if team.flagHolder:
				team.points += 1
				break

	# update weapons delay (and targets)
	if Game._game.roundCounter % globals.team_manager.totalTeams == 0:
		if Game._game.gameMode == GameMode.TARGETS:
			ShootingTarget.numTargets -= 1
			if ShootingTarget.numTargets == 0:
				GameEvents().post(EventComment([{'text': 'final targets round'}]))
	
	# update stuff
	Debrie._debries = []
	Bubble.cought = []
	
	HomingMissile.showTarget = False
	# change wind:
	GameVariables().physics.wind = uniform(-1, 1)
	
	# flares reduction
	# if Game._game.darkness:
	# 	for flare in Flare._flares:
	# 		if not flare in PhysObj._reg:
	# 			Flare._flares.remove(flare)
	# 		flare.lightRadius -= 10
	
	# sick:
	for worm in PhysObj._worms:
		if not worm.sick == 0 and worm.health > 5:
			worm.damage(min(int(5 / GameVariables().damage_mult) + 1, int((worm.health - 5) / GameVariables().damage_mult) + 1), 2)
		
	# select next team
	index = globals.team_manager.teams.index(globals.team_manager.currentTeam)
	index = (index + 1) % globals.team_manager.totalTeams
	globals.team_manager.currentTeam = globals.team_manager.teams[index]
	while not len(globals.team_manager.currentTeam.worms) > 0:
		index = globals.team_manager.teams.index(globals.team_manager.currentTeam)
		index = (index + 1) % globals.team_manager.totalTeams
		globals.team_manager.currentTeam = globals.team_manager.teams[index]
	
	if Game._game.gameMode == GameMode.TERMINATOR:
		pickVictim()
	
	if Game._game.gameMode == GameMode.ARENA:
		ArenaManager._arena.wormsCheck()
	
	if Game._game.gameMode == GameMode.MISSIONS:
		MissionManager._mm.endTurn()

	Game._game.damageThisTurn = 0
	if Game._game.nextState == PLAYER_CONTROL_1:
	
		# sort worms by health for drawing purpuses
		PhysObj._reg.sort(key = lambda worm: worm.health if worm.health else 0)
		
		# actual worm switch:
		switched = False
		while not switched:
			w = globals.team_manager.currentTeam.worms.pop(0)
			globals.team_manager.currentTeam.worms.append(w)
			if w.sleep:
				w.sleep = False
				continue
			switched = True
			
		if Game._game.game_config.random_mode == RandomMode.COMPLETE: # complete random
			globals.team_manager.currentTeam = choice(globals.team_manager.teams)
			while not len(globals.team_manager.currentTeam.worms) > 0:
				globals.team_manager.currentTeam = choice(globals.team_manager.teams)
			w = choice(globals.team_manager.currentTeam.worms)
		if Game._game.game_config.random_mode == RandomMode.IN_TEAM: # random in the current team
			w = choice(globals.team_manager.currentTeam.worms)
	
		Game._game.player = w
		GameVariables().cam_track = Game._game.player
		WeaponManager._wm.switchWeapon(WeaponManager._wm.currentWeapon)
		if Game._game.gameMode == GameMode.MISSIONS:
			MissionManager._mm.cycle()

def switchWorms():
	currentWorm = globals.team_manager.currentTeam.worms.index(Game._game.player)
	totalWorms = len(globals.team_manager.currentTeam.worms)
	currentWorm = (currentWorm + 1) % totalWorms
	Game._game.player = globals.team_manager.currentTeam.worms[currentWorm]
	GameVariables().cam_track = Game._game.player
	if Game._game.gameMode == GameMode.MISSIONS:
		MissionManager._mm.cycle()

def isGroundAround(place, radius = 5):
	for i in range(8):
		checkPos = place + Vector(radius * cos((i/4) * pi), radius * sin((i/4) * pi))
		# extra.append((checkPos.x, checkPos.y, (255,0,0), 10000))
		if checkPos.x < 0 or checkPos.x > Game._game.map_manager.game_map.get_width() or checkPos.y < 0 or checkPos.y > Game._game.map_manager.game_map.get_height():
			return False
		try:
			at = (int(checkPos.x), int(checkPos.y))
			if Game._game.map_manager.game_map.get_at(at) == GRD or Game._game.map_manager.worm_col_map.get_at(at) != (0,0,0) or Game._game.map_manager.objects_col_map.get_at(at) != (0,0,0):
				return True
		except IndexError:
			print("isGroundAround index error")
			
	return False

def randomPlacing():
	for i in range(Game._game.game_config.worms_per_team * len(globals.team_manager.teams)):
		if Game._game.game_config.option_forts:
			place = giveGoodPlace(i)
		else:
			place = giveGoodPlace()
		if Game._game.game_config.option_digging:
			pygame.draw.circle(Game._game.map_manager.game_map, SKY, place, 35)
			pygame.draw.circle(Game._game.map_manager.ground_map, SKY, place, 35)
			pygame.draw.circle(Game._game.map_manager.ground_secondary, SKY, place, 30)
		current_team = globals.team_manager.teams[globals.team_manager.teamChoser]
		new_worm_name = current_team.get_new_worm_name()
		current_team.worms.append(Worm(place, new_worm_name, current_team))
		globals.team_manager.teamChoser = (globals.team_manager.teamChoser + 1) % globals.team_manager.totalTeams
		Game._game.lstepper()
	Game._game.state = Game._game.nextState

def squareCollision(pos1, pos2, rad1, rad2):
	return True if pos1.x < pos2.x + rad2*2 and pos1.x + rad1*2 > pos2.x and pos1.y < pos2.y + rad2*2 and pos1.y + rad1*2 > pos2.y else False

################################################################################ Gui

def weaponMenuRadialInit():
	# get categories

	current_team = globals.team_manager.currentTeam
	
	layout = []

	for category in reversed(list(WeaponCategory)):
		weapons_in_category = WeaponManager._wm.get_weapons_list_of_category(category)
		weapons_in_category = [weapon for weapon in weapons_in_category if current_team.ammo(weapon) != 0]
		if len(weapons_in_category) == 0:
			continue
		get_amount = lambda x: str(current_team.ammo(x)) if current_team.ammo(x) > 0 else ''
		sub_layout = [RadialButton(weapon, weapon.name, get_amount(weapon), weapon_bg_color[category], WeaponManager._wm.get_surface_portion(weapon)) for weapon in reversed(weapons_in_category)]
		main_button = RadialButton(weapons_in_category[0], '', '', weapon_bg_color[category], WeaponManager._wm.get_surface_portion(weapons_in_category[0]), sub_layout)
		layout.append(main_button)

	Game._game.radial_weapon_menu = RadialMenu(layout, Vector(GameVariables().win_width // 2, GameVariables().win_height // 2))

class Camera:
	def __init__(self, pos):
		self.pos = pos
		self.radius = 1

def toastInfo():
	if Game._game.gameMode < GameMode.POINTS:
		return
	if Toast.toastCount > 0:
		Toast._toasts[0].time = 0
		if Toast._toasts[0].state == 2:
			Toast._toasts[0].state = 0
		return
	toastWidth = 100
	surfs = []
	for team in globals.team_manager.teams:
		name = fonts.pixel5.render(team.name, False, team.color)
		points = fonts.pixel5.render(str(team.points), False, (0,0,0))
		surfs.append((name, points))
	surf = pygame.Surface((toastWidth, (surfs[0][0].get_height() + 3) * globals.team_manager.totalTeams), pygame.SRCALPHA)
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
		self.pos = Vector(Game._game.map_manager.game_map.get_width(), Game._game.map_manager.game_map.get_height())//2 - self.size//2
	def step(self):
		pass
	def draw(self, win: pygame.Surface):
		pygame.draw.rect(Game._game.map_manager.game_map, GRD,(self.pos, self.size))
		for i in range(10):
			Game._game.map_manager.ground_map.blit(sprites.sprite_atlas, self.pos + Vector(i * 16, 0), (64,80,16,16))
	def wormsCheck(self):
		for worm in PhysObj._worms:
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
			MissionManager._log += f"{worm.nameStr} received mission {newMission.missionType}\n"

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
					if mission.target not in PhysObj._worms or not mission.target.alive:
						replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))
		if "hit a worm from _" in currentWormMissionsTypes:
			for mission in self.wormMissionDict[worm]:
				if mission.missionType == "hit a worm from _":
					if len(mission.teamTarget) == 0:
						replaceMissions.append((mission, self.wormMissionDict[worm].index(mission)))

		# count alive worms from other teams
		aliveWorms = 0
		for w in PhysObj._worms:
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
				MissionManager._log += f"{worm.nameStr} received mission {newMission.missionType}\n"

		if len(self.wormMissionDict[worm]) < 3:
			for i in range(3 - len(self.wormMissionDict[worm])):
				newMission = self.assignOneMission(worm, oldMission)
				self.wormMissionDict[worm].append(newMission)
				# self.wormMissionDict[worm].append(newMission)
				MissionManager._log += f"{worm.nameStr} received mission {newMission.missionType}\n"

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
		notFromTeam = Game._game.player.team
		worms = []
		for worm in PhysObj._worms:
			if worm.team == notFromTeam:
				continue
			if not worm.alive:
				continue
			worms.append(worm)
		return worms

	def createMarker(self):
		return giveGoodPlace(-1, True)

	def chooseTarget(self):
		notFromTeam = Game._game.player.team
		worms = self.getAliveWormsFromOtherTeams()
		return choice(worms)

	def chooseTeamTarget(self):
		notFromTeam = Game._game.player.team
		teams = []
		for team in globals.team_manager.teams:
			if team == notFromTeam:
				continue
			if len(team.worms) == 0:
				continue
			teams.append(team)
		if len(teams) == 0:
			return None
		return choice(teams)

	def removeMission(self, mission):
		if mission in self.wormMissionDict[Game._game.player]:
			self.wormMissionDict[Game._game.player].remove(mission)

		if Game._game.isPlayingState():
			self.assignMissions(Game._game.player, mission)

	def notifyKill(self, worm):
		if worm == Game._game.player:
			return
		self.killedThisTurn.append(worm)
		self.checkMissions(["kill a worm", "kill _", "double kill", "triple kill", "above 50 damage"])

	def notifyHit(self, worm):
		if worm in self.hitThisTurn or worm == Game._game.player:
			self.checkMissions(["above 50 damage"])
			return
		self.hitThisTurn.append(worm)
		self.checkMissions(["hit a worm from _", "hit _", "hit 3 worms", "above 50 damage"])
		# check highest
		worms = []
		for w in PhysObj._worms:
			if w.alive and w.team != Game._game.player.team:
				worms.append(w)
		
		highestWorm = min(worms, key=lambda w: w.pos.y)
		if worm == highestWorm:
			self.checkMissions(["hit highest worm"])
		# check distance
		if distus(worm.pos, Game._game.player.pos) > 300 * 300:
			self.checkMissions(["hit distant worm"])

	def checkMissions(self, missionTypes):
		for mission in self.wormMissionDict[Game._game.player]:
			if mission.missionType in missionTypes:
				mission.check()

	def notifySick(self, worm):
		pass

	def endTurn(self):
		pass

	def cycle(self):
		# start of turn, assign missions to current worm
		self.assignMissions(Game._game.player)
		self.updateDisplay()
		self.killedThisTurn = []
		self.hitThisTurn = []
		self.sickThisTurn = []
		self.marker = None

		if "reach marker" in self.wormMissionDict[Game._game.player]:
			self.createMarker()

	def updateDisplay(self):
		for mission in self.wormMissionDict[Game._game.player]:
			mission.updateDisplay()

	def step(self):
		if Game._game.player == None:
			return
		for mission in self.wormMissionDict[Game._game.player]:
			mission.step()

	def draw(self, win: pygame.Surface):
		if Game._game.player == None:
			return
		currentWorm = Game._game.player
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
				string = string.replace("_", self.target.nameStr)

		string += " (" + str(self.reward) + ")"
		return string

	def complete(self, stringReplacement = None):
		string = self.missionType
		if "_" in string:
			string = string.replace("_", stringReplacement)
		comment = [
			{'text': 'mission '}, {'text': string, 'color': Game._game.player.team.color}, {'text': ' passed'}
		]

		GameEvents().post(EventComment(comment))
		Game._game.player.team.points += self.reward
		Game._game.addToScoreList(self.reward)

		self.completed = True
		MissionManager._log += f"{Game._game.player.nameStr} completed mission {self.missionType} {str(self.reward)}\n"
		
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
				self.complete(self.target.nameStr)
		elif self.missionType == "hit a worm from _":
			team = self.teamTarget
			for worm in missionManager.hitThisTurn:
				if worm.team == team:
					self.complete(team.name)
		elif self.missionType == "hit _":
			if self.target in missionManager.hitThisTurn:
				self.complete(self.target.nameStr)
		elif self.missionType == "above 50 damage":
			if Game._game.damageThisTurn >= 50:
				self.complete()

	def step(self):
		if self.marker:
			if distus(self.marker, Game._game.player.pos) < 20 * 20:
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
		currentWorm = Game._game.player
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
			drawDirInd(self.marker)
		# draw indicators
		elif self.target:
			drawDirInd(self.target.pos)
			drawTarget(self.target.pos)

	def updateDisplay(self):
		if not self.textSurf:
			self.textSurf = fonts.pixel5.render(self.missionToString(), False, WHITE)
			self.surf = pygame.Surface((self.textSurf.get_width() + 2, self.textSurf.get_height() + 2))

		# interpolate from Black to Green base on timer [0, 3 * fps]
		amount = (1 - self.timer / (3 * fps)) * 4
		bColor = (0, min(255 * amount, 255), 0)

		self.surf.fill(bColor)
		self.surf.blit(self.textSurf, (1,1))

def list2str(_list):
	string = ""
	for i, item in enumerate(_list):
		string += str(item)
		if not i == len(_list)-1:
			string += " "
	return string

def loadGame():
	file = open("wormsSave.txt", 'r')
	
	checkingForTeam = False
	checkingForWorm = False
	
	# teams
	teamCount = 0
	for line in file:
		if line == "team:\n":
			checkingForTeam = True
			continue
		if checkingForTeam:
			pass

def randomStartingWeapons(amount):
	startingWeapons = ["holy grenade", "gemino mine", "bee hive", "electro boom", "pokeball", "green shell", "guided missile", "fireworks"]
	if GameVariables().initial_variables.allow_air_strikes:
		startingWeapons.append("mine strike")
	for i in range(amount):
		for team in globals.team_manager.teams:
			chosen_weapon: Weapon = globals.weapon_manager.get_weapon(choice(startingWeapons))
			team.ammo(chosen_weapon, 1)
			if randint(0,2) >= 1:
				chosen_weapon = globals.weapon_manager.get_weapon(choice(["moon gravity", "teleport", "jet pack", "aim aid", "switch worms"]))
				team.ammo(chosen_weapon, 1)
			if randint(0,6) == 1:
				chosen_weapon = globals.weapon_manager.get_weapon(choice(["portal gun", "trampoline", "ender pearl"]))
				team.ammo(chosen_weapon, 3)

def randomWeaponsGive():
	for team in globals.team_manager.teams:
		for i, teamCount in enumerate(team.weaponCounter):
			if teamCount == -1:
				continue
			else:
				if randint(0,1) == 1:
					teamCount = randint(0,5)

def seek(obj, target, maxSpeed, maxForce ,arrival=False):
	force = tup2vec(target) - obj.pos
	desiredSpeed = maxSpeed
	if arrival:
		slowRadius = 50
		distance = force.getMag()
		if (distance < slowRadius):
			# desiredSpeed = smap(distance, 0, slowRadius, 0, maxSpeed)
			force.setMag(desiredSpeed)
	force.setMag(desiredSpeed)
	force -= obj.vel
	force.limit(maxForce)
	return force
	
def flee(obj, target, maxSpeed, maxForce):
	return seek(obj, target, maxSpeed, maxForce) * -1

def suddenDeath():
	sudden_death_modes = [Game._game.game_config.sudden_death_style]
	if Game._game.game_config.sudden_death_style == SuddenDeathMode.ALL:
		for mode in SuddenDeathMode:
			sudden_death_modes.append(mode)

	if SuddenDeathMode.PLAGUE in sudden_death_modes:
		for worm in PhysObj._worms:
			worm.sicken()
			if not worm.health == 1:
				worm.health = worm.health // 2
	if SuddenDeathMode.FLOOD in sudden_death_modes:
		string += " water rise!"
		Game._game.waterRise = True
	text = fonts.pixel10.render("sudden death", False, (220,0,0))
	Toast(pygame.transform.scale(text, tup2vec(text.get_size()) * 2), Toast.middle)

def cheatActive(code):
	code = code[:-1].lower()
	mouse_pos = globals.mouse_pos_in_world()

	if code == "gibguns":
		for team in globals.team_manager.teams:
			for i, teamCount in enumerate(team.weaponCounter):
				team.weaponCounter[i] = -1
		for weapon in WeaponManager._wm.weapons:
			# weapon [5] = 0 # todo
			pass
		Game._game.game_config.option_cool_down = False
	elif code == "suddendeath":
		suddenDeath()
	elif code == "wind":
		GameVariables().physics.wind = uniform(-1, 1)
	elif code == "goodbyecruelworld":
		boom(Game._game.player.pos, 100)
	elif code == "armageddon":
		Armageddon()
	elif code == "reset":
		Game._game.state, Game._game.nextState = RESET, RESET
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
		for worm in PhysObj._worms:
			# if worm in globals.team_manager.currentTeam.worms:
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
		globals.team_manager.currentTeam.ammo("jet pack", 6)
		globals.team_manager.currentTeam.ammo("rope", 6)
		globals.team_manager.currentTeam.ammo("ender pearl", 6)
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
		for worm in PhysObj._worms:
			if dist(worm.pos, pos) < closestDist:
				closestDist = dist(worm.pos, pos)
				closest = worm
		if closest:
			closest.damage(1000)
	elif "gib" in code:
		try:
			code = code.replace("gib", "")
			weapons = [w[0].replace('p', "").replace(' ', "").lower() for w in WeaponManager._wm.weapons]
			if code in weapons:
				globals.team_manager.currentTeam.ammo(WeaponManager._wm.weapons[weapons.index(code)][0], 1)
		except:
			pass
		
def gameDistable(): 
	Game._game.gameStable = False
	Game._game.gameStableCounter = 0

def pickVictim():
	Game._game.terminatorHit = False
	worms = []
	for w in PhysObj._worms:
		if w in globals.team_manager.currentTeam.worms:
			continue
		worms.append(w)
	if len(worms) == 0:
		Game._game.victim = None
		return
	Game._game.victim = choice(worms)
	wormComment = {'text': Game._game.victim.nameStr, 'color': Game._game.victim.team.color}
	comments = [
		[wormComment, {'text': ' is marked for death'}],
		[{'text': 'kill '}, wormComment],
		[wormComment, {'text': ' is the weakest link'}],
		[{'text': 'your target: '}, wormComment],
	]
	GameEvents().post(EventComment(choice(comments)))

def drawDirInd(pos):
	border = 20
	if not (pos[0] < GameVariables().cam_pos[0] - border/4 or pos[0] > (Vector(GameVariables().win_width, GameVariables().win_height) + GameVariables().cam_pos)[0] + border/4 or pos[1] < GameVariables().cam_pos[1] - border/4 or pos[1] > (Vector(GameVariables().win_width, GameVariables().win_height) + GameVariables().cam_pos)[1] + border/4):
		return

	cam = GameVariables().cam_pos + Vector(GameVariables().win_width//2, GameVariables().win_height//2)
	direction = pos - cam
	
	intersection = tup2vec(point2world((GameVariables().win_width, GameVariables().win_height))) + pos -  Vector(GameVariables().win_width, GameVariables().win_height)
	
	intersection[0] = min(max(intersection[0], border), GameVariables().win_width - border)
	intersection[1] = min(max(intersection[1], border), GameVariables().win_height - border)
	
	points = [Vector(0,2), Vector(0,-2), Vector(5,0)]
	angle = direction.getAngle()
	
	for point in points:
		point.rotate(angle)
	
	pygame.draw.polygon(win, (255,0,0), [intersection + i + normalize(direction) * 4 * sin(GameVariables().time_overall / 5) for i in points])

class Anim:
	_a = None
	def __init__(self):
		Anim._a = self
		Game._game.nonPhys.append(self)
		num = -1
		for folder in os.listdir("./anims"):
			if not os.path.isdir("./anims/" + folder):
				continue
			try:
				folderNum = int(folder)
			except:
				continue
			if folderNum > num:
				num = folderNum
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
			Game._game.nonPhysToRemove.append(self)
			print("record End")
	def draw(self, win: pygame.Surface):
		pass

################################################################################ State machine

def stateMachine():
	if Game._game.state == RESET:
		Game._game.gameStable = False
		Game._game.playerControl = False
		
		Game._game.create_new_game()
		Game._game.nextState = PLAYER_CONTROL_1
		Game._game.state = Game._game.nextState
	
	elif Game._game.state == PLAYER_CONTROL_1:
		Game._game.playerControl = True #can play
		Game._game.playerShootAble = True
		
		Game._game.nextState = PLAYER_CONTROL_2
	elif Game._game.state == PLAYER_CONTROL_2:
		Game._game.playerControl = True #can play
		Game._game.playerShootAble = False
		
		Game._game.gameStableCounter = 0
		Game._game.nextState = WAIT_STABLE
	elif Game._game.state == WAIT_STABLE:
		Game._game.playerControl = False #can play
		Game._game.playerShootAble = False
		if Game._game.gameStable:
			Game._game.gameStableCounter += 1
			if Game._game.gameStableCounter == 10:
				# next turn
				Game._game.gameStableCounter = 0
				TimeManager._tm.timeReset()
				cycleWorms()
				WeaponManager._wm.renderWeaponCount()
				Game._game.state = Game._game.nextState

		Game._game.nextState = PLAYER_CONTROL_1
	elif Game._game.state == FIRE_MULTIPLE:
		Game._game.playerControl = True #can play
		Game._game.playerShootAble = True
		
		if WeaponManager._wm.currentWeapon.name in WeaponManager._wm.multipleFires:
			Game._game.fireWeapon = True
			if not Game._game.shotCount == 0:
				Game._game.nextState = FIRE_MULTIPLE
	elif Game._game.state == WIN:
		Game._game.gameStableCounter += 1
		if Game._game.gameStableCounter == 30*3:
			return 1
			# subprocess.Popen("wormsLauncher.py -popwin", shell=True)
	return 0

################################################################################ Key bindings
def onKeyPressRight():
	if not Game._game.playerMoveable:
		return
	Game._game.player.facing = RIGHT
	if Game._game.player.shootAngle >= pi/2 and Game._game.player.shootAngle <= (3/2)*pi:
		Game._game.player.shootAngle = pi - Game._game.player.shootAngle
	GameVariables().cam_track = Game._game.player

def onKeyPressLeft():
	if not Game._game.playerMoveable:
		return
	Game._game.player.facing = LEFT
	if Game._game.player.shootAngle >= -pi/2 and Game._game.player.shootAngle <= pi/2:
		Game._game.player.shootAngle = pi - Game._game.player.shootAngle
	GameVariables().cam_track = Game._game.player

def onKeyPressSpace():
	if not globals.weapon_manager.can_shoot():
		print('cant shoot')
		return

	if WeaponManager._wm.currentWeapon.style == WeaponStyle.CHARGABLE:
		Game._game.energising = True
		Game._game.energyLevel = 0
		Game._game.fireWeapon = False
		if WeaponManager._wm.currentWeapon in ["homing missile", "seeker"] and not HomingMissile.showTarget:
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
	if globals.weapon_manager.can_shoot():
		if Game._game.timeTravel:
			TimeTravel._tt.timeTravelPlay()
			Game._game.energyLevel = 0
		
		# chargeable
		elif WeaponManager._wm.currentWeapon.style == WeaponStyle.CHARGABLE and Game._game.energising:
			Game._game.fireWeapon = True
		
		# putable & guns
		elif (WeaponManager._wm.currentWeapon.style in [WeaponStyle.PUTABLE, WeaponStyle.GUN]):
			Game._game.fireWeapon = True
			Game._game.playerShootAble = False
		
		elif (WeaponManager._wm.currentWeapon.style in [WeaponStyle.UTILITY]):
			fireUtility()
			
		Game._game.energising = False
	elif Sheep.trigger == False:
		Sheep.trigger = True

def onKeyPressTab():
	if not Game._game.state == PLAYER_CONTROL_1:
		if Game._game.state == FIRE_MULTIPLE and Game._game.switchingWorms:
			switchWorms()
		return
	if WeaponManager._wm.currentWeapon.name == "drill missile":
		DrillMissile.mode = not DrillMissile.mode
		if DrillMissile.mode:
			FloatingText(Game._game.player.pos + Vector(0,-5), "drill mode", (20,20,20))
		else:
			FloatingText(Game._game.player.pos + Vector(0,-5), "rocket mode", (20,20,20))
		WeaponManager._wm.renderWeaponCount()
	elif WeaponManager._wm.currentWeapon.name == "venus fly trap":
		PlantBomb.mode = (PlantBomb.mode + 1) % 2
		if PlantBomb.mode == PlantBomb.venus:
			FloatingText(Game._game.player.pos + Vector(0,-5), "venus fly trap", (20,20,20))
		elif PlantBomb.mode == PlantBomb.bomb:
			FloatingText(Game._game.player.pos + Vector(0,-5), "plant mode", (20,20,20))
	elif WeaponManager._wm.currentWeapon.name == "long bow":
		LongBow._sleep = not LongBow._sleep
		if LongBow._sleep:
			FloatingText(Game._game.player.pos + Vector(0,-5), "sleeping", (20,20,20))
		else:
			FloatingText(Game._game.player.pos + Vector(0,-5), "regular", (20,20,20))
	elif WeaponManager._wm.currentWeapon.name == "girder":
		Game._game.girderAngle += 45
		if Game._game.girderAngle == 180:
			Game._game.girderSize = 100
		if Game._game.girderAngle == 360:
			Game._game.girderSize = 50
			Game._game.girderAngle = 0
	elif WeaponManager._wm.currentWeapon.is_fused:
		GameVariables().fuse_time += fps
		if GameVariables().fuse_time > fps*4:
			GameVariables().fuse_time = fps
		string = "delay " + str(GameVariables().fuse_time//fps) + " sec"
		FloatingText(Game._game.player.pos + Vector(0,-5), string, (20,20,20))
		WeaponManager._wm.renderWeaponCount()
	elif WeaponManager._wm.currentWeapon.category == WeaponCategory.AIRSTRIKE:
		Game._game.airStrikeDir *= -1
	elif Game._game.switchingWorms:
		switchWorms()

def onKeyPressEnter():
	# jump
	if Game._game.player.stable and Game._game.player.health > 0:
		Game._game.player.vel += Vector(cos(Game._game.player.shootAngle), sin(Game._game.player.shootAngle)) * JUMP_VELOCITY
		Game._game.player.stable = False

################################################################################ Main

def gameMain(game_config: GameConfig=None):
	global scalingFactor, win

	Game(game_config)
	TimeManager()
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
				if Game._game.state == PLAYER_CONTROL_1 and WeaponManager._wm.currentWeapon.style == WeaponStyle.CLICKABLE:
					fireClickable()
				if Game._game.state == PLAYER_CONTROL_1 and WeaponManager._wm.currentWeapon in ["homing missile", "seeker"] and not Game._game.radial_weapon_menu:
					mouse_pos = globals.mouse_pos_in_world()
					HomingMissile.Target.x, HomingMissile.Target.y = mouse_pos.x, mouse_pos.y
					HomingMissile.showTarget = True

			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)
				pass
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
				# this is the next Game._game.state after placing all worms
				if Game._game.state == PLAYER_CONTROL_1:
					if Game._game.radial_weapon_menu is None:
						if WeaponManager._wm.can_open_menu():
							weaponMenuRadialInit()
					else:
						Game._game.radial_weapon_menu = None
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll down
				if not Game._game.radial_weapon_menu:
					scalingFactor *= 1.1
					globals.scalingFactor = scalingFactor
					if scalingFactor >= globals.scalingMax:
						scalingFactor = globals.scalingMax
						globals.scalingFactor = scalingFactor
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll up
				if not Game._game.radial_weapon_menu:
					scalingFactor *= 0.9
					globals.scalingFactor = scalingFactor
					if scalingFactor <= globals.scalingMin:
						scalingFactor = globals.scalingMin
						globals.scalingFactor = scalingFactor
	
			# key press
			if event.type == pygame.KEYDOWN:
				# controll worm, jump and facing
					if Game._game.player and Game._game.playerControl:
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
						toastInfo()
					if event.key == pygame.K_F2:
						Worm.healthMode = (Worm.healthMode + 1) % 2
						if Worm.healthMode == 1:
							for worm in PhysObj._worms:
								worm.healthStr = fonts.pixel5.render(str(worm.health), False, worm.team.color)
					if event.key == pygame.K_F3:
						MapManager().draw_ground_secondary = not MapManager().draw_ground_secondary
					if event.key == pygame.K_m:
						pass
						# TimeSlow()
					if event.key == pygame.K_RCTRL or event.key == pygame.K_LCTRL:
						scalingFactor = globals.scalingMax
						globals.scalingFactor = scalingFactor
						if GameVariables().cam_track == None:
							GameVariables().cam_track = Game._game.player

					Game._game.cheatCode += event.unicode
					if event.key == pygame.K_EQUALS:
						cheatActive(Game._game.cheatCode)
						Game._game.cheatCode = ""
			if event.type == pygame.KEYUP:
				# fire release
				if event.key == pygame.K_SPACE:
					onKeyReleaseSpace()
		keys = pygame.key.get_pressed()
		#key hold:
		if Game._game.player and Game._game.playerControl and Game._game.playerMoveable:
			if keys[pygame.K_RIGHT]:
				Game._game.actionMove = True
			if keys[pygame.K_LEFT]:
				Game._game.actionMove = True
			# fire hold
			if Game._game.playerShootAble and (keys[pygame.K_SPACE]) and WeaponManager._wm.currentWeapon.style == WeaponStyle.CHARGABLE and Game._game.energising:
				onKeyHoldSpace()
		
		if pause:
			result = [0]
			# todo here False V
			args = {"showPoints": False, "teams":globals.team_manager.teams}
			pauseMenu(args, result)
			pause = not pause
			if result[0] == 1:
				run = False
			continue
		
		result = stateMachine()
		if result == 1:
			run = False

		if Game._game.state in [RESET]:
			continue

		# use edge map scroll
		if pygame.mouse.get_focused():
			mousePos = pygame.mouse.get_pos()
			scroll = Vector()
			if mousePos[0] < EDGE_BORDER:
				scroll.x -= MAP_SCROLL_SPEED * (2.5 - scalingFactor / 2)
			if mousePos[0] > screenWidth - EDGE_BORDER:
				scroll.x += MAP_SCROLL_SPEED * (2.5 - scalingFactor / 2)
			if mousePos[1] < EDGE_BORDER:
				scroll.y -= MAP_SCROLL_SPEED * (2.5 - scalingFactor / 2)
			if mousePos[1] > screenHeight - EDGE_BORDER:
				scroll.y += MAP_SCROLL_SPEED * (2.5 - scalingFactor / 2)
			if scroll != Vector():
				GameVariables().cam_track = Camera(GameVariables().cam_pos + Vector(GameVariables().win_width, GameVariables().win_height)/2 + scroll)
		
		# handle scale:
		oldSize = (GameVariables().win_width, GameVariables().win_height)
		GameVariables().win_width += (globals.screenWidth / scalingFactor - GameVariables().win_width) * 0.2
		GameVariables().win_height += (globals.screenHeight / scalingFactor - GameVariables().win_height) * 0.2
		GameVariables().win_width = int(GameVariables().win_width)
		GameVariables().win_height = int(GameVariables().win_height)
		
		if oldSize != (GameVariables().win_width, GameVariables().win_height):
			globals.win = pygame.Surface((GameVariables().win_width, GameVariables().win_height))
			win = globals.win
			globals.GameVariables().win_width = GameVariables().win_width
			globals.GameVariables().win_height = GameVariables().win_height
			updateWin(win, scalingFactor)
		
		# handle position:
		if GameVariables().cam_track:
			# actual position target:
			### GameVariables().cam_pos = GameVariables().cam_track.pos - Vector(GameVariables().win_width, GameVariables().win_height)/2
			# with smooth transition:
			GameVariables().cam_pos += ((GameVariables().cam_track.pos - Vector(int(globals.screenWidth / scalingFactor), int(globals.screenHeight / scalingFactor))/2) - GameVariables().cam_pos) * 0.2
		
		# constraints:
		if GameVariables().cam_pos[1] < 0: GameVariables().cam_pos[1] = 0
		if GameVariables().cam_pos[1] >= Game._game.map_manager.game_map.get_height() - GameVariables().win_height: GameVariables().cam_pos[1] = Game._game.map_manager.game_map.get_height() - GameVariables().win_height
		# if GameVariables().config.option_closed_map or Game._game.darkness:
		# 	if GameVariables().cam_pos[0] < 0:
		# 		GameVariables().cam_pos[0] = 0
		# 	if GameVariables().cam_pos[0] >= Game._game.map_manager.game_map.get_width() - GameVariables().win_width:
		# 		GameVariables().cam_pos[0] = Game._game.map_manager.game_map.get_width() - GameVariables().win_width
		
		if Earthquake.earthquake > 0:
			GameVariables().cam_pos[0] += Earthquake.earthquake * 25 * sin(GameVariables().time_overall)
			GameVariables().cam_pos[1] += Earthquake.earthquake * 15 * sin(GameVariables().time_overall * 1.8)
		
		# Fire
		if Game._game.fireWeapon and Game._game.playerShootAble: fire()
		
		# step:
		Game._game.step()
		Game._game.gameStable = True
		for p in PhysObj._reg:
			p.step()
			if not p.stable:
				gameDistable()
		for p in PhysObj._toRemove:
			try:
				PhysObj._reg.remove(p)
			except ValueError:
				print("remove from phys list error")
		PhysObj._toRemove = []
		for f in Game._game.nonPhys:
			f.step()
		for f in Game._game.nonPhysToRemove:
			try:
				Game._game.nonPhys.remove(f)
			except ValueError:
				print("remove from nonphys list error")
		Game._game.nonPhysToRemove = []

		# step effects
		EffectManager().step()
		
		for t in Toast._toasts:
			t.step()
		SmokeParticles._sp.step()
		GasParticles._sp.step()
		if Game._game.timeTravel: 
			TimeTravel._tt.step()
			
		# camera for wait to stable:
		if Game._game.state == WAIT_STABLE and GameVariables().time_overall % 20 == 0:
			for worm in PhysObj._worms:
				if worm.stable:
					continue
				else:
					GameVariables().cam_track = worm
					break
		
		# advance timer
		TimeManager._tm.step()
		Game._game.background.step()
		
		if ArenaManager._arena: ArenaManager._arena.step()
		if MissionManager._mm: MissionManager._mm.step()
		
		# menu step
		if Game._game.radial_weapon_menu:
			Game._game.radial_weapon_menu.step()
		
		# reset actions
		Game._game.actionMove = False

		wind_flag.step()
		commentator.step()


		# draw:
		Game._game.background.draw(win)
		drawLand()
		for p in PhysObj._reg: 
			p.draw(win)
		for f in Game._game.nonPhys:
			f.draw(win)
		
		# draw effects
		EffectManager().draw(win)

		Game._game.background.drawSecondary(win)
		for t in Toast._toasts:
			t.draw(win)
		
		if ArenaManager._arena: ArenaManager._arena.draw(win)
		SmokeParticles._sp.draw(win)
		GasParticles._sp.draw(win)

		# if Game._game.darkness and Game._game.map_manager.dark_mask: win.blit(Game._game.map_manager.dark_mask, (-int(GameVariables().cam_pos[0]), -int(GameVariables().cam_pos[1])))
		# draw shooting indicator
		if Game._game.player and Game._game.state in [PLAYER_CONTROL_1, PLAYER_CONTROL_2, FIRE_MULTIPLE] and Game._game.player.health > 0:
			Game._game.player.drawCursor()
			if Game._game.aimAid and WeaponManager._wm.currentWeapon.style == WeaponStyle.GUN:
				p1 = vectorCopy(Game._game.player.pos)
				p2 = p1 + Vector(cos(Game._game.player.shootAngle), sin(Game._game.player.shootAngle)) * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))
			i = 0
			while i < 20 * Game._game.energyLevel:
				cPos = vectorCopy(Game._game.player.pos)
				angle = Game._game.player.shootAngle
				pygame.draw.line(win, (0,0,0), point2world(cPos), point2world(cPos + vectorFromAngle(angle) * i))
				i += 1
		
		Game._game.drawExtra()
		Game._game.drawLayers()
		
		# HUD
		wind_flag.draw(win)
		TimeManager._tm.draw(win)
		if WeaponManager._wm.surf: win.blit(WeaponManager._wm.surf, (25, 5))
		commentator.draw(win)
		# draw weapon indicators
		WeaponManager._wm.drawWeaponIndicators()
		WeaponManager._wm.draw(win)
		
		# draw health bar
		globals.team_manager.step()
		globals.team_manager.draw(win)
		
		if Game._game.gameMode == GameMode.TERMINATOR and Game._game.victim and Game._game.victim.alive:
			drawTarget(Game._game.victim.pos)
			drawDirInd(Game._game.victim.pos)
		if Game._game.gameMode == GameMode.TARGETS and Game._game.player:
			for target in ShootingTarget._reg:
				drawDirInd(target.pos)
		if Game._game.gameMode == GameMode.MISSIONS:
			if MissionManager._mm: MissionManager._mm.draw(win)
		
		
		# weapon menu:
		# move menus
		if len(Toast._toasts) > 0:
			for t in Toast._toasts:
				if t.mode == Toast.bottom:
					t.updateWinPos((GameVariables().win_width/2, GameVariables().win_height))
				elif t.mode == Toast.middle:
					t.updateWinPos(Vector(GameVariables().win_width/2, GameVariables().win_height/2) - tup2vec(t.surf.get_size())/2)
		
		if Game._game.radial_weapon_menu:
			Game._game.radial_weapon_menu.draw(win)

		# draw kill list
		if Game._game.gameMode in [GameMode.POINTS, GameMode.TARGETS, GameMode.TERMINATOR, GameMode.MISSIONS]:
			while len(Game._game.killList) > 8:
				Game._game.killList.pop(-1)
			for i, killed in enumerate(Game._game.killList):
				win.blit(killed[0], (5, GameVariables().win_height - 20 - i * (killed[0].get_height() + 1)))
		
		# debug:
		if damageText[0] != Game._game.damageThisTurn: damageText = (Game._game.damageThisTurn, fonts.pixel5_halo.render(str(int(Game._game.damageThisTurn)), False, GameVariables().initial_variables.hud_color))
		win.blit(damageText[1], ((int(5), int(GameVariables().win_height -5 -damageText[1].get_height()))))
		
		# draw loading screen
		if Game._game.state in [RESET]:
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
