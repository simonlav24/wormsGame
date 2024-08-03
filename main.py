from math import pi, cos, sin, atan2, sqrt, exp, degrees, radians, copysign, fabs
from random import shuffle ,randint, uniform, choice, sample
from vector import *
import globals
from mainMenus import renderMountains, renderCloud, feels, grabMapsFrom, mainMenu, pauseMenu, initGui, updateWin
from pygame import gfxdraw
import pygame
import argparse
import xml.etree.ElementTree as ET
import os
from typing import Type, Any

from Constants import *
from Common import *
from Effects import *
from Hud import *
from Gui import *
from tempFuncs import *
from MapManager import *
from Weapons.WeaponManager import *

def getGlobals():
	global fpsClock, fps, pixelFont5, pixelFont5halo, pixelFont10, screenWidth, screenHeight, scalingFactor, winWidth, winHeight, win, screen
	fpsClock = globals.fpsClock
	fps = globals.fps
	pixelFont5halo = globals.pixelFont5halo
	pixelFont5 = globals.pixelFont5
	pixelFont10 = globals.pixelFont10
	screenWidth = globals.screenWidth
	screenHeight = globals.screenHeight
	scalingFactor = globals.scalingFactor
	winWidth = globals.winWidth
	winHeight = globals.winHeight
	win = globals.win
	screen = globals.screen
globals.globalsInit()
initGui()
getGlobals()

class Game:
	_game = None
	def __init__(self, argumentsString=None):
		Game._game = self
		globals.game_manager = self

		self.map_manager = MapManager()

		self.clearLists()

		self.initiateGameSettings()
		self.initiateGameVariables()

		self.suddenDeathStyle = []
		self.roundCounter = 0
		self.damageThisTurn = 0
		self.mostDamage = (0, None)

		if argumentsString:
			self.evaluateArgs(argumentsString.split())
		else:
			self.evaluateArgs()

		self.extra = []
		self.layersCircles = [[], [], []]
		self.layersLines = [] #color, start, end, width, delay

		self.nonPhys = []
		self.nonPhysToRemove = []

		self.girderAngle = 0
		self.girderSize = 50

		self.airStrikeDir = RIGHT
		self.airStrikeSpr = pixelFont10.render(">>>", False, BLACK)

		self.killList = []
		self.lstep = 0
		self.lstepmax = 1

		self.state = RESET
		self.nextState = RESET
		self.loadingSurf = pixelFont10.render("Simon's Worms Loading", False, WHITE)
		self.gameStable = False
		self.playerControl = False
		self.playerMoveable = True
		self.playerControlPlacing = False
		self.playerShootAble = False
		self.gameStableCounter = 0

		self.endGameDict = None

		self.imageBlood = pygame.image.load("assets/blood.png").convert_alpha()
		self.imageHole = pygame.image.load("assets/hole.png").convert_alpha()
		self.sprites = pygame.image.load("assets/sprites.png").convert_alpha()
		self.imageMjolnir = pygame.Surface((24,31), pygame.SRCALPHA)
		self.imageMjolnir.blit(self.sprites, (0,0), (100, 32, 24, 31))
		self.weaponHold = pygame.Surface((16,16), pygame.SRCALPHA)

		self.radial_weapon_menu: RadialMenu = None

		self.dt = 1

	@property
	def win(self) -> pygame.Surface:
		return globals.win

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
			self.allowAirStrikes = False
			for team in TeamManager._tm.teams:
				for i, _ in enumerate(team.weaponCounter):
					if WeaponManager._wm.weapons[i].category == WeaponCategory.AIRSTRIKE:
						team.weaponCounter[i] = 0

		# select current team
		TeamManager._tm.currentTeam = TeamManager._tm.teams[0]
		TeamManager._tm.teamChoser = TeamManager._tm.teams.index(TeamManager._tm.currentTeam)

		# place worms
		randomPlacing()
		
		# place objects
		if not self.diggingMatch:
			amount = randint(2,4)
			for _ in range(amount):
				mine = place_object(Mine, None, True)
				mine.damp = 0.1

		amount = randint(2,4)
		for _ in range(amount):
			place_object(PetrolCan, None, False)

		if not Game._game.diggingMatch:
			amount = randint(0, 2)
			for _ in range(amount):
				place_object(PlantBomb, ((0,0), (0,0), 0, PlantBomb.venus), False)

		# give random legendary starting weapons:
		randomStartingWeapons(1)
		if Game._game.args.flying:
			for team in TeamManager._tm.teams:
				team.ammo("jet pack", 20)
				team.ammo("switch worms", 20)

		# choose starting worm
		w = TeamManager._tm.currentTeam.worms.pop(0)
		TeamManager._tm.currentTeam.worms.append(w)
		
		TeamManager._tm.nWormsPerTeam = 0
		for team in TeamManager._tm.teams:
			if len(team) > TeamManager._tm.nWormsPerTeam:
				TeamManager._tm.nWormsPerTeam = len(team)
		
		if Game._game.randomCycle:
			w = choice(TeamManager._tm.currentTeam.worms)
		
		Game._game.objectUnderControl = w
		Game._game.camTrack = w

		# health calc:
		HealthBar._healthBar.calculateInit()

		# reset time
		TimeManager._tm.timeReset()
		WeaponManager._wm.switchWeapon(WeaponManager._wm.currentWeapon, force=True)

		# handle game mode
		self.init_handle_game_mode()

	def init_handle_game_mode(self) -> None:
		''' on init, handle game mode parameter and variables '''
		# targets:
		if Game._game.gameMode == TARGETS:
			for i in range(ShootingTarget.numTargets):
				ShootingTarget()

		# digging match
		if Game._game.diggingMatch:
			for _ in range(80):
				mine = place_object(Mine, None)
				mine.damp = 0.1
			# more digging
			for team in TeamManager._tm.teams:
				team.ammo("minigun", 5)
				team.ammo("bunker buster", 3)
				team.ammo("laser gun", 3)
			Game._game.mapClosed = True

		# david and goliath
		if Game._game.gameMode == DAVID_AND_GOLIATH:
			for team in TeamManager._tm.teams:
				length = len(team.worms)
				for i in range(length):
					if i == 0:
						team.worms[i].health = Game._game.initialHealth + (length - 1) * (Game._game.initialHealth//2)
						team.worms[i].healthStr = pixelFont5.render(str(team.worms[i].health), False, team.worms[i].team.color)
					else:
						team.worms[i].health = (Game._game.initialHealth//2)
						team.worms[i].healthStr = pixelFont5.render(str(team.worms[i].health), False, team.worms[i].team.color)
			Game._game.initialHealth = TeamManager._tm.teams[0].worms[0].health
		
		# disable points in battle
		if Game._game.gameMode in [BATTLE]:
			HealthBar.drawPoints = False

		if Game._game.darkness:
			Game._game.HUDColor = WHITE
			WeaponManager._wm.renderWeaponCount()
			for team in TeamManager._tm.teams:
				team.ammo("flare", 3)

		if Game._game.gameMode == CAPTURE_THE_FLAG:
			place_object(Flag, None)

		if Game._game.gameMode == ARENA:
			ArenaManager()

		if Game._game.gameMode == MISSIONS:
			MissionManager()
			Game._game.turnTime = Game._game.turnTime + 10
			MissionManager._mm.cycle()
		
		if Game._game.gameMode == TERMINATOR:
			pickVictim()
			

	def point_to_world(self, point):
		return (int(point[0]) - int(self.camPos[0]), int(point[1]) - int(self.camPos[1]))

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
		Water.layerTop = None
		Water.layerMiddle = None
		Water.layerBottom = None

		ArenaManager._arena = None
		MissionManager._mm = None
	
	def createMapSurfaces0(self, dims):
		"""
		create all map related surfaces
		"""
		self.mapWidth = dims[0]
		self.mapHeight = dims[1]
		self.gameMap = pygame.Surface((self.mapWidth, self.mapHeight))
		self.gameMap.fill(SKY)
		self.wormCol = pygame.Surface((self.mapWidth, self.mapHeight))
		self.wormCol.fill(SKY)
		self.extraCol = pygame.Surface((self.mapWidth, self.mapHeight))
		self.extraCol.fill(SKY)

		self.ground = pygame.Surface((self.mapWidth, self.mapHeight)).convert_alpha()
		self.groundSec = pygame.Surface((self.mapWidth, self.mapHeight)).convert_alpha()
		if self.darkness:
			self.darkMask = pygame.Surface((self.mapWidth, self.mapHeight)).convert_alpha()

	def create_map(self) -> None:
		''' create game map '''
		custom_height = 512
		if self.args.map_ratio != -1:
			custom_height = self.args.map_ratio

		if self.diggingMatch:
			self.map_manager.create_map_digging(custom_height)
		elif 'PerlinMaps' in self.args.map_choice:
			self.map_manager.create_map_image(self.args.map_choice, custom_height, True)
		else:
			self.map_manager.create_map_image(self.args.map_choice, custom_height, self.args.recolor_ground)
	
	def initiateGameSettings(self):
		self.turnTime = 45 # amount of time for each turn
		self.retreatTime = 5 # amount of time for retreat
		self.wormDieTime = 3 # amount of time after worm dies
		self.shockRadius = 1.5 # radius of shock wave
		self.globalGravity = 0.2 # global gravity strength
		self.edgeBorder = 65 # border for mouse scroll
		self.mapScrollSpeed = 35 # speed of map scroll
		self.jetPackFuel = 100 # fuel for jetpack
		self.lightRadius = 70 # radius of light in darkness mode
		self.damageMult = 0.8 # damage multiplier
		self.fallDamageMult = 1 # fall damage multiplier
		self.windMult = 1.5 # Game._game.wind strength multiplier
		self.radiusMult = 1 # radius multiplier
		self.dampMult = 1.5 # dampening multiplier
		self.initialWaterLevel = 50 # initial water level height
		self.weaponSet = "default"
		self.fallVelocityHurt = 5
		self.jumpVelocity = 3
	
	def initiateGameVariables(self):
		self.deployPacks = True # whether to deploy packs 
		self.drawHealthBar = True # whether to draw health bar
		self.moreWindAffected = False # whether more objects affected by wind
		self.randomWeapons = False # initial weapons are random
		self.allowAirStrikes = True # whether to allow air strikes
		self.drawGroundSec = True # whether to draw secondary ground 
		self.waterRise = False # whether water rises at the end of each turn
		self.waterRising = False # water rises in current state
		self.raoning = False  # raons advancing in current state
		self.deploying = False # deploying pack in current state
		self.sentring = False # sentry guns active in current state
		self.deployingArtifact = False  # deploying artifacts in current state
		self.victim = None # worm targeted for termination
		self.terminatorHit = False # whether terminator hit in current turn
		self.cheatCode = "" # cheat code
		self.HUDColor = WHITE # color of HUD
		self.holdArtifact = True # whether to hold artifact
		self.worldArtifacts = [MJOLNIR, PLANT_MASTER, AVATAR, MINECRAFT] # world artifacts
		self.trigerArtifact = False # whether to trigger artifact drop next turn
		self.shotCount = 0 # number of gun shots fired

		self.lights = [] # list of lights in darkenss mode
		self.camPos = Vector(0,0) # camera position
		self.camTrack = None # object to track
		self.objectUnderControl = None # object under control
		self.energising = False
		self.energyLevel = 0
		self.fireWeapon = False

		self.wind = uniform(-1,1)
		self.actionMove = False

		self.aimAid = False
		self.switchingWorms = False
		self.timeTravel = False
		self.megaTrigger = False
		self.fuseTime = fps*2
	
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
			surf.blit(Game._game.sprites, (i * 16, 0), (64,80,16,16))
		surfGround = pygame.transform.rotate(surf, self.girderAngle)
		self.map_manager.ground_map.blit(surfGround, (int(pos[0] - surfGround.get_width()/2), int(pos[1] - surfGround.get_height()/2)) )
		surf.fill(GRD)
		surfMap = pygame.transform.rotate(surf, self.girderAngle)
		self.map_manager.game_map.blit(surfMap, (int(pos[0] - surfMap.get_width()/2), int(pos[1] - surfMap.get_height()/2)) )
	
	def drawGirderHint(self):
		surf = pygame.Surface((self.girderSize, 10)).convert_alpha()
		for i in range(self.girderSize // 16 + 1):
			surf.blit(Game._game.sprites, (i * 16, 0), (64,80,16,16))
		surf.set_alpha(100)
		surf = pygame.transform.rotate(surf, self.girderAngle)
		pos = pygame.mouse.get_pos()
		pos = Vector(pos[0]/scalingFactor , pos[1]/scalingFactor )
		win.blit(surf, (int(pos[0] - surf.get_width()/2), int(pos[1] - surf.get_height()/2)))
	
	def drawTrampolineHint(self):
		surf = pygame.Surface((24, 7), pygame.SRCALPHA)
		surf.blit(Game._game.sprites, (0,0), (100, 117, 24, 7))
		position = self.objectUnderControl.pos + vectorFromAngle(self.objectUnderControl.shootAngle, 20)
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
	
	def evaluateArgs(self, argumentsString=None):
		args = parseArgs(argumentsString)
		self.mapChoice = args.map_choice
		self.gameMode = args.game_mode
		self.fortsMode = args.forts
		self.initialHealth = args.initial_health
		self.diggingMatch = args.digging
		self.darkness = args.darkness
		self.packMult = args.pack_mult
		self.wormsPerTeam = args.worms_per_team
		self.useListMode = args.used_list
		self.mapClosed = args.closed_map
		self.warpedMode = args.warped
		self.randomCycle = args.random
		self.unlimitedMode = args.unlimited
		self.manualPlace = args.place
		self.roundsTillSuddenDeath = args.sudden_death
		self.artifactsMode = args.artifacts
		if args.sudden_death_tsunami:
			self.suddenDeathStyle.append(TSUNAMI)
		if args.sudden_death_plague:
			self.suddenDeathStyle.append(PLAGUE)
		if args.feel_index == -1:
			args.feel_index = randint(0, len(feels) - 1)
		self.feelColor = feels[args.feel_index]
		self.args = args
	
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
		if len(self.killList) > 0 and self.killList[0][1] == self.objectUnderControl.nameStr:
			amount += self.killList[0][2]
			self.killList.pop(0)
		string = self.objectUnderControl.nameStr + ": " + str(amount)
		self.killList.insert(0, (pixelFont5halo.render(string, False, self.HUDColor), self.objectUnderControl.nameStr, amount))

	def lstepper(self):
		self.lstep += 1
		pos = (winWidth/2 - Game._game.loadingSurf.get_width()/2, winHeight/2 - Game._game.loadingSurf.get_height()/2)
		width = Game._game.loadingSurf.get_width()
		height = Game._game.loadingSurf.get_height()
		pygame.draw.rect(win, (255,255,255), ((pos[0], pos[1] + 20), ((self.lstep / self.lstepmax)*width, height)))
		screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
		pygame.display.update()
	
	def isPlayingState(self):
		return self.state in [PLAYER_CONTROL_1, PLAYER_CONTROL_2, FIRE_MULTIPLE]

def parseArgs(arguments=None):
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-f", "--forts", type=bool, nargs='?', const=True, default=False, help="Activate forts mode")
	parser.add_argument("-ih", "--initial_health", default=100, help="Initial health", type=int)
	parser.add_argument("-gm", "--game_mode", default=0, help="Game Mode", type=int)
	parser.add_argument("-dig", "--digging", type=bool, nargs='?', const=True, default=False, help="Activate Digging mode")
	parser.add_argument("-dark", "--darkness", type=bool, nargs='?', const=True, default=False, help="Activate Darkness mode")
	parser.add_argument("-pm", "--pack_mult", default=1, help="Number of packs", type=int)
	parser.add_argument("-wpt", "--worms_per_team", default=8, help="Worms per team", type=int)
	parser.add_argument("-map", "--map_choice", default="", help="world map choice", type=str)
	parser.add_argument("-ratio", "--map_ratio", default=-1, help="world map ratio", type=int)
	parser.add_argument("-used", "--used_list", type=bool, nargs="?", const=True, default=False, help="Activate Used List mode")
	parser.add_argument("-closed", "--closed_map", type=bool, nargs="?", const=True, default=False, help="Activate closed gameMap mode")
	parser.add_argument("-warped", "--warped", type=bool, nargs='?', const=True, default=False, help="Activate warped gameMap mode")
	parser.add_argument("-random", "--random", default=0, help="Activate random worms cycle mode", type=int)
	parser.add_argument("-rg", "--recolor_ground", type=bool, nargs='?', const=True, default=False, help="color ground in digging color")
	parser.add_argument("-u", "--unlimited", type=bool, nargs='?', const=True, default=False, help="Activate unlimited mode")
	parser.add_argument("-place", "--place", type=bool, nargs='?', const=True, default=False, help="manually placing worms")
	parser.add_argument("-sd", "--sudden_death", default=-1, help="rounds untill sudden death", type=int)
	parser.add_argument("-sdt", "--sudden_death_tsunami", type=bool, nargs='?', const=True, default=False, help="tsunami sudden death style")
	parser.add_argument("-sdp", "--sudden_death_plague", type=bool, nargs='?', const=True, default=False, help="plague sudden death style")
	parser.add_argument("-art", "--artifacts", type=bool, nargs='?', const=True, default=False, help="artifacts mode")
	parser.add_argument("-feel", "--feel_index", default=-1, help="choice of background feel color", type=int)
	parser.add_argument("-nm", "--no-menu", type=bool, nargs='?', const=True, default=False, help="no main menu")
	parser.add_argument("-ws", "--weapon-set", default="", help="weapon set name")
	parser.add_argument("-fly", "--flying", type=bool, nargs='?', const=True, default=False, help="more flying tools")
	if arguments:
		args = parser.parse_args(args=arguments)
	else:
		args = parser.parse_args()

	return args

def drawLand():
	if Game._game.map_manager.game_map.get_width() == 0:
		return
	if Game._game.drawGroundSec: win.blit(Game._game.map_manager.ground_secondary, point2world((0,0)))
	win.blit(Game._game.map_manager.ground_map, point2world((0,0)))
	
	if Game._game.darkness:
		Game._game.map_manager.dark_mask.fill(DARK_COLOR)
		if Game._game.objectUnderControl:
			pygame.draw.circle(Game._game.map_manager.dark_mask, (0,0,0,0), Game._game.objectUnderControl.pos.vec2tupint(), Game._game.lightRadius)
	
		for light in Game._game.lights:
			pygame.draw.circle(Game._game.map_manager.dark_mask, light[3], (int(light[0]), int(light[1])), int(light[2]))
		Game._game.lights = []
	
	Game._game.map_manager.worm_col_map.fill(SKY)
	Game._game.map_manager.objects_col_map.fill(SKY)

def boom(pos, radius, debries = True, gravity = False, fire = False):
	if not fire: radius *= Game._game.radiusMult
	boomPos = Vector(pos[0], pos[1])
	# sample Game._game.map_manager.ground_map colors:
	if debries:
		colors = []
		for _ in range(10):
			sample = (pos + vectorUnitRandom() * uniform(0,radius)).vec2tupint()
			if isOnMap(sample):
				color = Game._game.map_manager.ground_map.get_at(sample)
				if not color == SKY:
					colors.append(color)
		if len(colors) == 0:
			colors = Blast._color

	# Game._game.map_manager.ground_map delete
	if not fire:
		Explossion(pos, radius * 1.2)
		if radius > 25:
			Earthquake(int(0.3 * fps), True, min(0.5, 0.02 * radius - 0.3))
		
	# draw burn:
	stain(pos, Game._game.imageHole, (int(radius*4),int(radius*4)), True)
	
	pygame.draw.circle(Game._game.map_manager.game_map, SKY, pos.vec2tupint(), int(radius))
	pygame.draw.circle(Game._game.map_manager.ground_map, SKY, pos.vec2tupint(), int(radius))
	if not fire:
		pygame.draw.circle(Game._game.map_manager.ground_secondary, SKY, pos.vec2tupint(), int(radius * 0.7))
	
	listToCheck = PhysObj._reg if not fire else PhysObj._worms
	
	for p in listToCheck:
		if not p.boomAffected:
			continue
		
		totalRadius = radius * Game._game.shockRadius
		if distus(p.pos, boomPos) < totalRadius * totalRadius:
			distance = dist(p.pos, boomPos)
			# shockwave
			direction = (p.pos - boomPos).normalize()
			p.vel += direction * - 0.5 * (1/Game._game.shockRadius) * (distance - radius * Game._game.shockRadius) * 1.3
			p.stable = False
			# damage
			if p.health:
				if p.health > 0:
					dmg = -(1/Game._game.shockRadius)*(distance - radius * Game._game.shockRadius) * 1.2
					p.damage(dmg)
			if p in PhysObj._worms:
				if gravity:
					p.gravity = p.gravity * -1
				if not fire:
					Game._game.camTrack = p
	if debries:
		for i in range(int(radius)):
			d = Debrie(pos, radius/5, colors, 2, radius > 25)
			d.radius = choice([2,1])

def stain(pos, surf, size, alphaMore):
	rotated = pygame.transform.rotate(pygame.transform.scale(surf, size), randint(0, 360))
	if alphaMore:
		rotated.set_alpha(randint(100,180))
	size = rotated.get_size()
	grounder = pygame.Surface(size, pygame.SRCALPHA)
	grounder.blit(Game._game.map_manager.ground_map, (0,0), (pos - tup2vec(size)/2, size))
	patch = pygame.Surface(size, pygame.SRCALPHA)
	
	# grounder.blit(Game._game.map_manager.ground_map, (0,0), (pos - tup2vec(size)/2, size))
	patch.blit(Game._game.map_manager.game_map, (0,0), (pos - tup2vec(size)/2, size))
	patch.set_colorkey(GRD)
	
	grounder.blit(rotated, (0,0))
	grounder.blit(patch, (0,0))
	
	grounder.set_colorkey(SKY)
	Game._game.map_manager.ground_map.blit(grounder, pos - tup2vec(size)/2)

def splash(pos, vel):
	amount = 10 + int(vel.getMag())
	for i in range(amount):
		d = Debrie(Vector(pos.x, Game._game.map_manager.game_map.get_height() - Water.level - 3), 10, [Water.waterColor[1]], 1, False, True)
		d.vel = vectorUnitRandom()
		d.vel.y = uniform(-1,0) * vel.getMag()
		d.vel.x *= vel.getMag() * 0.17
		d.radius = choice([2,1])

class Water:
	''' water manager '''
	level = 50
	quiet = 0
	waterAmp = 2
	rising = 1
	layerTop = None
	layerMiddle = None
	layerBottom = None
	waterColor = []
	def __init__(self):
		self.points = [Vector(i * 20, 3 + Water.waterAmp + Water.waterAmp * (-1)**i) for i in range(-1,12)]
		self.speeds = [uniform(0.95, 1.05) for i in range(-1,11)]
		self.phase = [sin(TimeManager._tm.timeOverall/(3 * self.speeds[i])) for i in range(-1,11)]
		
		self.surf = pygame.Surface((200, Water.waterAmp * 2 + 6), pygame.SRCALPHA)
		self.state = Water.quiet
		self.amount = 0
	def rise(amount):
		Water.layerTop.amount = amount
		Water.layerMiddle.amount = amount
		Water.layerBottom.amount = amount
		Water.layerTop.state = Water.rising
		Water.layerMiddle.state = Water.rising
		Water.layerBottom.state = Water.rising
	def step(self):
		self.surf.fill((0,0,0,0))
		self.points = [Vector(i * 20, 3 + Water.waterAmp + self.phase[i % 10] * Water.waterAmp * (-1)**i) for i in range(-1,12)]
		pygame.draw.polygon(self.surf, Water.waterColor[0], self.points + [(200, Water.waterAmp * 2 + 6), (0, Water.waterAmp * 2 + 6)])
		pygame.draw.lines(self.surf, Water.waterColor[1], False, self.points, 2)
		
		self.phase = [sin(TimeManager._tm.timeOverall/(3 * self.speeds[i])) for i in range(-1,11)]
	
		if self.state == Water.rising:
			gameDistable()
			Water.level += 1
			self.amount -= 1
			if self.amount <= 0:
				self.amount = 0
				self.state = Water.quiet
	def draw(self, offsetY=0):
		width = 200
		height = 10
		offset = (Game._game.camPos.x)//width
		times = winWidth//width + 2
		for i in range(times):
			x = int(-Game._game.camPos.x) + int(int(offset) * width + i * width)
			y =  int(Game._game.map_manager.game_map.get_height() - Water.level - 3 - Water.waterAmp - offsetY) - int(Game._game.camPos.y)
			win.blit(self.surf, (x, y))
		
		pygame.draw.rect(win, Water.waterColor[0], ((0,y + height), (winWidth, Water.level)))
	def createLayers():
		Water.layerTop = Water()
		Water.layerMiddle = Water()
		Water.layerBottom = Water()
	def stepAll():
		Water.layerTop.step()
		Water.layerMiddle.step()
		Water.layerBottom.step()

class Cloud:
	''' single cloud, procedurally rendered, affected by wind '''
	_reg = []
	_toRemove = []
	cWidth = 170
	def __init__(self, pos):
		self._reg.append(self)
		self.pos = Vector(pos[0],pos[1])
		self.vel = Vector(0,0)
		self.acc = Vector(0,0)
		self.surf = renderCloud()
		self.randomness = uniform(0.97, 1.02)
	def step(self):
		self.acc.x = Game._game.wind
		self.vel += self.acc * Game._game.dt
		self.vel *= 0.85 * self.randomness
		self.pos += self.vel * Game._game.dt
		
		if self.pos.x > Game._game.camPos.x + winWidth + 100 or self.pos.x < Game._game.camPos.x - 100 - self.cWidth:
			self._toRemove.append(self)
	def draw(self):
		win.blit(self.surf, point2world(self.pos))

class BackGround:
	''' manages background entitiey: clouds, water '''
	_bg = None
	def __init__(self, feelColor, isDark=False):
		BackGround._bg = self
		self.mountains = [renderMountains((180, 110), feelColor[3]), renderMountains((180, 150), feelColor[2])]
		colorRect = pygame.Surface((2,2))
		pygame.draw.line(colorRect, feelColor[0], (0,0), (2,0))
		pygame.draw.line(colorRect, feelColor[1], (0,1), (2,1))
		self.imageSky = pygame.transform.smoothscale(colorRect, (winWidth, winHeight))

		self.backColor = feelColor[0]
		if isDark:
			self.backColor = DARK_COLOR

		Water.level = Game._game.initialWaterLevel
		Water.waterColor = [tuple((feelColor[0][i] + feelColor[1][i]) // 2 for i in range(3))]
		Water.waterColor.append(tuple(min(int(Water.waterColor[0][i] * 1.5), 255) for i in range(3)))

		Water.createLayers()
	def step(self):
		self.manageClouds()
		Water.stepAll()
	def manageClouds(self):
		if Game._game.map_manager.game_map.get_height() == 0:
			return
		if len(Cloud._reg) < 8 and randint(0,10) == 1:
			pos = Vector(choice([Game._game.camPos.x - Cloud.cWidth - 100, Game._game.camPos.x + winWidth + 100]), randint(5, Game._game.map_manager.game_map.get_height() - 150))
			Cloud(pos)
		for cloud in Cloud._reg: cloud.step()
		for cloud in Cloud._toRemove: Cloud._reg.remove(cloud)
		Cloud._toRemove = []
	def draw(self):
		win.fill(self.backColor)
		win.blit(pygame.transform.scale(self.imageSky, (win.get_width(), Game._game.map_manager.game_map.get_height())), (0,0 - Game._game.camPos[1]))
		
		for cloud in Cloud._reg:
			cloud.draw()
		self.drawBackGround(self.mountains[1],4)
		self.drawBackGround(self.mountains[0],2)
		Water.layerTop.draw(22)
	def drawSecondary(self):
		# draw top layer of water
		Water.layerMiddle.draw(12)
		Water.layerBottom.draw(2)
	def drawBackGround(self, surf, parallax):
		width = surf.get_width()
		height = surf.get_height()
		offset = (Game._game.camPos.x/parallax)//width
		times = winWidth//width + 2
		for i in range(times):
			x = int(-Game._game.camPos.x/parallax) + int(int(offset) * width + i * width)
			y = int(Game._game.map_manager.game_map.get_height() - Game._game.initialWaterLevel - height) - int(Game._game.camPos.y) + int((Game._game.map_manager.game_map.get_height() - Game._game.initialWaterLevel - winHeight - int(Game._game.camPos.y))/(parallax*1.5)) + 20 - parallax * 3
			win.blit(surf, (x, y))
	def drawBackGroundxy(self, surf, parallax):
		width = surf.get_width()
		height = surf.get_height()
		offsetx = (Game._game.camPos.x/parallax)//width
		offsety = (Game._game.camPos.y/parallax)//height
		timesx = winWidth//width + 2
		timesy = winHeight//height + 2
		for i in range(timesx):
			for j in range(timesy):
				x = int(-Game._game.camPos.x/parallax) + int(int(offsetx) * width + i * width)
				y = int(-Game._game.camPos.y/parallax) + int(int(offsety) * height + j * height)
				win.blit(surf, (x, y))

# todo: determine where this belongs
def giveGoodPlace(div = 0, girderPlace = True):
	goodPlace = False
	counter = 0
	
	if Game._game.fortsMode and not div == -1:
		half = Game._game.map_manager.game_map.get_width() / TeamManager._tm.totalTeams
		Slice = div % TeamManager._tm.totalTeams
		
		left = half * Slice
		right = left + half
		if left <= 0: left += 6
		if right >= Game._game.map_manager.game_map.get_width(): right -= 6
	else:
		left, right = 6, Game._game.map_manager.game_map.get_width() - 6
	
	if Game._game.diggingMatch:
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
			# print("problem with map", Game._game.mapChoice[0], "at ratio", Game._game.mapChoice[1])
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
	if checkFreePos(obj, obj.pos + Vector(dir, 0)):
		obj.pos += Vector(dir, 0) * Game._game.dt
		return True
	else:
		for i in range(1,5):
			if checkFreePos(obj, obj.pos + Vector(dir, -i)):
				obj.pos += Vector(dir, -i) * Game._game.dt
				return True
		for i in range(1,5):
			if checkFreePos(obj, obj.pos + Vector(dir, i)):
				obj.pos += Vector(dir, i) * Game._game.dt
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

def checkFreePos(obj, pos, wormCol = False):
	## moveable objs only
	r = 0
	while r < 2 * pi:
		testPos = Vector((obj.radius) * cos(r) + pos.x, (obj.radius) * sin(r) + pos.y)
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level or testPos.x < 0:
			if Game._game.mapClosed:
				return False
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			if Game._game.map_manager.game_map.get_at((int(testPos.x), 0)) == GRD:#Game._game.mapClosed and 
				return False
			else:
				r += pi /8
				continue
		
		getAt = testPos.vec2tupint()
		if Game._game.map_manager.game_map.get_at(getAt) == GRD:
			return False
		if Game._game.map_manager.objects_col_map.get_at(getAt) != (0,0,0):
			return False
		if wormCol and Game._game.map_manager.worm_col_map.get_at(getAt) != (0,0,0):
			return False
		
		r += pi /8
	return True

def checkFreePosFallProof(obj, pos):
	r = 0
	while r < 2 * pi:
		testPos = Vector((obj.radius) * cos(r) + pos.x, (obj.radius) * sin(r) + pos.y)
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level or testPos.x < 0:
			if Game._game.mapClosed:
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

def getClosestPosAvail(obj):
	r = 0
	found = None
	orgPos = vectorCopy(obj.pos)
	t = 0
	while not found:
		checkPos = orgPos + t * vectorFromAngle(r)
		# addExtra(checkPos, (255,255,255), 100)
		if checkFreePos(obj, checkPos, True):
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
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level or testPos.x < 0:
			if Game._game.mapClosed:
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
		self.timeCounter = Game._game.turnTime
		self.timeOverall = 0
		self.generateTimeSurf()
	def generateTimeSurf(self):
		self.timeSurf = (self.timeCounter, pixelFont5halo.render(str(self.timeCounter), False, Game._game.HUDColor))
	def step(self):
		self.timeOverall += 1
		if self.timeOverall % fps == 0:
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
			
		elif Game._game.state == FIRE_MULTIPLE:
			Game._game.state = PLAYER_CONTROL_2
			
		if Game._game.objectUnderControl.rope:
			Game._game.objectUnderControl.toggleRope(None)
		if Game._game.objectUnderControl.parachuting:
			Game._game.objectUnderControl.toggleParachute()
	def draw(self):
		if self.timeSurf[0] != self.timeCounter:
			self.generateTimeSurf()
		win.blit(self.timeSurf[1] , ((5, 5)))
	def timeReset(self):
		self.timeCounter = Game._game.turnTime
	def timeRemaining(self, amount):
		self.timeCounter = amount

class PhysObj:
	''' a physical object '''
	_reg = []
	_toRemove = []
	_worms = []
	_mines = []
	_fastest = 10
	def initialize(self):
		PhysObj._reg.append(self)
		self.vel = Vector(0,0)
		self.acc = Vector(0,0)
		
		self.stable = False
		self.damp = 0.4
		
		self.bounceBeforeDeath = -1
		self.dead = False
		self.color = (255,0,0)
		self.windAffected = Game._game.moreWindAffected
		self.boomAffected = True
		self.fallAffected = True
		self.health = None
		self.extraCollider = False
		self.wormCollider = False
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0],pos[1])
		
		self.radius = 4
	def step(self):
		self.applyForce()
		
		# velocity
		self.vel += self.acc * Game._game.dt
		self.limitVel()
		# position
		ppos = self.pos + self.vel * Game._game.dt
		
		# reset forces
		self.acc *= 0
		self.stable = False
		
		angle = atan2(self.vel.y, self.vel.x)
		response = Vector(0,0)
		collision = False
		
		# colission with world:
		r = angle - pi
		while r < angle + pi:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level or testPos.x < 0:
				if Game._game.mapClosed:
					response += ppos - testPos
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				if Game._game.map_manager.is_ground_at((int(testPos.x), 0)):#Game._game.mapClosed and 
					response += ppos - testPos
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
				continue
			
			# collission with Game._game.map_manager.game_map:
			if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
				collision = True
				r += pi /8; continue

			else:
				if not self.wormCollider and Game._game.map_manager.worm_col_map.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
				elif not self.extraCollider and Game._game.map_manager.objects_col_map.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
			
			r += pi / 8
		
		magVel = self.vel.getMag()
		
		if collision:
			
			self.collisionRespone(ppos)
			if magVel > Game._game.fallVelocityHurt and self.fallAffected:
				self.damage(magVel * 1.5 * Game._game.fallDamageMult, 1)
				# blood
				if self in PhysObj._worms:
					stain(self.pos, Game._game.imageBlood, Game._game.imageBlood.get_size(), False)
			self.stable = True
			
			response.normalize()
			#addExtra(self.pos + 5 * response, (0,0,0), 1)
			fdot = self.vel.dot(response)
			if not self.bounceBeforeDeath == 1:
				
				# damp formula 1 - logarithmic
				# dampening = max(self.damp, self.damp * log(magVel) if magVel > 0.001 else 1)
				# dampening = min(dampening, min(self.damp * 2, 0.9))
				# newVel = ((response * -2 * fdot) + self.vel) * dampening
				
				# legacy formula
				newVel = ((response * -2 * fdot) + self.vel) * self.damp * Game._game.dampMult
					
				self.vel = newVel
				# max speed recorded ~ 25
			
			if self.bounceBeforeDeath > 0:
				self.bounceBeforeDeath -= 1
				self.dead = self.bounceBeforeDeath == 0
				
		else:
			self.pos = ppos
			
		# flew out Game._game.map_manager.game_map but not worms !
		if self.pos.y > Game._game.map_manager.game_map.get_height() - Water.level and not self in self._worms:
			if self not in Debrie._debries:
				splash(self.pos, self.vel)
			angle = self.vel.getAngle()
			if (angle > 2.7 and angle < 3.14) or (angle > 0 and angle < 0.4):
				if self.vel.getMag() > 7:
					self.pos.y = Game._game.map_manager.game_map.get_height() - Water.level - 1
					self.vel.y *= -1
					self.vel.x *= 0.8
			else:
				self.outOfMapResponse()
				self.removeFromGame()
				return
		
		if magVel < 0.1: # creates a double jump problem
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self.removeFromGame()
			self.deathResponse()
	def applyForce(self):
		# gravity:
		self.acc.y += Game._game.globalGravity
		if self.windAffected > 0:
			if self.pos.x < - 3 * Game._game.map_manager.game_map.get_width() or self.pos.x > 4 * Game._game.map_manager.game_map.get_width():
				return
			self.acc.x += Game._game.wind * 0.1 * Game._game.windMult * self.windAffected
	def deathResponse(self):
		pass
	def secondaryStep(self):
		pass
	def removeFromGame(self):
		PhysObj._toRemove.append(self)
	def damage(self, value, damageType=0):
		pass
	def collisionRespone(self, ppos):
		pass
	def outOfMapResponse(self):
		pass
	def limitVel(self):
		pass
	def draw(self):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)

class Debrie (PhysObj):
	''' debrie resulting from explossions '''
	_debries = []
	def __init__(self, pos, blast, colors, bounces=2, firey=True, water=False):
		Debrie._debries.append(self)
		self.initialize()
		self.vel = Vector(cos(uniform(0,1) * 2 *pi), sin(uniform(0,1) * 2 *pi)) * blast
		self.pos = Vector(pos[0], pos[1])
		
		self.boomAffected = False
		self.bounceBeforeDeath = bounces
		self.color = choice(colors)
		self.radius = 1
		self.damp = 0.2
		
		width = randint(1,3)
		height = randint(1,3)
		point = Vector(width/2, height/2)
		
		self.rect = [point, Vector(point.x, -point.y), -point, -Vector(point.x, -point.y)]
		self.angle = 0
		
		self.firey = randint(0, 5) == 0 and firey
		self.water = water
	def applyForce(self):
		factor = 2.5# if self.water else 1
		self.acc.y += Game._game.globalGravity * factor
	def secondaryStep(self):
		self.angle -= self.vel.x * 2
		if self.firey:
			Blast(self.pos + vectorUnitRandom() * randint(0,4) + vectorFromAngle(-radians(self.angle)-pi/2) * 8, randint(3,6), 150)
	def collisionRespone(self, ppos):
		self.firey = False
	def draw(self):
		if self.water:
			pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius))
			return
		points = [point2world(self.pos + rotateVector(i, -self.angle)) for i in self.rect]
		pygame.draw.polygon(win, self.color, points)

class Missile (PhysObj):#1
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255,255,0)
		self.bounceBeforeDeath = 1
		self.windAffected = 1
		self.boomRadius = 28
		self.megaBoom = False or Game._game.megaTrigger
		if randint(0,50) == 1:
			self.megaBoom = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "missile")
	def deathResponse(self):
		if self.megaBoom:
			self.boomRadius *= 2
		boom(self.pos, self.boomRadius)
	def draw(self):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), randint(5,8), 30, 3)

class Grenade (PhysObj):#2
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1)
		self.radius = 2
		self.color = (0,100,0)
		self.damp = 0.4
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "grenade")
		self.angle = 0
	def deathResponse(self):
		rad = 30
		if randint(0,50) == 1 or Game._game.megaTrigger:
			rad *= 2
		boom(self.pos, rad)
	def secondaryStep(self):
		self.angle -= self.vel.x * 4 * Game._game.dt
		self.timer += 1 * Game._game.dt
		if self.timer >= Game._game.fuseTime:
			self.dead = True
		self.stable = False
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Mortar (Grenade):#3
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1)
		self.radius = 2
		self.color = (0,50,0)
		self.bounceBeforeDeath = -1
		self.damp = 0.4
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "mortar")
		self.angle = 0
	def deathResponse(self):
		megaBoom = False
		boom(self.pos, 25)
		if randint(0,50) == 1 or Game._game.megaTrigger:
			megaBoom = True
		if megaBoom:
				for j in range(10):
					k = Missile(self.pos, (uniform(-0.5,0.5),uniform(-0.7,-0.1)), 0.5)
					k.vel.x += self.vel.x * 0.5
					k.vel.y += self.vel.y * 0.5
					k.windAffected = 0
					k.boomAffected = False
					k.boomRadius = 20
					k.color = (0,50,0)
					k.radius = 1.5
					k.surf.fill((0,0,0,0))
					k.surf.blit(Game._game.sprites, (0,0), (0,96,16,16))
					if j == 5:
						Game._game.camTrack = k
				return
		for i in range(-1,2):
			m = Missile(self.pos, (i*0.3,-0.7), 0.5)
			m.megaBoom = False
			m.vel.x += self.vel.x * 0.5
			m.vel.y += self.vel.y * 0.5
			m.windAffected = 0
			m.boomAffected = False
			m.color = (0,50,0)
			m.radius = 1.5
			m.surf.fill((0,0,0,0))
			m.surf.blit(Game._game.sprites, (0,0), (0,96,16,16))
			if i == 0:
				Game._game.camTrack = m

class PetrolBomb(PhysObj):#4
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (158,66,43)
		self.bounceBeforeDeath = 1 
		self.damp = 0.5
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "petrol bomb")
		self.angle = 0
	def secondaryStep(self):
		self.angle -= self.vel.x * 4
		Blast(self.pos + vectorUnitRandom() * randint(0,4) + vectorFromAngle(-radians(self.angle)-pi/2) * 8, randint(3,6), 150)
	def deathResponse(self):
		boom(self.pos, 15)
		if randint(0,50) == 1 or Game._game.megaTrigger:
			for i in range(80):
				s = Fire(self.pos, 5)
				s.vel = Vector(cos(2*pi*i/80), sin(2*pi*i/80))*uniform(3,4)
		else:
			for i in range(40):
				s = Fire(self.pos, 5)
				s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2)
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

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
		self.facing = RIGHT if self.pos.x < Game._game.map_manager.game_map.get_width()/2 else LEFT
		self.shootAngle = 0 if self.pos.x < Game._game.map_manager.game_map.get_width()/2 else pi
		self.shootAcc = 0
		self.shootVel = 0
		self.health = Game._game.initialHealth
		self.alive = True
		self.team = team
		self.sick = 0
		self.gravity = DOWN
		self.nameStr = name
		self.name = pixelFont5.render(self.nameStr, False, self.team.color)
		self.healthStr = pixelFont5.render(str(self.health), False, self.team.color)
		self.score = 0
		self.jetpacking = False
		self.rope = None #[pos, radius]
		self.parachuting = False
		self.wormCollider = True
		self.flagHolder = False
		self.sleep = False
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (0,0,16,16))
		self.surf.blit(self.team.hatSurf, (0,0))
		self.angle = 0
		self.stableCount = 0
	def applyForce(self):
		# gravity:
		if self.gravity == DOWN:
			### JETPACK
			if self.jetpacking and Game._game.playerControl and Game._game.objectUnderControl == self:
				if pygame.key.get_pressed()[pygame.K_UP]:# or joystick.get_axis(1) < -0.5:
					self.acc.y -= Game._game.globalGravity + 0.5
					Game._game.jetPackFuel -= 0.5
				if pygame.key.get_pressed()[pygame.K_LEFT]:
					self.acc.x -= 0.5
					Game._game.jetPackFuel -= 0.5
				if pygame.key.get_pressed()[pygame.K_RIGHT]:
					self.acc.x += 0.5
					Game._game.jetPackFuel -= 0.5
				if Game._game.jetPackFuel <= 0:
					self.toggleJetpack()
			#### ROPE
			if self.rope and Game._game.playerControl:
				if pygame.key.get_pressed()[pygame.K_LEFT]:
					self.acc.x -= 0.1
				if pygame.key.get_pressed()[pygame.K_RIGHT]:
					self.acc.x += 0.1
				if pygame.key.get_pressed()[pygame.K_UP]:
					if self.rope[1] > 5:
						self.rope[1] = self.rope[1]-2
						directionToRope = (self.rope[0][-1] - self.pos).getDir()
						ppos = self.pos + directionToRope * (dist(self.pos, self.rope[0][-1]) - self.rope[1])
						if not checkFreePos(self, ppos):
							self.rope[1] = self.rope[1]+2
				if pygame.key.get_pressed()[pygame.K_DOWN]:
					self.rope[1] = self.rope[1]+2
					directionToRope = (self.rope[0][-1] - self.pos).getDir()
					ppos = self.pos + directionToRope * (dist(self.pos, self.rope[0][-1]) - self.rope[1])
					if not checkFreePos(self, ppos):
						self.rope[1] = self.rope[1]-2
			
			self.acc.y += Game._game.globalGravity
			
			if self.parachuting:
				if self.vel.y > 1:
					self.vel.y = 1
		else:# up
			self.acc.y -= Game._game.globalGravity
	def drawCursor(self):
		shootVec = self.pos + Vector((cos(self.shootAngle) * 20) ,sin(self.shootAngle) * 20)
		pygame.draw.circle(win, (255,255,255), (int(shootVec.x) - int(Game._game.camPos.x), int(shootVec.y) - int(Game._game.camPos.y)), 2)
	def sicken(self, sickness = 1):
		self.sick = sickness
		self.surf.fill((0,0,0,0))
		self.surf.blit(Game._game.sprites, (0,0), (16,0,16,16))
		self.surf.blit(self.team.hatSurf, (0,0))
		self.color = (128, 189,66)
		if MissionManager._mm: MissionManager._mm.notifySick(self)
	def heal(self, hp):
		self.health += hp
		if self.healthMode == 1:
			self.healthStr = pixelFont5.render(str(self.health), False, self.team.color)
		self.sick = 0
		self.color = (255, 206, 167)
		self.surf.fill((0,0,0,0))
		self.surf.blit(Game._game.sprites, (0,0), (0,0,16,16))
		self.surf.blit(self.team.hatSurf, (0,0))
	def toggleJetpack(self):
		self.jetpacking = not self.jetpacking
		self.fallAffected = not self.fallAffected
		Game._game.jetPackFuel = 100
	def toggleRope(self, pos):
		if pos:
			self.rope = [[pos], dist(self.pos, pos)]
			self.damp = 0.7
			self.fallAffected = False
		else:
			self.rope = None
			self.damp = 0.2
			self.fallAffected = True
	def toggleParachute(self):
		self.parachuting = not self.parachuting
	def damage(self, value, damageType=0):
		if self.alive:
			dmg = int(value * Game._game.damageMult)
			if dmg < 1:
				dmg = 1
			if dmg > self.health:
				dmg = self.health
			
			if dmg != 0: FloatingText(self.pos.vec2tup(), str(dmg))
			self.health -= dmg
			if self.health < 0:
				self.health = 0
			if Worm.healthMode == 1:
				self.healthStr = pixelFont5.render(str(self.health), False, self.team.color)
			if not self == Game._game.objectUnderControl:
				if not Game._game.sentring and not Game._game.raoning and not Game._game.waterRising and not self in TeamManager._tm.currentTeam.worms:
					Game._game.damageThisTurn += dmg
			if Game._game.gameMode == CAPTURE_THE_FLAG and damageType != 2:
				if self.flagHolder:
					self.team.flagHolder = False
					self.flagHolder = False
					Flag(self.pos)
			if Game._game.gameMode == TERMINATOR and Game._game.victim == self and not Game._game.terminatorHit:
				TeamManager._tm.currentTeam.points += 1
				Game._game.addToScoreList()
				Game._game.terminatorHit = True
			if Game._game.gameMode == MISSIONS:
				MissionManager._mm.notifyHit(self)
	def draw(self):
		if not self is Game._game.objectUnderControl and self.alive:
			pygame.draw.circle(Game._game.map_manager.worm_col_map, GRD, self.pos.vec2tupint(), int(self.radius)+1)

		if self.parachuting:
			win.blit(Game._game.sprites, point2world(self.pos - Vector(46,31)//2 + Vector(0,-15)), (80, 64, 46, 31))
		if self.flagHolder:
			pygame.draw.line(win, (51, 51, 0), point2world(self.pos), point2world(self.pos + Vector(0, -3 * self.radius)))
			pygame.draw.rect(win, (220,0,0), (point2world(self.pos + Vector(1, -3 * self.radius)), (self.radius*2, self.radius*2)))
			
		# draw artifact
		if len(self.team.artifacts) > 0 and Game._game.holdArtifact:
			if self is Game._game.objectUnderControl and WeaponManager._wm.getCategory(WeaponManager._wm.currentWeapon) == CATEGORY_ARTIFACTS:
				if WeaponManager._wm.currentArtifact() in self.team.artifacts:
					if WeaponManager._wm.currentArtifact() == MJOLNIR:
						win.blit(Game._game.imageMjolnir, point2world(self.pos + Vector(self.facing * 3, -5) - tup2vec(Game._game.imageMjolnir.get_size())/2))

		# draw worm sprite
		angle = 45 * int(self.angle / 45)
		fliped = pygame.transform.flip(self.surf, self.facing == RIGHT, False)
		rotated = pygame.transform.rotate(fliped, angle)
		if self.gravity == UP:
			rotated = pygame.transform.flip(rotated, False, True)
		if self.jetpacking:
			WeaponManager._wm.blitWeaponSprite(win, point2world(self.pos - Vector(8,8)), "jet pack")
		pygame.draw.circle(win, self.color, point2world(self.pos), self.radius + 1)
		win.blit(rotated, point2world(self.pos - tup2vec(rotated.get_size())//2))
		
		# draw name
		nameHeight = -21
		namePos = Vector(self.pos.x - self.name.get_width()/2, max(self.pos.y + nameHeight, 10))
		win.blit(self.name , point2world(namePos))
		if self.alive and self.pos.y < 0:
			num = pixelFont5.render(str(int(-self.pos.y)), False, self.team.color)
			win.blit(num, point2world(namePos + Vector(self.name.get_width() + 2,0)))
		
		if Game._game.warpedMode:
			pygame.draw.circle(win, self.color, point2world(self.pos + Vector(Game._game.map_manager.game_map.get_width())), int(self.radius)+1)
			pygame.draw.circle(win, self.color, point2world(self.pos + Vector(-Game._game.map_manager.game_map.get_width())), int(self.radius)+1)
			win.blit(self.name , ((int(self.pos.x) - int(Game._game.camPos.x) - Game._game.map_manager.game_map.get_width() - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(Game._game.camPos.y) - 21)))
			win.blit(self.name , ((int(self.pos.x) - int(Game._game.camPos.x) + Game._game.map_manager.game_map.get_width() - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(Game._game.camPos.y) - 21)))
		
		if self.rope:
			rope = [point2world(x) for x in self.rope[0]]
			rope.append(point2world(self.pos))
			pygame.draw.lines(win, (250,250,0), False, rope)
		if self.alive and Game._game.drawHealthBar:
			self.drawHealth()
		if self.sleep and self.alive:
			if TimeManager._tm.timeOverall % fps == 0:
				FloatingText(self.pos, "z", (0,0,0))
				
		# draw holding weapon
		if self is Game._game.objectUnderControl and Game._game.state in [PLAYER_CONTROL_1, FIRE_MULTIPLE]:
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
		self.surf.blit(Game._game.sprites, (0,0), (32,0,16,16))
		self.name = pixelFont5.render(self.nameStr, False, grayen(self.team.color))

		# insert to kill list:
		if not Game._game.sentring and not Game._game.raoning and not Game._game.waterRising and not self in TeamManager._tm.currentTeam.worms:
			Game._game.damageThisTurn += self.health
			TeamManager._tm.currentTeam.killCount += 1
			if Game._game.gameMode == POINTS:
				string = self.nameStr + " by " + Game._game.objectUnderControl.nameStr
				Game._game.killList.insert(0, (pixelFont5halo.render(string, False, Game._game.HUDColor), 0))
		
		self.health = 0
		
		# if capture the flag:
		if self.flagHolder:
			self.flagHolder = False
			self.team.flagHolder = False
			if cause == Worm.causeFlew:
				p = deployPack(Flag)
				Game._game.camTrack = p
			else:
				Flag(self.pos)
		
		# commentator:
		if cause == -1:
			Commentator.commentDeath(self, Commentator.CAUSE_DAMAGE)
		elif cause == Worm.causeFlew:
			comment = True
			if not self in TeamManager._tm.currentTeam.worms and WeaponManager._wm.currentWeapon == "baseball" and Game._game.state in [PLAYER_CONTROL_2, WAIT_STABLE]:
				Commentator.comment([{'text': self.nameStr, 'color': self.team.color}, {'text': 'home run'}])
				comment = False
			if comment:
				Commentator.commentDeath(self, Commentator.CAUSE_FLEW)
		
		# remove from regs:
		if self in PhysObj._worms:
			PhysObj._worms.remove(self)
		if self in self.team.worms:
			self.team.worms.remove(self)
		if cause == Worm.causeFlew or cause == Worm.causeVenus:
			self.removeFromGame()
		
		# if under control 
		if Game._game.objectUnderControl == self:
			if Game._game.state == FIRE_MULTIPLE:
				if WeaponManager._wm.currentWeapon.style == WeaponStyle.GUN:
					self.team.ammo(WeaponManager._wm.currentWeapon, -1)
					WeaponManager._wm.renderWeaponCount()
			Game._game.nextState = PLAYER_CONTROL_2
			Game._game.state = Game._game.nextState
			TimeManager._tm.timeRemaining(Game._game.wormDieTime)
		if Game._game.gameMode == TERMINATOR and self == Game._game.victim:
			TeamManager._tm.currentTeam.points += 1
			Game._game.addToScoreList()
			if not Game._game.terminatorHit:
				TeamManager._tm.currentTeam.points += 1
				Game._game.addToScoreList()
			if Game._game.state in [PLAYER_CONTROL_1, FIRE_MULTIPLE]:
				pickVictim()
		
		# if team kill and artifacts
		if Game._game.artifactsMode and len(self.team.worms) == 0:
			if len(self.team.artifacts) > 0:
				for artifact in self.team.artifacts:
					dropArtifact(WeaponManager._wm.artifactDict[artifact], self.pos)

		# if mission
		if Game._game.gameMode == MISSIONS:
			MissionManager._mm.notifyKill(self)

	def drawHealth(self):
		healthHeight = -15
		if Worm.healthMode == 0:
			value = 20 * min(self.health/Game._game.initialHealth, 1)
			if value < 1:
				value = 1
			pygame.draw.rect(win, (220,220,220),(point2world(self.pos + Vector(-10, healthHeight)),(20,3)))
			pygame.draw.rect(win, (0,220,0),(point2world(self.pos + Vector(-10, healthHeight)), (int(value),3)))
		else:
			win.blit(self.healthStr , point2world(self.pos + Vector(-self.healthStr.get_width()/2, healthHeight)))
		# draw jetpack fuel
		if self.jetpacking:
			value = 20 * (Game._game.jetPackFuel/100)
			if value < 1:
				value = 1
			pygame.draw.rect(win, (220,220,220),(point2world(self.pos + Vector(-10, -25)), (20,3)))
			pygame.draw.rect(win, (0,0,220),(point2world(self.pos + Vector(-10, -25)), (int(value),3)))
	def secondaryStep(self):
	
		if self.stable and self.alive:
			self.stableCount += 1
			if self.stableCount >= 30:
				
				self.angle *= 0.8
		else:
			self.stableCount = 0
			if not self is Game._game.objectUnderControl:
				self.angle -= self.vel.x * 4
				self.angle = self.angle % 360
		
		if Game._game.objectUnderControl == self and Game._game.playerControl and self.alive:
			if not self.rope: self.damp = 0.1
			else: self.damp = 0.5
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

		## jetpacking
		if self.jetpacking and not Game._game.state == WAIT_STABLE and Game._game.objectUnderControl == self:
			self.vel.limit(5)
			if pygame.key.get_pressed()[pygame.K_UP]:
				Blast(self.pos + Vector(0, self.radius*1.5) + vectorUnitRandom()*2, randint(5,8), 80)
			if pygame.key.get_pressed()[pygame.K_LEFT]:
				Blast(self.pos + Vector(self.radius*1.5, 0) + vectorUnitRandom()*2, randint(5,8), 80)
			if pygame.key.get_pressed()[pygame.K_RIGHT]:
				Blast(self.pos + Vector(-self.radius*1.5, 0) + vectorUnitRandom()*2, randint(5,8), 80)
		
		## roping
		if self.rope:
			if dist(self.pos, self.rope[0][-1]) > self.rope[1]:
				directionToRope = (self.rope[0][-1] - self.pos).getDir()
				ppos = self.pos + directionToRope * (dist(self.pos, self.rope[0][-1]) - self.rope[1])
				# if checkFreePos(self, ppos):
				self.pos = ppos
				normal = directionToRope.normal()
				mul = dotProduct(self.vel, normal)/(normal.getMag()**2)
				self.vel = normal * mul
			
			if dist(self.pos, self.rope[0][-1]) < self.rope[1] - 2:
				directionToRope = (self.rope[0][-1] - self.pos).getDir()
				ppos = self.pos + directionToRope * (dist(self.pos, self.rope[0][-1]) - self.rope[1])
				# if checkFreePos(self, ppos):
				self.pos = ppos
				normal = directionToRope.normal()
				mul = dotProduct(self.vel, normal)/(normal.getMag()**2)
				self.vel = normal * mul
			
			# check secondary rope position
			for i in range(int(self.rope[1])-2):
				start = self.pos
				direction = (self.rope[0][-1] - self.pos).normalize()
				testPos = start + direction * i
				if not isOnMap(testPos):
					break
				if Game._game.map_manager.game_map.get_at(testPos.vec2tupint()) == GRD:
					self.rope[0].append(testPos)
					self.rope[1] = dist(self.pos, self.rope[0][-1])
					break
			if len(self.rope[0]) > 1:
				count = int(dist(self.pos, self.rope[0][-2]))
				for i in range(int(dist(self.pos, self.rope[0][-2]))):
					start = self.pos
					direction = (self.rope[0][-2] - self.pos).normalize()
					testPos = start + direction * i
					if not isOnMap(testPos):
						break
					if Game._game.map_manager.game_map.get_at(testPos.vec2tupint()) == GRD:
						break
					if i == count-1:
						self.rope[1] = dist(self.pos, self.rope[0][-2])
						self.rope[0].pop(-1)
			self.damp = 0.7
		
		## parachuting
		if self.parachuting:
			# print(self.vel.y)
			if self.vel.y < 1:
				self.toggleParachute()
			self.vel.x = Game._game.wind * 1.5
		
		# virus
		if self.sick == 2 and self.health > 0 and not Game._game.state == WAIT_STABLE:
			if randint(1,200) == 1:
				SmokeParticles._sp.addSmoke(self.pos, color=(102, 255, 127), sick=2)
		
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
		if self.pos.y > Game._game.map_manager.game_map.get_height() - Water.level:
			splash(self.pos, self.vel)
			angle = self.vel.getAngle()
			if (angle > 2.7 and angle < 3.14) or (angle > 0 and angle < 0.4):
				if self.vel.getMag() > 7:
					self.pos.y = Game._game.map_manager.game_map.get_height() - Water.level - 1
					self.vel.y *= -1
					self.vel.x *= 0.7
			else:
				self.dieded(Worm.causeFlew)
		if self.pos.y < 0:
			self.gravity = DOWN
		if Game._game.actionMove:
			if Game._game.objectUnderControl == self and self.health > 0 and not self.jetpacking and not self.rope:
				move(self)

		if not self.stable:
			velocity = self.vel.getMag()
			if velocity > 5:
				for worm in PhysObj._worms:
					if worm == self or not worm.stable:
						continue
					if distus(self.pos, worm.pos) < (self.radius + worm.radius) * (self.radius + worm.radius):
						worm.vel = vectorCopy(self.vel)
						# print(self.nameStr, "collided with", worm.nameStr)

class Fire(PhysObj):
	def __init__(self, pos, delay = 0):
		self.initialize()
		Debrie._debries.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.damp = 0
		self.red = 255
		self.yellow = 106
		self.phase = uniform(0,2)
		self.radius = 2
		self.windAffected = 1
		self.life = randint(50,70)
		self.fallen = False
		self.delay = delay
		self.timer = 0
		self.wormCollider = True
	def collisionRespone(self, ppos):
		self.fallen = True
	def secondaryStep(self):
		self.stable = False
		if randint(0,10) < 3:
			FireBlast(self.pos + vectorUnitRandom(), randint(self.radius,4))
		if randint(0,50) < 1:
			SmokeParticles._sp.addSmoke(self.pos)
			# Smoke(self.pos)
		self.timer += 1 * Game._game.dt
		if self.fallen:
			self.life -= 1
		if Game._game.darkness:
			Game._game.lights.append((self.pos[0], self.pos[1], 20, (0,0,0,0)))
		if self.life == 0:
			self.removeFromGame()
			return
		if randint(0,1) == 1 and self.timer > self.delay:
			boom(self.pos + Vector(randint(-1,1),randint(-1,1)), 3, False, False, True)
	def draw(self):
		radius = 1
		if self.life > 20:
			radius += 1
		if self.life > 10:
			radius += 1
		self.yellow = int(sin(0.3*TimeManager._tm.timeOverall + self.phase) * ((255-106)/4) + 255 - ((255-106)/2))
		pygame.draw.circle(win, (self.red, self.yellow, 69), (int(self.pos.x - Game._game.camPos.x), int(self.pos.y - Game._game.camPos.y)), radius)

class TNT(PhysObj):#5
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 2
		self.color = (230,57,70)
		self.bounceBeforeDeath = -1
		self.damp = 0.2
		self.timer = 0
	def secondaryStep(self):
		self.timer += 1
		self.stable = False
		if self.timer == fps*4:
			self.dead = True
	def deathResponse(self):
		boom(self.pos, 40)
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -2) - int(Game._game.camPos.x),int(self.pos.y -4) - int(Game._game.camPos.y) , 3,8))
		pygame.draw.line(win, (90,90,90), point2world(self.pos + Vector(-1,-4)), point2world(self.pos + Vector(-1, -5*(fps*4 - self.timer)/(fps*4) - 4)), 1)
		if randint(0,10) == 1:
			Blast(self.pos + Vector(-1, -5*(fps*4 - self.timer)/(fps*4) - 4), randint(3,6), 150)

def fireShotgun(start, direction, power=15):#6
	GunShell(start + Vector(0, -4))
	for t in range(5,500):
		testPos = start + direction * t
		Game._game.addExtra(testPos, (255, 204, 102), 3)
		
		if testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level:
			splash(testPos, Vector(10,0))
			break
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue

		# hit worms or Game._game.map_manager.ground_map:
		# hit Game._game.map_manager.ground_map:
		at = (int(testPos.x), int(testPos.y))
		if Game._game.map_manager.game_map.get_at(at) == GRD or Game._game.map_manager.worm_col_map.get_at(at) != (0,0,0) or Game._game.map_manager.objects_col_map.get_at(at) != (0,0,0):
			if Game._game.map_manager.worm_col_map.get_at(at) != (0,0,0):
				stain(testPos, Game._game.imageBlood, Game._game.imageBlood.get_size(), False)
			boom(testPos, power)
			break

def fireFlameThrower(pos, direction):#8
	offset = uniform(1,2)
	f = Fire(pos + direction * 5)
	f.vel = direction * offset * 2.4

class StickyBomb (Grenade):#9
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1)
		self.radius = 2
		self.color = (117,47,7)
		self.bounceBeforeDeath = -1
		self.damp = 0.5
		self.timer = 0
		self.sticked = False
		self.stick = None
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "sticky bomb")
		self.angle = 0
	def collisionRespone(self, ppos):
		if not self.sticked:
			self.sticked = True
			self.stick = vectorCopy((self.pos + ppos)/2)
		self.vel *= 0
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		if self.stick:
			self.pos = self.stick
		self.timer += 1
		if self.timer == Game._game.fuseTime:
			self.dead = True

def fireMiniGun(start, direction):#0
	angle = atan2(direction[1], direction[0])
	angle += uniform(-0.2, 0.2)
	direction[0], direction[1] = cos(angle), sin(angle)
	fireShotgun(start, direction,randint(7,9))

class PetrolCan(PhysObj):
	_cans = [] 
	def __init__(self, pos = (0,0)):
		PetrolCan._cans.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 6
		self.color = (191, 44, 44)
		self.damp = 0.1
		self.health = 5
		self.extraCollider = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (64, 96, 16, 16))
	def deathResponse(self):
		boom(self.pos, 20)
		pygame.draw.rect(Game._game.map_manager.objects_col_map, SKY, (int(self.pos.x -3),int(self.pos.y -5), 7,10))
		for i in range(40):
			s = Fire(self.pos, 5)
			s.vel = vectorFromAngle(2*pi*i/40, uniform(1.3,2))
		if self in PetrolCan._cans:
			PetrolCan._cans.remove(self)
	def secondaryStep(self):
		if self.health <= 0:
			self.dead = True
	def damage(self, value, damageType=0):
		dmg = value * Game._game.damageMult
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0
	def draw(self):
		win.blit(self.surf , point2world(self.pos - tup2vec(self.surf.get_size())/2))
		pygame.draw.rect(Game._game.map_manager.objects_col_map, GRD, (int(self.pos.x -6),int(self.pos.y -8), 12,16))

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
				
		if Game._game.darkness and self.activated:
			Game._game.lights.append((self.pos[0], self.pos[1], 50, (100,0,0,100)))
	def deathResponse(self):
		boom(self.pos, 30)
	def draw(self):
		if Game._game.diggingMatch:
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
		self.direction = vectorFromAngle(Game._game.objectUnderControl.shootAngle)
		Game._game.nonPhys.append(self)
		self.timer = 0
		hitted = []
		for t in range(5, 25):
			testPositions = []
			testPos = Game._game.objectUnderControl.pos + self.direction * t
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
						Game._game.camTrack = worm
	def step(self):
		self.timer += 1 * Game._game.dt
		if self.timer >= 15:
			Game._game.nonPhysToRemove.append(self)
	def draw(self):
		weaponSurf = pygame.transform.rotate(pygame.transform.flip(Game._game.weaponHold, False, Game._game.objectUnderControl.facing == LEFT), -degrees(Game._game.objectUnderControl.shootAngle) + 180)
		win.blit(weaponSurf, point2world(Game._game.objectUnderControl.pos - tup2vec(weaponSurf.get_size())/2 + self.direction * 16))

class GasGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1)
		self.radius = 2
		self.color = (113,117,41)
		self.bounceBeforeDeath = -1
		self.damp = 0.5
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "gas grenade")
		self.angle = 0
		self.state = "throw"
	def deathResponse(self):
		boom(self.pos, 20)
		for i in range(40):
			vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1,1.5)
			SmokeParticles._sp.addSmoke(self.pos, vel, color=(102, 255, 127), sick=1)
	def secondaryStep(self):
		gameDistable()
		self.angle -= self.vel.x*4
		self.timer += 1
		if self.state == "throw":
			if self.timer >= Game._game.fuseTime:
				self.state = "release"
		if self.state == "release":
			if self.timer % 3 == 0:
				SmokeParticles._sp.addSmoke(self.pos, vectorUnitRandom(), color=(102, 255, 127), sick=1)
			if self.timer >= Game._game.fuseTime + 5 * fps:
				self.dead = True

class HealthPack(PetrolCan):
	def __init__(self, pos = (0,0)):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 5
		self.color = (235, 235, 235)
		self.damp = 0.01
		self.health = 5
		self.fallAffected = False
		self.windAffected = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (112, 96, 16, 16))
	def draw(self):
		win.blit(self.surf , point2world(self.pos - tup2vec(self.surf.get_size())/2))
	def secondaryStep(self):
		if distus(Game._game.objectUnderControl.pos, self.pos) < (self.radius + Game._game.objectUnderControl.radius + 5) * (self.radius + Game._game.objectUnderControl.radius + 5)\
			and not Game._game.objectUnderControl.health <= 0:
			self.effect(Game._game.objectUnderControl)
			self.removeFromGame()
			return
		if self.health <= 0:
			self.deathResponse()
			self.removeFromGame()
	def effect(self, worm):
		worm.heal(50)
		FloatingText(self.pos, "+50", (0,230,0))

class UtilityPack(HealthPack):# Utility Pack
	def __init__(self, pos = (0,0)):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 5
		self.color = (166, 102, 33)
		self.damp = 0.01
		self.health = 5
		self.fallAffected = False
		self.windAffected = 0
		self.box = choice(["moon gravity", "double damage", "aim aid", "teleport", "switch worms", "time travel", "jet pack", "tool set", "travel kit"])
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (96, 96, 16, 16))
	def effect(self, worm):
		if Game._game.unlimitedMode:
			return
		FloatingText(self.pos, self.box, (0,200,200))
		if self.box == "tool set":
			worm.team.ammo("portal gun", 1)
			worm.team.ammo("ender pearl", 5)
			worm.team.ammo("trampoline", 3)
			return
		elif self.box == "travel kit":
			worm.team.ammo("rope", 3)
			worm.team.ammo("parachute", 3)
			return
		
		worm.team.ammo(self.box, 1)

class WeaponPack(HealthPack):# Weapon Pack
	def __init__(self, pos = (0,0)):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 5
		self.color = (166, 102, 33)
		self.damp = 0.01
		self.health = 5
		self.fallAffected = False
		self.windAffected = 0
		weaponsInBox = ["banana", "holy grenade", "earthquake", "gemino mine", "sentry turret", "bee hive", "vortex grenade", "chilli pepper", "covid 19", "raging bull", "electro boom", "pokeball", "green shell", "guided missile", "fireworks"]
		if Game._game.allowAirStrikes:
			weaponsInBox .append("mine strike")
		self.box = choice(weaponsInBox)
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (80, 96, 16, 16))
	def effect(self, worm):
		if Game._game.unlimitedMode:
			return
		FloatingText(self.pos, self.box, (0,200,200))
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
			if y + i >= Game._game.map_manager.game_map.get_height() - Water.level:
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
			Game._game.camTrack = f

def fireMineStrike(pos):
	megaBoom = False
	if randint(0,50) == 1 or Game._game.megaTrigger:
		megaBoom = True
	x = pos[0]
	y = 5
	if megaBoom:
		for i in range(20):
			m = Mine((x - 40 + 4*i, y - i))
			m.vel.x = Game._game.airStrikeDir
			if i == 10:
				Game._game.camTrack = m
	else:
		for i in range(5):
			m = Mine((x - 40 + 20*i, y - i))
			m.vel.x = Game._game.airStrikeDir
			if i == 2:
				Game._game.camTrack = m

def fireNapalmStrike(pos):
	x = pos[0]
	y = 5
	for i in range(70):
		f = Fire((x - 35 + i, y ))
		f.vel = Vector(cos(uniform(pi, 2*pi)), sin(uniform(pi, 2*pi))) * 0.5
		if i == 2:
			Game._game.camTrack = f

class GravityMissile(Missile):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255,255,0)
		self.bounceBeforeDeath = 1
		self.windAffected = 1
		self.boomRadius = 28
		self.megaBoom = False or Game._game.megaTrigger
		if randint(0,50) == 1:
			self.megaBoom = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "gravity missile")
	def deathResponse(self):
		boom(self.pos, self.boomRadius, True, True)
	def applyForce(self):
		# gravity:
		self.acc.y -= Game._game.globalGravity
		self.acc.x += Game._game.wind * 0.1 * Game._game.windMult
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2, 5)
		if self.pos.y < 0:
			self.removeFromGame()

def fireGammaGun(start, direction):
	hitted = []
	normal = Vector(-direction.y, direction.x).normalize()
	for t in range(5,500):
		testPos = start + direction * t + normal * 1.5 * sin(t * 0.6) * (t + 1)/70
		Game._game.addExtra(testPos, (0,255,255), 10)
		
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue
		# if hits worm:
		for worm in PhysObj._worms:
			if distus(testPos, worm.pos) < worm.radius * worm.radius and not worm in hitted:
				worm.damage(int(10/Game._game.damageMult)+1)
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

class HolyGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1)
		self.radius = 3
		self.color = (230, 230, 0)
		self.damp = 0.5
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "holy grenade")
		self.angle = 0
	def deathResponse(self):
		boom(self.pos, 45)
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		self.timer += 1
		if self.timer == Game._game.fuseTime + 2*fps:
			self.dead = True
		if self.timer == Game._game.fuseTime + fps:
			comments = [
				[{'text': "o lord bless this thy "}, {'text': 'hand grenade', 'color': (210,210,0)}],
				[{'text': "blow thine enemy to tiny bits"}],
				[{'text': "feast upon the lambs and sloths and carp"}],
				[{'text': "three shall be the number thou shalt count"}],
				[{'text': "thou shall snuff that"}],
			]
			Commentator.comment(choice(comments))

class Banana(Grenade):
	def __init__(self, pos, direction, energy, used = False):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255, 204, 0)
		self.damp = 0.5
		self.timer = 0
		# self.surf = pixelFont10.render("(", False, self.color)
		self.angle = 0
		self.used = used
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "banana")
		self.angle = 0
	def collisionRespone(self, ppos):
		if self.used:
			self.dead = True
	def deathResponse(self):
		if self.used:
			boom(self.pos, 40)
			return
		boom(self.pos, 40)
		for i in range(5):
			angle = (i * pi) / 6 + pi / 6
			direction = (cos(angle)*uniform(0.2,0.6), -sin(angle))
			m = Banana(self.pos, direction, uniform(0.3,0.8), True)
			m.boomAffected = False
			if i == 2:
				Game._game.camTrack = m
	def secondaryStep(self):
		if not self.used: 
			self.timer += 1
		if self.timer == Game._game.fuseTime:
			self.dead = True
		self.angle -= self.vel.x*4

class Earthquake:
	earthquake = 0
	def __init__(self, timer = 7 * fps, decorative = False, strength = 1):
		self.timer = timer
		Game._game.nonPhys.append(self)
		self.stable = False
		self.boomAffected = False
		Earthquake.earthquake = strength
		self.decorative = decorative
	def step(self):
		if not self.decorative:
			for obj in PhysObj._reg:
				if obj == self:
					continue
				if randint(0,5) == 1:
					obj.vel += Vector(randint(-1,1), -uniform(0,1))
		self.timer -= 1 * Game._game.dt
		if self.timer <= 0:
			Game._game.nonPhysToRemove.append(self)
			Earthquake.earthquake = 0
	def draw(self):
		pass

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
	def draw(self):
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(Game._game.camPos.x), int(self.pos.y) - int(Game._game.camPos.y)), int(self.radius)+1)
		pygame.draw.circle(win, (222,63,49), (int(self.pos.x) - int(Game._game.camPos.x), int(self.pos.y) - int(Game._game.camPos.y)), 1)

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
	def draw(self):
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "venus fly trap")
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
			Game._game.camTrack = w
		elif self.mode == PlantBomb.mine:
			for i in range(randint(2,3)):
				Plant(ppos, 5, -1, PlantBomb.mine)
		
	def draw(self):
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
		self.surf.blit(Game._game.sprites, (0,0), (80, 32, 17, 26))
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
			if TimeManager._tm.timeOverall % 2 == 0:
				self.angle = uniform(0,2*pi)
				fireMiniGun(self.pos, vectorFromAngle(self.angle))
		
		self.angle += (self.angle2for - self.angle)*0.2
		if not self.target and TimeManager._tm.timeOverall % (fps*2) == 0:
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
			
	def draw(self):
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
	def draw(self):
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "bee hive")
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
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class BunkerBuster(PhysObj):
	mode = False #True = drill
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.lastPos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 7
		self.color = (102, 51, 0)
		self.boomRadius = 30
		self.boomAffected = False
		
		self.drillVel = None
		self.inGround = False
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "bunker buster")
	def step(self):
		self.applyForce()
		
		# velocity
		if self.inGround:
			if self.mode:
				self.vel = self.drillVel
				self.vel.setMag(2)
			else:
				self.vel += self.acc * Game._game.dt
				self.vel.limit(5)
		else:
			self.vel += self.acc * Game._game.dt
		
		# position
		ppos = self.pos + self.vel * Game._game.dt
		
		# reset forces
		self.acc *= 0
		self.stable = False
		
		collision = False
		# colission with world:
		direction = self.vel.getDir()
		
		checkPos = (self.pos + direction*self.radius).vec2tupint()
		if not(checkPos[0] >= Game._game.map_manager.game_map.get_width() or checkPos[0] < 0 or checkPos[1] >= Game._game.map_manager.game_map.get_height() or checkPos[1] < 0):
			if Game._game.map_manager.game_map.get_at(checkPos) == GRD:
				self.inGround = True
				self.drillVel = vectorCopy(self.vel)
		if self.inGround:
			self.timer += 1 * Game._game.dt
					
		checkPos = (self.pos + direction*(self.radius + 2)).vec2tupint()
		if not(checkPos[0] >= Game._game.map_manager.game_map.get_width() or checkPos[0] < 0 or checkPos[1] >= Game._game.map_manager.game_map.get_height() or checkPos[1] < 0):
			if not Game._game.map_manager.game_map.get_at(checkPos) == GRD and self.inGround:
				self.dead = True
				
		if self.timer >= fps*2:
			self.dead = True
			
		self.lastPos.x, self.lastPos.y = self.pos.x, self.pos.y
		self.pos = ppos
		
		if self.inGround:
			boom(self.pos, self.radius, False)
		self.lineOut((self.lastPos.vec2tupint(), self.pos.vec2tupint()))
		
		# flew out Game._game.map_manager.game_map but not worms !
		if self.pos.y > Game._game.map_manager.game_map.get_height():
			self.removeFromGame()
			return
		if self.inGround and self.pos.y <= 0:
			self.dead = True

		if self.vel.getMag() < 0.1:
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self.removeFromGame()
			self.deathResponse()
	def lineOut(self,line):
		pygame.draw.line(Game._game.map_manager.game_map, SKY, line[0], line[1], self.radius*2)
		pygame.draw.line(Game._game.map_manager.ground_map, SKY, line[0], line[1], self.radius*2)
	def draw(self):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	def deathResponse(self):
		boom(self.pos, 23)

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
	if Game._game.darkness:
		for i in lightings:
			Game._game.lights.append((i[0], i[1], 50, [color[0], color[1], color[2], 100]))
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
		GunShell(self.pos, index=1)
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "electric grenade")
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
		if self.timer == Game._game.fuseTime:
			self.electrifying = True
		if self.timer >= Game._game.fuseTime + self.lifespan:
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
	def draw(self):
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

class HomingMissile(PhysObj):
	Target = Vector()
	showTarget = False
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0, 51, 204)
		self.bounceBeforeDeath = 1
		self.windAffected = 1
		self.boomRadius = 30
		self.activated = False
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "homing missile")
	def applyForce(self):
		# gravity:
		if self.activated:
			desired = HomingMissile.Target - self.pos
			desired.setMag(50)
			self.acc = desired - self.vel
			self.acc.limit(1)
		else:
			self.acc.y += Game._game.globalGravity
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), 5)
		self.timer += 1
		if self.timer == 20:
			self.activated = True
		if self.timer == 20 + fps*5:
			self.activated = False
	def limitVel(self):
		self.vel.limit(15)
	def outOfMapResponse(self):
		HomingMissile.showTarget = False
	def collisionRespone(self, ppos):
		HomingMissile.showTarget = False
		boom(ppos, self.boomRadius)
	def draw(self):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

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
	def draw(self):
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
				if getAt[0] < 0 or getAt[0] >= winWidth or getAt[1] < 0 or getAt[1] >= winHeight:
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
		GunShell(self.pos, index=1)
		self.radius = 3
		self.color = (25, 102, 102)
		self.damp = 0.5
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "vortex grenade")
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
	def draw(self):
		pygame.draw.circle(win, Game._game.objectUnderControl.color, point2world(self.pos), 3+1)
		facing = self.facings.pop(0)
		win.blit(pygame.transform.flip(self.surf, facing == 1, False), point2world(tup2vec(self.pos) - tup2vec(self.surf.get_size()) / 2))
		win.blit(self.nameSurf , ((int(self.pos[0]) - int(Game._game.camPos.x) - int(self.nameSurf.get_size()[0]/2)), (int(self.pos[1]) - int(Game._game.camPos.y) - 21)))
		pygame.draw.rect(win, (220,220,220),(int(self.pos[0]) -10 -int(Game._game.camPos.x), int(self.pos[1]) -15 -int(Game._game.camPos.y), 20,3))
		value = 20 * self.health/Game._game.initialHealth
		if value < 1:
			value = 1
		pygame.draw.rect(win, (0,220,0),(int(self.pos[0]) -10 -int(Game._game.camPos.x), int(self.pos[1]) -15 -int(Game._game.camPos.y), int(value),3))
		
		i = 0
		while i < 20 * self.energy:
			cPos = vectorCopy(self.pos)
			angle = TimeTravel._tt.timeTravelList["weaponDir"].getAngle()
			pygame.draw.line(win, (0,0,0), (int(cPos[0] - Game._game.camPos.x), int(cPos[1] - Game._game.camPos.y)), ((int(cPos[0] + cos(angle) * i - Game._game.camPos.x), int(cPos[1] + sin(angle) * i - Game._game.camPos.y))))
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
		self.timeTravelList["surf"] = Game._game.objectUnderControl.surf
		self.timeTravelList["name"] = Game._game.objectUnderControl.name
		self.timeTravelList["health"] = Game._game.objectUnderControl.health
		self.timeTravelList["initial pos"] = vectorCopy(Game._game.objectUnderControl.pos)
		self.timeTravelList["timeCounter in turn"] = TimeManager._tm.timeCounter
		self.timeTravelList["jet pack"] = Game._game.jetPackFuel
	def timeTravelRecord(self):
		self.timeTravelPositions.append(Game._game.objectUnderControl.pos.vec2tup())
		self.timeTravelFacings.append(Game._game.objectUnderControl.facing)
	def timeTravelPlay(self):
		TimeManager._tm.timeCounter = self.timeTravelList["timeCounter in turn"]
		Game._game.timeTravel = False
		self.timeTravelList["weapon"] = WeaponManager._wm.currentWeapon
		self.timeTravelList["weaponOrigin"] = vectorCopy(Game._game.objectUnderControl.pos)
		self.timeTravelList["energy"] = Game._game.energyLevel
		self.timeTravelList["weaponDir"] = Vector(cos(Game._game.objectUnderControl.shootAngle), sin(Game._game.objectUnderControl.shootAngle))
		Game._game.objectUnderControl.health = self.timeTravelList["health"]
		if Worm.healthMode == 1:
			Game._game.objectUnderControl.healthStr = pixelFont5.render(str(Game._game.objectUnderControl.health), False, Game._game.objectUnderControl.team.color)
		Game._game.objectUnderControl.pos = self.timeTravelList["initial pos"]
		Game._game.objectUnderControl.vel *= 0
		Game._game.jetPackFuel = self.timeTravelList["jet pack"]
		TimeAgent()
	def timeTravelReset(self):
		self.timeTravelFire = False
		self.timeTravelPositions = []
		self.timeTravelList = {}
	def step(self):
		self.timeTravelRecord()

class ChilliPepper(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "chilli pepper")
		self.damp = 0.5
		self.angle = 0
		self.boomAffected = False
		self.bounceBeforeDeath = 6
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , (int(self.pos.x - Game._game.camPos.x - surf.get_size()[0]/2), int(self.pos.y - Game._game.camPos.y - surf.get_size()[1]/2)))
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
	def collisionRespone(self, ppos):
		boom(ppos, 25)
		for i in range(40):
			s = Fire(self.pos, 5)
			s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2)

class Artillery(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (128, 0, 0)
		self.damp = 0.5
		self.timer = 0
		self.bombing = False
		self.boomAffected = False
		self.booms = randint(3,5)
		self.boomCount = 20 if randint(0,50) == 0 or Game._game.megaTrigger else self.booms
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "flare")
		self.angle = 0
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	def secondaryStep(self):
		if not self.bombing:
			self.angle -= self.vel.x*4
			if self.stable:
				self.timer += 1
			else:
				self.timer = 0
			if randint(0, 5) == 0:
				SmokeParticles._sp.addSmoke(self.pos, color=(200,0,0))
			self.stable = False
			if self.timer == 50:
				self.bombing = True
		else:
			self.stable = False
			self.timer += 1
			if self.timer % 10 == 0:
				m = Missile((self.pos[0] + randint(-20,20), 0),(0,0),0 )
				m.windAffected = 0
				m.boomAffected = False
				m.megaBoom = False
				m.surf.fill((0,0,0,0))
				m.surf.blit(Game._game.sprites, (0,0), (0,96,16,16))
				if self.boomCount == self.booms:
					Game._game.camTrack = m
				self.boomCount -= 1
			if self.boomCount == 0:
				self.dead = True

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
		self.triangle = [Vector(0,3), Vector(6,0), Vector(0,-3)]
		for vec in self.triangle:
			vec.rotate(self.direction.getAngle())
		self.timer = 0
	def destroy(self):
		Game._game.nonPhysToRemove.append(self)
	def step(self):
		self.timer += 1
		if self.timer >= fps * 3:
			self.vel.y += Game._game.globalGravity
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
				if isOnMap(testPos.vec2tupint()):
					if Game._game.map_manager.is_ground_at(testPos.vec2tupint()):
						self.stuck = vectorCopy(testPos)
				if self.pos.y < 0:
					self.destroy()
					return
				if self.pos.y > Game._game.map_manager.game_map.get_height() - Water.level:
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
		Game._game.camTrack = worm
		if self.sleep: worm.sleep = True
		self.destroy()
		stain(worm.pos, Game._game.imageBlood, Game._game.imageBlood.get_size(), False)
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
	def draw(self):
		points = [point2world(self.pos - self.direction * 10 + i) for i in self.triangle]
		pygame.draw.polygon(win, (230,235,240), points)
	
		pygame.draw.line(win, self.color, point2world(self.pos), point2world(self.pos - self.direction*8), 3)
		
		points = [point2world(self.pos + i) for i in self.triangle]
		pygame.draw.polygon(win, (230,235,240), points)

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
	def draw(self):
		rad = self.radius + 1
		wig = 0.4*sin(0.5*self.timer)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(pi/4 + wig), rad * sin(pi/4 + wig))), 2)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(rad * cos(3*pi/4 - wig), rad * sin(3*pi/4 - wig))), 2)
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		pygame.draw.circle(win, (10,10,10), point2world(self.pos + Vector(self.facing*self.radius,0)), 4)

def shootRope(start, direction):
	for t in range(5,500):
		testPos = start + direction * t
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue
		if Game._game.map_manager.game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
			Game._game.objectUnderControl.toggleRope(testPos)
			Worm.roped = True
			break

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
		if TimeManager._tm.timeOverall % 10 == 0:
			for i in range(randint(1,2)):
				x = randint(-100, Game._game.map_manager.game_map.get_width() + 100)
				m = Missile((x, -10), Vector(randint(-10,10), 5).normalize(), 1)
				m.windAffected = 0
				m.boomRadius = 40
	def draw(self):
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
	def draw(self):
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
		GunShell(self.pos, index=1)
		self.radius = 2
		self.color = (120, 230, 230)
		self.damp = 0.6
		self.timer = 0
		self.worms = []
		self.network = []
		self.used = []
		self.electrifying = False
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "electro boom")
		self.angle = 0
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		self.timer += 1
		if self.timer == Game._game.fuseTime:
			self.electrifying = True
			self.calculate()
		if self.timer == Game._game.fuseTime + fps*2:
			for net in self.network:
				for worm in net[1]:
					boom(worm.pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
				boom(net[0].pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
			boom(self.pos + vectorUnitRandom() * uniform(1,5), randint(10,16))
			self.dead = True
	def calculate(self):
		for worm in PhysObj._worms:
			if worm in Game._game.objectUnderControl.team.worms:
				continue
			if dist(self.pos, worm.pos) < 150:
				self.worms.append(worm)
		for selfWorm in self.worms:
			net = []
			for worm in PhysObj._worms:
				if worm == selfWorm or worm in self.used or worm in self.worms or worm in Game._game.objectUnderControl.team.worms:
					continue
				if dist(selfWorm.pos, worm.pos) < 150 and not worm in self.worms:
					net.append(worm)
					self.used.append(worm)
			self.network.append((selfWorm, net))
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		for worm in self.worms:
			drawLightning(self, worm, (250, 250, 21))
		for net in self.network:
			for worm in net[1]:
				drawLightning(net[0], worm, (250, 250, 21))

def firePortal(start, direction):
	steps = 500
	for t in range(5,steps):
		testPos = start + direction * t
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
			Bro = (self.pos - Game._game.objectUnderControl.pos)
			angle = self.direction.getAngle() - (self.pos - Game._game.objectUnderControl.pos).getAngle()
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
	def draw(self):
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
		self.surf.blit(Game._game.sprites, (0,0), (0, 64, 48, 16))
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
						Commentator.comment(choice(comments))
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
		if isOnMap(self.pos.vec2tupint()):
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
		if self.pos.y >= Game._game.map_manager.game_map.get_height() - Water.level:
			Game._game.nonPhysToRemove.append(self)
			Venus._reg.remove(self)
	def mutate(self):
		if self.mutant:
			return
		self.mutant = True
		self.surf.fill((0, 125, 255, 100), special_flags=pygame.BLEND_MULT)
	def draw(self):
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
				if Game._game.mapClosed:
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
				self.damage(self.vel.getMag() * 1.5 * Game._game.fallDamageMult)
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
		
		
	def draw(self):
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "pokeball")
		self.angle = 0
	def damage(self, value, damageType=0):
		if damageType == 1:
			return
		dmg = int(value * Game._game.damageMult)
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
		
		if self.timer >= Game._game.fuseTime and self.timer <= Game._game.fuseTime + fps*2 and not self.hold:
			self.stable = False
			closer = [None, 7000]
			for worm in PhysObj._worms:
				distance = dist(self.pos, worm.pos)
				if distance < closer[1]:
					closer = [worm, distance]
			if closer[1] < 50:
				self.hold = closer[0]
				
		if self.timer == Game._game.fuseTime + fps*2:
			if self.hold:
				PhysObj._reg.remove(self.hold)
				PhysObj._worms.remove(self.hold)
				self.hold.team.worms.remove(self.hold)
				if self.hold.flagHolder:
					self.hold.flagHolder = False
					self.hold.team.flagHolder = False
					Flag(self.hold.pos)
				self.name = pixelFont5.render(self.hold.nameStr, False, self.hold.team.color)
				name = self.hold.nameStr
				color = self.hold.team.color
				comments = [
					[{'text': name, 'color': color}, {'text': ', i choose you'}],
					[{'text': "gotta catch 'em al"}],
					[{'text': name, 'color': color}, {'text': ' will help beat the next gym leader'}],
				]
				Commentator.comment(choice(comments))
			else:
				self.dead = True
		
		if self.timer <= Game._game.fuseTime + fps*2 + fps/2:
			gameDistable()
		
		if self.vel.getMag() > 0.25:
			self.angle -= self.vel.x*4
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		if self.timer >= Game._game.fuseTime and self.timer < Game._game.fuseTime + fps*2 and self.hold:
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
	def draw(self):
		if not self.speed == 0:
			index = int((self.timer*(self.speed/3) % 12)/3)
		else:
			index = 0	
		win.blit(Game._game.sprites, point2world(self.pos - Vector(16,16)/2), ((index*16, 48), (16,16)))

def fireLaser(start, direction):
	hit = False
	color = (254, 153, 35)
	square = [Vector(1,5), Vector(1,-5), Vector(-10,-5), Vector(-10,5)]
	for i in square:
		i.rotate(direction.getAngle())
	
	for t in range(5,500):
		testPos = start + direction * t
		# extra.append((testPos.x, testPos.y, (255,0,0), 3))
		
		if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			Game._game.layersCircles[0].append((color, start, 5))
			Game._game.layersCircles[0].append((color, testPos, 5))
			Game._game.layersLines.append((color, start, testPos, 10, 1))
			continue
			
		# if hits worm:
		for worm in PhysObj._worms:
			if worm == Game._game.objectUnderControl:
				continue
			if distus(testPos, worm.pos) < (worm.radius + 2) * (worm.radius + 2):
				if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
				Game._game.layersCircles[0].append((color, start + direction * 5, 5))
				Game._game.layersCircles[0].append((color, testPos, 5))
				Game._game.layersLines.append((color, start + direction * 5, testPos, 10, 1))
				
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
			Game._game.layersCircles[0].append((color, start + direction * 5, 5))
			Game._game.layersCircles[0].append((color, testPos, 5))
			Game._game.layersLines.append((color, start + direction * 5, testPos, 10, 1))
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "guided missile")
		self.radius = 3
	def applyForce(self):
		pass
	def turn(self, direc):
		self.vel.rotate(direc * 0.1)
	def step(self):
		Game._game.camTrack = self
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
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level or testPos.x < 0:
				if Game._game.mapClosed:
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
			if randint(0,30) == 1 or Game._game.megaTrigger:
				for i in range(80):
					s = Fire(self.pos, 5)
					s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,4)
			self.removeFromGame()
		if self.pos.y > Game._game.map_manager.game_map.get_height():
			self.removeFromGame()
	def draw(self):
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "flare")
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
		Game._game.lights.append((self.pos[0], self.pos[1], self.lightRadius, (100,0,0,100)))
	def draw(self):
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
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level or testPos.x < 0:
				if Game._game.mapClosed:
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
		pos = self.pos + response * (Game._game.objectUnderControl.radius + 2)
		Game._game.objectUnderControl.pos = pos
	def draw(self):
		WeaponManager._wm.blitWeaponSprite(win, point2world(self.pos - Vector(8,8)), "ender pearl")

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
		if Game._game.objectUnderControl:
			if not Game._game.objectUnderControl in PhysObj._worms:
				return
			if dist(Game._game.objectUnderControl.pos, self.pos) < self.radius + Game._game.objectUnderControl.radius:
				# worm has flag
				Game._game.objectUnderControl.flagHolder = True
				Game._game.objectUnderControl.team.flagHolder = True
				self.removeFromGame()
				Flag.flags.remove(self)
				return
	def outOfMapResponse(self):
		Flag.flags.remove(self)
		p = deployPack(Flag)
		Game._game.camTrack = p
	def draw(self):
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
		TeamManager._tm.currentTeam.points += 1
		if len(ShootingTarget._reg) < ShootingTarget.numTargets:
			ShootingTarget()
		# add to kill list(surf, name, amount):
		Game._game.addToScoreList()
	def draw(self):
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius))
		pygame.draw.circle(win, RED, point2world(self.pos), int(self.radius - 4))
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius - 8))

class Distorter(Grenade):# EXPERIMENTAL
	def deathResponse(self):
		width = randint(100, 150)
		rotMult = uniform(0.05, 0.1)
		arr = []
		for x in range(int(self.pos.x) - width//2, int(self.pos.x) + width//2):
			for y in range(int(self.pos.y) - width//2, int(self.pos.y) + width//2):
				if dist(Vector(x,y), self.pos) > width//2:
					continue
				rot = (dist(Vector(x,y), self.pos) - width//2) * rotMult
				direction = Vector(x,y) - self.pos
				direction.rotate(rot)
				getAt = (self.pos + direction)
				getAt = getAt.vec2tupint()
				if getAt[0] < 0 or getAt[0] >= Game._game.map_manager.game_map.get_width() or getAt[1] < 0 or getAt[1] >= Game._game.map_manager.game_map.get_height():
					arr.append((0,0,0,0))
				else:
					pixelColor = Game._game.map_manager.ground_map.get_at(getAt)
					arr.append(pixelColor)
		# for worm in PhysObj._worms:
			# if dist(self.pos, worm.pos) < width//2:
				# rot = (dist(worm.pos, self.pos) - width//2) * 0.1
				# direction = worm.pos - self.pos
				# direction.rotate(rot)
				# getAt = (self.pos + direction)
				# worm.pos = getAt
		for x in range(int(self.pos.x) - width//2, int(self.pos.x) + width//2):
			for y in range(int(self.pos.y) - width//2, int(self.pos.y) + width//2):
				if dist(Vector(x,y), self.pos) > width//2:
					continue
				color = arr.pop(0)
				if len(color) == 4 and color[3] == 0:
					Game._game.map_manager.game_map.set_at((x,y), SKY)
				else:
					Game._game.map_manager.game_map.set_at((x,y), GRD)
				Game._game.map_manager.ground_map.set_at((x,y), color)

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
	def draw(self):
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

def fireFusrodah(start, direction):# EXPERIMENTAL
	# layersCircles[0].append(((0,0,0), start + direction * 40, 40))
	# layersCircles[0].append(((0,0,0), start + direction * 80, 26))
	# layersCircles[0].append(((0,0,0), start + direction * 110, 10))
	
	circles = [(start + direction * 40, 40), (start + direction * 80, 26), (start + direction * 110, 10)]
	tagged = []
	for circle in circles:
		for worm in PhysObj._reg:
			if worm == Game._game.objectUnderControl:
				continue
			if not worm in tagged and dist(worm.pos, circle[0]) < circle[1]:
				tagged.append(worm)
				worm.vel += (direction * 6) + Vector(0, -2)

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
		self.ignore = [Game._game.objectUnderControl]
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
			stain(self.pos, Game._game.imageBlood, Game._game.imageBlood.get_size(), False)
		if len(self.worms) > 1:
			name = Game._game.objectUnderControl.nameStr
			color = Game._game.objectUnderControl.team.color
			Commentator.comment([{'text': name, 'color': color}, {'text': ' the impaler!'}])
	def draw(self):
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
		self.surf.blit(Game._game.sprites, (0,0), (70,48,6,6))
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
	def draw(self):
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
		self.clockwise = Game._game.objectUnderControl.facing
		self.timer = 0
		self.surf = pygame.Surface((6,6), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (64,48, 6,6))
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

		Game._game.camTrack = self.obj(finalPos, finalAnchor, self.clockwise)
	def draw(self):
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
		self.acc.y -= Game._game.globalGravity * 0.3
		self.acc.x += Game._game.wind * 0.1 * Game._game.windMult * 0.5
	def step(self):
		gameDistable()
		self.applyForce()
		self.vel += self.acc * Game._game.dt
		self.pos += self.vel * Game._game.dt
		self.vel.x *= 0.99
		self.acc *= 0
		
		if self.radius <= self.grow and TimeManager._tm.timeOverall % 5 == 0:
			self.radius += 1 * Game._game.dt
			
		if not self.catch:
			for worm in PhysObj._reg:
				if worm == Game._game.objectUnderControl or worm in Bubble.cought or worm in Debrie._debries:
					continue
				if dist(worm.pos, self.pos) < worm.radius + self.radius:
					self.catch = worm
					Bubble.cought.append(self.catch)
					Game._game.camTrack = self
		else:
			self.catch.pos = self.pos
			self.catch.vel *= 0
		if Game._game.mapClosed and (self.pos.x - self.radius <= 0 or self.pos.x + self.radius >= Game._game.map_manager.game_map.get_width() - Water.level):
			self.burst()
		if self.pos.y < 0 and (Game._game.map_manager.is_ground_at((self.pos.x + self.radius, 0)) or Game._game.map_manager.is_ground_at((self.pos.x - self.radius, 0))):
			self.burst()
		if self.pos.y < -50:
			self.burst()
		if self.pos.y - self.radius <= 0 and Game._game.map_manager.is_ground_at((self.pos.x, 0)):
			self.burst()
		if randint(0, 300) == 1:
			if not Game._game.map_manager.is_ground_at(self.pos):
				self.burst()
	def burst(self):
		if self.catch:
			self.catch.vel = self.vel * 0.6
			if self == Game._game.camTrack:
				Game._game.camTrack = self.catch
		self.catch = None
		pygame.draw.circle(Game._game.map_manager.game_map, SKY, self.pos, self.radius)
		pygame.draw.circle(Game._game.map_manager.ground_map, SKY, self.pos, self.radius)
		Game._game.nonPhysToRemove.append(self)
		for i in range(min(int(self.radius), 8)):
			d = Debrie(self.pos + vectorUnitRandom() * self.radius, self.radius/5, [self.color], 1, False, True)
			d.vel += self.vel
			d.radius = 1
	def draw(self):
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
	def draw(self):
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "acid bottle")
	def secondaryStep(self):
		self.angle -= self.vel.x*4
	def deathResponse(self):
		boom(self.pos, 10)
		for i in range(40):
			s = Acid(self.pos, Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2))
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Seeker:
	def __init__(self, pos, direction, energy):
		self.initialize(pos, direction, energy)
		self.timer = 15 * fps
		self.target = HomingMissile.Target
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "seeker")
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
	def draw(self):
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
	def draw(self):
		dir = self.vel.x > 0
		width = 16
		height = 13
		frame = TimeManager._tm.timeOverall//2 % 3
		surf = pygame.Surface((16,16), pygame.SRCALPHA)
		surf.blit(Game._game.sprites, (0,0), (frame * 16,80, 16, 16))
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
			if worm in TeamManager._tm.currentTeam.worms or worm in self.bitten or worm in self.unreachable:
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
	def draw(self):
		width = 16
		height = 16
		frame = TimeManager._tm.timeOverall//2 % 5
		win.blit(Game._game.sprites, point2world(self.pos - Vector(8, 8)), ((frame * 16, 32), (16, 16)) )

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
	def draw(self):
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
			if worm in TeamManager._tm.currentTeam.worms:
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
	def draw(self):
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
		Game._game.camTrack = self
		self.speedLimit = 8
	def step(self):
		self.acc = seek(self, Game._game.objectUnderControl.pos, self.speedLimit, 1)
		
		self.vel += self.acc
		self.vel.limit(self.speedLimit)
		self.pos += self.vel
		
		self.angle += (0 - self.angle) * 0.1
		gameDistable()
		if distus(self.pos, Game._game.objectUnderControl.pos) < Game._game.objectUnderControl.radius * Game._game.objectUnderControl.radius * 2:
			Game._game.nonPhysToRemove.append(self)
			Game._game.holdArtifact = True
	def draw(self):
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
		Game._game.camTrack = self
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
		if dist(Game._game.objectUnderControl.pos, self.pos) < self.radius + Game._game.objectUnderControl.radius + 5 and not Game._game.objectUnderControl.health <= 0\
			and not len(Game._game.objectUnderControl.team.artifacts) > 0: 
			self.removeFromGame()
			Game._game.worldArtifacts.remove(self.artifact)
			self.commentPicked()
			TeamManager._tm.currentTeam.artifacts.append(self.artifact)
			# add artifacts moves:
			WeaponManager._wm.addArtifactMoves(self.artifact)
			return
		self.trenaryStep()
	def removeFromGame(self):
		super().removeFromGame()
		Game._game.worldArtifacts.append(self.artifact)
	def trenaryStep(self):
		pass
	def draw(self):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Mjolnir(Artifact):
	def getArtifact(self):
		return MJOLNIR
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (0,112,16,16))
	def commentCreation(self):
		Commentator.comment([{'text': "a gift from the gods"}])
	def commentPicked(self):
		Commentator.comment([{'text': Game._game.objectUnderControl.nameStr, 'color': TeamManager._tm.currentTeam.color}, {'text': " is worthy to wield mjolnir!"}])
	def trenaryStep(self):
		if self.vel.getMag() > 1:
			self.angle = -degrees(self.vel.getAngle()) - 90
	def collisionRespone(self, ppos):
		vel = self.vel.getMag()
		if vel > 4:
			boom(self.pos, max(20, 2 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	def draw(self):
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
			
		Game._game.objectUnderControl.pos = vectorCopy(self.pos)
		Game._game.objectUnderControl.vel = Vector()
	def collisionRespone(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= Game._game.map_manager.game_map.get_width() or testPos.y >= Game._game.map_manager.game_map.get_height() - Water.level or testPos.x < 0:
				if Game._game.mapClosed:
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
		pos = self.pos + response * (Game._game.objectUnderControl.radius + 2)
		Game._game.objectUnderControl.pos = pos
		
	def removeFromGame(self):
		PhysObj._toRemove.append(self)
		MjolnirFly.flying = False
		Game._game.holdArtifact = True
	def draw(self):
		surf = pygame.transform.rotate(Game._game.imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirStrike:
	def __init__(self):
		self.pos = Game._game.objectUnderControl.pos
		Game._game.nonPhys.append(self)
		Game._game.holdArtifact = False
		self.stage = 0
		self.timer = 0
		self.angle = 0
		self.worms = []
		self.facing = Game._game.objectUnderControl.facing
		Game._game.objectUnderControl.boomAffected = False
		self.radius = 0
	def step(self):
		self.pos = Game._game.objectUnderControl.pos
		self.facing = Game._game.objectUnderControl.facing
		if self.stage == 0:
			self.angle += 1
			if self.timer >= fps * 4:
				self.stage = 1
				self.timer = 0
			# electrocute:
			self.worms = []
			for worm in PhysObj._worms:
				if worm in TeamManager._tm.currentTeam.worms:
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
				Game._game.objectUnderControl.boomAffected = True
		self.timer += 1
		gameDistable()
	def draw(self):
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
		self.surf.blit(Game._game.sprites, (0,0), (48, 64, 16,16))

		self.windAffected = True
		self.turbulance = vectorUnitRandom()
	def commentCreation(self):
		Commentator.comment([{'text': "a leaf of heavens tree"}])
	def commentPicked(self):
		Commentator.comment([{'text': Game._game.objectUnderControl.nameStr, 'color': TeamManager._tm.currentTeam.color}, {'text': "  became master of plants"}])
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
	def draw(self):
		pass

def leaf(pos, direction, color):
	# create procedural leaf
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
	def draw(self):
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
	def draw(self):
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
	def draw(self):
		for p in self.springs:
			p.draw()

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
	def draw(self):
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
	def draw(self):
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "icicle")
		self.timer = 0
	def secondaryStep(self):
		if randint(0,5) == 0:
			Frost(self.pos + vectorUnitRandom() * 3)
	def destroy(self):
		Game._game.nonPhysToRemove.append(self)
		for i in range(8):
			d = Debrie(self.pos, 5, [(200,200,255)], 1, False, True)
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
		Game._game.camTrack = worm
		for i in range(8):
			d = Debrie(self.pos, 5, [(200,200,255)], 1, False, True)
		self.destroy()
	def draw(self):
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())//2))

def calcEarthSpikePos():
	amount = (pi/2 - Game._game.objectUnderControl.shootAngle) * Game._game.objectUnderControl.facing / pi
	xFromWorm = Game._game.objectUnderControl.pos.x + Game._game.objectUnderControl.facing * amount * 70
	if Game._game.map_manager.is_ground_at(Vector(xFromWorm, Game._game.objectUnderControl.pos.y)):
		y = Game._game.objectUnderControl.pos.y
		while Game._game.map_manager.is_ground_at(Vector(xFromWorm, y)):
			y -= 2
			if y < 0:
				return None
	else:
		y = Game._game.objectUnderControl.pos.y
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
		self.surf.blit(Game._game.sprites, (0,0), ((32, 96), (32, 32)))
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
			stain(self.pos - Vector(0, 3), Game._game.imageHole, (32,32), True)
			
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
					if obj in PhysObj._worms and not obj in TeamManager._tm.currentTeam.worms:
						obj.damage(randint(25,35))
			
			Game._game.map_manager.ground_map.blit(self.surf, rectPos)
			surf = self.surf.copy()
			pixels = pygame.PixelArray(surf)
			for i in self.colors:
				pixels.replace(i, GRD)
			del pixels
			Game._game.map_manager.game_map.blit(surf, rectPos)
		self.timer += 1
	def draw(self):
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
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "fire ball")
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
	def draw(self):
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
		win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())//2))

class Tornado:
	def __init__(self):
		self.width = 30
		self.pos = Game._game.objectUnderControl.pos + Vector(Game._game.objectUnderControl.radius + self.width / 2, 0) * Game._game.objectUnderControl.facing
		self.facing = Game._game.objectUnderControl.facing
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
	def draw(self):
		for i, swirl in enumerate(self.swirles):
			five = [point2world(Vector(swirl[0] * cos(swirl[2] + t/5) + self.pos.x, 10 * i + swirl[1] * sin(swirl[2] + t/5))) for t in range(5)]
			pygame.draw.lines(win, (255,255,255), False, five)

class Avatar(Artifact):
	def getArtifact(self):
		return AVATAR
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(Game._game.sprites, (0,0), (0,112,16,16))
	def commentCreation(self):
		Commentator.comment([{'text': "who is the next avatar?"}])
	def commentPicked(self):
		Commentator.comment([{'text': 'everything changed when the '}, {'text': TeamManager._tm.currentTeam.name, 'color': TeamManager._tm.currentTeam.color}, {'text': ' attacked'}])
	def trenaryStep(self):
		self.angle -= self.vel.x*4

class GunShell(PhysObj):
	def __init__(self, pos, vel=None, index=0):
		self.initialize()
		self.pos = pos
		self.vel = Vector(-uniform(1,2.5) * Game._game.objectUnderControl.facing, uniform(-8,-5))
		if vel:
			self.vel = vel
		self.radius = 2
		self.bounceBeforeDeath = 4
		self.index = index
		self.damp = 0.2
		if index == 0:
			self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
			self.surf.blit(Game._game.sprites, (0,0), (16,112,16,16))
		self.angle = uniform(0, 2*pi)
	def applyForce(self):
		self.acc.y += Game._game.globalGravity * 2.5
	def secondaryStep(self):
		self.angle -= self.vel.x*4
	def draw(self):
		if self.index == 0:
			angle = 45 * round(self.angle / 45)
			surf = pygame.transform.rotate(self.surf, angle)
			win.blit(surf, point2world(self.pos - tup2vec(surf.get_size())/2))
		if self.index == 1:
			pygame.draw.circle(win, (25,25,25), point2world(self.pos), 3, 1)

class PickAxe:
	_pa = None
	def __init__(self):
		PickAxe._pa = self
		Game._game.nonPhys.append(self)
		self.count = 6
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "pick axe")
		self.animating = 0
	def mine(self):
		worm = Game._game.objectUnderControl
		position = worm.pos + vectorFromAngle(worm.shootAngle, 20)
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

		colors = []
		for i in range(10):
			sample = (position + Vector(8,8) + vectorUnitRandom() * uniform(0,8)).vec2tupint()
			if isOnMap(sample):
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
		if not Game._game.objectUnderControl.alive:
			Game._game.nonPhysToRemove.append(self)
			PickAxe._pa = None
	def draw(self):
		worm = Game._game.objectUnderControl
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
		worm = Game._game.objectUnderControl
		position = worm.pos + vectorFromAngle(worm.shootAngle, 20)
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)

		pygame.draw.rect(Game._game.map_manager.game_map, GRD, (position, Vector(16,16)))
		if position + Vector(0,16) in self.locations:
			WeaponManager._wm.blitWeaponSprite(Game._game.map_manager.ground_map, position, "build")
			Game._game.map_manager.ground_map.blit(Game._game.sprites, position + Vector(0,16), (80,112,16,16))
		elif position + Vector(0,-16) in self.locations:
			Game._game.map_manager.ground_map.blit(Game._game.sprites, position, (80,112,16,16))
		else:
			WeaponManager._wm.blitWeaponSprite(Game._game.map_manager.ground_map, position, "build")

		self.locations.append(position)
		
		self.count -= 1
		if self.count == 0:
			return True
		return False
	def step(self):
		if self.count == 0:
			Game._game.nonPhysToRemove.append(self)
			MineBuild._mb = None
			
		if not Game._game.objectUnderControl.alive:
			Game._game.nonPhysToRemove.append(self)
			MineBuild._mb = None
	def draw(self):
		worm = Game._game.objectUnderControl
		position = worm.pos + vectorFromAngle(worm.shootAngle, 20)
		# closest grid of 16
		position = Vector(int(position.x / 16) * 16, int(position.y / 16) * 16)
		pygame.draw.rect(win, (255,255,255), (point2world(position), Vector(16,16)), 1)

class PickAxeArtifact(Artifact):
	def getArtifact(self):
		return MINECRAFT
	def setSurf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		WeaponManager._wm.blitWeaponSprite(self.surf, (0,0), "pick axe")
	def commentCreation(self):
		Commentator.comment([{'text': "a game changer"}])
	def commentPicked(self):
		Commentator.comment([{'text': 'its mining time'}])
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
			Game._game.dt *= 0.9
			if Game._game.dt < 0.1:
				self.state = "fast"
		elif self.state == "fast":
			Game._game.dt *= 1.1
			if Game._game.dt > 1:
				Game._game.dt = 1
				Game._game.nonPhysToRemove.append(self)
	def draw(self):
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
				FireWork(obj.pos, Game._game.objectUnderControl.team.color)
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
				if obj == Game._game.objectUnderControl or obj in self.objects:
					continue
				if distus(obj.pos, Game._game.objectUnderControl.pos) < 15*15:
					candidates.append(obj)
			# take the closest
			if len(candidates) > 0:
				candidates.sort(key = lambda x: distus(x.pos, Game._game.objectUnderControl.pos))
				self.objects.append(candidates[0])
			self.picked += 1
			if self.picked >= 3:
				self.state = "ready"
		elif self.state == "ready":
			self.state = "thrusting"
			for obj in self.objects:
				obj.vel += Vector(randint(-3,3), -2)
			if len(self.objects) > 0:
				Game._game.camTrack = choice(self.objects)
			return True
		return False
	def draw(self):
		if self.state in ["tag"]:
			for obj in PhysObj._reg:
				if obj == Game._game.objectUnderControl or obj in self.objects:
					continue
				if distus(obj.pos, Game._game.objectUnderControl.pos) < 15*15:
					drawTarget(obj.pos)
		
		for obj in self.objects:
			WeaponManager._wm.blitWeaponSprite(win, point2world(obj.pos - Vector(8,8)), "fireworks")

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
				vel += Vector(0, 0.5 * Game._game.globalGravity)
				vel *= 0.9
				self.blasts[i][0] += vel
				Blast(self.blasts[i][0] + vectorUnitRandom(), randint(3,6), 150, color=self.color)
		
		self.timer += 1
		if self.timer > 0.9 * fps:
			if self in Game._game.nonPhys:
				Game._game.nonPhysToRemove.append(self)
	def draw(self):
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
			Trampoline._sprite.blit(Game._game.sprites, (0,0), (100, 117, 24, 7))
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
				if abs(obj.vel.y) < Game._game.jumpVelocity:
					obj.vel.y = -Game._game.jumpVelocity
				if Game._game.state == WAIT_STABLE:
					obj.vel.x += uniform(-0.5,0.5)
	def spring(self, amount):
		self.offset = -amount
		self.stable = False
	def draw(self):
		startPos = self.anchor.y
		endPos = self.pos.y + self.offset - 4
		i = startPos
		while i > endPos:
			win.blit(Game._game.sprites, point2world((self.pos.x - 5, i)), (107, 124, 10, 4))
			i -= 4
		win.blit(Trampoline._sprite, point2world(self.pos + Vector(0, self.offset) - self.size / 2))

################################################################################ Weapons setup

def fire(weapon = None):
	global decrease
	if not weapon:
		weapon = WeaponManager._wm.currentWeapon
	decrease = True
	if Game._game.objectUnderControl:
		weaponOrigin = vectorCopy(Game._game.objectUnderControl.pos)
		weaponDir = vectorFromAngle(Game._game.objectUnderControl.shootAngle)
		energy = Game._game.energyLevel
		
	if TimeTravel._tt.timeTravelFire:
		decrease = False
		weaponOrigin = TimeTravel._tt.timeTravelList["weaponOrigin"]
		energy = TimeTravel._tt.timeTravelList["energy"]
		weaponDir = TimeTravel._tt.timeTravelList["weaponDir"]
	
	avail = True
	w = None
	if weapon.name == "missile":
		w = Missile(weaponOrigin, weaponDir, energy)
	elif weapon.name == "grenade":
		w = Grenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "mortar":
		w = Mortar(weaponOrigin, weaponDir, energy)
	elif weapon.name == "petrol bomb":
		w = PetrolBomb(weaponOrigin, weaponDir, energy)
	elif weapon.name == "TNT":
		w = TNT(weaponOrigin)
		w.vel.x = Game._game.objectUnderControl.facing * 0.5
		w.vel.y = -0.8
	elif weapon.name == "shotgun":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 3 # three shots
		fireShotgun(weaponOrigin, weaponDir) # fire
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
	elif weapon.name == "flame thrower":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 70
		fireFlameThrower(weaponOrigin, weaponDir)
		if not Game._game.shotCount == 0:
			Game._game.shotCount -= 1
			Game._game.nextState = FIRE_MULTIPLE
		else:
			Game._game.nextState = PLAYER_CONTROL_2
			decrease = True
	elif weapon.name == "sticky bomb":
		w = StickyBomb(weaponOrigin, weaponDir, energy)
	elif weapon.name == "minigun":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 20
			if randint(0,50) == 1 or Game._game.megaTrigger:
				Game._game.shotCount = 60
		
		fireMiniGun(weaponOrigin, weaponDir)
		if not Game._game.shotCount == 0:
			Game._game.shotCount -= 1
			Game._game.nextState = FIRE_MULTIPLE
		else:
			Game._game.nextState = PLAYER_CONTROL_2
			decrease = True
	elif weapon.name == "mine":
		w = Mine(weaponOrigin, fps * 2.5)
		w.vel.x = Game._game.objectUnderControl.facing * 0.5
	elif weapon.name == "baseball":
		Baseball()
	elif weapon.name == "gas grenade":
		w = GasGrenade(weaponOrigin, weaponDir, energy)
	elif weapon.name == "gravity missile":
		w = GravityMissile(weaponOrigin, weaponDir, energy)
	elif weapon.name == "gamma gun":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 2 # two shots
		fireGammaGun(weaponOrigin, weaponDir) # fire
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
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
		w = SentryGun(weaponOrigin, TeamManager._tm.currentTeam.color)
		w.pos.y -= Game._game.objectUnderControl.radius + w.radius
	elif weapon.name == "bee hive":
		w = BeeHive(weaponOrigin, weaponDir, energy)
	elif weapon.name == "bunker buster":
		w = BunkerBuster(weaponOrigin, weaponDir, energy)
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
		for worm in Game._game.objectUnderControl.team.worms:
			w.bitten.append(worm)
	elif weapon.name == "artillery assist":
		w = Artillery(weaponOrigin, weaponDir, energy)
	elif weapon.name == "long bow":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 3 # three shots
		w = LongBow(weaponOrigin + weaponDir * 5, weaponDir, LongBow._sleep) # fire
		w.ignore = Game._game.objectUnderControl
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
		avail = False
	elif weapon.name == "sheep":
		w = Sheep(weaponOrigin + Vector(0,-5))
		w.facing = Game._game.objectUnderControl.facing
	elif weapon.name == "rope":
		angle = weaponDir.getAngle()
		if angle > 0:
			decrease = False
		else:
			decrease = False
			shootRope(weaponOrigin, weaponDir)
		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "raging bull":
		w = Bull(weaponOrigin + Vector(0,-5))
		w.facing = Game._game.objectUnderControl.facing
		w.ignore.append(Game._game.objectUnderControl)
	elif weapon.name == "electro boom":
		w = ElectroBoom(weaponOrigin, weaponDir, energy)
	elif weapon.name == "portal gun":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 2
		firePortal(weaponOrigin, weaponDir)
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "parachute":
		if Game._game.objectUnderControl.parachuting:
			Game._game.objectUnderControl.toggleParachute()
			decrease = False
		else:
			if Game._game.objectUnderControl.vel.y > 1:
				Game._game.objectUnderControl.toggleParachute()
			else:
				decrease = False
		Game._game.nextState = PLAYER_CONTROL_1
	elif weapon.name == "pokeball":
		w = PokeBall(weaponOrigin, weaponDir, energy)
	elif weapon.name == "green shell":
		w = GreenShell(weaponOrigin + Vector(0,-5))
		w.facing = Game._game.objectUnderControl.facing
		w.ignore.append(Game._game.objectUnderControl)
	elif weapon.name == "laser gun":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 70
		fireLaser(weaponOrigin, weaponDir)
		if not Game._game.shotCount == 0:
			Game._game.shotCount -= 1
			Game._game.nextState = FIRE_MULTIPLE
		else:
			Game._game.nextState = PLAYER_CONTROL_2
			decrease = True
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
		if randint(0, 10) == 0 or Game._game.megaTrigger:
			w = Raon(weaponOrigin, weaponDir, energy * 1.08)
			w = Raon(weaponOrigin, weaponDir, energy * 0.92)
	elif weapon.name == "snail":
		w = SnailShell(weaponOrigin, weaponDir, energy)
	elif weapon.name == "fus ro duh":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 3 # three shots
		fireFusrodah(weaponOrigin, weaponDir) # fire
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
	elif weapon.name == "spear":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 2
		w = Spear(weaponOrigin, weaponDir, energy * 0.95)
		# w.ignore = Game._game.objectUnderControl
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
		avail = False
	elif weapon.name == "distorter":
		w = Distorter(weaponOrigin, weaponDir, energy)
	elif weapon.name == "bubble gun":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 10
		
		u = Bubble(getClosestPosAvail(Game._game.objectUnderControl), weaponDir, uniform(0.5, 0.9))
		if not Game._game.shotCount == 0:
			Game._game.shotCount -= 1
			Game._game.nextState = FIRE_MULTIPLE
		else:
			Game._game.nextState = PLAYER_CONTROL_2
			Game._game.camTrack = u
			decrease = True
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
		position = Game._game.objectUnderControl.pos + vectorFromAngle(Game._game.objectUnderControl.shootAngle, 20)
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
	elif weapon.name == "razor leaf":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 50
		
		RazorLeaf(weaponOrigin + weaponDir * 10, weaponDir)
		if not Game._game.shotCount == 0:
			Game._game.shotCount -= 1
			Game._game.nextState = FIRE_MULTIPLE
		else:
			Game._game.nextState = PLAYER_CONTROL_2
			decrease = True
	elif weapon.name == "icicle":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 4
		w = Icicle(weaponOrigin + weaponDir * 5, weaponDir) # fire
		w.ignore = Game._game.objectUnderControl
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
		avail = False
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
	elif weapon.name == "fire ball":
		decrease = False
		if Game._game.state == PLAYER_CONTROL_1:
			Game._game.shotCount = 3
		w = FireBall(weaponOrigin + weaponDir * 5, weaponDir) # fire
		w.ignore = Game._game.objectUnderControl
		Game._game.shotCount -= 1
		if Game._game.shotCount > 0:
			Game._game.nextState = FIRE_MULTIPLE
		if Game._game.shotCount == 0:
			decrease = True
			Game._game.nextState = PLAYER_CONTROL_2
		avail = False
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

	if w and not TimeTravel._tt.timeTravelFire: Game._game.camTrack = w	
	
	# position to available position
	if w and avail:
		availpos = getClosestPosAvail(w)
		if availpos:
			w.pos = availpos
	
	if decrease:
		if TeamManager._tm.currentTeam.ammo(weapon) != -1:
			TeamManager._tm.currentTeam.ammo(weapon, -1)
		WeaponManager._wm.renderWeaponCount()

	Game._game.fireWeapon = False
	Game._game.energyLevel = 0
	Game._game.energising = False
	
	if TimeTravel._tt.timeTravelFire:
		TimeTravel._tt.timeTravelFire = False
		return
	
	Game._game.state = Game._game.nextState
	if Game._game.state == PLAYER_CONTROL_2: TimeManager._tm.timeRemaining(Game._game.retreatTime)
	
	# for uselist:
	if Game._game.useListMode and (Game._game.state == PLAYER_CONTROL_2 or Game._game.state == WAIT_STABLE):
		globals.weapon_manager.add_to_cool_down(globals.weapon_manager.currentWeapon)

def fireClickable():
	decrease = True
	if not Game._game.radial_weapon_menu is None:
		return
	if TeamManager._tm.currentTeam.ammo(WeaponManager._wm.currentWeapon) == 0:
		return
	mousePos = pygame.mouse.get_pos()
	mousePosition = Vector(mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y)
	addToUsed = True
	
	if WeaponManager._wm.currentWeapon == "girder":
		Game._game.girder(mousePosition)
	elif WeaponManager._wm.currentWeapon == "teleport":
		Game._game.objectUnderControl.pos = mousePosition
		addToUsed = False
	elif WeaponManager._wm.currentWeapon == "airstrike":
		fireAirstrike(mousePosition)
	elif WeaponManager._wm.currentWeapon == "mine strike":
		fireMineStrike(mousePosition)
	elif WeaponManager._wm.currentWeapon == "napalm strike":
		fireNapalmStrike(mousePosition)

	if decrease and TeamManager._tm.currentTeam.ammo(WeaponManager._wm.currentWeapon) != -1:
		TeamManager._tm.currentTeam.ammo(WeaponManager._wm.currentWeapon, -1)
	
	if Game._game.useListMode and (Game._game.nextState == PLAYER_CONTROL_2 or Game._game.nextState == WAIT_STABLE) and addToUsed:
		globals.weapon_manager.add_to_cool_down(globals.weapon_manager.currentWeapon)
	
	WeaponManager._wm.renderWeaponCount()
	TimeManager._tm.timeRemaining(Game._game.retreatTime)
	Game._game.state = Game._game.nextState
  
def fireUtility(weapon = None):
	if not weapon:
		weapon = WeaponManager._wm.currentWeapon
	decrease = True
	if weapon == "moon gravity":
		Game._game.globalGravity = 0.1
		Commentator.comment([{'text': "small step for wormanity"}])
	elif weapon == "double damage":
		Game._game.damageMult *= 2
		Game._game.radiusMult *= 1.5
		comments = ["that's will hurt", "that'll leave a mark"]
		Commentator.comment([{'text': choice(comments)}])
	elif weapon == "aim aid":
		Game._game.aimAid = True
		Commentator.comment([{'text': "snipe em'"}])
	elif weapon == "teleport":
		WeaponManager._wm.switchWeapon(weapon)
		decrease = False
	elif weapon == "switch worms":
		if Game._game.switchingWorms:
			decrease = False
		Game._game.switchingWorms = True
		Commentator.comment([{'text': "the ol' switcheroo"}])
	elif weapon == "time travel":
		if not Game._game.timeTravel:
			TimeTravel._tt.timeTravelInitiate()
		Commentator.comment([{'text': "great scott"}])
	elif weapon == "jet pack":
		Game._game.objectUnderControl.toggleJetpack()
	elif weapon == "flare":
		WeaponManager._wm.switchWeapon(weapon)
		decrease = False
	elif weapon == "control plants":
		PlantControl()
	
	if decrease:
		TeamManager._tm.currentTeam.ammo(weapon, -1)

################################################################################ Teams
class Team:
	def __init__(self, nameList=None, color=(255,0,0), name = ""):
		if nameList:
			self.nameList = nameList
		else:
			self.nameList = []
		self.color = color
		self.weaponCounter = WeaponManager._wm.basic_set.copy()
		self.worms = []
		self.name = name
		self.damage = 0
		self.killCount = 0
		self.points = 0
		self.flagHolder = False
		self.artifacts = []
		self.hatOptions = None
		self.hatSurf = None
	def makeHat(self, index):
		self.hatSurf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.hatSurf.blit(Game._game.sprites, (0,0), (16 * (index % 8),16 * (index // 8),16,16))
		pixels = pygame.PixelArray(self.hatSurf)
		color = desaturate(self.color)
		pixels.replace((101, 101, 101), color)
		pixels.replace((81, 81, 81), tuple(max(i - 30,0) for i in color))
		del pixels
	def __len__(self):
		return len(self.worms)
	def addWorm(self, pos):
		if len(self.nameList) > 0:
			w = Worm(pos, self.nameList.pop(0), self)
			self.worms.append(w)
	def ammo(self, weapon: Weapon, amount: int=None, absolute: bool=False):
		# adding amount of weapon to team
		if amount and not absolute:
			self.weaponCounter[weapon.index] += amount
		elif amount and absolute:
			self.weaponCounter[weapon.index] = amount
		return self.weaponCounter[weapon.index]

class TeamManager:
	_tm = None
	def __init__(self):
		TeamManager._tm = self
		globals.team_manager = self

		self.teams: List[Team] = []
		for teamsData in ET.parse('wormsTeams.xml').getroot():
			newTeam = Team()
			newTeam.name = teamsData.attrib["name"]
			newTeam.hatOptions = teamsData.attrib["hat"]
			newTeam.color = tuple([int(i) for i in teamsData.attrib["color"][1:-1].split(",")])
			for team in teamsData:
				if team.tag == "worm":
					newTeam.nameList.append(team.attrib["name"])
			self.teams.append(newTeam)

		# hats
		hatsChosen = []
		for team in self.teams:
			indexChoice = []
			options = team.hatOptions.replace(" ", "").split(",")
			for option in options:
				if "-" in option:
					indexChoice += [i for i in range(int(option.split("-")[0]), int(option.split("-")[1]) + 1)]
				else:
					indexChoice.append(int(option))
			hatChoice = choice([hat for hat in indexChoice if hat not in hatsChosen])
			team.makeHat(hatChoice)
			hatsChosen.append(hatChoice)

		self.totalTeams = len(self.teams)
		self.currentTeam: Team = None
		self.teamChoser = 0
		self.nWormsPerTeam = 0
		shuffle(self.teams)

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
	for team in TeamManager._tm.teams:
		if len(team.worms) == 0:
			count += 1
	if count == TeamManager._tm.totalTeams - 1:
		# one team remains
		end = True
		for team in TeamManager._tm.teams:
			if not len(team.worms) == 0:
				lastTeam = team
	if count == TeamManager._tm.totalTeams:
		# no team remains
		end = True
	
	if Game._game.gameMode == TARGETS and len(ShootingTarget._reg) == 0 and ShootingTarget.numTargets <= 0:
		end = True
	
	if not end:
		return False
	# game end:
	dic = {}
	winningTeam = None
		
	# win bonuse:
	if Game._game.gameMode == CAPTURE_THE_FLAG:
		dic["mode"] = "CTF"
		pointsGame = True
		for team in TeamManager._tm.teams:
			if team.flagHolder:
				team.points += 1 + 3 # bonus points
				print("[ctf win, team", team.name, "got 3 bonus points]")
				break
		
	elif Game._game.gameMode == POINTS:
		pointsGame = True
		if lastTeam:
			lastTeam.points += 150 # bonus points
			dic["mode"] = "points"
			print("[points win, team", lastTeam.name, "got 150 bonus points]")
			
	elif Game._game.gameMode == TARGETS:
		pointsGame = True
		TeamManager._tm.currentTeam.points += 3 # bonus points
		dic["mode"] = "targets"
		print("[targets win, team", TeamManager._tm.currentTeam.name, "got 3 bonus points]")
	
	elif Game._game.gameMode == TERMINATOR:
		pointsGame = True
		if lastTeam:
			lastTeam.points += 3 # bonus points
			print("[team", lastTeam.name, "got 3 bonus points]")
		dic["mode"] = "terminator"
	
	elif Game._game.gameMode == ARENA:
		pointsGame = True
		if lastTeam:
			pass
		dic["mode"] = "arena"

	elif Game._game.gameMode == MISSIONS:
		pointsGame = True
		if lastTeam:
			pass
		dic["mode"] = "missions"
	
	# win points:
	if pointsGame:
		for team in TeamManager._tm.teams:
			print("[ |", team.name, "got", team.points, "points! | ]")
		teamsFinals = sorted(TeamManager._tm.teams, key = lambda x: x.points)
		winningTeam = teamsFinals[-1]
		print("[most points to team", winningTeam.name, "]")
		dic["points"] = str(winningTeam.points)
	# regular win:
	else:
		winningTeam = lastTeam
		if winningTeam:
			print("[last team standing is", winningTeam.name, "]")
		if Game._game.gameMode == DAVID_AND_GOLIATH:
			dic["mode"] = "davidVsGoliath"
	
	if end:
		if winningTeam != None:
			print("Team", winningTeam.name, "won!")
			dic["time"] = str(TimeManager._tm.timeOverall//fps)
			dic["winner"] = winningTeam.name
			if Game._game.mostDamage[1]:
				dic["mostDamage"] = str(int(Game._game.mostDamage[0]))
				dic["damager"] = Game._game.mostDamage[1]
			addToRecord(dic)
			if len(winningTeam.worms) > 0:
				Game._game.camTrack = winningTeam.worms[0]
			Commentator.comment([
				{'text': 'team '},
				{'text': winningTeam.name, 'color': winningTeam.color},
				{'text': ' Won!'}
			])
		else:
			Commentator.comment([{'text': 'its a tie!'}])
			print("Tie!")
		
		# add teams to dic
		dic["teams"] = {}
		for team in TeamManager._tm.teams:
			dic["teams"][team.name] = [team.color, team.points]

		Game._game.endGameDict = dic
		Game._game.nextState = WIN
		
		GroundScreenShoot = pygame.Surface((Game._game.map_manager.ground_map.get_width(), Game._game.map_manager.ground_map.get_height() - Water.level), pygame.SRCALPHA)
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
	Game._game.globalGravity = 0.2
	Game._game.damageMult = 0.8
	Game._game.radiusMult = 1
	Game._game.megaTrigger = False
	Game._game.aimAid = False
	if Game._game.timeTravel: TimeTravel._tt.timeTravelReset()
	if Game._game.objectUnderControl.jetpacking: Game._game.objectUnderControl.toggleJetpack()
	Game._game.switchingWorms = False
	if Worm.roped:
		Game._game.objectUnderControl.team.ammo("rope", -1)
		Worm.roped = False
	
	# update damage:
	wormName = Game._game.objectUnderControl.nameStr
	wormColor = Game._game.objectUnderControl.team.color
	if Game._game.damageThisTurn > Game._game.mostDamage[0]:
		Game._game.mostDamage = (Game._game.damageThisTurn, Game._game.objectUnderControl.nameStr)	
	if Game._game.damageThisTurn > int(Game._game.initialHealth * 2.5):
		if Game._game.damageThisTurn == 300:
			Commentator.comment([{'text': "THIS IS "}, {'text': wormName, 'color': wormColor}])
		else:
			comment = choice([
					[{'text': 'awesome shot '}, {'text': wormName, 'color': wormColor}, {'text': '!'}],
					[{'text': wormName, 'color': wormColor}, {'text': ' is on fire!'}],
					[{'text': wormName, 'color': wormColor}, {'text': ' shows no mercy'}],
				])
			Commentator.comment(comment)
	elif Game._game.damageThisTurn > int(Game._game.initialHealth * 1.5):
		comment = choice([
					[{'text': 'good shot '}, {'text': wormName, 'color': wormColor}, {'text': '!'}],
					[{'text': 'nicely done '}, {'text': wormName, 'color': wormColor}],
				])
		Commentator.comment(comment)
	
	TeamManager._tm.currentTeam.damage += Game._game.damageThisTurn
	if Game._game.gameMode in [POINTS, BATTLE]:
		TeamManager._tm.currentTeam.points = TeamManager._tm.currentTeam.damage + 50 * TeamManager._tm.currentTeam.killCount
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
					Game._game.camTrack = sentry
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
					Game._game.camTrack = raon
			Game._game.raoning = True
			Game._game.roundCounter -= 1
			Game._game.nextState = WAIT_STABLE
			return
		
	# deploy pack:
	if Game._game.deployPacks and Game._game.roundCounter % TeamManager._tm.totalTeams == 0 and not Game._game.deploying:
		Game._game.deploying = True
		Game._game.roundCounter -= 1
		Game._game.nextState = WAIT_STABLE
		comments = [
			[{'text': 'a jewel from the heavens!'}],
			[{'text': 'its raining crates, halelujah!'}],
			[{'text': ' '}],
		]
		Commentator.comment(choice(comments))
		for i in range(Game._game.packMult):
			w = deployPack(choice([HealthPack,UtilityPack, WeaponPack]))
			Game._game.camTrack = w
		if Game._game.darkness:
			for team in TeamManager._tm.teams:
				team.ammo("flare", 1)
				if team.ammo("flare") > 3:
					team.ammo("flare", -1)
		return
	
	# rise water:
	if Game._game.waterRise and not Game._game.waterRising:
		Water.rise(20)
		Game._game.nextState = WAIT_STABLE
		Game._game.roundCounter -= 1
		Game._game.waterRising = True
		return
	
	# throw artifact:
	if Game._game.artifactsMode:
		for team in TeamManager._tm.teams:
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
				dropArtifact(WeaponManager._wm.artifactDict[artifact], None, comment=True)
				Game._game.nextState = WAIT_STABLE
				Game._game.roundCounter -= 1
				return
	
	Game._game.waterRising = False
	Game._game.raoning = False
	Game._game.deploying = False
	Game._game.sentring = False
	Game._game.deployingArtifact = False
	
	if Game._game.roundCounter % TeamManager._tm.totalTeams == 0:
		Game._game.roundsTillSuddenDeath -= 1
		if Game._game.roundsTillSuddenDeath == 0:
			suddenDeath()
	
	if Game._game.gameMode == CAPTURE_THE_FLAG:
		for team in TeamManager._tm.teams:
			if team.flagHolder:
				team.points += 1
				break

	# update weapons delay (and targets)
	if Game._game.roundCounter % TeamManager._tm.totalTeams == 0:
		if Game._game.gameMode == TARGETS:
			ShootingTarget.numTargets -= 1
			if ShootingTarget.numTargets == 0:
				Commentator.comment([{'text': 'final targets round'}])
	
	# update stuff
	Debrie._debries = []
	Bubble.cought = []
	
	HomingMissile.showTarget = False
	# change Game._game.wind:
	Game._game.wind = uniform(-1,1)
	
	# flares reduction
	if Game._game.darkness:
		for flare in Flare._flares:
			if not flare in PhysObj._reg:
				Flare._flares.remove(flare)
			flare.lightRadius -= 10
	
	# sick:
	for worm in PhysObj._worms:
		if not worm.sick == 0 and worm.health > 5:
			worm.damage(min(int(5/Game._game.damageMult)+1, int((worm.health-5)/Game._game.damageMult) +1), 2)
		
	# select next team
	index = TeamManager._tm.teams.index(TeamManager._tm.currentTeam)
	index = (index + 1) % TeamManager._tm.totalTeams
	TeamManager._tm.currentTeam = TeamManager._tm.teams[index]
	while not len(TeamManager._tm.currentTeam.worms) > 0:
		index = TeamManager._tm.teams.index(TeamManager._tm.currentTeam)
		index = (index + 1) % TeamManager._tm.totalTeams
		TeamManager._tm.currentTeam = TeamManager._tm.teams[index]
	
	if Game._game.gameMode == TERMINATOR:
		pickVictim()
	
	if Game._game.gameMode == ARENA:
		ArenaManager._arena.wormsCheck()
	
	if Game._game.gameMode == MISSIONS:
		MissionManager._mm.endTurn()

	Game._game.damageThisTurn = 0
	if Game._game.nextState == PLAYER_CONTROL_1:
	
		# sort worms by health for drawing purpuses
		PhysObj._reg.sort(key = lambda worm: worm.health if worm.health else 0)
		
		# actual worm switch:
		switched = False
		while not switched:
			w = TeamManager._tm.currentTeam.worms.pop(0)
			TeamManager._tm.currentTeam.worms.append(w)
			if w.sleep:
				w.sleep = False
				continue
			switched = True
			
		if Game._game.randomCycle == 1: # complete random
			TeamManager._tm.currentTeam = choice(TeamManager._tm.teams)
			while not len(TeamManager._tm.currentTeam.worms) > 0:
				TeamManager._tm.currentTeam = choice(TeamManager._tm.teams)
			w = choice(TeamManager._tm.currentTeam.worms)
		if Game._game.randomCycle == 2: # random in the current team
			w = choice(TeamManager._tm.currentTeam.worms)
	
		Game._game.objectUnderControl = w
		Game._game.camTrack = Game._game.objectUnderControl
		WeaponManager._wm.switchWeapon(WeaponManager._wm.currentWeapon, force=True)
		if Game._game.gameMode == MISSIONS:
			MissionManager._mm.cycle()

def switchWorms():
	currentWorm = TeamManager._tm.currentTeam.worms.index(Game._game.objectUnderControl)
	totalWorms = len(TeamManager._tm.currentTeam.worms)
	currentWorm = (currentWorm + 1) % totalWorms
	Game._game.objectUnderControl = TeamManager._tm.currentTeam.worms[currentWorm]
	Game._game.camTrack = Game._game.objectUnderControl
	if Game._game.gameMode == MISSIONS:
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
	for i in range(Game._game.wormsPerTeam * len(TeamManager._tm.teams)):
		if Game._game.fortsMode:
			place = giveGoodPlace(i)
		else:
			place = giveGoodPlace()
		if Game._game.diggingMatch:
			pygame.draw.circle(Game._game.map_manager.game_map, SKY, place, 35)
			pygame.draw.circle(Game._game.map_manager.ground_map, SKY, place, 35)
			pygame.draw.circle(Game._game.map_manager.ground_secondary, SKY, place, 30)
		TeamManager._tm.teams[TeamManager._tm.teamChoser].addWorm(place.vec2tup())
		TeamManager._tm.teamChoser = (TeamManager._tm.teamChoser + 1) % TeamManager._tm.totalTeams
		Game._game.lstepper()
	Game._game.state = Game._game.nextState

def squareCollision(pos1, pos2, rad1, rad2):
	return True if pos1.x < pos2.x + rad2*2 and pos1.x + rad1*2 > pos2.x and pos1.y < pos2.y + rad2*2 and pos1.y + rad1*2 > pos2.y else False

def dropArtifact(artifact, pos, comment=False):
	deploy = False
	if not pos:
		# find good position for artifact
		goodPlace = False
		count = 0
		deploy = False
		while not goodPlace:
			pos = Vector(randint(20, Game._game.map_manager.game_map.get_width() - 20), -50)
			if not Game._game.map_manager.is_ground_at((pos.x, 0)):
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
	Game._game.camTrack = m

################################################################################ Gui
	

def weaponMenuRadialInit():
	# get categories

	current_team = TeamManager._tm.currentTeam
	
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

	Game._game.radial_weapon_menu = RadialMenu(layout, Vector(winWidth // 2, winHeight // 2))


	# Game._game.radial_weapon_menu = RadialMenu()
	# categories = []
	# for _, weapon in enumerate(WeaponManager._wm.weapons):
	# 	if TeamManager._tm.currentTeam.ammo(weapon) == 0:
	# 		continue
	# 	if not weapon.category in categories:
	# 		categories.append(weapon.category)
	# 		b = Game._game.radial_weapon_menu.addButton(weapon, weapon.get_bg_color())
	# 		b.category = weapon.category
	# 		WeaponManager._wm.blitWeaponSprite(b.surf, (0,0), weapon.name)

class Camera:
	def __init__(self, pos):
		self.pos = pos
		self.radius = 1

def toastInfo():
	if Game._game.gameMode < POINTS:
		return
	if Toast.toastCount > 0:
		Toast._toasts[0].time = 0
		if Toast._toasts[0].state == 2:
			Toast._toasts[0].state = 0
		return
	toastWidth = 100
	surfs = []
	for team in TeamManager._tm.teams:
		name = pixelFont5.render(team.name, False, team.color)
		points = pixelFont5.render(str(team.points), False, (0,0,0))
		surfs.append((name, points))
	surf = pygame.Surface((toastWidth, (surfs[0][0].get_height() + 3) * TeamManager._tm.totalTeams), pygame.SRCALPHA)
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
	def draw(self):
		pygame.draw.rect(Game._game.map_manager.game_map, GRD,(self.pos, self.size))
		for i in range(10):
			Game._game.map_manager.ground_map.blit(Game._game.sprites, self.pos + Vector(i * 16, 0), (64,80,16,16))
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
		notFromTeam = Game._game.objectUnderControl.team
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
		notFromTeam = Game._game.objectUnderControl.team
		worms = self.getAliveWormsFromOtherTeams()
		return choice(worms)

	def chooseTeamTarget(self):
		notFromTeam = Game._game.objectUnderControl.team
		teams = []
		for team in TeamManager._tm.teams:
			if team == notFromTeam:
				continue
			if len(team.worms) == 0:
				continue
			teams.append(team)
		if len(teams) == 0:
			return None
		return choice(teams)

	def removeMission(self, mission):
		if mission in self.wormMissionDict[Game._game.objectUnderControl]:
			self.wormMissionDict[Game._game.objectUnderControl].remove(mission)

		if Game._game.isPlayingState():
			self.assignMissions(Game._game.objectUnderControl, mission)

	def notifyKill(self, worm):
		if worm == Game._game.objectUnderControl:
			return
		self.killedThisTurn.append(worm)
		self.checkMissions(["kill a worm", "kill _", "double kill", "triple kill", "above 50 damage"])

	def notifyHit(self, worm):
		if worm in self.hitThisTurn or worm == Game._game.objectUnderControl:
			self.checkMissions(["above 50 damage"])
			return
		self.hitThisTurn.append(worm)
		self.checkMissions(["hit a worm from _", "hit _", "hit 3 worms", "above 50 damage"])
		# check highest
		worms = []
		for w in PhysObj._worms:
			if w.alive and w.team != Game._game.objectUnderControl.team:
				worms.append(w)
		
		highestWorm = min(worms, key=lambda w: w.pos.y)
		if worm == highestWorm:
			self.checkMissions(["hit highest worm"])
		# check distance
		if distus(worm.pos, Game._game.objectUnderControl.pos) > 300 * 300:
			self.checkMissions(["hit distant worm"])

	def checkMissions(self, missionTypes):
		for mission in self.wormMissionDict[Game._game.objectUnderControl]:
			if mission.missionType in missionTypes:
				mission.check()

	def notifySick(self, worm):
		pass

	def endTurn(self):
		pass

	def cycle(self):
		# start of turn, assign missions to current worm
		self.assignMissions(Game._game.objectUnderControl)
		self.updateDisplay()
		self.killedThisTurn = []
		self.hitThisTurn = []
		self.sickThisTurn = []
		self.marker = None

		if "reach marker" in self.wormMissionDict[Game._game.objectUnderControl]:
			self.createMarker()

	def updateDisplay(self):
		for mission in self.wormMissionDict[Game._game.objectUnderControl]:
			mission.updateDisplay()

	def step(self):
		if Game._game.objectUnderControl == None:
			return
		for mission in self.wormMissionDict[Game._game.objectUnderControl]:
			mission.step()

	def draw(self):
		if Game._game.objectUnderControl == None:
			return
		currentWorm = Game._game.objectUnderControl
		# draw missions gui in lower right of screen
		yOffset = 0
		for mission in self.wormMissionDict[currentWorm]:
			surf = mission.surf
			win.blit(surf, (winWidth - surf.get_width() - 5, winHeight - surf.get_height() - 5 - yOffset))
			yOffset += surf.get_height() + 2
		
		# draw mission indicators
		for mission in self.wormMissionDict[currentWorm]:
			mission.draw()

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
			{'text': 'mission '}, {'text': string, 'color': Game._game.objectUnderControl.team.color}, {'text': ' passed'}
		]
		Commentator.comment(comment)
		Game._game.objectUnderControl.team.points += self.reward
		Game._game.addToScoreList(self.reward)

		self.completed = True
		MissionManager._log += f"{Game._game.objectUnderControl.nameStr} completed mission {self.missionType} {str(self.reward)}\n"
		
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
			if distus(self.marker, Game._game.objectUnderControl.pos) < 20 * 20:
				self.check()
		if self.completed:
			self.timer = max(0, self.timer - 1)
			self.updateDisplay()
			if self.timer == 0 and Game._game.isPlayingState():
				self.readyToChange = True
				MissionManager._mm.removeMission(self)

	def draw(self):
		# draw indicators
		# draw distance indicator
		currentWorm = Game._game.objectUnderControl
		if self.missionType == "hit distant worm":
			radius = 300
			da = 2 * pi / 40
			time = da * int(TimeManager._tm.timeOverall / 2)
			timeAngles = [time + i * pi/2 for i in range(4)]
			for ta in timeAngles:
				for i in range(9):
					size = int(i / 3)
					pos = currentWorm.pos + vectorFromAngle(ta + i * da, radius)
					pygame.draw.circle(win, (255,0,0), point2world(pos), size)
		# draw marker
		elif self.marker:
			offset = sin(TimeManager._tm.timeOverall / 5) * 5
			pygame.draw.circle(win, (255,0,0), point2world(self.marker), 10 + offset, 1)
			drawDirInd(self.marker)
		# draw indicators
		elif self.target:
			drawDirInd(self.target.pos)
			drawTarget(self.target.pos)

	def updateDisplay(self):
		if not self.textSurf:
			self.textSurf = pixelFont5.render(self.missionToString(), False, WHITE)
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
	if Game._game.allowAirStrikes:
		startingWeapons.append("mine strike")
	if Game._game.unlimitedMode: return
	for i in range(amount):
		for team in TeamManager._tm.teams:
			chosen_weapon: Weapon = globals.weapon_manager.get_weapon(choice(startingWeapons))
			team.ammo(chosen_weapon, 1)
			if randint(0,2) >= 1:
				chosen_weapon = globals.weapon_manager.get_weapon(choice(["moon gravity", "teleport", "jet pack", "aim aid", "switch worms"]))
				team.ammo(chosen_weapon, 1)
			if randint(0,6) == 1:
				chosen_weapon = globals.weapon_manager.get_weapon(choice(["portal gun", "trampoline", "ender pearl"]))
				team.ammo(chosen_weapon, 3)

def randomWeaponsGive():
	for team in TeamManager._tm.teams:
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
	string = "Sudden Death!"
	if len(Game._game.suddenDeathStyle) == 0:
		Game._game.suddenDeathStyle += [PLAGUE, TSUNAMI]
	if PLAGUE in Game._game.suddenDeathStyle:
		string += " plague!"
		for worm in PhysObj._worms:
			worm.sicken()
			if not worm.health == 1:
				worm.health = worm.health // 2
	if TSUNAMI in Game._game.suddenDeathStyle:
		string += " water rise!"
		Game._game.waterRise = True
	text = pixelFont10.render("sudden death", False, (220,0,0))
	Toast(pygame.transform.scale(text, tup2vec(text.get_size()) * 2), Toast.middle)

def isOnMap(vec):
	return not (vec[0] < 0 or vec[0] >= Game._game.map_manager.game_map.get_width() or vec[1] < 0 or vec[1] >= Game._game.map_manager.game_map.get_height())

def cheatActive(code):
	code = code[:-1].lower()

	if code == "gibguns":
		Game._game.unlimitedMode = True
		for team in TeamManager._tm.teams:
			for i, teamCount in enumerate(team.weaponCounter):
				team.weaponCounter[i] = -1
		for weapon in WeaponManager._wm.weapons:
			# weapon [5] = 0 # todo
			pass
		Game._game.useListMode = False
	elif code == "suddendeath":
		suddenDeath()
	elif code == "wind":
		Game._game.wind = uniform(-1,1)
	elif code == "goodbyecruelworld":
		boom(Game._game.objectUnderControl.pos, 100)
	elif code == "armageddon":
		Armageddon()
	elif code == "reset":
		Game._game.state, Game._game.nextState = RESET, RESET
	elif code[0:5] == "gunme" and len(code) == 6:
		amount = int(code[5])
		for i in range(amount):
			mousePos = pygame.mouse.get_pos()
			WeaponPack((mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
	elif code[0:9] == "utilizeme" and len(code) == 10:
		amount = int(code[9])
		for i in range(amount):
			mousePos = pygame.mouse.get_pos()
			UtilityPack((mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
	elif code == "aspirin":
		mousePos = pygame.mouse.get_pos()
		HealthPack((mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
	elif code == "globalshift":
		for worm in PhysObj._worms:
			# if worm in TeamManager._tm.currentTeam.worms:
				# continue
			worm.gravity = worm.gravity * -1
	elif code == "gibpetrolcan":
		mousePos = pygame.mouse.get_pos()
		PetrolCan((mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
	elif code == "megaboom":
		Game._game.megaTrigger = True
	elif code == "tsunami":
		Game._game.waterRise = True
		Commentator.comment([{'text': "water rising!"}])
	elif code == "comeflywithme":
		TeamManager._tm.currentTeam.ammo("jet pack", 6)
		TeamManager._tm.currentTeam.ammo("rope", 6)
		TeamManager._tm.currentTeam.ammo("ender pearl", 6)
	elif code == "odinson":
		mousePos = pygame.mouse.get_pos()
		m = Mjolnir(Vector(mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
		m.vel *= 0
	elif code == "bulbasaur":
		mousePos = pygame.mouse.get_pos()
		m = MagicLeaf(Vector(mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
	elif code == "avatar":
		mousePos = pygame.mouse.get_pos()
		m = Avatar(Vector(mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
	elif code == "masterofpuppets":
		MasterOfPuppets()
	elif code == "artifact":
		Game._game.trigerArtifact = True
	elif code == "minecraft":
		mousePos = pygame.mouse.get_pos()
		PickAxeArtifact(Vector(mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
	elif code == "deathtouch":
		mousePos = pygame.mouse.get_pos()
		pos = Vector(mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y)
		closest = None
		closestDist = 100000
		for worm in PhysObj._worms:
			if dist(worm.pos, pos) < closestDist:
				closestDist = dist(worm.pos, pos)
				closest = worm
		if closest:
			closest.damage(1000)
	elif "gib" in code:
		code = code.replace("gib", "")
		weapons = [w[0].replace('p', "").replace(' ', "").lower() for w in WeaponManager._wm.weapons]
		if code in weapons:
			TeamManager._tm.currentTeam.ammo(WeaponManager._wm.weapons[weapons.index(code)][0], 1)
		
def gameDistable(): 
	Game._game.gameStable = False
	Game._game.gameStableCounter = 0

def pickVictim():
	Game._game.terminatorHit = False
	worms = []
	for w in PhysObj._worms:
		if w in TeamManager._tm.currentTeam.worms:
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
	Commentator.comment(choice(comments))

def drawDirInd(pos):
	border = 20
	if not (pos[0] < Game._game.camPos[0] - border/4 or pos[0] > (Vector(winWidth, winHeight) + Game._game.camPos)[0] + border/4 or pos[1] < Game._game.camPos[1] - border/4 or pos[1] > (Vector(winWidth, winHeight) + Game._game.camPos)[1] + border/4):
		return

	cam = Game._game.camPos + Vector(winWidth//2, winHeight//2)
	direction = pos - cam
	
	intersection = tup2vec(point2world((winWidth, winHeight))) + pos -  Vector(winWidth, winHeight)
	
	intersection[0] = min(max(intersection[0], border), winWidth - border)
	intersection[1] = min(max(intersection[1], border), winHeight - border)
	
	points = [Vector(0,2), Vector(0,-2), Vector(5,0)]
	angle = direction.getAngle()
	
	for point in points:
		point.rotate(angle)
	
	pygame.draw.polygon(win, (255,0,0), [intersection + i + normalize(direction) * 4 * sin(TimeManager._tm.timeOverall / 5) for i in points])

def testerFunc():
	mousePos = pygame.mouse.get_pos()
	mouse = Vector(mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y)
	mouse.integer()

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
	def draw(self):
		pass

################################################################################ State machine

def stateMachine():
	if Game._game.state == RESET:
		Game._game.gameStable = False
		Game._game.playerControl = False
		Game._game.playerControlPlacing = False
		
		Game._game.create_new_game()
		Game._game.nextState = PLAYER_CONTROL_1
		Game._game.state = Game._game.nextState
	
	elif Game._game.state == PLAYER_CONTROL_1:
		Game._game.playerControlPlacing = False
		Game._game.playerControl = True #can play
		Game._game.playerShootAble = True
		
		Game._game.nextState = PLAYER_CONTROL_2
	elif Game._game.state == PLAYER_CONTROL_2:
		Game._game.playerControlPlacing = False
		Game._game.playerControl = True #can play
		Game._game.playerShootAble = False
		
		Game._game.gameStableCounter = 0
		Game._game.nextState = WAIT_STABLE
	elif Game._game.state == WAIT_STABLE:
		Game._game.playerControlPlacing = False
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
		Game._game.playerControlPlacing = False
		Game._game.playerControl = True #can play
		Game._game.playerShootAble = True
		
		if WeaponManager._wm.currentWeapon in WeaponManager._wm.multipleFires:
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
	Game._game.objectUnderControl.facing = RIGHT
	if Game._game.objectUnderControl.shootAngle >= pi/2 and Game._game.objectUnderControl.shootAngle <= (3/2)*pi:
		Game._game.objectUnderControl.shootAngle = pi - Game._game.objectUnderControl.shootAngle
	Game._game.camTrack = Game._game.objectUnderControl

def onKeyPressLeft():
	if not Game._game.playerMoveable:
		return
	Game._game.objectUnderControl.facing = LEFT
	if Game._game.objectUnderControl.shootAngle >= -pi/2 and Game._game.objectUnderControl.shootAngle <= pi/2:
		Game._game.objectUnderControl.shootAngle = pi - Game._game.objectUnderControl.shootAngle
	Game._game.camTrack = Game._game.objectUnderControl

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
			
		#rope
		elif WeaponManager._wm.currentWeapon == "rope":
			# if not currently roping:
			Game._game.fireWeapon = True
			Game._game.playerShootAble = False
			# if currently roping:
			if Game._game.objectUnderControl.rope: 
				Game._game.objectUnderControl.toggleRope(None)
				Game._game.fireWeapon = False
		
		# chargeable
		elif WeaponManager._wm.currentWeapon.style == WeaponStyle.CHARGABLE and Game._game.energising:
			Game._game.fireWeapon = True
		
		# putable & guns
		elif (WeaponManager._wm.currentWeapon.style in [WeaponStyle.PUTABLE, WeaponStyle.GUN]):
			Game._game.fireWeapon = True
			Game._game.playerShootAble = False
			
		Game._game.energising = False
	elif Game._game.objectUnderControl.rope:
		Game._game.objectUnderControl.toggleRope(None)
	elif Game._game.objectUnderControl.parachuting:
		Game._game.objectUnderControl.toggleParachute()
	elif Sheep.trigger == False:
		Sheep.trigger = True

def onKeyPressTab():
	if not Game._game.state == PLAYER_CONTROL_1:
		if Game._game.state == FIRE_MULTIPLE and Game._game.switchingWorms:
			switchWorms()
		return
	if WeaponManager._wm.currentWeapon == "bunker buster":
		BunkerBuster.mode = not BunkerBuster.mode
		if BunkerBuster.mode:
			FloatingText(Game._game.objectUnderControl.pos + Vector(0,-5), "drill mode", (20,20,20))
		else:
			FloatingText(Game._game.objectUnderControl.pos + Vector(0,-5), "rocket mode", (20,20,20))
		WeaponManager._wm.renderWeaponCount()
	elif WeaponManager._wm.currentWeapon == "venus fly trap":
		PlantBomb.mode = (PlantBomb.mode + 1) % 2
		if PlantBomb.mode == PlantBomb.venus:
			FloatingText(Game._game.objectUnderControl.pos + Vector(0,-5), "venus fly trap", (20,20,20))
		elif PlantBomb.mode == PlantBomb.bomb:
			FloatingText(Game._game.objectUnderControl.pos + Vector(0,-5), "plant mode", (20,20,20))
	elif WeaponManager._wm.currentWeapon == "long bow":
		LongBow._sleep = not LongBow._sleep
		if LongBow._sleep:
			FloatingText(Game._game.objectUnderControl.pos + Vector(0,-5), "sleeping", (20,20,20))
		else:
			FloatingText(Game._game.objectUnderControl.pos + Vector(0,-5), "regular", (20,20,20))
	elif WeaponManager._wm.currentWeapon == "girder":
		Game._game.girderAngle += 45
		if Game._game.girderAngle == 180:
			Game._game.girderSize = 100
		if Game._game.girderAngle == 360:
			Game._game.girderSize = 50
			Game._game.girderAngle = 0
	elif WeaponManager._wm.getFused(WeaponManager._wm.currentWeapon):
		Game._game.fuseTime += fps
		if Game._game.fuseTime > fps*4:
			Game._game.fuseTime = fps
		string = "delay " + str(Game._game.fuseTime//fps) + " sec"
		FloatingText(Game._game.objectUnderControl.pos + Vector(0,-5), string, (20,20,20))
		WeaponManager._wm.renderWeaponCount()
	elif WeaponManager._wm.getBackColor(WeaponManager._wm.currentWeapon) == AIRSTRIKE:
		Game._game.airStrikeDir *= -1
	elif Game._game.switchingWorms:
		switchWorms()

def onKeyPressEnter():
	# jump
	if Game._game.objectUnderControl.stable and Game._game.objectUnderControl.health > 0:
		Game._game.objectUnderControl.vel += Vector(cos(Game._game.objectUnderControl.shootAngle), sin(Game._game.objectUnderControl.shootAngle)) * Game._game.jumpVelocity
		Game._game.objectUnderControl.stable = False

################################################################################ Main

def gameMain(gameParameters=None):
	global winWidth, winHeight, scalingFactor, win
	Game(gameParameters)
	TimeManager()
	WeaponManager()
	TeamManager()

	BackGround(Game._game.feelColor, Game._game.darkness)
	HealthBar()
	SmokeParticles()
	
	damageText = (Game._game.damageThisTurn, pixelFont5halo.render(str(int(Game._game.damageThisTurn)), False, Game._game.HUDColor))
	Commentator()
	TimeTravel()

	WindFlag()

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
				#mouse position:
				mousePos = pygame.mouse.get_pos()
				if Game._game.playerControlPlacing:
					TeamManager._tm.teams[TeamManager._tm.teamChoser].addWorm((mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y))
					TeamManager._tm.teamChoser = (TeamManager._tm.teamChoser + 1) % TeamManager._tm.totalTeams
				# CLICKABLE weapon check:
				if Game._game.state == PLAYER_CONTROL_1 and WeaponManager._wm.currentWeapon.style == WeaponStyle.CLICKABLE:
					fireClickable()
				if Game._game.state == PLAYER_CONTROL_1 and WeaponManager._wm.currentWeapon in ["homing missile", "seeker"] and not Game._game.radial_weapon_menu:
					HomingMissile.Target.x, HomingMissile.Target.y = mousePos[0]/scalingFactor + Game._game.camPos.x, mousePos[1]/scalingFactor + Game._game.camPos.y
					HomingMissile.showTarget = True

			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)
				pass
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
				# this is the next Game._game.state after placing all worms
				if Game._game.state == PLAYER_CONTROL_1:
					if Game._game.radial_weapon_menu is None:
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
					if Game._game.objectUnderControl and Game._game.playerControl:
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
						testerFunc()
					if event.key == pygame.K_F1:
						toastInfo()
					if event.key == pygame.K_F2:
						Worm.healthMode = (Worm.healthMode + 1) % 2
						if Worm.healthMode == 1:
							for worm in PhysObj._worms:
								worm.healthStr = pixelFont5.render(str(worm.health), False, worm.team.color)
					if event.key == pygame.K_F3:
						Game._game.drawGroundSec = not Game._game.drawGroundSec
					if event.key == pygame.K_m:
						TimeSlow()
					if event.key == pygame.K_RCTRL or event.key == pygame.K_LCTRL:
						scalingFactor = globals.scalingMax
						globals.scalingFactor = scalingFactor
						if Game._game.camTrack == None:
							Game._game.camTrack = Game._game.objectUnderControl
					# if event.key == pygame.K_n:
						# pygame.image.save(win, "wormshoot" + str(timeManager.timeOverall) + ".png")	
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
		if Game._game.objectUnderControl and Game._game.playerControl and Game._game.playerMoveable:
			if keys[pygame.K_RIGHT]:
				Game._game.actionMove = True
			if keys[pygame.K_LEFT]:
				Game._game.actionMove = True
			# fire hold
			if Game._game.playerShootAble and (keys[pygame.K_SPACE]) and WeaponManager._wm.currentWeapon.style == WeaponStyle.CHARGABLE and Game._game.energising:
				onKeyHoldSpace()
		
		if pause:
			result = [0]
			args = {"showPoints": HealthBar._healthBar.drawPoints, "teams":TeamManager._tm.teams}
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
			if mousePos[0] < Game._game.edgeBorder:
				scroll.x -= Game._game.mapScrollSpeed * (2.5 - scalingFactor/2)
			if mousePos[0] > screenWidth - Game._game.edgeBorder:
				scroll.x += Game._game.mapScrollSpeed * (2.5 - scalingFactor/2)
			if mousePos[1] < Game._game.edgeBorder:
				scroll.y -= Game._game.mapScrollSpeed * (2.5 - scalingFactor/2)
			if mousePos[1] > screenHeight - Game._game.edgeBorder:
				scroll.y += Game._game.mapScrollSpeed * (2.5 - scalingFactor/2)
			if scroll != Vector():
				Game._game.camTrack = Camera(Game._game.camPos + Vector(winWidth, winHeight)/2 + scroll)
		
		# handle scale:
		oldSize = (winWidth, winHeight)
		winWidth += (globals.screenWidth / scalingFactor - winWidth) * 0.2
		winHeight += (globals.screenHeight / scalingFactor - winHeight) * 0.2
		winWidth = int(winWidth)
		winHeight = int(winHeight)
		
		if oldSize != (winWidth, winHeight):
			globals.win = pygame.Surface((winWidth, winHeight))
			win = globals.win
			globals.winWidth = winWidth
			globals.winHeight = winHeight
			updateWin(win, scalingFactor)
		
		# handle position:
		if Game._game.camTrack:
			# actual position target:
			### Game._game.camPos = Game._game.camTrack.pos - Vector(winWidth, winHeight)/2
			# with smooth transition:
			Game._game.camPos += ((Game._game.camTrack.pos - Vector(int(globals.screenWidth / scalingFactor), int(globals.screenHeight / scalingFactor))/2) - Game._game.camPos) * 0.2
		
		# constraints:
		if Game._game.camPos.y < 0: Game._game.camPos.y = 0
		if Game._game.camPos.y >= Game._game.map_manager.game_map.get_height() - winHeight: Game._game.camPos.y = Game._game.map_manager.game_map.get_height() - winHeight
		if Game._game.mapClosed or Game._game.darkness:
			if Game._game.camPos.x < 0:
				Game._game.camPos.x = 0
			if Game._game.camPos.x >= Game._game.map_manager.game_map.get_width() - winWidth:
				Game._game.camPos.x = Game._game.map_manager.game_map.get_width() - winWidth
		
		if Earthquake.earthquake > 0:
			Game._game.camPos.x += Earthquake.earthquake * 25 * sin(TimeManager._tm.timeOverall)
			Game._game.camPos.y += Earthquake.earthquake * 15 * sin(TimeManager._tm.timeOverall * 1.8)
		
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
		for t in Toast._toasts:
			t.step()
		SmokeParticles._sp.step()
		if Game._game.timeTravel: 
			TimeTravel._tt.step()
			
		# camera for wait to stable:
		if Game._game.state == WAIT_STABLE and TimeManager._tm.timeOverall % 20 == 0:
			for worm in PhysObj._worms:
				if worm.stable:
					continue
				else:
					Game._game.camTrack = worm
					break
		
		# advance timer
		TimeManager._tm.step()
		BackGround._bg.step()
		
		if ArenaManager._arena: ArenaManager._arena.step()
		if MissionManager._mm: MissionManager._mm.step()
		
		# menu step
		if Game._game.radial_weapon_menu:
			Game._game.radial_weapon_menu.step()
		
		# reset actions
		Game._game.actionMove = False

		WindFlag._instance.step()

		# draw:
		BackGround._bg.draw()
		drawLand()
		for p in PhysObj._reg: 
			p.draw()
		for f in Game._game.nonPhys:
			f.draw()
		BackGround._bg.drawSecondary()
		for t in Toast._toasts:
			t.draw()
		
		if ArenaManager._arena: ArenaManager._arena.draw()
		SmokeParticles._sp.draw()

		if Game._game.darkness and Game._game.map_manager.dark_mask: win.blit(Game._game.map_manager.dark_mask, (-int(Game._game.camPos.x), -int(Game._game.camPos.y)))
		# draw shooting indicator
		if Game._game.objectUnderControl and Game._game.state in [PLAYER_CONTROL_1, PLAYER_CONTROL_2, FIRE_MULTIPLE] and Game._game.objectUnderControl.health > 0:
			Game._game.objectUnderControl.drawCursor()
			if Game._game.aimAid and WeaponManager._wm.currentWeapon.style == WeaponStyle.GUN:
				p1 = vectorCopy(Game._game.objectUnderControl.pos)
				p2 = p1 + Vector(cos(Game._game.objectUnderControl.shootAngle), sin(Game._game.objectUnderControl.shootAngle)) * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))
			i = 0
			while i < 20 * Game._game.energyLevel:
				cPos = vectorCopy(Game._game.objectUnderControl.pos)
				angle = Game._game.objectUnderControl.shootAngle
				pygame.draw.line(win, (0,0,0), point2world(cPos), point2world(cPos + vectorFromAngle(angle) * i))
				i += 1
		
		Game._game.drawExtra()
		Game._game.drawLayers()
		
		# HUD
		WindFlag._instance.draw()
		TimeManager._tm.draw()
		if WeaponManager._wm.surf: win.blit(WeaponManager._wm.surf, (25, 5))
		Commentator._com.step()
		# draw weapon indicators
		WeaponManager._wm.drawWeaponIndicators()
		WeaponManager._wm.draw()
		
		# draw health bar
		if not Game._game.state in [RESET] and Game._game.drawHealthBar: HealthBar._healthBar.step()
		if not Game._game.state in [RESET] and Game._game.drawHealthBar: HealthBar._healthBar.draw() # teamHealthDraw()
		if Game._game.gameMode == TERMINATOR and Game._game.victim and Game._game.victim.alive:
			drawTarget(Game._game.victim.pos)
			drawDirInd(Game._game.victim.pos)
		if Game._game.gameMode == TARGETS and Game._game.objectUnderControl:
			for target in ShootingTarget._reg:
				drawDirInd(target.pos)
		if Game._game.gameMode == MISSIONS:
			if MissionManager._mm: MissionManager._mm.draw()
			
		
		# weapon menu:
		# move menus
		if len(Toast._toasts) > 0:
			for t in Toast._toasts:
				if t.mode == Toast.bottom:
					t.updateWinPos((winWidth/2, winHeight))
				elif t.mode == Toast.middle:
					t.updateWinPos(Vector(winWidth/2, winHeight/2) - tup2vec(t.surf.get_size())/2)
		
		if Game._game.radial_weapon_menu:
			Game._game.radial_weapon_menu.draw(win)

		# draw kill list
		if Game._game.gameMode in [POINTS, TARGETS, TERMINATOR, MISSIONS]:
			while len(Game._game.killList) > 8:
				Game._game.killList.pop(-1)
			for i, killed in enumerate(Game._game.killList):
				win.blit(killed[0], (5, winHeight - 20 - i * (killed[0].get_height() + 1)))
		
		# debug:
		if damageText[0] != Game._game.damageThisTurn: damageText = (Game._game.damageThisTurn, pixelFont5halo.render(str(int(Game._game.damageThisTurn)), False, Game._game.HUDColor))
		win.blit(damageText[1], ((int(5), int(winHeight -5 -damageText[1].get_height()))))
		
		# draw loading screen
		if Game._game.state in [RESET]:
			win.fill((0,0,0))
			pos = (winWidth/2 - Game._game.loadingSurf.get_width()/2, winHeight/2 - Game._game.loadingSurf.get_height()/2)
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
		win.blit(splashImage, ((winWidth/2 - splashImage.get_width()/2, winHeight/2 - splashImage.get_height()/2)))
		screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
		pygame.display.update()
		fpsClock.tick(fps)

if __name__ == "__main__":
	args = parseArgs()
	gameParameters = [None]
	if not args.no_menu: splashScreen()
	while True:
		mainMenu(args, Game._game.endGameDict if Game._game else None, gameParameters)
		gameMain(gameParameters[0])
