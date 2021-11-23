from math import pi, cos, sin, atan2, sqrt, exp, degrees, radians, log
from random import shuffle ,randint, uniform, choice
from vector import *
from pygame import gfxdraw
import pygame
import argparse
import xml.etree.ElementTree as ET
import os
import subprocess
pygame.init()

if True:
	fpsClock = pygame.time.Clock()
	fps = 30
	
	pygame.font.init()
	myfont = pygame.font.Font("fonts\pixelFont.ttf", 5)
	myfontbigger = pygame.font.Font("fonts\pixelFont.ttf", 10)
	
	scalingFactor = 3
	winWidth = int(1280 / scalingFactor)
	winHeight = int(720 / scalingFactor)
	win = pygame.Surface((winWidth, winHeight))
	
	screenWidth = int(winWidth * scalingFactor)
	screenHeight = int(winHeight * scalingFactor)
	pygame.display.set_caption("Simon's Worms")
	screen = pygame.display.set_mode((screenWidth,screenHeight))

# Macros
if True:
	SKY = (0,0,0,0)
	GRD = (255,255,255,255)
	LAND_GREEN = (62,201,83,255)
	SKY_CYAN = (139,255,247,255)
	
	CHARGABLE = 0
	PUTABLE = 1
	CLICKABLE = 2
	GUN = 3
	UTILITY = 4
	
	WEAPONS = 0
	UTILITIES = 1
	ARTIFACTS = 2
	
	RIGHT = 1
	LEFT = -1
	RED = (255,0,0)
	YELLOW = (255,255,0)
	BLUE = (0,0,255)
	GREEN = (0,255,0)
	BLACK = (0,0,0)
	WHITE = (255,255,255)
	GREY = (100,100,100)
	DOWN = 1
	UP = -1
	
	HEALTH_PACK = 0
	UTILITY_PACK = 1
	WEAPON_PACK = 2
	FLAG_DEPLOY = 3
	
	MISSILES = (255, 255, 255)
	GRENADES = (204, 255, 204)
	GUNS = (255, 204, 153)
	FIREY = (255, 204, 204)
	MISC = (224, 224, 235)
	AIRSTRIKE = (204, 255, 255)
	LEGENDARY = (255, 255, 102)
	
	PLAGUE = 0
	TSUNAMI = 1
	
	BATTLE = 0
	DAVID_AND_GOLIATH = 1
	POINTS = 2
	TARGETS = 3
	CAPTURE_THE_FLAG = 4
	TERMINATOR = 5
	ARENA = 6
	
	MJOLNIR = 0

# Game settings
if True:
	turnTime = 45
	retreatTime = 5
	wormDieTime = 3
	shockRadius = 1.5
	burnRadius = 1.15
	globalGravity = 0.2
	edgeBorder = 65
	mapScrollSpeed = 35
	jetPackFuel = 100
	lightRadius = 70
	initialWaterLevel = 50
	damageMult = 0.8
	fallDamageMult = 1
	windMult = 1.5
	radiusMult = 1
	packMult = 1
	dampMult = 1.5

# Game parameters
if True:
	initialHealth = 100
	gameMode = BATTLE
	deployPacks = True
	diggingMatch = False
	manualPlace = False
	drawHealthBar = True
	mapClosed = False
	unlimitedMode = False
	moreWindAffected = 0
	fortsMode = False
	randomWeapons = False
	darkness = False
	useListMode = False
	warpedMode = False
	randomCycle = 0
	allowAirStrikes = True
	drawGroundSec = True
	waterRise = False
	waterRising = False
	roundsTillSuddenDeath = -1
	suddenDeathStyle = []
	victim = None
	terminatorHit = False
	cheatCode = ""
	HUDColor = BLACK
	holdArtifact = True
	artifactsMode = True
	worldArtifacts = [MJOLNIR]

# bugs & improvements:
# chum and seagulls to not spawn on top of world
# convert fire (and more ?) collisions with worms to square collision for better performance. maybe a constant fire will be a thing
# bungee using spring dynamics
# nerf: acid bottle, 
# make bat act like seeker

################################################################################ Map
if True:
	gameMap = None
	ground = None
	wormCol = None
	extraCol = None
	groundSec = None
	darkMask = None

	mapWidth = 0
	mapHeight = 0
	lights = []
	
	camPos = Vector(0,0)
	camTarget = Vector(0,0)
	
	objectUnderControl = None
	camTrack = None # object to track
	
	energising = False
	energyLevel = 0
	fireWeapon = False
	# color feel 0:up 1:down 2:mountfar 3:mountclose
	feels = [[(238, 217, 97), (251, 236, 187), (222, 171, 51), (253, 215, 109)],
			 [(122, 196, 233), (199, 233, 251), (116, 208, 186), (100, 173, 133)],
			 [(110, 109, 166), (174, 95, 124), (68, 55, 101), (121, 93, 142)],
			 [(35, 150, 197), (248, 182, 130), (165, 97, 62), (227, 150, 104)],
			 [(121, 135, 174), (195, 190, 186), (101, 136, 174), (72, 113, 133)],
			 [(68, 19, 136), (160, 100, 170), (63, 49, 124), (45, 29, 78)],
			 [(40,40,30), (62, 19, 8), (20,20,26), (56, 41, 28)],
			 [(0,38,95), (23, 199, 248), (2,113,194), (0, 66, 153)],
			 [(252,255,186), (248, 243, 237), (165,176,194), (64, 97, 138)],
			 [(37,145,184), (232, 213, 155), (85,179,191), (16, 160, 187)],
			 [(246,153,121), (255, 205, 187), (252,117,92), (196, 78, 63)]
			 ]
	feelColor = choice(feels)
	wind = uniform(-1,1)
	actionMove = False
	aimAid = False
	switchingWorms = False
	timeTravel = False
	megaTrigger = False
	fuseTime = fps*2

# parse arguments
if True:
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
	args = parser.parse_args()
	
	gameMode = args.game_mode
	fortsMode = args.forts
	initialHealth = args.initial_health
	diggingMatch = args.digging
	darkness = args.darkness
	packMult = args.pack_mult
	wormsPerTeam = args.worms_per_team
	useListMode = args.used_list
	mapClosed = args.closed_map
	warpedMode = args.warped
	randomCycle = args.random
	unlimitedMode = args.unlimited
	manualPlace = args.place
	roundsTillSuddenDeath = args.sudden_death
	artifactsMode = args.artifacts
	if args.sudden_death_tsunami:
		suddenDeathStyle.append(TSUNAMI)
	if args.sudden_death_plague:
		suddenDeathStyle.append(PLAGUE)
	
def grabMapsFrom(path):
	if not os.path.exists(path):
		return
	maps = []
	for imageFile in os.listdir(path):
		if imageFile[-4:] != ".png":
			continue
		string = path + "/" + imageFile
		ratio = 512
		if string.find("big") != -1:
			ratio = 800
		if string.find("big1.png") != -1:
			ratio = 1000
		elif string.find("big6.png") != -1:
			ratio = 700
		elif string.find("big13.png") != -1:
			ratio = 1000
		elif string.find("big16.png") != -1:
			ratio = 2000
		string = os.path.abspath(string)
		maps.append((string, ratio))
	return maps

def createWorld():
	# choose map
	maps = []
	maps += grabMapsFrom("wormsMaps")
	maps += grabMapsFrom("wormsMaps/moreMaps")
	
	if args.map_choice == "":
		# no map chosed in arguments pick one at random
		imageChoice = choice(maps)
	else:
		imageChoice = [None, None]
		for m in maps:
			if args.map_choice in m[0]:
				imageChoice = m
				break
		# if not found, then custom map
		if imageChoice[0] == None:
			imageChoice[0] = args.map_choice
			imageChoice[1] = randint(512, 600)
		# if perlin map, recolor ground
		if "PerlinMaps" in args.map_choice:
			args.recolor_ground = True
		
	if args.map_ratio != -1:
		imageChoice[1] = args.map_ratio
	
	createMap(imageChoice)
	renderLand()

def createMapSurfaces(dims):
	"""
	create all map related surfaces
	"""
	global gameMap, mapWidth, mapHeight, ground, wormCol, extraCol, groundSec, darkMask
	mapWidth, mapHeight = dims
	gameMap = pygame.Surface((mapWidth, mapHeight))
	gameMap.fill(SKY)
	wormCol = pygame.Surface((mapWidth, mapHeight))
	wormCol.fill(SKY)
	extraCol = pygame.Surface((mapWidth, mapHeight))
	extraCol.fill(SKY)

	ground = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	groundSec = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	if darkness:
		darkMask = pygame.Surface((mapWidth, mapHeight)).convert_alpha()

def createMap(imageChoice):
	"""
	create and initialize all map related surfaces
	"""	
	if diggingMatch:
		createMapSurfaces((int(1024 * 1.5), 512))
		gameMap.fill(GRD)
		return

	# load map
	global mapImage
	mapImage = pygame.image.load(imageChoice[0])
	
	# flip for diversity
	if randint(0,1) == 0:
		mapImage = pygame.transform.flip(mapImage, True, False)
	
	# rescale based on ratio
	ratio = mapImage.get_width() / mapImage.get_height()
	mapImage = pygame.transform.scale(mapImage, (int(imageChoice[1] * ratio), imageChoice[1]))
		
	createMapSurfaces((mapImage.get_width(), mapImage.get_height() + initialWaterLevel))
	
	# fill gameMap
	global lstepmax
	lstepmax = mapWidth//10 + wormsPerTeam * len(teams) + 1
	for x in range(mapWidth):
		for y in range(mapHeight - initialWaterLevel):
			if not (mapImage.get_at((x, y)) == (0,0,0) or mapImage.get_at((x, y))[3] < 100):
				gameMap.set_at((x, y), GRD)
		if x % 10 == 0:
			lstepper()
	mapImage.set_colorkey((0,0,0))

def renderLand():
	ground.fill(SKY)
	if diggingMatch or args.recolor_ground:
		patternImage = pygame.image.load("assets/pattern.png")
		grassColor = choice([(10, 225, 10), (10,100,10)] + [i[3] for i in feels])
		
		for x in range(0,mapWidth):
			for y in range(0,mapHeight):
				if gameMap.get_at((x,y)) == GRD:
					ground.set_at((x,y), patternImage.get_at((x % patternImage.get_width(), y % patternImage.get_height())))
		
		for x in range(0,mapWidth):
			for y in range(0,mapHeight):
				if gameMap.get_at((x,y)) == GRD:
					if y > 0 and gameMap.get_at((x,y - 1)) != GRD:
						for i in range(randint(3,5)):
							if y + i < mapHeight:
								if gameMap.get_at((x, y + i)) == GRD:
									ground.set_at((x,y + i), [min(abs(i + randint(-30,30)), 255) for i in grassColor])
								
		groundSec.fill(feelColor[0])
		groundCopy = ground.copy()
		groundCopy.set_alpha(64)
		groundSec.blit(groundCopy, (0,0))
		groundSec.set_colorkey(feelColor[0])
		return
		
	ground.blit(mapImage, (0,0))
	groundSec.fill(feelColor[0])
	mapImage.set_alpha(64)
	groundSec.blit(mapImage, (0,0))
	groundSec.set_colorkey(feelColor[0])

def drawLand():
	if mapWidth == 0:
		return
	if drawGroundSec: win.blit(groundSec, point2world((0,0)))
	win.blit(ground, point2world((0,0)))
	if warpedMode:
		if drawGroundSec: win.blit(groundSec, point2world((mapWidth,0)))
		win.blit(ground, point2world((mapWidth,0)))
		if drawGroundSec: win.blit(groundSec, point2world((-mapWidth,0)))
		win.blit(ground, point2world((-mapWidth,0)))
	if darkness and not state == PLACING_WORMS:
		darkMask.fill((30,30,30))
		if objectUnderControl:
			# advanced darkness:
			if False:
				center = objectUnderControl.pos
				points = []
				for i in range(100):
					direction = vectorFromAngle((pi * i)/(100/2))
					for t in range(100):
						testPos = center + direction * (t*5)
						if mapGetAt(testPos) == GRD:
							points.append(testPos)
							break
						if t == 100 - 1:
							points.append(testPos)
							break
				pygame.draw.polygon(darkMask, (0,0,0,0), points)
			else:
				pygame.draw.circle(darkMask, (0,0,0,0), objectUnderControl.pos.vec2tupint(), lightRadius)
	
		global lights
		for light in lights:
			pygame.draw.circle(darkMask, light[3], (int(light[0]), int(light[1])), int(light[2]))
		lights = []
	
		win.blit(darkMask, (-int(camPos.x), -int(camPos.y)))
		
	wormCol.fill(SKY)
	extraCol.fill(SKY)

def boom(pos, radius, debries = True, gravity = False, fire = False):
	global camTrack
	if not fire: radius *= radiusMult
	boomPos = Vector(pos[0], pos[1])
	# sample ground colors:
	if debries:
		colors = []
		for i in range(10):
			sample = (pos + vectorUnitRandom() * uniform(0,radius)).vec2tupint()
			if isOnMap(sample):
				color = ground.get_at(sample)
				if not color == SKY:
					colors.append(color)
		if len(colors) == 0:
			colors = Blast._color
	
	# ground delete
	if not fire:
		Explossion(pos, radius)
		
	# draw burn:
	stain(pos, imageHole, (int(radius*4),int(radius*4)), True)
	
	pygame.draw.circle(gameMap, SKY, pos.vec2tupint(), int(radius))
	pygame.draw.circle(ground, SKY, pos.vec2tupint(), int(radius))
	if not fire:
		pygame.draw.circle(groundSec, SKY, pos.vec2tupint(), int(radius * 0.7))
	
	listToCheck = PhysObj._reg if not fire else PhysObj._worms
	
	for p in listToCheck:
		if not p.boomAffected:
			continue
		distance = dist(p.pos, boomPos)
		
		if distance < radius * shockRadius:
			# shockwave
			direction = (p.pos - boomPos).normalize()
			p.vel += direction * - 0.5 * (1/shockRadius) * (distance - radius * shockRadius) * 1.3
			p.stable = False
			# damage
			if p.health:
				if p.health > 0:
					dmg = -(1/shockRadius)*(distance - radius * shockRadius) * 1.2
					p.damage(dmg)
			if p in PhysObj._worms:
				if gravity:
					p.gravity = p.gravity * -1
				if not fire:
					camTrack = p
	if debries:
		for i in range(int(radius)):
			d = Debrie(pos, radius/5, colors)
			d.radius = choice([2,1])

def stain(pos, surf, size, alphaMore):
	rotated = pygame.transform.rotate(pygame.transform.scale(surf, size), randint(0, 360))
	if alphaMore:
		rotated.set_alpha(randint(100,180))
	size = rotated.get_size()
	grounder = pygame.Surface(size, pygame.SRCALPHA)
	grounder.blit(ground, (0,0), (pos - tup2vec(size)/2, size))
	patch = pygame.Surface(size, pygame.SRCALPHA)
	
	grounder.blit(ground, (0,0), (pos - tup2vec(size)/2, size))
	patch.blit(gameMap, (0,0), (pos - tup2vec(size)/2, size))
	patch.set_colorkey(GRD)
	
	grounder.blit(rotated, (0,0))
	grounder.blit(patch, (0,0))
	
	grounder.set_colorkey(SKY)
	ground.blit(grounder, pos - tup2vec(size)/2)

def splash(pos, vel):
	for i in range(10 + int(vel.getMag())):
		d = Debrie(Vector(pos.x, mapHeight - Water.level - 3), 10, [waterColor[1]], 1)
		d.vel = vectorUnitRandom()
		d.vel.y = uniform(-1,0) * vel.getMag()
		d.vel.x *= vel.getMag() * 0.17
		d.radius = choice([2,1])

class Blast:
	_color = [(255,255,255), (255, 222, 3), (255, 109, 10), (254, 153, 35), (242, 74, 1), (93, 91, 86)]
	def __init__(self, pos, radius, smoke = 30, moving=0):
		nonPhys.append(self)
		self.timeCounter = 0
		self.pos = pos + vectorUnitRandom() * moving
		self.radius = radius
		self.rad = 0
		self.timeCounter = 0
		self.smoke = smoke
		self.rand = vectorUnitRandom() * randint(1, int(self.radius / 2))
	def step(self):
		if randint(0,self.smoke) == 0:
			Smoke(self.pos)
		self.timeCounter += 0.5
		self.rad = 1.359 * self.timeCounter * exp(- 0.5 * self.timeCounter) * self.radius
		if darkness:
			color = self._color[int(max(min(self.timeCounter, 5), 0))]
			lights.append((self.pos[0], self.pos[1], self.rad * 3, (color[0], color[1], color[2], 100) ))
		if self.timeCounter >= 10:
			nonPhys.remove(self)
			del self
	def draw(self):
		layersCircles[0].append((self._color[int(max(min(self.timeCounter, 5), 0))], self.pos, self.rad))
		layersCircles[1].append((self._color[int(max(min(self.timeCounter-1, 5), 0))], self.pos + self.rand, self.rad*0.6))
		layersCircles[2].append((self._color[int(max(min(self.timeCounter-2, 5), 0))], self.pos + self.rand, self.rad*0.3))

class FireBlast():
	_color = [(255, 222, 3), (242, 74, 1), (255, 109, 10), (254, 153, 35)]
	def __init__(self, pos, radius):
		self.pos = vectorCopy(pos) + vectorUnitRandom() * randint(1, 5)
		self.radius = radius
		nonPhys.append(self)
		self.color = choice(self._color)
	def step(self):
		self.pos.y -= 2 - 0.4 * self.radius
		self.pos.x += wind
		if randint(0, 10) < 3:
			self.radius -= 1
		if self.radius < 0:
			nonPhys.remove(self)
			del self
	def draw(self):
		if self.radius == 0:
			win.set_at(point2world(self.pos), self.color)
		pygame.draw.circle(win, self.color, point2world(self.pos), self.radius)

class Explossion:
	def __init__(self, pos, radius):	
		nonPhys.append(self)
		self.pos = pos
		self.radius = radius
		self.times = radius//5
		self.timeCounter = 0
	def step(self):
		Blast(self.pos + vectorUnitRandom() * uniform(0,self.radius/2), uniform(10, self.radius*0.7))
		self.timeCounter += 1
		if self.timeCounter == self.times:
			nonPhys.remove(self)
			del self
	def draw(self):
		pass

def mapGetAt(pos, mat=None):
	if not mat:
		mat = gameMap
	if pos[0] >= mapWidth or pos[0] < 0 or pos[1] >= mapHeight or pos[1] < 0:
		return SKY
	return mat.get_at((int(pos[0]), int(pos[1])))

def isVisibleInDarkness(self):
	if state == PLACING_WORMS:
		return True
	if self in PhysObj._worms and objectUnderControl:
		if dist(self.pos, objectUnderControl.pos) < lightRadius:
			return True
	
	if isOnMap(self.pos):
		if darkMask.get_at(self.pos.vec2tupint())[3] < 255:
			return True
	return False

def drawWindIndicator():
	pygame.draw.line(win, (100,100,255), (20, 15), (int(20 + wind * 20),15))
	pygame.draw.line(win, (0,0,255), (20, 10), (20,20))

def giveGoodPlace(div = 0, girderPlace = True):
	goodPlace = False
	counter = 0
	
	if fortsMode and not div == -1:
		half = mapWidth/totalTeams
		Slice = div % totalTeams
		
		left = half * Slice
		right = left + half
		if left <= 0: left += 6
		if right >= mapWidth: right -= 6
	else:
		left, right = 6, mapWidth - 6
	
	if diggingMatch:
		while not goodPlace:
			place = Vector(randint(int(left), int(right)), randint(6, mapHeight - 50))
			goodPlace = True
			for worm in PhysObj._worms:
				if dist(worm.pos, place) < 75:
					goodPlace = False
					break
				if  not goodPlace:
					continue
		return place
	
	while not goodPlace:
		# give rand place
		counter += 1
		goodPlace = True
		place = Vector(randint(int(left), int(right)), randint(6, mapHeight - 6))
		
		# if in ground 
		if isGroundAround(place):
			goodPlace = False
			continue
		
		if counter > 8000:
			# if too many iterations, girder place
			if not girderPlace:
				return None
			for worm in PhysObj._worms:
				if dist(worm.pos, place) < 50:
					goodPlace = False
					break
			if  not goodPlace:
				continue
			girder(place + Vector(0,20))
			return place
		
		# put place down
		y = place.y
		for i in range(mapHeight):
			if y + i >= mapHeight:
				goodPlace = False
				break
			if gameMap.get_at((place.x, y + i)) == GRD or wormCol.get_at((place.x, y + i)) != (0,0,0) or extraCol.get_at((place.x, y + i)) != (0,0,0):
				y = y + i - 7
				break
		if  not goodPlace:
			continue
		place.y = y
		
		# check for nearby worms in radius 50
		for worm in PhysObj._worms:
			if dist(worm.pos, place) < 50:
				goodPlace = False
				break
		if  not goodPlace:
			continue
		
		# check for nearby mines in radius 40
		for mine in PhysObj._mines:
			if dist(mine.pos, place) < 40:
				goodPlace = False
				break
		if  not goodPlace:
			continue
		
		# check for nearby petrol cans in radius 30
		for can in PetrolCan._cans:
			if dist(can.pos, place) < 40:
				goodPlace = False
				break
		if  not goodPlace:
			continue
		
		# if all conditions are met, make hole and place
		if isGroundAround(place):
			pygame.draw.circle(gameMap, SKY, place.vec2tup(), 5)
			pygame.draw.circle(ground, SKY, place.vec2tup(), 5)
	return place

def placePetrolCan(quantity = 1):
	for times in range(quantity):
		place = giveGoodPlace(-1, False)
		if place:
			pt = PetrolCan((place.x, place.y - 2))

def placeMines(quantity = 1):
	for times in range(quantity):
		place = giveGoodPlace(-1)
		m = Mine((place.x, place.y - 2))
		m.damp = 0.1

def placePlants(quantity = 1):
	for times in range(quantity):
		place = giveGoodPlace(-1, False)
		if place:
			PlantBomb((place.x, place.y - 2), (0,0), 0)

def placeFlag():
	place = giveGoodPlace(-1)
	Flag(place)

extra = [] #posx, posy, color, repeat
def addExtra(pos, color = (255,255,255), delay = 5, absolute = False):
	extra.append((pos[0], pos[1], color, delay, absolute))

def drawExtra():
	global extra
	extraNext = []
	for i in extra:
		if not i[4]:
			win.fill(i[2], (point2world((i[0], i[1])),(1,1)))
		else:
			win.fill(i[2], ((i[0], i[1]),(1,1)))
		if i[3] > 0:
			extraNext.append((i[0], i[1], i[2], i[3]-1, i[4]))
	extra = extraNext

layersCircles = [[],[],[]]
layersLines = [] #color, start, end, width, delay
def drawLayers():
	global layersCircles, layersLines
	layersLinesNext = []
	
	for i in layersLines:
		pygame.draw.line(win, i[0], point2world(i[1]), point2world(i[2]), i[3])
		if i[4]:
			layersLinesNext.append((i[0], i[1], i[2], i[3], i[4]-1))
	layersLines = layersLinesNext
	
	for j in layersCircles:
		for i in j:
			pygame.draw.circle(win, i[0], point2world(i[1]), int(i[2]))
	layersCircles = [[],[],[]]
	
def clamp(value, upper, lower):
	if value > upper:
		value = upper
	if value < lower:
		value = lower
	return value

def renderMountains(dims, color):
	
	mount = pygame.Surface(dims, pygame.SRCALPHA)
	mount.fill((0,0,0,0))
	
	noiseSeed = []
	
	for i in range(dims[0]):
		noiseSeed.append(uniform(0,1))
	noiseSeed[0] = 0.5
	surface = perlinNoise1D(dims[0], noiseSeed, 7, 2) # 8 , 2.0
	
	for x in range(0,dims[0]):
		for y in range(0,dims[1]):
			if y >= surface[x] * dims[1]:
				mount.set_at((x,y), color)

	return mount
	
def createLandNoise(dims):
	pass
	
def perlinNoise1D(count, seed, octaves, bias):
	output = []
	for x in range(count):
		noise = 0.0
		scaleAcc = 0.0
		scale = 1.0
		
		for o in range(octaves):
			pitch = count >> o
			sample1 = (x // pitch) * pitch
			sample2 = (sample1 + pitch) % count
			blend = (x - sample1) / pitch
			sample = (1 - blend) * seed[int(sample1)] + blend * seed[int(sample2)]
			scaleAcc += scale
			noise += sample * scale
			scale = scale / bias
		output.append(noise / scaleAcc)
	return output

def renderCloud2():
	c1 = (224, 233, 232)
	c2 = (192, 204, 220)
	surf = pygame.Surface((170, 70), pygame.SRCALPHA)
	circles = []
	leng = randint(15,30)
	space = 5
	gpos = (20, 40) 
	for i in range(leng):
		pos = Vector(gpos[0] + i * space, gpos[1]) + vectorUnitRandom() * uniform(0, 10)
		radius = max(20 * (exp(-(1/(5*leng)) * ((pos[0]-gpos[0])/space -leng/2)**2)), 5) * uniform(0.8,1.2)
		circles.append((pos, radius))
	circles.sort(key=lambda x: x[0][0])
	for c in circles:
		pygame.draw.circle(surf, c2, c[0], c[1])
	for c in circles:
		pygame.draw.circle(surf, c1, c[0] - Vector(1,1) * 0.7 * 0.2 * c[1], c[1] * 0.8)
	for i in range(0,len(circles),int(len(circles)/4)):
		pygame.draw.circle(surf, c2, circles[i][0], circles[i][1])
	for i in range(0,len(circles),int(len(circles)/8)):
		pygame.draw.circle(surf, c1, circles[i][0] - Vector(1,1) * 0.8 * 0.2 * circles[i][1], circles[i][1] * 0.8)
	
	return surf

# sprites
if True:
	imageMountain = renderMountains((180, 110), feelColor[3])
	imageMountain2 = renderMountains((180, 150), feelColor[2])
	colorRect = pygame.Surface((2,2))
	pygame.draw.line(colorRect, feelColor[0], (0,0), (2,0))
	pygame.draw.line(colorRect, feelColor[1], (0,1), (2,1))
	imageSky = pygame.transform.smoothscale(colorRect, (winWidth, winHeight))
	imageBat = pygame.image.load("assets/bat.png").convert_alpha()
	imageTurret = pygame.image.load("assets/turret.png").convert_alpha()
	imageParachute = pygame.image.load("assets/parachute.png").convert_alpha()
	imageVenus = pygame.image.load("assets/venus.png").convert_alpha()
	imagePokeball = pygame.image.load("assets/pokeball.png").convert_alpha()
	imageGreenShell = pygame.image.load("assets/greenShell.png").convert_alpha()
	imageEnder = pygame.image.load("assets/ender.png").convert_alpha()
	imageBlood = pygame.image.load("assets/blood.png").convert_alpha()
	imageSnail = pygame.image.load("assets/snail.png").convert_alpha()
	imageHole = pygame.image.load("assets/hole.png").convert_alpha()
	imageSeagull = pygame.image.load("assets/seagull.png").convert_alpha()
	imageMjolnir = pygame.image.load("assets/mjolnir.png").convert_alpha()

def drawBackGround(surf, parallax):
	width = surf.get_width()
	height = surf.get_height()
	offset = (camPos.x/parallax)//width
	times = winWidth//width + 2
	for i in range(times):
		x = int(-camPos.x/parallax) + int(int(offset) * width + i * width)
		y = int(mapHeight - initialWaterLevel - height) - int(camPos.y) + int((mapHeight - initialWaterLevel - winHeight - int(camPos.y))/(parallax*1.5)) + 20 - parallax * 3
		win.blit(surf, (x, y))

def point2world(point):
	return (int(point[0]) - int(camPos[0]), int(point[1]) - int(camPos[1]))

def move(obj):
	dir = obj.facing
	if checkFreePos(obj, obj.pos + Vector(dir, 0)):
		obj.pos += Vector(dir, 0)
		return True
	else:
		for i in range(1,5):
			if checkFreePos(obj, obj.pos + Vector(dir, -i)):
				obj.pos += Vector(dir, -i)
				return True
		for i in range(1,5):
			if checkFreePos(obj, obj.pos + Vector(dir, i)):
				obj.pos += Vector(dir, i)
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

def checkFreePos(obj, pos, wormcol = False):
	## moveable objs only
	r = 0
	while r < 2 * pi:
		testPos = Vector((obj.radius) * cos(r) + pos.x, (obj.radius) * sin(r) + pos.y)
		if testPos.x >= mapWidth or testPos.y >= mapHeight - Water.level or testPos.x < 0:
			if mapClosed:
				return False
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			if gameMap.get_at((int(testPos.x), 0)) == GRD:#mapClosed and 
				return False
			else:
				r += pi /8
				continue
		
		getAt = testPos.vec2tupint()
		if gameMap.get_at(getAt) == GRD:
			return False
		if extraCol.get_at(getAt) != (0,0,0):
			return False
		if wormcol and wormCol.get_at(getAt) != (0,0,0):
			return False
		
		r += pi /8
	return True

def checkFreePosFallProof(obj, pos):
	r = 0
	while r < 2 * pi:
		testPos = Vector((obj.radius) * cos(r) + pos.x, (obj.radius) * sin(r) + pos.y)
		if testPos.x >= mapWidth or testPos.y >= mapHeight - Water.level or testPos.x < 0:
			if mapClosed:
				return False
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			r += pi /8
			continue
			
		if not gameMap.get_at((int(testPos.x), int(testPos.y))) == (0,0,0):
			return False
		
		r += pi /8
	# check for falling
	groundUnder = False
	for i in range(int(obj.radius), 50):
		# extra.append((pos.x, pos.y + i, (255,255,255), 5))
		if gameMap.get_at((int(pos.x), int(pos.y + i))) == GRD:
			groundUnder = True
			break
	return groundUnder

def checkPotential(obj, count):
	pot = []
	
	for i in range(1, count):
		pos = obj.pos + Vector(i * obj.facing, 0)
		if not isOnMap(pos):
			break
		pot.append(pos)
	
	for i in pot:
		if gameMap.get_at(i.vec2tupint()) == (0,0,0):
			while gameMap.get_at(i.vec2tupint()) == (0,0,0):
				if isOnMap((i[0], i[1] + 1)):
					i.y += 1
				else:
					break
		else:
			while gameMap.get_at(i.vec2tupint()) == GRD:
				if isOnMap((i[0], i[1] - 1)):
					i.y -= 1
				else:
					break
	
	if len(pot) == 0:
		return pot
		
	cut = None
	for i in range(1, len(pot)):
		prev = pot[i-1]
		curr = pot[i]
		# check for fall safety:
		distance = prev.y - curr.y
		if distance < 0:
			#going down
			if abs(distance) > 70:
				cut = i
				break
		if distance > 0:
			#going up
			if abs(distance) > 5:
				cut = i
				break
			
	pot = pot[0:i]
	
	for i in pot:
		addExtra(i)
	return pot

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

def grayen(color):
	return tuple(i//5 + 167 for i in color)

def getNormal(pos, vel, radius, wormCollision, extraCollision):
	# colission with world:
	response = Vector(0,0)
	angle = atan2(vel.y, vel.x)
	r = angle - pi
	while r < angle + pi:
		testPos = Vector((radius) * cos(r) + pos.x, (radius) * sin(r) + pos.y)
		if testPos.x >= mapWidth or testPos.y >= mapHeight - Water.level or testPos.x < 0:
			if mapClosed:
				response += pos - testPos
				r += pi /8
				continue
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			r += pi /8
			continue
		
		if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
			response += pos - testPos
		if wormCollision and wormCol.get_at((int(testPos.x), int(testPos.y))) == GRD:
			response += pos - testPos
		if extraCollision and extraCol.get_at((int(testPos.x), int(testPos.y))) == GRD:
			response += pos - testPos
		
		r += pi /8
	return response

################################################################################ Objects
timeCounter = turnTime
timeOverall = 0
timeSurf = (timeCounter, myfont.render(str(timeCounter), False, HUDColor))
def timeStep():
	global timeCounter
	if timeCounter == 0:
		timeOnTimer()
	if not timeCounter <= 0:
		timeCounter -= 1
def timeOnTimer():
	global state, nextState
	if state == PLAYER_CONTROL_1:
		state = WAIT_STABLE
		
	elif state == PLAYER_CONTROL_2:
		state = nextState
		
	elif state == FIRE_MULTIPLE:
		state = PLAYER_CONTROL_2
		
	if objectUnderControl.rope:
		objectUnderControl.toggleRope(None)
	if objectUnderControl.parachuting:
		objectUnderControl.toggleParachute()
def timeDraw():
	global timeSurf
	if timeSurf[0] != timeCounter:
		timeSurf = (timeCounter, myfont.render(str(timeCounter), False, HUDColor))
	win.blit(timeSurf[1] , ((int(10), int(8))))
def timeReset():
	global timeCounter
	timeCounter = turnTime
def timeRemaining(amount):
	global timeCounter
	timeCounter = amount

nonPhys = []
class FloatingText: #pos, text, color
	def __init__(self, pos, text, color = (255,0,0)):
		nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.surf = myfont.render(str(text), False, color)
		self.timeCounter = 0
		self.phase = uniform(0,2*pi)
	def step(self):
		self.timeCounter += 1
		self.pos.y -= 0.5
		self.pos.x += 0.25 * sin(0.1 * timeOverall + self.phase)
		if self.timeCounter == 50:
			nonPhys.remove(self)
			del self
	def draw(self):
		win.blit(self.surf , (int(self.pos.x - camPos.x - self.surf.get_size()[0]/2), int(self.pos.y - camPos.y)))

class PhysObj:
	_reg = []
	_worms = []
	_mines = []
	_fastest = 10
	def initialize(self):
		self._reg.append(self)
		self.vel = Vector(0,0)
		self.acc = Vector(0,0)
		
		self.stable = False
		self.damp = 0.4
		
		self.bounceBeforeDeath = -1
		self.dead = False
		self.color = (255,0,0)
		self.windAffected = moreWindAffected
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
		self.vel += self.acc
		self.limitVel()
		# position
		ppos = self.pos + self.vel
		
		# reset forces
		self.acc *= 0
		self.stable = False
		
		angle = atan2(self.vel.y, self.vel.x)
		response = Vector(0,0)
		collision = False
		
		if warpedMode and camTrack == self:
			if ppos.x > mapWidth:
				ppos.x = 0
				camPos.x -= mapWidth
			if ppos.x < 0:
				ppos.x = mapWidth
				camPos.x += mapWidth
		
		# colission with world:
		r = angle - pi
		while r < angle + pi:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= mapWidth or testPos.y >= mapHeight - Water.level or testPos.x < 0:
				if mapClosed:
					response += ppos - testPos
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				if gameMap.get_at((int(testPos.x), 0)) == GRD:#mapClosed and 
					response += ppos - testPos
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
				continue
			
			# collission with gameMap:
			if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
				collision = True
				r += pi /8; continue

			else:
				if not self.wormCollider and wormCol.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
				elif not self.extraCollider and extraCol.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
			
			r += pi / 8
		
		magVel = self.vel.getMag()
		
		if collision:
			
			self.collisionRespone(ppos)
			if magVel > 5 and self.fallAffected:
				self.damage(magVel * 1.5 * fallDamageMult, 1)
				# blood
				if self in PhysObj._worms:
					stain(self.pos, imageBlood, imageBlood.get_size(), False)
			self.stable = True
			
			response.normalize()
			
			fdot = self.vel.dot(response)
			if not self.bounceBeforeDeath == 1:
				
				# damp formula 1 - logarithmic
				# dampening = max(self.damp, self.damp * log(magVel) if magVel > 0.001 else 1)
				# dampening = min(dampening, min(self.damp * 2, 0.9))
				# newVel = ((response * -2 * fdot) + self.vel) * dampening
				
				# legacy formula
				newVel = ((response * -2 * fdot) + self.vel) * self.damp * dampMult
					
				self.vel = newVel
				# max speed recorded ~ 25
			
			if self.bounceBeforeDeath > 0:
				self.bounceBeforeDeath -= 1
				self.dead = self.bounceBeforeDeath == 0
				
		else:
			self.pos = ppos
			
		# flew out gameMap but not worms !
		if self.pos.y > mapHeight - Water.level and not self in self._worms:
			if self not in Debrie._debries:
				splash(self.pos, self.vel)
			angle = self.vel.getAngle()
			if (angle > 2.7 and angle < 3.14) or (angle > 0 and angle < 0.4):
				if self.vel.getMag() > 7:
					self.pos.y = mapHeight - Water.level - 1
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
			del self
	def applyForce(self):
		# gravity:
		self.acc.y += globalGravity
		if self.windAffected > 0:
			if self.pos.x < - 3 * mapWidth or self.pos.x > 4 * mapWidth:
				return
			self.acc.x += wind * 0.1 * windMult * self.windAffected
	def deathResponse(self):
		pass
	def secondaryStep(self):
		pass
	def removeFromGame(self):
		PhysObj._reg.remove(self)
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
	_debries = []
	def __init__(self, pos, blast, colors, bounces=2):
		Debrie._debries.append(self)
		self.initialize()
		self.vel = Vector(cos(uniform(0,1) * 2 *pi), sin(uniform(0,1) * 2 *pi)) * blast
		self.pos = Vector(pos[0],pos[1])
		
		self.boomAffected = False
		self.bounceBeforeDeath = bounces
		self.color = choice(colors)
		self.radius = 1
		self.damp = 0.5
	def applyForce(self):
		# gravity:
		self.acc.y += globalGravity * 2.5
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius))

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
		self.megaBoom = False or megaTrigger
		if randint(0,50) == 1:
			self.megaBoom = True
	def deathResponse(self):
		if self.megaBoom:
			self.boomRadius *= 2
		boom(self.pos, self.boomRadius)
	def draw(self):
		theta = self.vel.getAngle()
		dir = vectorCopy(self.vel)
		dir.setMag(self.radius + 6)
		dir2 = vectorCopy(dir)
		dir2.setDir(dir.getAngle() + pi/2)
		dir2.setMag(2)
		a,b = self.pos.x,self.pos.y
		pygame.draw.polygon(win, self.color, [(int(a+dir.x - camPos.x),int(b+dir.y- camPos.y)), (int(a+dir2.x- camPos.x),int(b+dir2.y- camPos.y)), (int(a-dir2.x- camPos.x),int(b-dir2.y- camPos.y)) ])
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2, randint(5,8), 30, 3)

class Grenade (PhysObj):#2
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,100,0)
		self.damp = 0.4
		self.timer = 0
	def deathResponse(self):
		rad = 30
		if randint(0,50) == 1 or megaTrigger:
			rad *= 2
		boom(self.pos, rad)
	def secondaryStep(self):
		self.timer += 1
		if self.timer == fuseTime:
			self.dead = True
		self.stable = False

class Mortar (Grenade):#3
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,50,0)
		self.bounceBeforeDeath = -1
		self.damp = 0.4
		self.timer = 0
	def deathResponse(self):
		global camTrack
		megaBoom = False
		boom(self.pos, 25)
		if randint(0,50) == 1 or megaTrigger:
			megaBoom = True
		if megaBoom:
				for j in range(10):
					k = Missile(self.pos, (uniform(-0.5,0.5),uniform(-0.7,-0.1)), 0.5)
					k.vel.x += self.vel.x * 0.5
					k.vel.y += self.vel.y * 0.5
					k.windAffected = 0
					k.boomAffected = False
					k.color = (0,50,0)
					k.radius = 1.5
					if j == 5:
						camTrack = k
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
			if i == 0:
				camTrack = m

class PetrolBomb(PhysObj):#4
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (158,66,43)
		self.bounceBeforeDeath = 1
		self.damp = 0.5
		self.surf = pygame.Surface((3, 8)).convert_alpha()
		self.surf.fill(self.color)
		self.angle = 0
	def secondaryStep(self):
		self.angle -= self.vel.x*4
	def deathResponse(self):
		boom(self.pos, 15)
		if randint(0,50) == 1 or megaTrigger:
			for i in range(80):
				s = Fire(self.pos, 5)
				s.vel = Vector(cos(2*pi*i/80), sin(2*pi*i/80))*uniform(3,4)
		else:
			for i in range(40):
				s = Fire(self.pos, 5)
				s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2)
	def draw(self):
		surf = pygame.transform.rotate(self.surf, self.angle)
		win.blit(surf , (int(self.pos.x - camPos.x - surf.get_size()[0]/2), int(self.pos.y - camPos.y - surf.get_size()[1]/2)))

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
		self.facing = RIGHT if self.pos.x < mapWidth/2 else LEFT
		self.shootAngle = 0 if self.pos.x < mapWidth/2 else pi
		self.shootAcc = 0
		self.shootVel = 0
		self.health = initialHealth
		self.alive = True
		self.team = team
		self.sick = 0
		self.gravity = DOWN
		if name:
			self.nameStr = name
		else:
			self.nameStr = randomNames.pop()
		self.name = myfont.render(self.nameStr, False, self.team.color)
		self.healthStr = myfont.render(str(self.health), False, self.team.color)
		self.score = 0
		self.jetpacking = False
		self.rope = None #[pos, radius]
		self.parachuting = False
		self.wormCollider = True
		self.flagHolder = False
		self.sleep = False
		self.surf = pygame.Surface((8, 8), pygame.SRCALPHA)
		self.setSurf()
		if darkness:
			self.darktree = []
	def applyForce(self):
		# gravity:
		if self.gravity == DOWN:
			### JETPACK
			if self.jetpacking and playerControl and objectUnderControl == self:
				global jetPackFuel
				if pygame.key.get_pressed()[pygame.K_UP]:# or joystick.get_axis(1) < -0.5:
					self.acc.y -= globalGravity + 0.5
					jetPackFuel -= 0.5
				if pygame.key.get_pressed()[pygame.K_LEFT]:
					self.acc.x -= 0.5
					jetPackFuel -= 0.5
				if pygame.key.get_pressed()[pygame.K_RIGHT]:
					self.acc.x += 0.5
					jetPackFuel -= 0.5
				if jetPackFuel <= 0:
					self.toggleJetpack()
			#### ROPE
			if self.rope and playerControl:
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
			
			self.acc.y += globalGravity
			
			if self.parachuting:
				if self.vel.y > 1:
					self.vel.y = 1
		else:# up
			self.acc.y -= globalGravity
	def drawCursor(self):
		shootVec = self.pos + Vector((cos(self.shootAngle) * 20) ,sin(self.shootAngle) * 20)
		pygame.draw.circle(win, (255,255,255), (int(shootVec.x) - int(camPos.x), int(shootVec.y) - int(camPos.y)), 2)
	def sicken(self, sickness = 1):
		self.sick = sickness
		self.color = (128, 189,66)
	def toggleJetpack(self):
		self.jetpacking = not self.jetpacking
		self.fallAffected = not self.fallAffected
		global jetPackFuel
		jetPackFuel = 100
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
			dmg = int(value * damageMult)
			if dmg < 1:
				dmg = 1
			if dmg > self.health:
				dmg = self.health
			
			if dmg != 0: FloatingText(self.pos.vec2tup(), str(dmg))
			self.health -= dmg
			if self.health < 0:
				self.health = 0
			if Worm.healthMode == 1:
				self.healthStr = myfont.render(str(self.health), False, self.team.color)
			global damageThisTurn
			if not self == objectUnderControl:
				if not sentring and not raoning and not waterRising and not self in currentTeam.worms:
					damageThisTurn += dmg
			if gameMode == CAPTURE_THE_FLAG and damageType != 2:
				if self.flagHolder:
					self.team.flagHolder = False
					self.flagHolder = False
					Flag(self.pos)
			global terminatorHit
			if gameMode == TERMINATOR and victim == self and not terminatorHit:
				currentTeam.points += 1
				addToKillList()
				terminatorHit = True
	def setSurf(self):
		pygame.draw.circle(self.surf, self.color, (4,4), 4)
	def draw(self):
		if not self is objectUnderControl and self.alive:
			pygame.draw.circle(wormCol, GRD, self.pos.vec2tupint(), int(self.radius)+1)
		if darkness and not isVisibleInDarkness(self):
			return
			
		if self.parachuting:
			win.blit(imageParachute, point2world(self.pos - tup2vec(imageParachute.get_size())//2 + Vector(0,-15)))
		if self.flagHolder:
			pygame.draw.line(win, (51, 51, 0), point2world(self.pos), point2world(self.pos + Vector(0, -3 * self.radius)))
			pygame.draw.rect(win, (220,0,0), (point2world(self.pos + Vector(1, -3 * self.radius)), (self.radius*2, self.radius*2)))
			
		# draw artifact
		if len(self.team.artifacts) > 0 and holdArtifact:
			if self is objectUnderControl and weaponMan.getCategory(weaponMan.currentWeapon) == ARTIFACTS:
				if weaponMan.currentArtifact() in self.team.artifacts:
					if weaponMan.currentArtifact() == MJOLNIR:
						win.blit(imageMjolnir, point2world(self.pos + Vector(self.facing * 3, -5) - tup2vec(imageMjolnir.get_size())/2))

		# draw worm sprite
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		
		# draw name
		nameHeight = -21
		namePos = Vector(self.pos.x - self.name.get_width()/2, max(self.pos.y + nameHeight, 10))
		win.blit(self.name , point2world(namePos))
		if self.alive and self.pos.y < 0:
			num = myfont.render(str(int(-self.pos.y)), False, self.team.color)
			win.blit(num, point2world(namePos + Vector(self.name.get_width() + 2,0)))
		
		if warpedMode:
			pygame.draw.circle(win, self.color, point2world(self.pos + Vector(mapWidth)), int(self.radius)+1)
			pygame.draw.circle(win, self.color, point2world(self.pos + Vector(-mapWidth)), int(self.radius)+1)
			win.blit(self.name , ((int(self.pos.x) - int(camPos.x) - mapWidth - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(camPos.y) - 21)))
			win.blit(self.name , ((int(self.pos.x) - int(camPos.x) + mapWidth - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(camPos.y) - 21)))
		
		if self.rope:
			rope = [point2world(x) for x in self.rope[0]]
			rope.append(point2world(self.pos))
			pygame.draw.lines(win, (250,250,0), False, rope)
		if self.alive and drawHealthBar:
			self.drawHealth()
		if self.sleep and self.alive:
			if timeOverall % fps == 0:
				FloatingText(self.pos, "z", (0,0,0))
	def __str__(self):
		return self.nameStr
	def __repr__(self):
		return str(self)
	def dieded(self, cause=-1):
		global state, nextState, teams, damageThisTurn
		
		if timeTravel:
			timeTravelPlay()
			return
		
		self.alive = False
		self.color = (167,167,167)
		self.name = myfont.render(self.nameStr, False, grayen(self.team.color))

		# insert to kill list:
		if not sentring and not raoning and not waterRising and not self in currentTeam.worms:
			damageThisTurn += self.health
			currentTeam.killCount += 1
			if gameMode == POINTS:
				string = self.nameStr + " by " + objectUnderControl.nameStr
				killList.insert(0, (myfont.render(string, False, HUDColor), 0))
		
		self.health = 0
		
		# if capture the flag:
		if self.flagHolder:
			self.flagHolder = False
			self.team.flagHolder = False
			if cause == Worm.causeFlew:
				p = deployPack(FLAG_DEPLOY)
				global camTrack
				camTrack = p
			else:
				Flag(self.pos)
		
		# commentator:
		if cause == -1:
			Commentator.que.append((self.nameStr, choice(Commentator.stringsDmg), self.team.color))
		elif cause == Worm.causeFlew:
			comment = True
			if not self in currentTeam.worms and weaponMan.currentWeapon == "baseball" and state in [PLAYER_CONTROL_2, WAIT_STABLE]:
				Commentator.que.append((self.nameStr, Commentator.stringBaseBall, self.team.color))
				comment = False
			if comment:
				Commentator.que.append((self.nameStr, choice(Commentator.stringsFlw), self.team.color))
		
		# remove from regs:
		if self in PhysObj._worms:
			PhysObj._worms.remove(self)
		if self in self.team.worms:
			self.team.worms.remove(self)
		if cause == Worm.causeFlew or cause == Worm.causeVenus:
			PhysObj._reg.remove(self)
		
		# if under control 
		if objectUnderControl == self:
			if state == FIRE_MULTIPLE:
				if weaponMan.getCurrentStyle() == GUN:
					self.team.ammo(weaponMan.currentWeapon, -1)
					weaponMan.renderWeaponCount()
			nextState = PLAYER_CONTROL_2
			state = nextState
			timeRemaining(wormDieTime)
		if gameMode == TERMINATOR and self == victim:
			currentTeam.points += 1
			addToKillList()
			if not terminatorHit:
				currentTeam.points += 1
				addToKillList()
			if state in [PLAYER_CONTROL_1, FIRE_MULTIPLE]:
				pickVictim()
	def drawHealth(self):
		healthHeight = -15
		if Worm.healthMode == 0:
			value = 20 * min(self.health/initialHealth, 1)
			if value < 1:
				value = 1
			pygame.draw.rect(win, (220,220,220),(point2world(self.pos + Vector(-10, healthHeight)),(20,3)))
			pygame.draw.rect(win, (0,220,0),(point2world(self.pos + Vector(-10, healthHeight)), (int(value),3)))
		else:
			win.blit(self.healthStr , point2world(self.pos + Vector(-self.healthStr.get_width()/2, healthHeight)))
		# draw jetpack fuel
		if self.jetpacking:
			value = 20 * (jetPackFuel/100)
			if value < 1:
				value = 1
			pygame.draw.rect(win, (220,220,220),(point2world(self.pos + Vector(-10, -25)), (20,3)))
			pygame.draw.rect(win, (0,0,220),(point2world(self.pos + Vector(-10, -25)), (int(value),3)))
	def secondaryStep(self):
		global state, nextState
		if objectUnderControl == self and playerControl and self.alive:
			if not self.rope: self.damp = 0.1
			else: self.damp = 0.5
		
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
		if self.jetpacking and not state == WAIT_STABLE and objectUnderControl == self:
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
				if gameMap.get_at(testPos.vec2tupint()) == GRD:
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
					if gameMap.get_at(testPos.vec2tupint()) == GRD:
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
			self.vel.x = wind * 1.5
		
		# virus
		if self.sick == 2 and self.health > 0 and not state == WAIT_STABLE:
			if randint(1,200) == 1:
				SickGas(self.pos, 2)
		
		# shooting angle
		self.shootVel = clamp(self.shootVel + self.shootAcc, 0.1, -0.1)
		self.shootAngle += self.shootVel * self.facing
		if self.facing == RIGHT:
			self.shootAngle = clamp(self.shootAngle, pi/2, -pi/2)
		elif self.facing == LEFT:
			self.shootAngle = clamp(self.shootAngle, pi + pi/2, pi/2)
		
		# maintain dark tree
		# if darkness and objectUnderControl and self in currentTeam.worms:
			# if dist(self.pos, objectUnderControl.pos) < lightRadius:
				# if not self in objectUnderControl.darktree:
					# objectUnderControl.darktree.append(self)
					# for worm in currentTeam.worms:
						# if dist()
			# if self in objectUnderControl.darktree and not dist(self.pos, objectUnderControl.pos) < lightRadius:
				# objectUnderControl.darktree.remove(self)
			
			
			# for w in self.darktree:
				# lights.append((w.pos[0], w.pos[1], lightRadius, (0,0,0,0)))
		
		# check if killed:
		if self.health <= 0 and self.alive:
			self.dieded()
		
		# check if on gameMap:
		if self.pos.y > mapHeight - Water.level:
			splash(self.pos, self.vel)
			angle = self.vel.getAngle()
			if (angle > 2.7 and angle < 3.14) or (angle > 0 and angle < 0.4):
				if self.vel.getMag() > 7:
					self.pos.y = mapHeight - Water.level - 1
					self.vel.y *= -1
					self.vel.x *= 0.7
			else:
				self.dieded(Worm.causeFlew)
		if self.pos.y < 0:
			self.gravity = DOWN
		if actionMove:
			if objectUnderControl == self and self.health > 0 and not self.jetpacking and not self.rope:
				move(self)
	def saveStr(self):
		string = ""
		string += str(self.nameStr) + ":\n"
		string += list2str(self.pos) + "\n"
		string += str(self.facing) + "\n"
		string += str(self.shootAngle) + "\n"
		string += str(self.health) + "\n"
		string += str(self.sick) + "\n"
		string += str(self.gravity) + "\n"
		return string

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
			Smoke(self.pos)
		self.timer += 1
		if self.fallen:
			self.life -= 1
		if darkness:
			lights.append((self.pos[0], self.pos[1], 20, (0,0,0,0)))
		if self.life == 0:
			self._reg.remove(self)
			del self
			return
		if randint(0,1) == 1 and self.timer > self.delay:
			boom(self.pos + Vector(randint(-1,1),randint(-1,1)), 3, False, False, True)
	def draw(self):
		radius = 1
		if self.life > 20:
			radius += 1
		if self.life > 10:
			radius += 1
		self.yellow = int(sin(0.3*timeOverall + self.phase) * ((255-106)/4) + 255 - ((255-106)/2))
		pygame.draw.circle(win, (self.red, self.yellow, 69), (int(self.pos.x - camPos.x), int(self.pos.y - camPos.y)), radius)

class Smoke:
	smokeCount = 0
	def __init__(self, pos, vel = None, color = None):
		nonPhys.append(self)
		Smoke.smokeCount += 1
		if color:
			self.color = color
		else:
			self.color = (randint(0,40), randint(0,40), randint(0,40), 50)
		self.radius = randint(8,10)
		self.pos = tup2vec(pos)
		self.acc = Vector(0,0)
		if vel:
			self.vel = vel
		else:
			self.vel = Vector(0,0)
		self.timeCounter = 0
	def draw(self):
		pygame.gfxdraw.filled_circle(win, int(self.pos.x - camPos.x), int(self.pos.y - camPos.y), self.radius, self.color)
	def step(self):
		self.timeCounter += 1
		if self.timeCounter % 5 == 0:
			self.radius -= 1
			if self.radius == 0:
				nonPhys.remove(self)
				Smoke.smokeCount -= 1
				del self
				return
		self.acc.x = wind * 0.1 * windMult * uniform(0.2,1)
		self.acc.y = -0.1
		self.vel += self.acc
		self.pos += self.vel

class TNT(PhysObj):#5
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 2
		self.color = (255,0,0)
		self.bounceBeforeDeath = -1
		self.damp = 0.2
		self.timer = 0
	def secondaryStep(self):
		self.timer += 1
		self.stable = False
		if self.timer == fps*4:
			self.dead = True
	def deathResponse(self):
		global camTrack, grenadeThrown, grenadeTimer
		boom(self.pos, 40)
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -2) - int(camPos.x),int(self.pos.y -4) - int(camPos.y) , 3,8))
		pygame.draw.line(win, (90,90,90), point2world(self.pos + Vector(-1,-4)), point2world(self.pos + Vector(-1, -5*(fps*4 - self.timer)/(fps*4) - 4)), 1)
		if randint(0,10) == 1:
			Blast(self.pos + Vector(-1, -5*(fps*4 - self.timer)/(fps*4) - 4), randint(3,6), 150)

shotCount = 0
def fireShotgun(start, direction, power=15):#6
	hit = False

	for t in range(5,500):
		testPos = start + direction * t
		addExtra(testPos, (255, 204, 102), 3)
		
		if testPos.y >= mapHeight - Water.level:
			splash(testPos, Vector(10,0))
			break
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue

		# hit worms or ground:
		# hit ground:
		at = (int(testPos.x), int(testPos.y))
		if gameMap.get_at(at) == GRD or wormCol.get_at(at) != (0,0,0) or extraCol.get_at(at) != (0,0,0):
			if wormCol.get_at(at) != (0,0,0):
				stain(testPos, imageBlood, imageBlood.get_size(), False)
			boom(testPos, power)
			break

girderAngle = 0
girderSize = 50
def girder(pos):
	surf = pygame.Surface((girderSize, 10)).convert_alpha()
	surf.fill((102, 102, 153, 255))
	surfGround = pygame.transform.rotate(surf, girderAngle)
	ground.blit(surfGround, (int(pos[0] - surfGround.get_width()/2), int(pos[1] - surfGround.get_height()/2)) )
	surf.fill(GRD)
	surfMap = pygame.transform.rotate(surf, girderAngle)
	gameMap.blit(surfMap, (int(pos[0] - surfMap.get_width()/2), int(pos[1] - surfMap.get_height()/2)) )
	
def drawGirderHint():#7
	surf = pygame.Surface((girderSize, 10)).convert_alpha()
	surf.fill((102, 102, 153, 100))
	surf = pygame.transform.rotate(surf, girderAngle)
	pos = pygame.mouse.get_pos()
	pos = Vector(pos[0]/scalingFactor , pos[1]/scalingFactor )
	win.blit(surf, (int(pos[0] - surf.get_width()/2), int(pos[1] - surf.get_height()/2)))

def fireFlameThrower(pos, direction):#8
	offset = uniform(1,2)
	f = Fire(pos + direction * 5)
	f.vel = direction * offset * 2.4

class StickyBomb (Grenade):#9
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (117,47,7)
		self.bounceBeforeDeath = -1
		self.damp = 0.5
		self.timer = 0
		self.sticked = False
		self.stick = None
	def collisionRespone(self, ppos):
		if not self.sticked:
			self.sticked = True
			self.stick = vectorCopy((self.pos + ppos)/2)
	def secondaryStep(self):
		self.stable = False
		if self.stick:
			self.pos = self.stick
		self.timer += 1
		if self.timer == fuseTime:
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
		self.radius = 5
		self.color = (191, 44, 44)
		self.damp = 0.1
		self.health = 5
		self.extraCollider = True
	def deathResponse(self):
		boom(self.pos, 20)
		pygame.draw.rect(extraCol, SKY, (int(self.pos.x -3),int(self.pos.y -5), 7,10))
		for i in range(40):
			f = Fire(self.pos)
			f.vel.x = (i-20)*0.1*1.5
			f.vel.y = uniform(-2,-0.4)
		PhysObj._reg.remove(self)
		if self in PetrolCan._cans:
			PetrolCan._cans.remove(self)
	def secondaryStep(self):
		if self.health <= 0:
			self.deathResponse()
	def damage(self, value, damageType=0):
		dmg = value * damageMult
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0
	def draw(self):
		pygame.draw.rect(extraCol, GRD, (int(self.pos.x -3),int(self.pos.y -5), 7,10))
		if darkness and not isVisibleInDarkness(self):
			return
		pygame.draw.rect(win, self.color, (int(self.pos.x -3) - int(camPos.x),int(self.pos.y -5) - int(camPos.y) , 7,10))
		pygame.draw.circle(win, (218, 238, 44), (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), 3)

class Mine(PhysObj):
	def __init__(self, pos, delay=0):
		self.initialize()
		self._mines.append(self)
		self.pos = tup2vec(pos)
		self.radius = 2
		self.color = (52,66,71)
		self.damp = 0.4
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
				if dist(self.pos, w.pos) < 25:
					self.activated = True
		else:
			self.timer += 1
			self.stable = False
			if self.timer == self.exploseTime:
				self.dead = True
	def deathResponse(self):
		boom(self.pos, 30)
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		if diggingMatch:
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

def fireBaseball(start, direction):
	global camTrack
	hitted = []
	layersLines.append(((255, 204, 0), start + direction * 5, start + direction * 20, 4, 15))
	for t in range(5, 20):
		testPos = start + direction * t
		for worm in PhysObj._worms:
			if dist(testPos, worm.pos) < worm.radius:
				if worm in hitted:
					continue
				hitted.append(worm)
				worm.damage(randint(15,25))
				worm.vel += direction*8
				camTrack = worm

class SickGas:
	def __init__(self, pos, sickness = 1):
		nonPhys.append(self)
		self.color = (102, 255, 127, 100)
		self.radius = randint(8,18)
		self.pos = tup2vec(pos)
		self.acc = Vector(0,0)
		self.vel = Vector(0,0)
		self.stable = False
		self.boomAffected = False
		self.timeCounter = 0
		self.sickness = sickness
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		pygame.gfxdraw.filled_circle(win, int(self.pos.x - camPos.x), int(self.pos.y - camPos.y), self.radius, self.color)
	def step(self):
		self.timeCounter += 1
		if self.timeCounter % 8 == 0:
			self.radius -= 1
			if self.radius == 0:
				nonPhys.remove(self)
				del self
				return
		self.acc.x = wind * 0.1 * windMult * uniform(0.2,1)
		self.acc.y = -0.1
		self.vel += self.acc
		self.pos += self.vel
		for worm in PhysObj._worms:
			if dist(self.pos, worm.pos) < self.radius + worm.radius:
				worm.sicken(self.sickness)

class GasGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (113,117,41)
		self.bounceBeforeDeath = -1
		self.damp = 0.5
		self.timer = 0
	def deathResponse(self):
		boom(self.pos, 20)
		for i in range(40):
			s = SickGas(self.pos)
			s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1,1.5)
	def secondaryStep(self):
		self.timer += 1
		if self.timer == fuseTime:
			self.dead = True
		if self.timer > 20 and self.timer % 5 == 0:
			SickGas(self.pos)

deploying = False
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
		#Commentator.que.append(("", choice(Commentator.stringsCrt), (0,0,0)))
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		pygame.draw.rect(win, self.color, (int(self.pos.x) -5 - int(camPos.x),int(self.pos.y) -5 - int(camPos.y) , 10,10))
		pygame.draw.rect(win, (255,108,80), (int(self.pos.x) -4 - int(camPos.x),int(self.pos.y) -1 - int(camPos.y) , 8,2))
		pygame.draw.rect(win, (255,108,80), (int(self.pos.x) -1 - int(camPos.x),int(self.pos.y) -4 - int(camPos.y) , 2,8))
	def secondaryStep(self):
		global objectUnderControl
		if dist(objectUnderControl.pos, self.pos) < self.radius + objectUnderControl.radius + 5 and not objectUnderControl.health <= 0:
			self._reg.remove(self)
			self.effect(objectUnderControl)
			del self
			return
		if self.health <= 0:
			self.deathResponse()
	def effect(self, worm):
		worm.health += 50
		FloatingText(self.pos, "+50", (0,230,0))
		if Worm.healthMode == 1:
			worm.healthStr = myfont.render(str(worm.health), False, worm.team.color)
		# if worm.health > 100:
			# worm.health = 100
		worm.sick = 0
		worm.color = (255, 206, 167)

class UtilityPack(HealthPack):# Utility Pack
	def __init__(self, pos = (0,0)):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 5
		self.color = (166, 102, 33)
		self.surf = myfont.render("?", False, (222,222,0))
		self.damp = 0.01
		self.health = 5
		self.fallAffected = False
		self.windAffected = 0
		self.box = choice(["moon gravity", "double damage", "aim aid", "teleport", "switch worms", "time travel", "jet pack", "portal gun", "travel kit", "ender pearls"])
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		pygame.draw.rect(win, self.color, (int(self.pos.x -5) - int(camPos.x),int(self.pos.y -5) - int(camPos.y) , 10,10))
		win.blit(self.surf, (int(self.pos.x) - int(camPos.x)-1, int(self.pos.y) - int(camPos.y)-2))
	def effect(self, worm):
		if unlimitedMode:
			return
		FloatingText(self.pos, self.box, (0,200,200))
		if self.box == "portal gun":
			worm.team.ammo(self.box, 1)
			return
		elif self.box == "travel kit":
			worm.team.ammo("rope", 3)
			worm.team.ammo("parachute", 3)
			return
		elif self.box == "ender pearls":
			worm.team.ammo("ender pearl", 5)
			return
		
		worm.team.ammo(self.box, 1)

class WeaponPack(HealthPack):# Weapon Pack
	def __init__(self, pos = (0,0)):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.radius = 5
		self.color = (166, 102, 33)
		self.surf = myfont.render("W", False, (222,222,0))
		self.damp = 0.01
		self.health = 5
		self.fallAffected = False
		self.windAffected = 0
		weaponsInBox = ["banana", "holy grenade", "earthquake", "gemino mine", "sentry turret", "bee hive", "vortex grenade", "chilli pepper", "covid 19", "raging bull", "electro boom", "pokeball", "green shell", "guided missile"]
		if allowAirStrikes:
			weaponsInBox .append("mine strike")
		self.box = choice(weaponsInBox)
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		pygame.draw.rect(win, self.color, (int(self.pos.x -5) - int(camPos.x),int(self.pos.y -5) - int(camPos.y) , 10,10))
		win.blit(self.surf, (int(self.pos.x) - int(camPos.x)-2, int(self.pos.y) - int(camPos.y)-2))
	def effect(self, worm):
		if unlimitedMode:
			return
		
		FloatingText(self.pos, self.box, (0,200,200))
		worm.team.ammo(self.box, 1)

def deployPack(pack):
	x = 0
	ymin = 20
	goodPlace = False #1 has ground under. #2 not in ground. #3 not above worm 
	while not goodPlace:
		x = randint(10, mapWidth - 10)
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
		for i in range(mapHeight):
			if y + i >= mapHeight - Water.level:
				# no ground bellow
				goodPlace = False
				continue
			if gameMap.get_at((x, y + i)) == GRD:
				goodPlace = True
				break
		# test3 (hopefully always possible)
		for worm in PhysObj._worms:
			if x > worm.pos.x-15 and x < worm.pos.x+15:
				goodPlace = False
				continue
	
	if pack == HEALTH_PACK:
		p = HealthPack((x, y))
	elif pack == UTILITY_PACK:
		p = UtilityPack((x, y))
	elif pack == WEAPON_PACK:
		p = WeaponPack((x, y))
	elif pack == FLAG_DEPLOY:
		p = Flag((x, y))
	return p

airStrikeDir = RIGHT
airStrikeSpr = myfontbigger.render(">>>", False, HUDColor)
def fireAirstrike(pos):
	global camTrack
	x = pos[0]
	y = 5
	for i in range(5):
		f = Missile((x - 40 + 20*i, y - i), (airStrikeDir ,0), 0.1)
		f.megaBoom = False
		f.boomAffected = False
		f.radius = 1
		f.boomRadius = 19
		if i == 2:
			camTrack = f

def fireMineStrike(pos):
	megaBoom = False
	if randint(0,50) == 1 or megaTrigger:
		megaBoom = True
	global camTrack
	x = pos[0]
	y = 5
	if megaBoom:
		for i in range(20):
			m = Mine((x - 40 + 4*i, y - i))
			m.vel.x = airStrikeDir
			if i == 10:
				camTrack = m
	else:
		for i in range(5):
			m = Mine((x - 40 + 20*i, y - i))
			m.vel.x = airStrikeDir
			if i == 2:
				camTrack = m

def fireNapalmStrike(pos):
	global camTrack
	x = pos[0]
	y = 5
	for i in range(70):
		f = Fire((x - 35 + i, y ))
		f.vel = Vector(cos(uniform(pi, 2*pi)), sin(uniform(pi, 2*pi))) * 0.5
		if i == 2:
			camTrack = f

class GravityMissile(Missile):
	def deathResponse(self):
		global camTrack
		# camTrack = objectUnderControl
		boom(self.pos, self.boomRadius, True, True)
	def applyForce(self):
		# gravity:
		self.acc.y -= globalGravity
		self.acc.x += wind * 0.1 * windMult
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2, 5)
		if self.pos.y < 0:
			self._reg.remove(self)
			del self

def fireGammaGun(start, direction):
	hitted = []
	normal = Vector(-direction.y, direction.x).normalize()
	for t in range(5,500):
		testPos = start + direction * t + normal * 1.5 * sin(t * 0.6) * (t + 1)/70
		addExtra(testPos, (0,255,255), 10)
		
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue
		# if hits worm:
		for worm in PhysObj._worms:
			if dist(testPos, worm.pos) < worm.radius and not worm in hitted:
				worm.damage(int(10/damageMult)+1)
				if randint(0,20) == 1:
					worm.sicken(2)
				else:
					worm.sicken()
				hitted.append(worm)
		# if hits plant:
		for plant in Venus._reg:
			if dist(testPos, plant.pos + plant.direction * 25) <= 25:
				plant.mutant = True
		for target in ShootingTarget._reg:
			if dist(testPos, target.pos) < target.radius:
				target.explode()

class HolyGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.color = (230, 230, 0)
		self.damp = 0.5
		self.timer = 0
	def deathResponse(self):
		boom(self.pos, 45)
	def secondaryStep(self):
		self.stable = False
		self.timer += 1
		if self.timer == fuseTime + 2*fps:
			self.dead = True
		if self.timer == fuseTime + fps:
			Commentator.que.append(choice([("hand grenade",("o lord bless this thy ",""),(210,210,0)), ("",("blow thine enemy to tiny bits ",""),(210,210,0)), ("",("feast upon the lambs and sloths and carp",""),(210,210,0)), ("",("three shall be the number thous shalt count",""),(210,210,0)), ("",("thou shall snuff that",""),(210,210,0))]))

class Banana(Grenade):
	def __init__(self, pos, direction, energy, used = False):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255, 204, 0)
		self.damp = 0.5
		self.timer = 0
		self.surf = myfontbigger.render("(", False, self.color)
		self.angle = 0
		self.used = used
	def collisionRespone(self, ppos):
		if self.used:
			self.dead = True
	def deathResponse(self):
		if self.used:
			boom(self.pos, 40)
			return
		global camTrack
		boom(self.pos, 40)
		for i in range(5):
			angle = (i * pi) / 6 + pi / 6
			direction = (cos(angle)*uniform(0.2,0.6), -sin(angle))
			m = Banana(self.pos, direction, uniform(0.3,0.8), True)
			m.boomAffected = False
			if i == 2:
				camTrack = m
	def secondaryStep(self):
		if not self.used: 
			self.timer += 1
		if self.timer == fuseTime:
			self.dead = True
		self.angle -= self.vel.x*4
	def draw(self):
		surf = pygame.transform.rotate(self.surf, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Earthquake:
	earthquake = False
	def __init__(self):
		self.timer = 210
		nonPhys.append(self)
		self.stable = False
		self.boomAffected = False
		Earthquake.earthquake = True
	def step(self):
		for obj in PhysObj._reg:
			if obj == self or obj in Portal._reg:
				continue
			if randint(0,5) == 1:
				obj.vel += Vector(randint(-1,1), -uniform(0,1))
		self.timer -= 1
		if self.timer == 0:
			nonPhys.remove(self)
			Earthquake.earthquake = False
			del self
		
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
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), int(self.radius)+1)
		pygame.draw.circle(win, (222,63,49), (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), 1)

class Plant:
	def __init__(self, pos, radius = 5, angle = -1, venus = False):
		PhysObj._reg.append(self)
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
		self.venus = venus
	def step(self):
		self.pos += vectorFromAngle(self.angle + uniform(-1,1))
		if randint(1,100) <= 2 and not self.venus:
			Plant(self.pos, self.radius, self.angle + choice([pi/3, -pi/3]))
		self.timeCounter += 1
		if self.timeCounter % 10 == 0:
			self.radius -= 1
		self.green += randint(-5,5)
		if self.green > 255:
			self.green = 255
		if self.green < 0:
			self.green = 0
		pygame.draw.circle(gameMap, GRD, (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		pygame.draw.circle(ground, (55,self.green,40), (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		
		if self.radius == 0:
			PhysObj._reg.remove(self)
			if self.venus:
				Venus(self.pos, self.angle)
			del self
	def draw(self):
		pass

class PlantBomb(PhysObj):
	venus = True
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (204, 204, 0)
		self.damp = 0.5
		self.venus = PlantBomb.venus
		self.wormCollider = True
	def collisionRespone(self, ppos):
		response = getNormal(ppos, self.vel, self.radius, False, True)
		
		
		PhysObj._reg.remove(self)
		
		if not self.venus:
			for i in range(randint(4,5)):
				Plant(ppos)
		else:
			Plant(ppos, 5, response.getAngle(), True)

sentring = False
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
		self.surf = imageTurret.copy()
		self.electrified = False
		pygame.draw.circle(self.surf, self.teamColor, tup2vec(self.surf.get_size())//2, 2)
	def fire(self):
		self.firing = True
	def engage(self):
		close = []
		for worm in PhysObj._worms:
			if worm.team.color == self.teamColor:
				continue
			distance = dist(worm.pos, self.pos)
			if distance < 100:
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
			if timeOverall % 2 == 0:
				self.angle = uniform(0,2*pi)
				fireMiniGun(self.pos, vectorFromAngle(self.angle))
		
		self.angle += (self.angle2for - self.angle)*0.2
		if not self.target and timeOverall % (fps*2) == 0:
			self.angle2for = uniform(0,2*pi)
		
		# extra "damp"
		if self.vel.x > 0.1:
			self.vel.x = 0.1
		if self.vel.x < -0.1:
			self.vel.x = -0.1
		if self.vel.y < 0.1:
			self.vel.y = 0.1
			
		if self.health <= 0:
			PhysObj._reg.remove(self)
			self._sentries.remove(self)
			boom(self.pos, 20)
			
			del self
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
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
		PhysObj._reg.remove(self)
	def step(self):
		self.lifespan -= 1
		gameDistable()
		if self.lifespan == 0:
			PhysObj._reg.remove(self)
			del self
			return
		if self.target:
			self.angle = (self.target.pos - self.pos).getAngle()
		else:
			self.angle += uniform(-0.6,0.6)
		ppos = self.pos + vectorFromAngle(self.angle)
		if ppos.x >= mapWidth or ppos.y >= mapHeight or ppos.x < 0 or ppos.y < 0:
			ppos = self.pos + vectorFromAngle(self.angle) * -1
			self.angle += pi
		try:
			if gameMap.get_at((ppos.vec2tupint())) == GRD:
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
					PhysObj._reg.remove(self)
					self.target.damage(uniform(1,8))
					del self
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
	def secondaryStep(self):
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
	def step(self):
		self.applyForce()
		
		# velocity
		if self.inGround:
			if self.mode:
				self.vel = self.drillVel
				self.vel.setMag(2)
			else:
				self.vel += self.acc
				self.vel.limit(5)
		else:
			self.vel += self.acc
		
		# position
		ppos = self.pos + self.vel
		
		# reset forces
		self.acc *= 0
		self.stable = False
		
		collision = False
		# colission with world:
		direction = self.vel.getDir()
		
		checkPos = (self.pos + direction*self.radius).vec2tupint()
		if not(checkPos[0] >= mapWidth or checkPos[0] < 0 or checkPos[1] >= mapHeight or checkPos[1] < 0):
			if gameMap.get_at(checkPos) == GRD:
				self.inGround = True
				self.drillVel = vectorCopy(self.vel)
		if self.inGround:
			self.timer += 1
					
		checkPos = (self.pos + direction*(self.radius + 2)).vec2tupint()
		if not(checkPos[0] >= mapWidth or checkPos[0] < 0 or checkPos[1] >= mapHeight or checkPos[1] < 0):
			if not gameMap.get_at(checkPos) == GRD and self.inGround:
				self.dead = True
				
		if self.timer == fps*2:
			self.dead = True
			
		self.lastPos.x, self.lastPos.y = self.pos.x, self.pos.y
		self.pos = ppos
		
		if self.inGround:
			boom(self.pos, self.radius, False)
		self.lineOut((self.lastPos.vec2tupint(), self.pos.vec2tupint()))
		
		# flew out gameMap but not worms !
		if self.pos.y > mapHeight:
			self._reg.remove(self)
			return
		if self.inGround and self.pos.y <= 0:
			self.dead = True

		if self.vel.getMag() < 0.1:
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self._reg.remove(self)
			self.deathResponse()
			del self
	def lineOut(self,line):
		pygame.draw.line(gameMap, SKY, line[0], line[1], self.radius*2)
		pygame.draw.line(ground, SKY, line[0], line[1], self.radius*2)
	def draw(self):
		theta = self.vel.getAngle()
		dir = vectorCopy(self.vel)
		dir.setMag(self.radius + 6)
		dir2 = vectorCopy(dir)
		dir2.setDir(dir.getAngle() + pi/2)
		dir2.setMag((self.radius + 6)/2)
		a,b = self.pos.x,self.pos.y
		pygame.draw.polygon(win, self.color, [(int(a+dir.x - camPos.x),int(b+dir.y- camPos.y)), (int(a+dir2.x- camPos.x),int(b+dir2.y- camPos.y)), (int(a-dir2.x- camPos.x),int(b-dir2.y- camPos.y)) ])
	def deathResponse(self):
		boom(self.pos, 23)

def drawLightning(start, end, color = (153, 255, 255)):
	radius = end.radius
	end = end.pos
	start = start.pos
	halves = int(dist(end, start) / 4)
	if halves == 0:
		halves = 1
	direction = (end - start)
	direction.setMag(dist(start, end)/halves)
	points = []
	for t in range(halves):
		if t == 0 or t == halves - 1:
			point = (start + direction * t).vec2tupint()
		else:
			point = ((start + direction * t) + vectorUnitRandom() * uniform(-10,10)).vec2tupint()
		points.append(point2world(point))
	if not len(points) <= 1:
		pygame.draw.lines(win, color, False, points, 2)
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
	def deathResponse(self):
		rad = 20
		boom(self.pos, rad)
		for sentry in self.sentries:
			sentry.electrified = False
	def secondaryStep(self):
		self.stable = False
		self.timer += 1
		if self.timer == fuseTime:
			self.electrifying = True
		if self.timer >= fuseTime + self.lifespan:
			self.dead = True
		if self.electrifying:
			self.stable = False
			self.worms = []
			self.raons = []
			self.shells = []
			for worm in PhysObj._worms:
				if dist(self.pos, worm.pos) < 100:
					self.worms.append(worm)
			for raon in Raon._raons:
				if dist(self.pos, raon.pos) < 100:
					self.raons.append(raon)
			for shell in GreenShell._shells:
				if dist(self.pos, shell.pos) < 100:
					self.shells.append(shell)
			for sentry in SentryGun._sentries:
				if dist(self.pos, sentry.pos) < 100:
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
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
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
	def applyForce(self):
		# gravity:
		if self.activated:
			desired = HomingMissile.Target - self.pos
			desired.setMag(50)
			self.acc = desired - self.vel
			self.acc.limit(1)
		else:
			self.acc.y += globalGravity
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2, 5)
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
		theta = self.vel.getAngle()
		dir = vectorCopy(self.vel)
		dir.setMag(self.radius + 6)
		dir2 = vectorCopy(dir)
		dir2.setDir(dir.getAngle() + pi/2)
		dir2.setMag((self.radius + 6)/2)
		a,b = self.pos.x,self.pos.y
		pygame.draw.polygon(win, self.color, [(int(a+dir.x - camPos.x),int(b+dir.y- camPos.y)), (int(a+dir2.x- camPos.x),int(b+dir2.y- camPos.y)), (int(a-dir2.x- camPos.x),int(b-dir2.y- camPos.y)) ])

def drawTarget(pos):
	pygame.draw.line(win, (180,0,0), point2world((pos.x - 10, pos.y - 8)) , point2world((pos.x + 10, pos.y + 8)), 2)
	pygame.draw.line(win, (180,0,0), point2world((pos.x + 10, pos.y - 8)) , point2world((pos.x - 10, pos.y + 8)), 2)

class Vortex():
	vortexRadius = 180
	def __init__(self, pos):
		nonPhys.append(self)
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
				if worm in Portal._reg:
					continue
				if dist(self.pos, worm.pos) < Vortex.vortexRadius:
					worm.acc += (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
					if randint(0,20) == 1:
						worm.vel.y -= 2
				if worm in PhysObj._worms and dist(self.pos, worm.pos) < Vortex.vortexRadius/2:
					if randint(0,20) == 1:
						worm.damage(randint(1,8))
		else:
			for worm in PhysObj._reg:
				if worm in Portal._reg:
					continue
				if dist(self.pos, worm.pos) < Vortex.vortexRadius:
					worm.acc -= (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
			
		if not self.inhale and self.rot < 0:
			nonPhys.remove(self)
			del self
	def draw(self):
		width = 50
		arr = []
		for x in range(int(self.pos.x) - width//2, int(self.pos.x) + width//2):
			for y in range(int(self.pos.y) - width//2, int(self.pos.y) + width//2):
				if dist(Vector(x,y), self.pos) > width//2:
					continue
				rot = (dist(Vector(x,y), self.pos) - width//2) * self.rot
				direction = Vector(x,y) - self.pos
				direction.rotate(rot)
				getAt = point2world(self.pos + direction)
				if getAt[0] < 0 or getAt[0] >= winWidth or getAt[1] < 0 or getAt[1] >= winHeight:
					arr.append((0,0,0))
				else:
					pixelColor = win.get_at(getAt)
					arr.append(pixelColor)
		for x in range(int(self.pos.x) - width//2, int(self.pos.x) + width//2):
			for y in range(int(self.pos.y) - width//2, int(self.pos.y) + width//2):
				if dist(Vector(x,y), self.pos) > width//2:
					continue
				
				win.set_at(point2world((x,y)), arr.pop(0))

class VortexGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.color = (25, 102, 102)
		self.damp = 0.5
		self.timer = 0
	def deathResponse(self):
		Vortex(self.pos)

class TimeAgent:
	def __init__(self):
		PhysObj._reg.append(self)
		self.stable = False
		self.boomAffected = False
		self.positions = timeTravelPositions
		self.timeCounter = 0
		self.pos = self.positions[0]
		self.color = timeTravelList["color"]
		self.health = timeTravelList["health"]
		self.nameSurf = timeTravelList["name"]
		self.weapon = timeTravelList["weapon"]
		
		self.energy = 0
		self.stepsForEnergy = int(timeTravelList["energy"]/0.05)
	def step(self):
		if len(self.positions) == 0:
			global timeTravelFire, timeTravelPositions, timeTravelList
			timeTravelFire = True
			fire(timeTravelList["weapon"])
			PhysObj._reg.remove(self)
			timeTravelPositions = []
			timeTravelList = {}
			return
		self.pos = self.positions.pop(0)
		if len(self.positions) <= self.stepsForEnergy:
			self.energy += 0.05
			
		self.timeCounter += 1
	def draw(self):
		pygame.draw.circle(win, self.color, point2world(self.pos), 3+1)
		win.blit(self.nameSurf , ((int(self.pos[0]) - int(camPos.x) - int(self.nameSurf.get_size()[0]/2)), (int(self.pos[1]) - int(camPos.y) - 21)))
		pygame.draw.rect(win, (220,220,220),(int(self.pos[0]) -10 -int(camPos.x), int(self.pos[1]) -15 -int(camPos.y), 20,3))
		value = 20 * self.health/initialHealth
		if value < 1:
			value = 1
		pygame.draw.rect(win, (0,220,0),(int(self.pos[0]) -10 -int(camPos.x), int(self.pos[1]) -15 -int(camPos.y), int(value),3))
		
		i = 0
		while i < 20 * self.energy:
			cPos = vectorCopy(self.pos)
			angle = timeTravelList["weaponDir"].getAngle()
			pygame.draw.line(win, (0,0,0), (int(cPos[0] - camPos.x), int(cPos[1] - camPos.y)), ((int(cPos[0] + cos(angle) * i - camPos.x), int(cPos[1] + sin(angle) * i - camPos.y))))
			i += 1

timeTravelPositions = []
timeTravelList = {}
timeTravelFire = False
def timeTravelInitiate():
	global timeTravel, timeTravelList, timeCounter
	timeTravel = True
	timeTravelList = {}
	timeTravelList["color"] = objectUnderControl.color
	timeTravelList["name"] = objectUnderControl.name
	timeTravelList["health"] = objectUnderControl.health
	timeTravelList["initial pos"] = vectorCopy(objectUnderControl.pos)
	timeTravelList["timeCounter in turn"] = timeCounter
	timeTravelList["jet pack"] = jetPackFuel
def timeTravelRecord():
	timeTravelPositions.append(objectUnderControl.pos.vec2tup())
def timeTravelPlay():
	global timeTravel, timeCounter, timeTravelList, jetPackFuel
	timeCounter = timeTravelList["timeCounter in turn"]
	timeTravel = False
	timeTravelList["weapon"] = weaponMan.currentWeapon
	timeTravelList["weaponOrigin"] = vectorCopy(objectUnderControl.pos)
	timeTravelList["energy"] = energyLevel
	timeTravelList["weaponDir"] = Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle))
	objectUnderControl.health = timeTravelList["health"]
	if Worm.healthMode == 1:
		objectUnderControl.healthStr = myfont.render(str(objectUnderControl.health), False, objectUnderControl.team.color)
	objectUnderControl.pos = timeTravelList["initial pos"]
	objectUnderControl.vel *= 0
	jetPackFuel = timeTravelList["jet pack"]
	TimeAgent()
def timeTravelReset():
	global timeTravelPositions, timeTravelList, timeTravelFire
	timeTravelFire = False
	timeTravelPositions = []
	timeTravelList = {}

class ChilliPepper(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		width = 8
		height = 13
		self.surf = pygame.Surface((width, height)).convert_alpha()
		self.surf.fill((0,0,0,0))
		pygame.draw.polygon(self.surf, (230, 46, 0), [(0,0), (width-1, 0), (width//2, height)])
		self.damp = 0.5
		self.angle = 0
		self.boomAffected = False
		self.bounceBeforeDeath = 6
	def draw(self):
		surf = pygame.transform.rotate(self.surf, self.angle)
		win.blit(surf , (int(self.pos.x - camPos.x - surf.get_size()[0]/2), int(self.pos.y - camPos.y - surf.get_size()[1]/2)))
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
	def collisionRespone(self, ppos):
		boom(ppos, 25)
		for i in range(40):
			s = Fire(self.pos, 5)
			s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2)

class Covid19Old:
	def __init__(self, pos, angle = vectorUnitRandom().getAngle()):
		PhysObj._reg.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.stable = False
		self.boomAffected = False
		self.radius = 1
		self.angle = angle
		self.target = None
		self.lifespan = fps * 12
		self.unreachable = []
		self.bitten = []
	def removeFromGame(self):
		PhysObj._reg.remove(self)
	def step(self):
		# life:
		self.lifespan -= 1
		if self.lifespan == 0:
			PhysObj._reg.remove(self)
			boom(self.pos, 25)
			del self
			return
		if self.target:
			self.angle = (self.target.pos - self.pos).getAngle()
		else:
			self.angle += uniform(-1,1)
		ppos = self.pos + vectorFromAngle(self.angle)*5
		if ppos.x >= mapWidth or ppos.y >= mapHeight or ppos.x < 0 or ppos.y < 0:
			ppos = self.pos + vectorFromAngle(self.angle) * -1
			self.angle += pi
		try:
			if gameMap.get_at((ppos.vec2tupint())) == GRD:
				ppos = self.pos + vectorFromAngle(self.angle) * -1
				self.angle += pi
				if self.target:
					self.unreachable.append(self.target)
					self.target = None
		except IndexError:
			print("bat index error")
		self.pos = ppos
		
		if self.lifespan % 80 == 0:
			self.unreachable = []
		
		if self.lifespan < 410: # if alive
			if not self.target:
				closestDist = 500
				for worm in PhysObj._worms:
					if worm in self.unreachable or worm in self.bitten:
						continue
					distance = dist(self.pos, worm.pos)
					if distance < 500 and distance < closestDist:
						self.target = worm
						closestDist = distance
			else:
				if dist(self.pos, self.target.pos) > 50 or self.target.health <= 0:
					self.target = None
					return
				if dist(self.pos, self.target.pos) < self.target.radius:
					# sting
					self.target.vel.y -= 2
					if self.target.vel.y < -3:
						self.target.vel.y = 3
					if self.pos.x > self.target.pos.x:
						self.target.vel.x -= 2
					else:
						self.target.vel.x += 2
					# PhysObj._reg.remove(self)
					self.target.damage(10)
					self.target.sicken(2)
					self.bitten.append(self.target)
					self.target = None
	def draw(self):
		global timeOverall
		width = 16
		height = 11
		frame = timeOverall//2 % 5
		win.blit(imageBat, point2world(self.pos - Vector(width//2, height//2)), ((frame*width, 0), (width, height)) )

class Artillery(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (128, 0, 0)
		self.damp = 0.5
		self.surf = pygame.Surface((3, 8)).convert_alpha()
		self.surf.fill(self.color)
		self.angle = 0
		self.timer = 0
		self.bombing = False
		self.boomAffected = False
		self.booms = randint(3,5)
		self.boomCount = 20 if randint(0,50) == 0 or megaTrigger else self.booms
	def draw(self):
		surf = pygame.transform.rotate(self.surf, self.angle)
		win.blit(surf , (int(self.pos.x - camPos.x - surf.get_size()[0]/2), int(self.pos.y - camPos.y - surf.get_size()[1]/2)))
	def secondaryStep(self):
		if not self.bombing:
			self.angle -= self.vel.x*4
			if self.stable:
				self.timer += 1
			else:
				self.timer = 0
			if randint(0,5) == 0 and Smoke.smokeCount < 30:
				Smoke(self.pos, None, (200,0,0,50))
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
				if self.boomCount == self.booms:
					global camTrack
					camTrack = m
				self.boomCount -= 1
			if self.boomCount == 0:
				self.dead = True

class LongBow:
	_sleep = False #0-regular 1-sleep
	def __init__(self, pos, direction, sleep=False):
		PhysObj._reg.append(self)
		self.pos = vectorCopy(pos)
		self.direction = direction
		self.vel = direction.normalize() * 20
		self.stable = False
		self.boomAffected = False
		self.stuck = None
		self.color = (204, 102, 0)
		self.ignore = None
		self.sleep = sleep
		self.triangle = [Vector(0,3), Vector(6,0), Vector(0,-3)]
		for vec in self.triangle:
			vec.rotate(self.direction.getAngle())
	def destroy(self):
		PhysObj._reg.remove(self)
		del self
	def removeFromGame(self):
		PhysObj._reg.remove(self)
	def step(self):
		if not self.stuck:
			ppos = self.pos + self.vel
			iterations = 15
			for t in range(iterations):
				value = t/iterations
				testPos = (self.pos * value) + (ppos * (1-value))
				# check cans collision:
				for can in PetrolCan._cans:
					if dist(testPos, can.pos) < can.radius + 1:
						can.deathResponse()
						self.destroy()
						return
				# check worm collision
				for worm in PhysObj._worms:
					if worm == self.ignore:
						continue
					if dist(testPos, worm.pos) < worm.radius + 1:
						worm.vel += self.direction*4
						worm.vel.y -= 2
						worm.damage(randint(10,20) if self.sleep else randint(15,25))
						global camTrack
						camTrack = worm
						if self.sleep: worm.sleep = True
						self.destroy()
						stain(worm.pos, imageBlood, imageBlood.get_size(), False)
						return
				# check target collision:
				for target in ShootingTarget._reg:
					if dist(testPos, target.pos) < target.radius:
						target.explode()
						self.destroy()
						return
				# check gameMap collision
				if not isOnMap(testPos.vec2tupint()):
					PhysObj._reg.remove(self)
					return
				if gameMap.get_at(testPos.vec2tupint()) == GRD:
					self.stuck = vectorCopy(testPos)
			self.pos = ppos
		if self.stuck:
			self.pos = self.stuck
			
			points = [(self.pos - self.direction * 10 + i).vec2tupint() for i in self.triangle]
			pygame.draw.polygon(ground, (230,235,240), points)
			pygame.draw.polygon(gameMap, GRD, points)
			
			pygame.draw.line(gameMap, GRD, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
			pygame.draw.line(ground, self.color, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
			
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
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue
		if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
			objectUnderControl.toggleRope(testPos)
			Worm.roped = True
			break

class Armageddon:
	def __init__(self):
		nonPhys.append(self)
		self.stable = False
		self.boomAffected = False
		self.timer = 700
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			nonPhys.remove(self)
			del self
			return
		if timeOverall % 10 == 0:
			for i in range(randint(1,2)):
				x = randint(-100, mapWidth + 100)
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
		self.radius = 2
		self.color = (120, 230, 230)
		self.damp = 0.6
		self.timer = 0
		self.worms = []
		self.network = []
		self.used = []
		self.electrifying = False
	def secondaryStep(self):
		self.stable = False
		self.timer += 1
		if self.timer == fuseTime:
			self.electrifying = True
			self.calculate()
		if self.timer == fuseTime + fps*2:
			for net in self.network:
				for worm in net[1]:
					boom(worm.pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
				boom(net[0].pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
			boom(self.pos + vectorUnitRandom() * uniform(1,5), randint(10,16))
			self.dead = True
	def calculate(self):
		for worm in PhysObj._worms:
			if worm in objectUnderControl.team.worms:
				continue
			if dist(self.pos, worm.pos) < 150:
				self.worms.append(worm)
		for selfWorm in self.worms:
			net = []
			for worm in PhysObj._worms:
				if worm == selfWorm or worm in self.used or worm in self.worms or worm in objectUnderControl.team.worms:
					continue
				if dist(selfWorm.pos, worm.pos) < 150 and not worm in self.worms:
					net.append(worm)
					self.used.append(worm)
			self.network.append((selfWorm, net))
	def draw(self):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		
		for worm in self.worms:
			drawLightning(self, worm)
		for net in self.network:
			for worm in net[1]:
				drawLightning(net[0], worm)

def firePortal(start, direction):
	steps = 500
	for t in range(5,steps):
		testPos = start + direction * t
		addExtra(testPos, (255,255,255), 3)
		
		# missed
		if t == steps - 1:
			if len(Portal._reg) % 2 == 1:
				p = Portal._reg.pop(-1)
				PhysObj._reg.remove(p)

		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue

		# if hits map:
		if gameMap.get_at(testPos.vec2tupint()) == GRD:
			
			response = Vector(0,0)
			
			for i in range(12):
				ti = (i/12) * 2 * pi
				
				check = testPos + Vector(8 * cos(ti), 8 * sin(ti))
				
				if check.x >= mapWidth or check.y >= mapHeight or check.x < 0 or check.y < 0:
					continue
				if gameMap.get_at(check.vec2tupint()) == GRD:
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
		PhysObj._reg.append(self)
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
		if not gameMap.get_at(self.holdPos.vec2tupint()) == GRD:
			PhysObj._reg.remove(self)
			Portal._reg.remove(self)
			
			if self.brother:
				PhysObj._reg.remove(self.brother)
				Portal._reg.remove(self.brother)
			
				del self.brother
			del self
			
			return
			
		if state == PLAYER_CONTROL_1 and not self.brother:
			PhysObj._reg.remove(self)
			Portal._reg.remove(self)
			del self
			return
		
		# mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
		if self.brother:
			Bro = (self.pos - objectUnderControl.pos)
			angle = self.direction.getAngle() - (self.pos - objectUnderControl.pos).getAngle()
			broAngle = self.brother.dirNeg.getAngle()
			finalAngle = broAngle + angle
			Bro.setAngle(finalAngle)
			self.posBro = self.brother.pos - Bro
			
		if self.brother:
			for worm in PhysObj._reg:
				if worm in Portal._reg:
					continue
				if dist(worm.pos, self.pos) <= Portal.radiusOfContact:
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
		if darkness and not isVisibleInDarkness(self):
			return
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))

class Venus:
	_reg = []
	grow = -1
	catch = 0
	idle = 1
	hold = 2
	release = 3
	def __init__(self, pos, angle = -1):
		nonPhys.append(self)
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
	def step(self):
	
		self.gap = 5*(self.snap + pi/2)/(pi/2)
		self.d1 = self.direction.normal()
		self.d2 = self.d1 * -1
		self.p1 = self.pos + self.d1 * self.gap
		self.p2 = self.pos + self.d2 * self.gap
		
		if self.mode == Venus.grow:
			# check if can eat a worm from here on first round:
			global roundCounter
			if roundCounter == 0 and state in [PLAYER_CONTROL_1, PLACING_WORMS, CHOOSE_STARTER] and self.scale == 0:
				pos = self.pos + self.direction * 25
				for worm in PhysObj._worms:
					if dist(worm.pos, pos) <= 25:
						nonPhys.remove(self)
						Venus._reg.remove(self)
						return
			
			self.scale += 0.1
			if self.scale >= 1:
					
				self.scale = 1
				self.mode = Venus.hold
				gameMap.set_at(self.pos.vec2tupint(), GRD)
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
				maxDist = 800
				closest = None
				for worm in PhysObj._worms:
					distance = dist(worm.pos, self.pos)
					if distance < maxDist and distance < 80:
						maxDist = distance
						closest = worm
				if closest:
					self.desired = (closest.pos - self.pos).getAngle()
			listToCheck = PhysObj._reg + Seagull._reg
			for worm in listToCheck:
				if worm in Debrie._debries or worm in Portal._reg or worm in Flag.flags:
					continue
				if dist(worm.pos, pos) <= 25:
					self.mode = Venus.catch
					if worm in PhysObj._worms:
						worm.dieded(Worm.causeVenus)
						Commentator.que.append(choice([("", ("yummy",""), worm.team.color), (worm.nameStr, ("", " was delicious"), worm.team.color), (worm.nameStr, ("", " is good protein"), worm.team.color), (worm.nameStr, ("", " is some serious gourmet s**t"), worm.team.color)]))
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
						s = Smoke(self.pos + self.direction * 25 + vectorUnitRandom() * randint(3,10))
						nonPhys.remove(s)
						nonPhys.insert(0,s)
		elif self.mode == Venus.release:
			gameDistable()
			self.snap -= 0.1
			if self.snap <= self.opening:
				self.snap = self.opening
				self.mode = Venus.idle
		
		# check if self is destroyed
		if isOnMap(self.pos.vec2tupint()):
			if not gameMap.get_at(self.pos.vec2tupint()) == GRD:
				nonPhys.remove(self)
				Venus._reg.remove(self)
		else:
			nonPhys.remove(self)
			Venus._reg.remove(self)
		if self.pos.y >= mapHeight - Water.level:
			nonPhys.remove(self)
			Venus._reg.remove(self)
	def draw(self):
		
		if self.scale < 1: image = pygame.transform.scale(imageVenus, (tup2vec(imageVenus.get_size()) * self.scale).vec2tupint())
		else: image = imageVenus.copy()
		if self.mutant: image.fill((0, 125, 255, 100), special_flags=pygame.BLEND_MULT)
			
		rotated_image = pygame.transform.rotate(image, -degrees(self.angle - self.snap))
		rotated_offset = rotateVector(self.offset, self.angle - self.snap)
		rect = rotated_image.get_rect(center=(self.p2 + rotated_offset).vec2tupint())
		if not (darkness and not isVisibleInDarkness(self)):
			win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))
		extraCol.blit(rotated_image, tup2vec(rect) + self.direction*-25*(1-self.scale))
		
		rotated_image = pygame.transform.rotate(pygame.transform.flip(image, False, True), -degrees(self.angle + self.snap))
		rotated_offset = rotateVector(self.offset, self.angle + self.snap)
		rect = rotated_image.get_rect(center=(self.p1 + rotated_offset).vec2tupint())
		if not (darkness and not isVisibleInDarkness(self)):
			win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))
		extraCol.blit(rotated_image, tup2vec(rect) + self.direction*-25*(1-self.scale))

class Ball(PhysObj):#########EXPERIMENTAL
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
			if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0:
				if mapClosed:
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
			
			if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
				collision = True
			
			r += pi /8
		
		magVel = self.vel.getMag()
		
		if collision:
			self.collisionRespone(ppos)
			if self.vel.getMag() > 5 and self.fallAffected:
				self.damage(self.vel.getMag() * 1.5 * fallDamageMult)
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
			# flew out gameMap but not worms !
			if self.pos.y > mapHeight and not self in self._worms:
				self.outOfMapResponse()
				self._reg.remove(self)
				return
		
		if magVel < 0.1: # double jump problem
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self._reg.remove(self)
			self.deathResponse()
			del self
	def collisionRespone(self, ppos):
		if self.vel.getMag() > 5:
			boom(ppos, 7)

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
		self.angle = 0
	def damage(self, value, damageType=0):
		if damageType == 1:
			return
		dmg = int(value * damageMult)
		if dmg < 1:
			dmg = 1
		if dmg > self.health:
			dmg = self.health
		
		# FloatingText(self.pos.vec2tup(), str(dmg))
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
		
		if self.timer >= fuseTime and self.timer <= fuseTime + fps*2 and not self.hold:
			self.stable = False
			closer = [None, 7000]
			for worm in PhysObj._worms:
				distance = dist(self.pos, worm.pos)
				if distance < closer[1]:
					closer = [worm, distance]
			if closer[1] < 50:
				self.hold = closer[0]
				
		if self.timer == fuseTime + fps*2:
			if self.hold:
				PhysObj._reg.remove(self.hold)
				PhysObj._worms.remove(self.hold)
				self.hold.team.worms.remove(self.hold)
				if self.hold.flagHolder:
					self.hold.flagHolder = False
					self.hold.team.flagHolder = False
					Flag(self.hold.pos)
				self.name = myfont.render(self.hold.nameStr, False, self.hold.team.color)
				Commentator.que.append(choice([(self.hold.nameStr, ("",", i choose you"), self.hold.team.color), ("", ("", "gotta catch 'em al"), self.hold.team.color), (self.hold.nameStr, ("", " will help beat the next gym leader"), self.hold.team.color)]))
			else:
				self.dead = True
		
		if self.timer <= fuseTime + fps*2 + fps/2:
			gameDistable()
		
		if self.vel.getMag() > 0.25:
			self.angle -= self.vel.x*4
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		surf = pygame.transform.rotate(imagePokeball, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		if self.timer >= fuseTime and self.timer < fuseTime + fps*2 and self.hold:
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
				if worm == self or worm in self.ignore or worm in Portal._reg:
					continue
				if dist(worm.pos, self.pos) < self.radius + worm.radius:
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
		if darkness and not isVisibleInDarkness(self):
			return
		if not self.speed == 0:
			index = int((self.timer*(self.speed/3) % 12)/3)
		else:
			index = 0	
		win.blit(imageGreenShell, point2world(self.pos - Vector(16,16)/2), ((index*16, 0), (16,16)))

def fireLaser(start, direction):
	hit = False
	color = (254, 153, 35)
	square = [Vector(1,5), Vector(1,-5), Vector(-10,-5), Vector(-10,5)]
	for i in square:
		i.rotate(direction.getAngle())
	
	for t in range(5,500):
		testPos = start + direction * t
		# extra.append((testPos.x, testPos.y, (255,0,0), 3))
		
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			layersCircles[0].append((color, start, 5))
			layersCircles[0].append((color, testPos, 5))
			layersLines.append((color, start, testPos, 10, 1))
			continue
			
		# if hits worm:
		for worm in PhysObj._worms:
			if worm == objectUnderControl:
				continue
			if dist(testPos, worm.pos) < worm.radius + 2:
				if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
				layersCircles[0].append((color, start + direction * 5, 5))
				layersCircles[0].append((color, testPos, 5))
				layersLines.append((color, start + direction * 5, testPos, 10, 1))
				
				boom(worm.pos + Vector(randint(-1,1),randint(-1,1)), 2, False, False, True)
				# worm.damage(randint(1,5))
				# worm.vel += direction*2 + vectorUnitRandom()
				hit = True
				break
		# if hits can:
		for can in PetrolCan._cans:
			if dist(testPos, can.pos) < can.radius + 1:
				can.deathResponse()
				# hit = True
				break
		if hit:
			break
		
		# if hits gameMap:
		if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
			if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
			layersCircles[0].append((color, start + direction * 5, 5))
			layersCircles[0].append((color, testPos, 5))
			layersLines.append((color, start + direction * 5, testPos, 10, 1))
			points = []
			for i in square:
				points.append((testPos + i).vec2tupint())
			
			pygame.draw.polygon(gameMap, SKY, points)
			pygame.draw.polygon(ground, SKY, points)
			break

class GuidedMissile(PhysObj):
	def __init__(self, pos):
		self.initialize()
		self.pos = pos
		self.speed = 5.5
		self.vel = Vector(0, -self.speed)
		self.stable = False
		self.surf = pygame.Surface((10,6), pygame.SRCALPHA)
		pygame.draw.polygon(self.surf, (255,255,0), [(0,0), (0,6), (10,3)])
		self.radius = 3
	def applyForce(self):
		pass
	def turn(self, direc):
		self.vel.rotate(direc * 0.1)
	def step(self):
		global camTrack
		camTrack = self
		self.pos += self.vel
		if pygame.key.get_pressed()[pygame.K_LEFT]:
			self.vel.rotate(-0.3)
		elif pygame.key.get_pressed()[pygame.K_RIGHT]:
			self.vel.rotate(0.3)
		Blast(self.pos - self.vel * 1.5 + vectorUnitRandom()*2, randint(5,8))
		
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi
		collision = False
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + self.pos.x, (self.radius) * sin(r) + self.pos.y)
			if testPos.x >= mapWidth or testPos.y >= mapHeight - Water.level or testPos.x < 0:
				if mapClosed:
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
				collision = True
			
			r += pi /8
		
		if collision:
			boom(self.pos, 35)
			if randint(0,30) == 1 or megaTrigger:
				for i in range(80):
					s = Fire(self.pos, 5)
					s.vel = Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,4)
			PhysObj._reg.remove(self)
		if self.pos.y > mapHeight:
			PhysObj._reg.remove(self)
		
	def draw(self):
		surf = pygame.transform.rotate(self.surf, -degrees(self.vel.getAngle()))
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
		self.surf = pygame.Surface((3, 8)).convert_alpha()
		self.surf.fill(self.color)
		self.angle = 0
		self.lightRadius = 50
	def secondaryStep(self):
		if self.vel.getMag() > 0.25:
			self.angle -= self.vel.x*4
		if randint(0,10) == 1:
			Blast(self.pos, randint(self.radius,7), 150)
		if self.lightRadius < 0:
			PhysObj._reg.remove(self)
			Flare._flares.remove(self)
			del self
			return
		lights.append((self.pos[0], self.pos[1], self.lightRadius, (100,0,0,100)))
		
	def draw(self):
		surf = pygame.transform.rotate(self.surf, self.angle)
		win.blit(surf , (int(self.pos.x - camPos.x - surf.get_size()[0]/2), int(self.pos.y - camPos.y - surf.get_size()[1]/2)))

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
			if testPos.x >= mapWidth or testPos.y >= mapHeight - Water.level or testPos.x < 0:
				if mapClosed:
					response += ppos - testPos
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		PhysObj._reg.remove(self)
		
		response.normalize()
		pos = self.pos + response * (objectUnderControl.radius + 2)
		objectUnderControl.pos = pos
	def draw(self):
		win.blit(imageEnder , point2world(self.pos - tup2vec(imageEnder.get_size())/2))

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
		if objectUnderControl:
			if not objectUnderControl in PhysObj._worms:
				return
			if dist(objectUnderControl.pos, self.pos) < self.radius + objectUnderControl.radius:
				# worm has flag
				objectUnderControl.flagHolder = True
				objectUnderControl.team.flagHolder = True
				PhysObj._reg.remove(self)
				Flag.flags.remove(self)
				del self
				return
	def outOfMapResponse(self):
		Flag.flags.remove(self)
		p = deployPack(FLAG_DEPLOY)
		global camTrack
		camTrack = p
	def draw(self):
		pygame.draw.line(win, (51, 51, 0), point2world(self.pos + Vector(0, self.radius)), point2world(self.pos + Vector(0, -3 * self.radius)))
		pygame.draw.rect(win, self.color, (point2world(self.pos + Vector(1, -3 * self.radius)), (self.radius*2, self.radius*2)))

class ShootingTarget:
	numTargets = 10
	_reg = []
	def __init__(self):
		nonPhys.append(self)
		ShootingTarget._reg.append(self)
		self.pos = Vector(randint(10, mapWidth - 10), randint(10, mapHeight - 50))
		self.radius = 10
		pygame.draw.circle(gameMap, GRD, self.pos, self.radius)
		self.points = [self.pos + vectorFromAngle((i / 11) * 2 * pi) * (self.radius - 2) for i in range(10)]
	def step(self):
		for point in self.points:
			if gameMap.get_at(point.vec2tupint()) != GRD:
				self.explode()
				return
	def explode(self):
		boom(self.pos, 15)
		nonPhys.remove(self)
		ShootingTarget._reg.remove(self)
		currentTeam.points += 1
		if len(ShootingTarget._reg) < ShootingTarget.numTargets:
			ShootingTarget()
		# add to kill list(surf, name, amount):
		addToKillList()
	def draw(self):
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius))
		pygame.draw.circle(win, RED, point2world(self.pos), int(self.radius - 4))
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius - 8))

class Distorter(Grenade):#########EXPERIMENTAL
	def deathResponse(self):
		global ground
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
				if getAt[0] < 0 or getAt[0] >= mapWidth or getAt[1] < 0 or getAt[1] >= mapHeight:
					arr.append((0,0,0,0))
				else:
					pixelColor = ground.get_at(getAt)
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
					gameMap.set_at((x,y), SKY)
				else:
					gameMap.set_at((x,y), GRD)
				ground.set_at((x,y), color)

raoning = False
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
			if dist(self.pos, self.target.pos) > 100:
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
		if dist(self.target.pos, self.pos) < self.radius + self.target.radius + 2:
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
		if darkness and not isVisibleInDarkness(self):
			return
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

class Path:#########EXPERIMENTAL
	spacing = 50
	def __init__(self, pos):
		nonPhys.append(self)
		self.wormPoints = []
		for worm in PhysObj._worms:
			self.wormPoints.append(self.pathPoint(worm.pos))
		self.start = self.pathPoint(pos)
		self.graph = []
		for x in range(mapWidth//Path.spacing+1):
			col = []
			for y in range(mapHeight//Path.spacing+1):
				col.append(((Path.spacing*x,Path.spacing*y), "white", None))
			self.graph.append(col)
	def changePointByPos(self, pos, value):
		pass
	def pathPoint(self, x):
		return (int(round(x[0]/Path.spacing) * Path.spacing), int(round(x[1]/Path.spacing) * Path.spacing))
	def posAddend(pos, index):
		if index == 0:
			return (pos[0] + Path.spacing, pos[1])
		elif index == 1:
			return (pos[0] + Path.spacing, pos[1] + Path.spacing)
		elif index == 2:
			return (pos[0], pos[1] + Path.spacing)
		elif index == 3:
			return (pos[0] - Path.spacing, pos[1] + Path.spacing)
		elif index == 4:
			return (pos[0] - Path.spacing, pos[1])
		elif index == 5:
			return (pos[0] - Path.spacing, pos[1] - Path.spacing)
		elif index == 6:
			return (pos[0], pos[1] - Path.spacing)
		elif index == 7:
			return (pos[0] + Path.spacing, pos[1] - Path.spacing)
	def runBfs(self):
		pass
	def step(self):
		pass
	def draw(self):
		for x in self.graph:
			for y in x:
				pygame.draw.circle(win, (0,0,0), point2world(y), 2)
		for point in self.wormPoints:
			pygame.draw.circle(win, (255,255,255), point2world(point), 2)
		pygame.draw.circle(win, (255,255,255), point2world(self.graph[2][3]), 2)

def fireFusrodah(start, direction):#########EXPERIMENTAL
	# layersCircles[0].append(((0,0,0), start + direction * 40, 40))
	# layersCircles[0].append(((0,0,0), start + direction * 80, 26))
	# layersCircles[0].append(((0,0,0), start + direction * 110, 10))
	
	circles = [(start + direction * 40, 40), (start + direction * 80, 26), (start + direction * 110, 10)]
	tagged = []
	for circle in circles:
		for worm in PhysObj._reg:
			if worm == objectUnderControl:
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
		self.ignore = [objectUnderControl]
	def secondaryStep(self):
		for worm in PhysObj._worms:
			if worm in self.ignore:
				continue
			if dist(self.pos, worm.pos) < worm.radius + 1:
				self.worms.append(worm)
				worm.damage(20 + self.vel.getMag()*1.5)
				self.ignore.append(worm)
		for worm in self.worms:
			worm.pos = vectorCopy(self.pos)
			worm.vel *= 0
		for target in ShootingTarget._reg:
			if dist(self.pos + normalize(self.vel) * 8, target.pos) < target.radius + 1:
				self.boomAffected = False
				target.explode()
				return
					
	def deathResponse(self):
		self.pos += self.vel
		point = self.pos - normalize(self.vel) * 30
		pygame.draw.line(gameMap, GRD, self.pos, point, self.radius)
		pygame.draw.polygon(gameMap, GRD, [self.pos + rotateVector(i, self.vel.getAngle()) for i in self.triangle])
		
		pygame.draw.line(ground, self.color, self.pos, point, self.radius)
		pygame.draw.polygon(ground, (230,235,240), [self.pos + rotateVector(i, self.vel.getAngle()) for i in self.triangle])
		
		if len(self.worms) > 0:
			stain(self.pos, imageBlood, imageBlood.get_size(), False)
		if len(self.worms) > 1:
			Commentator.que.append((objectUnderControl.nameStr, ("", " the impaler!"), objectUnderControl.team.color))
	def draw(self):
		point = self.pos - normalize(self.vel) * 30
		pygame.draw.line(win, self.color, point2world(self.pos), point2world(point), self.radius)
		pygame.draw.polygon(win, (230,235,240), [point2world(self.pos + rotateVector(i, self.vel.getAngle())) for i in self.triangle])

class SnailShell(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 1
		self.bounceBeforeDeath = 1
		self.damp = 0.2
		self.wormCollider = True
		self.extraCollider = True
		self.clockwise = objectUnderControl.facing
		self.timer = 0
		self.surf = pygame.Surface((6,6), pygame.SRCALPHA)
		self.surf.blit(imageSnail, (0,0))
	def collisionRespone(self, ppos):
		finalPos = vectorCopy(self.pos)
		finalAnchor = None

		for t in range(50):
			testPos = self.pos + normalize(self.vel) * t
			testPos.integer()
			if mapGetAt(testPos) == GRD:
				finalAnchor = testPos
				break
			else:
				finalPos = testPos

		if not finalAnchor:
			print("snail error")
			return

		global camTrack
		camTrack = Snail(finalPos, finalAnchor, self.clockwise)
	def draw(self):
		self.timer += 1
		
		win.blit(pygame.transform.rotate(self.surf, (self.timer % 4) * 90), point2world(self.pos - Vector(3,3)))
		
class Snail:
	around = [Vector(1,0), Vector(1,-1), Vector(0,-1), Vector(-1,-1), Vector(-1,0), Vector(-1,1), Vector(0,1), Vector(1,1)]
	def __init__(self, pos, anchor, clockwise=RIGHT):
		nonPhys.append(self)
		self.pos = pos
		self.pos.integer()
		self.clockwise = clockwise
		self.anchor = anchor
		self.life = 0
		self.surf = pygame.Surface((6,6), pygame.SRCALPHA)
		self.surf.blit(imageSnail, (0,0), ((6,0),(6,6)))
		if self.clockwise == LEFT:
			self.surf = pygame.transform.flip(self.surf, True, False)
	def climb(self):
		while True:
			revolvment = self.pos - self.anchor
			index = Snail.around.index(revolvment)
			candidate = self.anchor + Snail.around[(index + self.clockwise * -1) % 8]
			if mapGetAt(candidate) == GRD:
				self.anchor = candidate
			else:
				self.pos = candidate
				break
	def step(self):
		self.life += 1
		for i in range(3):
				self.climb()
		for worm in PhysObj._worms:
			if dist(self.pos, worm.pos) < 3 + worm.radius:
				nonPhys.remove(self)
				boom(self.pos, 30)
				return
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		angle = Snail.around.index(self.anchor - self.pos)//2 * 90 + (90 if self.clockwise == LEFT else 180)
		win.blit(pygame.transform.rotate(self.surf, angle) , point2world(self.pos - Vector(3,3)))

class Bubble:
	cought = []
	# to do: dont pick up fire and debrie, portal 
	def __init__(self, pos, direction, energy):
		nonPhys.append(self)
		self.pos = vectorCopy(pos)
		self.acc = Vector()
		self.vel = Vector(direction[0], direction[1]).rotate(uniform(-0.1, 0.1)) * energy * 5
		self.radius = 1
		self.grow = randint(7, 13)
		self.color = (220,220,220)
		self.catch = None
	def applyForce(self):
		self.acc.y -= globalGravity * 0.3
		self.acc.x += wind * 0.1 * windMult * 0.5
	def step(self):
		gameDistable()
		self.applyForce()
		self.vel += self.acc
		self.pos += self.vel
		self.vel.x *= 0.99
		self.acc *= 0
		
		if self.radius != self.grow and timeOverall % 5 == 0:
			self.radius += 1
			
		if not self.catch:
			for worm in PhysObj._reg:
				if worm == objectUnderControl or worm in Bubble.cought or worm in Portal._reg or worm in Debrie._debries:
					continue
				if dist(worm.pos, self.pos) < worm.radius + self.radius:
					self.catch = worm
					Bubble.cought.append(self.catch)
					global camTrack
					camTrack = self
		else:
			self.catch.pos = self.pos
			self.catch.vel *= 0
		if mapClosed and (self.pos.x - self.radius <= 0 or self.pos.x + self.radius >= mapWidth - Water.level):
			self.burst()
		if self.pos.y < 0 and (mapGetAt((self.pos.x + self.radius, 0)) == GRD or mapGetAt((self.pos.x - self.radius, 0)) == GRD):
			self.burst()
		if self.pos.y < -50:
			self.burst()
		if self.pos.y - self.radius <= 0 and mapGetAt((self.pos.x, 0)) == GRD:
			self.burst()
		if randint(0, 300) == 1:
			if mapGetAt(self.pos) != GRD:
				self.burst()
	def burst(self):
		if self.catch:
			self.catch.vel = self.vel * 0.6
			global camTrack
			if self == camTrack:
				camTrack = self.catch
		self.catch = None
		pygame.draw.circle(gameMap, SKY, self.pos, self.radius)
		pygame.draw.circle(ground, SKY, self.pos, self.radius)
		if self in nonPhys:
			nonPhys.remove(self)
		for i in range(min(int(self.radius), 8)):
			d = Debrie(self.pos, self.radius/5, [self.color], 1)
			d.radius = 1
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		pygame.gfxdraw.circle(win, *point2world(self.pos), self.radius, self.color)

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
			pygame.draw.circle(gameMap, SKY, self.pos + Vector(0, 1), self.radius + 2)
			pygame.draw.circle(ground, SKY, self.pos + Vector(0, 1), self.radius + 2)
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
					worm.damage(randint(0,3))
					self.damageCooldown = 15
		self.inGround = False
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
		self.bottle = [(1,2), (1,6), (-1,6), (-1,2), (-3,-2), (3,-2)]
		self.angle = 0
	def secondaryStep(self):
		self.angle += self.vel.x*4
	def deathResponse(self):
		boom(self.pos, 10)
		for i in range(40):
			s = Acid(self.pos, Vector(cos(2*pi*i/40), sin(2*pi*i/40))*uniform(1.3,2))
	def draw(self):
		poly = [point2world(self.pos + rotateVector(i, radians(self.angle))) for i in self.bottle]
		pygame.draw.polygon(win, self.color, poly)

class Seeker:#########EXPERIMENTAL
	def __init__(self, pos, direction, energy):
		self.initialize(pos, direction, energy)
		self.timer = 15 * fps
		self.triangle = [(0,-2), (0,2), (7,0)]
		self.target = HomingMissile.Target
	def initialize(self, pos, direction, energy):
		nonPhys.append(self)
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
		getForce = self.seek(self.target)
		avoidForce = Vector()
		distance = dist(self.pos, self.target)
		if distance > 30:
			self.avoid = []
			visibility = int(0.1 * distance + 10)
			for i in range(20):
				direction = vectorFromAngle((i / 20) * 2 * pi)
				for j in range(visibility):
					testPos = self.pos + direction * j
					if mapGetAt(testPos) == GRD:
						self.avoid.append(testPos)
		else:
			if mapGetAt(self.pos) == GRD:
				self.hitResponse()
				return
			
		if distance < 8:
			self.hitResponse()
			return
			
		for i in self.avoid:
			# if dist(self.pos, i) < 50:
			avoidForce += self.flee(i)
		
		force = avoidForce + getForce
		self.applyForce(force)
		
		self.vel += self.acc
		self.vel.limit(self.maxSpeed)
		
		ppos = self.pos + self.vel
		while mapGetAt(ppos) == GRD:
			self.vel *= -1
			self.vel.rotate(uniform(-0.5,0.5))
			ppos = self.pos + self.vel
		
		self.pos = ppos
		self.secondaryStep()
	def hitResponse(self):
		self.deathResponse()
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2, randint(5,8), 30, 3)
	def deathResponse(self):
		boom(self.pos, 30)
		nonPhys.remove(self)
		HomingMissile.showTarget = False
	def applyForce(self, force):
		force.limit(self.maxForce)
		self.acc = vectorCopy(force)
	def flee(self, target):
		return self.seek(target) * -1
	def seek(self, target, arrival=False):
		force = tup2vec(target) - self.pos
		desiredSpeed = self.maxSpeed
		if arrival:
			slowRadius = 50
			distance = force.getMag()
			if (distance < slowRadius):
				desiredSpeed = smap(distance, 0, slowRadius, 0, self.maxSpeed)
				force.setMag(desiredSpeed)
		force.setMag(desiredSpeed)
		force -= self.vel
		force.limit(self.maxForce)
		return force
	def draw(self):
		# for i in self.avoid:
			# pygame.draw.circle(win, (0,0,0), point2world(i), 6)
		shape = []
		for i in self.triangle:
			shape.append(point2world(self.pos + tup2vec(i).rotate(self.vel.getAngle())))
		pygame.draw.polygon(win, self.color, shape)

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
		Seagull._reg.remove(self)
		nonPhys.remove(self)
		self.chum.dead = True
	def secondaryStep(self):
		self.target = self.chum.pos
	def draw(self):
		global timeOverall
		dir = self.vel.x > 0
		width = 16
		height = 13
		frame = timeOverall//2 % 3
		win.blit(pygame.transform.flip(imageSeagull, dir, False), point2world(self.pos - Vector(width//2, height//2)), ((frame*width, 0), (width, height)) )

class Covid19(Seeker):
	def __init__(self, pos, direction, energy):
		self.initialize(pos, direction, energy)
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
			if worm in currentTeam.worms or worm in self.bitten or worm in self.unreachable:
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
		global timeOverall
		width = 16
		height = 11
		frame = timeOverall//2 % 5
		win.blit(imageBat, point2world(self.pos - Vector(width//2, height//2)), ((frame*width, 0), (width, height)))

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
			gameMap.set_at(self.stick.integer(), GRD)
	def deathResponse(self):
		Chum._chums.remove(self)
		if self.stick:
			gameMap.set_at(self.stick.integer(), SKY)
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
			if mapGetAt(self.stick) != GRD:
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
		global holdArtifact
		holdArtifact = False
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
			PhysObj._reg.remove(self)
			self.returnToWorm()
		
		# electrocute
		self.worms = []
		for worm in PhysObj._worms:
			if worm in currentTeam.worms:
				continue
			if dist(self.pos, worm.pos) < 100:
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
		surf = pygame.transform.rotate(imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirReturn:
	def __init__(self, pos, angle):
		nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.acc = Vector()
		self.vel = Vector()
		self.angle = angle
		global camTrack
		camTrack = self
	def step(self):
		self.acc = objectUnderControl.pos - self.pos
		self.acc.normalize()
		self.acc *= 0.3
		
		self.vel += self.acc
		self.vel.limit(10)
		self.pos += self.vel
		
		self.angle += (0 - self.angle) * 0.1
		gameDistable()
		if dist(self.pos, objectUnderControl.pos) < objectUnderControl.radius * 2:
			nonPhys.remove(self)
			global holdArtifact
			holdArtifact = True
	def draw(self):
		surf = pygame.transform.rotate(imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class Mjolnir(PhysObj):
	def __init__(self):
		self.initialize()
		self.pos = Vector(randint(20, mapWidth - 20), -50)
		self.vel = Vector(randint(-2,2), 0)
		self.radius = 3
		self.damp = 0.2
		self.angle = 0
		global camTrack
		camTrack = self
		commentator.que.append(("", ("a gift from the gods", ""), HUDColor))
	def secondaryStep(self):
		if self.vel.getMag() > 1:
			self.rotating = True
		else:
			self.rotating = False
		if self.rotating:
			self.angle = -degrees(self.vel.getAngle()) - 90
		# pick up
		if dist(objectUnderControl.pos, self.pos) < self.radius + objectUnderControl.radius + 5 and not objectUnderControl.health <= 0:
			PhysObj._reg.remove(self)
			commentator.que.append((objectUnderControl.nameStr, ("", " is worthy to wield mjolnir!"), currentTeam.color))
			currentTeam.artifacts.append(MJOLNIR)
			for w in weaponMan.artifactWeapons(MJOLNIR):
				currentTeam.ammo(w[0], -1, True)
			del self
			return
	def removeFromGame(self):
		# print("mjolnir gone")
		if self in PhysObj._reg:
			PhysObj._reg.remove(self)
		worldArtifacts.append(MJOLNIR)
	def collisionRespone(self, ppos):
		vel = self.vel.getMag()
		# print(vel, vel * 4)
		if vel > 4:
			boom(self.pos, max(20, 2 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	def draw(self):
		surf = pygame.transform.rotate(imageMjolnir, self.angle)
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
		global holdArtifact
		holdArtifact = False
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
			
		objectUnderControl.pos = vectorCopy(self.pos)
		objectUnderControl.vel = Vector()
	def collisionRespone(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= mapWidth or testPos.y >= mapHeight - Water.level or testPos.x < 0:
				if mapClosed:
					response += ppos - testPos
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if gameMap.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		
		self.removeFromGame()
		response.normalize()
		pos = self.pos + response * (objectUnderControl.radius + 2)
		objectUnderControl.pos = pos
		
	def removeFromGame(self):
		PhysObj._reg.remove(self)
		MjolnirFly.flying = False
		global holdArtifact
		holdArtifact = True
	def draw(self):
		surf = pygame.transform.rotate(imageMjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirStrike:
	def __init__(self):
		self.pos = objectUnderControl.pos
		nonPhys.append(self)
		global holdArtifact
		holdArtifact = False
		self.stage = 0
		self.timer = 0
		self.angle = 0
		self.worms = []
		self.facing = objectUnderControl.facing
		objectUnderControl.boomAffected = False
		self.radius = 0
	def step(self):
		self.pos = objectUnderControl.pos
		self.facing = objectUnderControl.facing
		if self.stage == 0:
			self.angle += 1
			if self.timer >= fps * 4:
				self.stage = 1
				self.timer = 0
			# electrocute:
			self.worms = []
			for worm in PhysObj._worms:
				if worm in currentTeam.worms:
					continue
				if self.pos.x - 60 < worm.pos.x and worm.pos.x < self.pos.x + 60 and worm.pos.y > self.pos.y:
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
				nonPhys.remove(self)
				objectUnderControl.boomAffected = True
		self.timer += 1
		gameDistable()
	def draw(self):
		surf = pygame.transform.rotate(imageMjolnir, self.angle)
		surf = pygame.transform.flip(surf, self.facing == LEFT, False)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2 + Vector(0, -5)))
		drawLightning(Camera(Vector(self.pos.x, 0)), self)
		for worm in self.worms:
			drawLightning(Camera(Vector(self.pos.x, randint(0, int(self.pos.y)))), worm)

################################################################################ Weapons setup

class WeaponManager:
	def __init__(self):
		self.weapons = []
		self.weapons.append(["missile", CHARGABLE, -1, MISSILES, False, 0])
		self.weapons.append(["gravity missile", CHARGABLE, 5, MISSILES, False, 0])
		self.weapons.append(["bunker buster", CHARGABLE, 2, MISSILES, False, 0])
		self.weapons.append(["homing missile", CHARGABLE, 2, MISSILES, False, 0])
		self.weapons.append(["seeker", CHARGABLE, 1, MISSILES, False, 0])
		self.weapons.append(["grenade", CHARGABLE, 5, GRENADES, True, 0])
		self.weapons.append(["mortar", CHARGABLE, 3, GRENADES, True, 0])
		self.weapons.append(["sticky bomb", CHARGABLE, 3, GRENADES, True, 0])
		self.weapons.append(["gas grenade", CHARGABLE, 5, GRENADES, True, 0])
		self.weapons.append(["electric grenade", CHARGABLE, 3, GRENADES, True, 0])
		self.weapons.append(["raon launcher", CHARGABLE, 2, GRENADES, False, 0])
		self.weapons.append(["distorter", CHARGABLE, 0, GRENADES, True, 0])
		self.weapons.append(["shotgun", GUN, 5, GUNS, False, 0])
		self.weapons.append(["long bow", GUN, 3, GUNS, False, 0])
		self.weapons.append(["minigun", GUN, 5, GUNS, False, 0])
		self.weapons.append(["gamma gun", GUN, 3, GUNS, False, 0])
		self.weapons.append(["spear", CHARGABLE, 2, GUNS, False, 0])
		self.weapons.append(["laser gun", GUN, 3, GUNS, False, 0])
		self.weapons.append(["portal gun", GUN, 0, GUNS, False, 0])
		self.weapons.append(["bubble gun", GUN, 1, GUNS, False, 2])
		self.weapons.append(["petrol bomb", CHARGABLE, 5, FIREY, False, 0])
		self.weapons.append(["flame thrower", PUTABLE, 5, FIREY, False, 0])
		self.weapons.append(["mine", PUTABLE, 5, GRENADES, False, 0])
		self.weapons.append(["TNT", PUTABLE, 1, GRENADES, False, 0])
		self.weapons.append(["covid 19", PUTABLE, 0, GRENADES, False, 0])
		self.weapons.append(["sheep", PUTABLE, 1, GRENADES, False, 0])
		self.weapons.append(["snail", CHARGABLE, 2, GRENADES, False, 0])
		self.weapons.append(["baseball", PUTABLE, 3, MISC, False, 0])
		self.weapons.append(["girder", CLICKABLE, -1, MISC, False, 0])
		self.weapons.append(["rope", PUTABLE, 3, MISC, False, 0])
		self.weapons.append(["parachute", PUTABLE, 3, MISC, False, 0])
		self.weapons.append(["venus fly trap", CHARGABLE, 1, MISC, False, 0])
		self.weapons.append(["sentry turret", PUTABLE, 0, MISC, False, 0])
		self.weapons.append(["ender pearl", CHARGABLE, 0, MISC, False, 0])
		self.weapons.append(["fus ro duh", PUTABLE, 0, MISC, False, 0])
		self.weapons.append(["acid bottle", CHARGABLE, 1, MISC, False, 0])
		self.weapons.append(["artillery assist", CHARGABLE, 1, AIRSTRIKE, False, 0])
		self.weapons.append(["chum bucket", CHARGABLE, 1, AIRSTRIKE, False, 0])
		self.weapons.append(["airstrike", CLICKABLE, 1, AIRSTRIKE, False, 8])
		self.weapons.append(["napalm strike", CLICKABLE, 1, AIRSTRIKE, False, 8])
		self.weapons.append(["mine strike", CLICKABLE, 0, AIRSTRIKE, False, 1])
		self.weapons.append(["holy grenade", CHARGABLE, 0, LEGENDARY, True, 1])
		self.weapons.append(["banana", CHARGABLE, 0, LEGENDARY, True, 1])
		self.weapons.append(["earthquake", PUTABLE, 0, LEGENDARY, False, 1])
		self.weapons.append(["gemino mine", CHARGABLE, 0, LEGENDARY, False, 1])
		self.weapons.append(["bee hive", CHARGABLE, 0, LEGENDARY, False, 1])
		self.weapons.append(["vortex grenade", CHARGABLE, 0, LEGENDARY, True, 1])
		self.weapons.append(["chilli pepper", CHARGABLE, 0, LEGENDARY, False, 1])
		self.weapons.append(["raging bull", PUTABLE, 0, LEGENDARY, False, 1])
		self.weapons.append(["electro boom", CHARGABLE, 0, LEGENDARY, True, 1])
		self.weapons.append(["pokeball", CHARGABLE, 0, LEGENDARY, True, 1])
		self.weapons.append(["green shell", PUTABLE, 0, LEGENDARY, False, 1])
		self.weapons.append(["guided missile", PUTABLE, 0, LEGENDARY, False, 1])
		
		self.weaponCount = len(self.weapons)
		
		self.weapons.append(["moon gravity", UTILITY, 0, WHITE, False, 0])
		self.weapons.append(["double damage", UTILITY, 0, WHITE, False, 0])
		self.weapons.append(["aim aid", UTILITY, 0, WHITE, False, 0])
		self.weapons.append(["teleport", CLICKABLE, 0, WHITE, False, 0])
		self.weapons.append(["switch worms", UTILITY, 0, WHITE, False, 0])
		self.weapons.append(["time travel", UTILITY, 0, WHITE, False, 0])
		self.weapons.append(["jet pack", UTILITY, 0, WHITE, False, 0])
		self.weapons.append(["flare", CHARGABLE, 0, WHITE, False, 0])
		
		self.utilityCount = len(self.weapons) - self.weaponCount
		
		self.weapons.append(["mjolnir strike", PUTABLE, 0, LEGENDARY, False, 0, MJOLNIR])
		self.weapons.append(["mjolnir throw", CHARGABLE, 0, LEGENDARY, False, 0, MJOLNIR])
		self.weapons.append(["fly", CHARGABLE, 0, LEGENDARY, False, 0, MJOLNIR])
		
		self.artifactCount = len(self.weapons) - self.weaponCount - self.utilityCount

		self.weaponDict = {}
		self.basicSet = []
		for i, w in enumerate(self.weapons):
			self.weaponDict[w[0]] = i
			self.weaponDict[i] = w[0]
			if not unlimitedMode: self.basicSet.append(w[2])
			else: self.basicSet.append(-1)
			
		self.currentWeapon = self.weapons[0][0]
		self.surf = myfont.render(self.currentWeapon, False, HUDColor)
	def getStyle(self, string):
		return self.weapons[self.weaponDict[string]][1]
	def getCurrentStyle(self):
		return self.getStyle(self.currentWeapon)
	def getFused(self, string):
		return self.weapons[self.weaponDict[string]][4]
	def getBackColor(self, string):
		return self.weapons[self.weaponDict[string]][3]
	def getCategory(self, string):
		index = self.weaponDict[string]
		if index < self.weaponCount:
			return WEAPONS
		elif index < self.weaponCount + self.utilityCount:
			return UTILITIES
		else:
			return ARTIFACTS
	def switchWeapon(self, string):
		self.currentWeapon = string
		self.renderWeaponCount()
	def artifactWeapons(self, artifact):
		moves = []
		for w in self.weapons[self.weaponCount + self.utilityCount:]:
			if w[6] == artifact:
				moves.append(w)
		return moves
	def currentArtifact(self):
		if self.getCategory(self.currentWeapon) == ARTIFACTS:
			return self.weapons[self.currentIndex()][6]
	def currentIndex(self):
		return self.weaponDict[self.currentWeapon]
	def currentActive(self):
		return self.weapons[self.currentIndex()][5] != 0
	def renderWeaponCount(self):
		color = HUDColor
		# if no ammo in current team
		ammo = currentTeam.ammo(weaponMan.currentWeapon)
		if ammo == 0 or self.currentActive() or inUsedList(self.currentWeapon):
			color = GREY
		weaponStr = self.currentWeapon

		# special addings
		if self.currentWeapon == "bunker buster":
			weaponStr += " (drill)" if BunkerBuster.mode else " (rocket)"
		
		# add quantity
		if ammo != -1:
			weaponStr += " " + str(ammo)
			
		# add fuse
		if self.getFused(self.currentWeapon):
			weaponStr += "  delay: " + str(fuseTime//fps)
			
		self.surf = myfont.render(weaponStr, False, color)
	def updateDelay(self):
		for w in self.weapons:
			if not w[5] == 0:
				w[5] -= 1

weaponMan = WeaponManager()

def fire(weapon = None):
	global decrease, shotCount, nextState, state, camTrack, fireWeapon, energyLevel, energising, timeTravelFire
	if not weapon:
		weapon = weaponMan.currentWeapon
	decrease = True
	if objectUnderControl:
		weaponOrigin = vectorCopy(objectUnderControl.pos)
		weaponDir = vectorFromAngle(objectUnderControl.shootAngle)
		energy = energyLevel
		
	if timeTravelFire:
		decrease = False
		weaponOrigin = timeTravelList["weaponOrigin"]
		energy = timeTravelList["energy"]
		weaponDir = timeTravelList["weaponDir"]
	
	avail = True
	w = None
	if weapon == "missile":
		w = Missile(weaponOrigin, weaponDir, energy)
	elif weapon == "grenade":
		w = Grenade(weaponOrigin, weaponDir, energy)
	elif weapon == "mortar":
		w = Mortar(weaponOrigin, weaponDir, energy)
	elif weapon == "petrol bomb":
		w = PetrolBomb(weaponOrigin, weaponDir, energy)
	elif weapon == "TNT":
		w = TNT(weaponOrigin)
		w.vel.x = objectUnderControl.facing * 0.5
		w.vel.y = -0.8
	elif weapon == "shotgun":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 3 # three shots
		fireShotgun(weaponOrigin, weaponDir) # fire
		shotCount -= 1
		if shotCount > 0:
			nextState = FIRE_MULTIPLE
		if shotCount == 0:
			decrease = True
			nextState = PLAYER_CONTROL_2
	elif weapon == "flame thrower":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 70
		fireFlameThrower(weaponOrigin, weaponDir)
		if not shotCount == 0:
			shotCount -= 1
			nextState = FIRE_MULTIPLE
		else:
			nextState = PLAYER_CONTROL_2
			decrease = True
	elif weapon == "sticky bomb":
		w = StickyBomb(weaponOrigin, weaponDir, energy)
	elif weapon == "minigun":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 20
			if randint(0,50) == 1 or megaTrigger:
				shotCount = 60
		
		fireMiniGun(weaponOrigin, weaponDir)
		if not shotCount == 0:
			shotCount -= 1
			nextState = FIRE_MULTIPLE
		else:
			nextState = PLAYER_CONTROL_2
			decrease = True
	elif weapon == "mine":
		w = Mine(weaponOrigin, 70)
		w.vel.x = objectUnderControl.facing * 0.5
	elif weapon == "baseball":
		fireBaseball(weaponOrigin, weaponDir)
	elif weapon == "gas grenade":
		w = GasGrenade(weaponOrigin, weaponDir, energy)
	elif weapon == "gravity missile":
		w = GravityMissile(weaponOrigin, weaponDir, energy)
	elif weapon == "gamma gun":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 2 # two shots
		fireGammaGun(weaponOrigin, weaponDir) # fire
		shotCount -= 1
		if shotCount > 0:
			nextState = FIRE_MULTIPLE
		if shotCount == 0:
			decrease = True
			nextState = PLAYER_CONTROL_2
	elif weapon == "holy grenade":
		w = HolyGrenade(weaponOrigin, weaponDir, energy)
	elif weapon == "banana":
		w = Banana(weaponOrigin, weaponDir, energy)
	elif weapon == "earthquake":
		Earthquake()
	elif weapon == "gemino mine":
		w = Gemino(weaponOrigin, weaponDir, energy)
	elif weapon == "venus fly trap":
		w = PlantBomb(weaponOrigin, weaponDir, energy)
	elif weapon == "sentry turret":
		w = SentryGun(weaponOrigin, currentTeam.color)
		w.pos.y -= objectUnderControl.radius + w.radius
	elif weapon == "bee hive":
		w = BeeHive(weaponOrigin, weaponDir, energy)
	elif weapon == "bunker buster":
		w = BunkerBuster(weaponOrigin, weaponDir, energy)
		avail = False
	elif weapon == "electric grenade":
		w = ElectricGrenade(weaponOrigin, weaponDir, energy)
	elif weapon == "homing missile":
		w = HomingMissile(weaponOrigin, weaponDir, energy)
	elif weapon == "vortex grenade":
		w = VortexGrenade(weaponOrigin, weaponDir, energy)
	elif weapon == "chilli pepper":
		w = ChilliPepper(weaponOrigin, weaponDir, energy)
	elif weapon == "covid 19":
		w = Covid19(weaponOrigin)
		for worm in objectUnderControl.team.worms:
			w.bitten.append(worm)
	elif weapon == "artillery assist":
		w = Artillery(weaponOrigin, weaponDir, energy)
	elif weapon == "long bow":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 3 # three shots
		w = LongBow(weaponOrigin + weaponDir * 5, weaponDir, LongBow._sleep) # fire
		w.ignore = objectUnderControl
		shotCount -= 1
		if shotCount > 0:
			nextState = FIRE_MULTIPLE
		if shotCount == 0:
			decrease = True
			nextState = PLAYER_CONTROL_2
		avail = False
	elif weapon == "sheep":
		w = Sheep(weaponOrigin + Vector(0,-5))
		w.facing = objectUnderControl.facing
	elif weapon == "rope":
		angle = weaponDir.getAngle()
		if angle > 0:
			decrease = False
		else:
			decrease = False
			shootRope(weaponOrigin, weaponDir)
		nextState = PLAYER_CONTROL_1
	elif weapon == "raging bull":
		w = Bull(weaponOrigin + Vector(0,-5))
		w.facing = objectUnderControl.facing
		w.ignore.append(objectUnderControl)
	elif weapon == "electro boom":
		w = ElectroBoom(weaponOrigin, weaponDir, energy)
	elif weapon == "portal gun":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 2
		firePortal(weaponOrigin, weaponDir)
		shotCount -= 1
		if shotCount > 0:
			nextState = FIRE_MULTIPLE
		if shotCount == 0:
			decrease = True
			nextState = PLAYER_CONTROL_1
	elif weapon == "parachute":
		if objectUnderControl.parachuting:
			objectUnderControl.toggleParachute()
			decrease = False
		else:
			if objectUnderControl.vel.y > 1:
				objectUnderControl.toggleParachute()
			else:
				decrease = False
		nextState = PLAYER_CONTROL_1
	elif weapon == "pokeball":
		w = PokeBall(weaponOrigin, weaponDir, energy)
	elif weapon == "green shell":
		w = GreenShell(weaponOrigin + Vector(0,-5))
		w.facing = objectUnderControl.facing
		w.ignore.append(objectUnderControl)
	elif weapon == "laser gun":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 70
		fireLaser(weaponOrigin, weaponDir)
		if not shotCount == 0:
			shotCount -= 1
			nextState = FIRE_MULTIPLE
		else:
			nextState = PLAYER_CONTROL_2
			decrease = True
	elif weapon == "guided missile":
		w = GuidedMissile(weaponOrigin + Vector(0,-5))
		nextState = WAIT_STABLE
	elif weapon == "flare":
		w = Flare(weaponOrigin, weaponDir, energy)
		nextState = PLAYER_CONTROL_1
	elif weapon == "ender pearl":
		w = EndPearl(weaponOrigin, weaponDir, energy)
		nextState = PLAYER_CONTROL_1
	elif weapon == "raon launcher":
		w = Raon(weaponOrigin, weaponDir, energy * 0.95)
		w = Raon(weaponOrigin, weaponDir, energy * 1.05)
		if randint(0, 10) == 0 or megaTrigger:
			w = Raon(weaponOrigin, weaponDir, energy * 1.08)
			w = Raon(weaponOrigin, weaponDir, energy * 0.92)
	elif weapon == "snail":
		w = SnailShell(weaponOrigin, weaponDir, energy)
	elif weapon == "fus ro duh":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 3 # three shots
		fireFusrodah(weaponOrigin, weaponDir) # fire
		shotCount -= 1
		if shotCount > 0:
			nextState = FIRE_MULTIPLE
		if shotCount == 0:
			decrease = True
			nextState = PLAYER_CONTROL_2
	elif weapon == "spear":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 2
		w = Spear(weaponOrigin, weaponDir, energy * 0.95)
		# w.ignore = objectUnderControl
		shotCount -= 1
		if shotCount > 0:
			nextState = FIRE_MULTIPLE
		if shotCount == 0:
			decrease = True
			nextState = PLAYER_CONTROL_2
		avail = False
	elif weapon == "distorter":
		w = Distorter(weaponOrigin, weaponDir, energy)
	elif weapon == "reflector":
		fireDeflectLaser(weaponOrigin, weaponDir)
		nextState = PLAYER_CONTROL_1
	elif weapon == "bubble gun":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 10
		
		u = Bubble(getClosestPosAvail(objectUnderControl), weaponDir, uniform(0.5, 0.9))
		if not shotCount == 0:
			shotCount -= 1
			nextState = FIRE_MULTIPLE
		else:
			nextState = PLAYER_CONTROL_2
			camTrack = u
			decrease = True
	elif weapon == "acid bottle":
		w = AcidBottle(weaponOrigin, weaponDir, energy)
	elif weapon == "seeker":
		w = Seeker(weaponOrigin, weaponDir, energy)
	elif weapon == "chum bucket":
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 1)
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 2)
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 3)
		Chum(weaponOrigin, weaponDir * uniform(0.8, 1.2), energy * uniform(0.8, 1.2), 1)
		w = Chum(weaponOrigin, weaponDir, energy)
	
	# artifacts
	elif weapon == "mjolnir strike":
		MjolnirStrike()
	elif weapon == "mjolnir throw":
		w = MjolnirThrow(weaponOrigin, weaponDir, energy)
	elif weapon == "fly":
		if not MjolnirFly.flying:
			w = MjolnirFly(weaponOrigin, weaponDir, energy)
		nextState = PLAYER_CONTROL_1
	
	if w and not timeTravelFire: camTrack = w	
	
	# position to available position
	if w and avail:
		availpos = getClosestPosAvail(w)
		if availpos:
			w.pos = availpos
	
	if decrease:
		if currentTeam.ammo(weapon) != -1:
			currentTeam.ammo(weapon, -1)
		weaponMan.renderWeaponCount()

	fireWeapon = False
	energyLevel = 0
	energising = False
	
	if timeTravelFire:
		timeTravelFire = False
		return
	
	state = nextState
	if state == PLAYER_CONTROL_2: timeRemaining(retreatTime)
	
	# for uselist:
	if useListMode and (state == PLAYER_CONTROL_2 or state == WAIT_STABLE):
		addToUseList(weaponMan.currentWeapon)

def fireClickable():
	global state
	decrease = True
	if len(Menu.menus) > 0 or inUsedList(weaponMan.currentWeapon):
		return
	if currentTeam.ammo(weaponMan.currentWeapon) == 0:
		return
		
	mousePosition = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
	
	if weaponMan.currentWeapon == "girder":
		girder(mousePosition)
	elif weaponMan.currentWeapon == "teleport":
		weaponMan.switchWeapon("missile")
		objectUnderControl.pos = mousePosition
		timeRemaining(retreatTime)
		state = nextState
		return
	elif weaponMan.currentWeapon == "airstrike":
		fireAirstrike(mousePosition)
	elif weaponMan.currentWeapon == "mine strike":
		fireMineStrike(mousePosition)
	elif weaponMan.currentWeapon == "napalm strike":
		fireNapalmStrike(mousePosition)
	
	if decrease and currentTeam.ammo(weaponMan.currentWeapon) != -1:
		currentTeam.ammo(weaponMan.currentWeapon, -1)
	
	if useListMode and (nextState == PLAYER_CONTROL_2 or nextState == WAIT_STABLE):
		addToUseList(weaponMan.currentWeapon)
	
	weaponMan.renderWeaponCount()
	timeRemaining(retreatTime)
	state = nextState

################################################################################ Teams
class Team:
	def __init__(self, nameList=None, color=(255,0,0), name = ""):
		if nameList:
			self.nameList = nameList
		else:
			self.nameList = []
		self.color = color
		self.weaponCounter = weaponMan.basicSet.copy()
		self.worms = []
		self.name = name
		self.damage = 0
		self.killCount = 0
		self.points = 0
		self.flagHolder = False
		self.artifacts = []
	def __len__(self):
		return len(self.worms)
	def addWorm(self, pos):
		if len(self.nameList) > 0:
			w = Worm(pos, self.nameList.pop(0), self)
			self.worms.append(w)
	def ammo(self, weapon, add=None, absolute=False):
		if add and not absolute:
			self.weaponCounter[weaponMan.weaponDict[weapon]] += add
		elif add and absolute:
			self.weaponCounter[weaponMan.weaponDict[weapon]] = add
		return self.weaponCounter[weaponMan.weaponDict[weapon]]

teams = []
# read teams from xml
for teamsData in ET.parse('wormsTeams.xml').getroot():
	newTeam = Team()
	newTeam.name = teamsData.attrib["name"]
	newTeam.color = tuple([int(i) for i in teamsData.attrib["color"][1:-1].split(",")])
	for team in teamsData:
		if team.tag == "worm":
			newTeam.nameList.append(team.attrib["name"])
	teams.append(newTeam)

totalTeams = len(teams)
currentTeam = None
teamChoser = 0
roundCounter = 0
mostDamage = (0,None)
damageThisTurn = 0
nWormsPerTeam = 0
shuffle(teams)

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
	global mostDamage, run, camTrack, nextState
	end = False
	lastTeam = None
	count = 0
	pointsGame = False
	for team in teams:
		if len(team.worms) == 0:
			count += 1
	if count == totalTeams - 1:
		# one team remains
		end = True
		for team in teams:
			if not len(team.worms) == 0:
				lastTeam = team
	if count == totalTeams:
		# no team remains
		end = True
	
	if gameMode == TARGETS and len(ShootingTarget._reg) == 0 and ShootingTarget.numTargets <= 0:
		end = True
	
	if not end:
		return False
	# game end:
	dic = {}
	winningTeam = None
		
	# win bonuse:
	if gameMode == CAPTURE_THE_FLAG:
		dic["mode"] = "CTF"
		pointsGame = True
		for team in teams:
			if team.flagHolder:
				team.points += 1 + 3 # bonus points
				print("[ctf win, team", team.name, "got 3 bonus points]")
				break
		
	elif gameMode == POINTS:
		pointsGame = True
		if lastTeam:
			lastTeam.points += 150 # bonus points
			dic["mode"] = "points"
			print("[points win, team", lastTeam.name, "got 150 bonus points]")
			
	elif gameMode == TARGETS:
		pointsGame = True
		currentTeam.points += 3 # bonus points
		dic["mode"] = "targets"
		print("[targets win, team", currentTeam.name, "got 3 bonus points]")
	
	elif gameMode == TERMINATOR:
		pointsGame = True
		if lastTeam:
			lastTeam.points += 3 # bonus points
			print("[team", lastTeam.name, "got 3 bonus points]")
		dic["mode"] = "terminator"
	
	elif gameMode == ARENA:
		pointsGame = True
		if lastTeam:
			pass
		dic["mode"] = "arena"
	
	# win points:
	if pointsGame:
		for team in teams:
			print("[ |", team.name, "got", team.points, "points! | ]")
		teamsFinals = sorted(teams, key = lambda x: x.points)
		winningTeam = teamsFinals[-1]
		print("[most points to team", winningTeam.name, "]")
		dic["points"] = str(winningTeam.points)
	# regular win:
	else:
		winningTeam = lastTeam
		print("[last team standing is", winningTeam.name, "]")
		if gameMode == DAVID_AND_GOLIATH:
			dic["mode"] = "davidVsGoliath"
	
	if end:
		print("[winning team is", winningTeam.name, "]")
		if winningTeam != None:
			print("Team", winningTeam.name, "won!")
			dic["time"] = str(timeOverall//fps)
			dic["winner"] = winningTeam.name
			if mostDamage[1]:
				dic["mostDamage"] = str(int(mostDamage[0]))
				dic["damager"] = mostDamage[1]
			addToRecord(dic)
			if len(winningTeam.worms) > 0:
				camTrack = winningTeam.worms[0]
			commentator.que.append((winningTeam.name, ("Team "," Won!"), HUDColor))
		else:
			commentator.que.append(("", ("Its a"," Tie!"), HUDColor))
			print("Tie!")
		
		nextState = WIN
		pygame.image.save(ground, "lastWormsGround.png")
	return end

def cycleWorms():
	global objectUnderControl, camTrack, currentTeam, run, nextState, roundCounter, mostDamage, damageThisTurn
	global deploying, sentring, deployPacks, switchingWorms, raoning, waterRising, roundsTillSuddenDeath

	# reset special effects:
	global globalGravity
	globalGravity = 0.2
	global damageMult
	global radiusMult
	damageMult = 0.8
	radiusMult = 1
	global aimAid, timeTravel, megaTrigger
	megaTrigger = False
	aimAid = False
	if timeTravel: timeTravelReset()
	if objectUnderControl.jetpacking: objectUnderControl.toggleJetpack()
	switchingWorms = False
	if Worm.roped:
		objectUnderControl.team.ammo("rope", -1)
		Worm.roped = False
	
	# update damage:
	if damageThisTurn > mostDamage[0]:
		mostDamage = (damageThisTurn, objectUnderControl.nameStr)	
	if damageThisTurn > int(initialHealth * 2.5):
		if damageThisTurn == 300:
			Commentator.que.append((objectUnderControl.nameStr, ("THIS IS ", "!"), objectUnderControl.team.color))
		else:
			Commentator.que.append((objectUnderControl.nameStr, choice([("awesome shot ", "!"), ("", " is on fire!"), ("", " shows no mercy")]), objectUnderControl.team.color))
	elif damageThisTurn > int(initialHealth * 1.5):
		Commentator.que.append((objectUnderControl.nameStr, choice([("good shot ", "!"), ("nicely done ","")]), objectUnderControl.team.color))
	
	currentTeam.damage += damageThisTurn
	if gameMode == POINTS:
		currentTeam.points = currentTeam.damage + 50 * currentTeam.killCount
	damageThisTurn = 0
	if checkWinners():
		return
	roundCounter += 1
	
	# shoot sentries:
	isThereTargets = False
	if len(SentryGun._sentries) > 0 and not sentring:
		for sentry in SentryGun._sentries:
			sentry.engage()
			if sentry.target:
				isThereTargets = True
		if isThereTargets:
			# shoot
			for sentry in SentryGun._sentries:
				if sentry.target:
					sentry.fire()
					camTrack = sentry
			sentring = True
			roundCounter -= 1
			nextState = WAIT_STABLE
			return

	# controlling raons:
	isTherePointing = False
	if len(Raon._raons) > 0 and not raoning:
		for raon in Raon._raons:
			if raon.state == Raon.pointing:
				isTherePointing = True
				break
		if isTherePointing:
			for raon in Raon._raons:
				moved = raon.advance()
				if moved:
					camTrack = raon
			raoning = True
			roundCounter -= 1
			nextState = WAIT_STABLE
			return
		
	# deploy pack:
	if deployPacks and roundCounter % totalTeams == 0 and not deploying:
		deploying = True
		roundCounter -= 1
		nextState = WAIT_STABLE
		Commentator.que.append(("", choice(Commentator.stringsCrt), (0,0,0)))
		for i in range(packMult):
			w = deployPack(choice([HEALTH_PACK,UTILITY_PACK, WEAPON_PACK]))
			camTrack = w
		if darkness:
			for team in teams:
				team.ammo("flare", 1)
				if team.ammo("flare") > 3:
					team.ammo("flare", -1)
		return
	
	# rise water:
	if waterRise and not waterRising:
		water.riseAll(20)
		nextState = WAIT_STABLE
		roundCounter -= 1
		waterRising = True
		return
	
	# throw artifact:
	if artifactsMode and len(worldArtifacts) > 0:
		if randint(0,10) == 0:
			artifact = choice(worldArtifacts)
			worldArtifacts.remove(artifact)
			if artifact == MJOLNIR:
				Mjolnir()
			nextState = WAIT_STABLE
			roundCounter -= 1
			return
	
	waterRising = False
	raoning = False
	deploying = False
	sentring = False
	
	if roundCounter % totalTeams == 0:
		roundsTillSuddenDeath -= 1
		if roundsTillSuddenDeath == 0:
			suddenDeath()
	
	if gameMode == CAPTURE_THE_FLAG:
		for team in teams:
			if team.flagHolder:
				team.points += 1
				break

	# update weapons delay (and targets)
	if roundCounter % totalTeams == 0:
		weaponMan.updateDelay()
	
		if gameMode == TARGETS:
			ShootingTarget.numTargets -= 1
			if ShootingTarget.numTargets == 0:
				commentator.que.append(("", ("final targets round",""), (0,0,0)))
	
	# update stuff
	Debrie._debries = []
	Bubble.cought = []
	
	HomingMissile.showTarget = False
	# change wind:
	global wind
	wind = uniform(-1,1)
	
	# flares reduction
	if darkness:
		for flare in Flare._flares:
			if not flare in PhysObj._reg:
				Flare._flares.remove(flare)
			flare.lightRadius -= 10
	
	# sick:
	for worm in PhysObj._worms:
		if not worm.sick == 0 and worm.health > 5:
			worm.damage(min(int(5/damageMult)+1, int((worm.health-5)/damageMult) +1), 2)
	
	# select next team
	index = teams.index(currentTeam)
	index = (index + 1) % totalTeams
	currentTeam = teams[index]
	while not len(currentTeam.worms) > 0:
		index = teams.index(currentTeam)
		index = (index + 1) % totalTeams
		currentTeam = teams[index]
	
	if gameMode == TERMINATOR:
		pickVictim()
	
	if gameMode == ARENA:
		Arena.arena.wormsCheck()
	
	damageThisTurn = 0
	if nextState == PLAYER_CONTROL_1:
	
		# sort worms by health for drawing purpuses
		PhysObj._reg.sort(key = lambda worm: worm.health if worm.health else 0)
		
		# actual worm switch:
		switched = False
		while not switched:
			w = currentTeam.worms.pop(0)
			currentTeam.worms.append(w)
			if w.sleep:
				w.sleep = False
				continue
			switched = True
			
		if randomCycle == 1:
			currentTeam = choice(teams)
			while not len(currentTeam.worms) > 0:
				currentTeam = choice(teams)
			w = choice(currentTeam.worms)
		if randomCycle == 2:
			w = choice(currentTeam.worms)
	
		objectUnderControl = w
		camTrack = objectUnderControl

def switchWorms():
	global objectUnderControl, camTrack
	currentWorm = currentTeam.worms.index(objectUnderControl)
	totalWorms = len(currentTeam.worms)
	currentWorm = (currentWorm + 1) % totalWorms
	objectUnderControl = currentTeam.worms[currentWorm]
	camTrack = objectUnderControl

def isGroundAround(place, radius = 5):
	for i in range(8):
		checkPos = place + Vector(radius * cos((i/4) * pi), radius * sin((i/4) * pi))
		# extra.append((checkPos.x, checkPos.y, (255,0,0), 10000))
		if checkPos.x < 0 or checkPos.x > mapWidth or checkPos.y < 0 or checkPos.y > mapHeight:
			return False
		try:
			at = (int(checkPos.x), int(checkPos.y))
			if gameMap.get_at(at) == GRD or wormCol.get_at(at) != (0,0,0) or extraCol.get_at(at) != (0,0,0):
				return True
		except IndexError:
			print("isGroundAround index error")
			
	return False

def randomPlacing(wormsPerTeam):
	for i in range(wormsPerTeam * len(teams)):
		if fortsMode:
			place = giveGoodPlace(i)
		else:
			place = giveGoodPlace()
		if diggingMatch:
			pygame.draw.circle(gameMap, SKY, place, 35)
			pygame.draw.circle(ground, SKY, place, 35)
			pygame.draw.circle(groundSec, SKY, place, 30)
		global teamChoser
		teams[teamChoser].addWorm(place.vec2tup())
		teamChoser = (teamChoser + 1) % totalTeams
		lstepper()
	global state
	state = nextState

def squareCollision(pos1, pos2, rad1, rad2):
	return True if pos1.x < pos2.x + rad2*2 and pos1.x + rad1*2 > pos2.x and pos1.y < pos2.y + rad2*2 and pos1.y + rad1*2 > pos2.y else False

################################################################################ Gui

class HealthBar:
	healthBar = None
	drawBar = True
	drawPoints = True
	width = 40
	def __init__(self):
		self.mode = 0
		self.teamHealthMod = [0] * totalTeams
		self.teamHealthAct = [0] * totalTeams
		self.maxHealth = 0
		if diggingMatch:
			HealthBar.drawBar = False

	def calculateInit(self):
		self.maxHealth = nWormsPerTeam * initialHealth
		if gameMode == DAVID_AND_GOLIATH:
			self.maxHealth = int(initialHealth/(1+0.5*(nWormsPerTeam - 1))) * nWormsPerTeam
		for i, team in enumerate(teams):
			self.teamHealthMod[i] = sum(worm.health for worm in team.worms)

	def step(self):
		for i, team in enumerate(teams):
			# calculate teamhealth
			self.teamHealthAct[i] = sum(worm.health for worm in team.worms)
			
			# animate health bar
			self.teamHealthMod[i] += (self.teamHealthAct[i] - self.teamHealthMod[i]) * 0.1
			if int(self.teamHealthMod[i]) == self.teamHealthAct[i]:
				self.teamHealthMod[i] = self.teamHealthAct[i]
	def draw(self):
		if not HealthBar.drawBar: return
		maxPoints = sum(i.points for i in teams)
		
		for i, team in enumerate(teams):
			pygame.draw.rect(win, (220,220,220), (int(winWidth - (HealthBar.width + 10)), 10 + i * 3, HealthBar.width, 2))
			
			# health:
			value = min(self.teamHealthMod[i] / self.maxHealth, 1) * HealthBar.width
			if value < 1 and value > 0:
				value = 1
			if not value <= 0:
				pygame.draw.rect(win, teams[i].color, (int(winWidth - (HealthBar.width + 10)), 10 + i * 3, int(value), 2))
			
			# points:
			if not HealthBar.drawPoints:
				continue
			if maxPoints == 0:
				continue
			value = (teams[i].points / maxPoints) * HealthBar.width
			if value < 1 and value > 0:
				value = 1
			if not value == 0:
				pygame.draw.rect(win, (220,220,220), (int(winWidth - (HealthBar.width + 10)) - 1 - int(value), int(10+i*3), int(value), 2))
			if gameMode == CAPTURE_THE_FLAG:
				if teams[i].flagHolder:
					pygame.draw.circle(win, (220,0,0), (int(winWidth - (HealthBar.width + 10)) - 1 - int(value) - 4, int(10+i*3) + 1) , 2)

class Menu:
	border = 1
	event = None
	textColor = BLACK
	TextColorInnactive = (170,170,170)
	menus = []
	def __init__(self):
		self.pos = Vector()
		self.size = Vector(100, 0)
		self.elements = []
	def updatePosX(self, pos, absolute=True):
		offset = pos
		if absolute:
			offset = pos - self.pos.x
		self.pos.x += offset
		for e in self.elements:
			e.pos.x += offset
	def updatePosY(self, pos, absolute=True):
		offset = pos
		if absolute:
			offset = pos - self.pos.y
		self.pos.y += offset
		for e in self.elements:
			e.pos.y += offset
	def step(self):
		for e in self.elements:
			e.step()
	def addButton(self, text, secText, key, bgColor, active=True):
		b = Button(text, key, bgColor)
		b.pos = self.pos + Vector(0, self.size.y)
		b.active = active
		b.secText = secText
		b.setSurf(b.text)
		self.size.y += b.size.y
		self.elements.append(b)
		return b
	def draw(self):
		pygame.draw.rect(win, BLACK, (self.pos - Vector(Menu.border, Menu.border), self.size + Vector(Menu.border * 2, Menu.border)))
		for e in self.elements:
			e.draw()

class Button:
	def __init__(self, text, key, bgColor):
		self.pos = Vector()
		self.size = Vector(100, 10)
		self.key = key
		self.text = text
		self.secText = None
		self.bgColor = bgColor
		self.active = True
		self.selected = False
		self.surf = None
		self.secSurf = None
	def setSurf(self, text):
		color = Menu.textColor if self.active else Menu.TextColorInnactive
		self.surf = myfont.render(text, False, color)
		if self.secText:
			self.secSurf = myfont.render(self.secText, False, color)
		self.size.y = self.surf.get_height() + 3 * Menu.border
	def step(self):
		if not self.active:
			return
		mousePos = (pygame.mouse.get_pos()[0]/scalingFactor, pygame.mouse.get_pos()[1]/scalingFactor)
		if mousePos[0] > self.pos[0] and mousePos[0] < self.pos[0] + self.size[0] and mousePos[1] > self.pos[1] and mousePos[1] < self.pos[1] + self.size[1]:
			self.selected = True
			Menu.event = self.key
		else:
			self.selected = False
	def draw(self):
		color = RED if self.selected else self.bgColor
		rect = (self.pos, self.size - Vector(0, 1 * Menu.border))
		pygame.draw.rect(win, color, rect)
		win.blit(self.surf, self.pos + Vector(Menu.border, Menu.border))
		if self.secSurf:
			win.blit(self.secSurf, self.pos + Vector(self.size.x - self.secSurf.get_width() - 3, Menu.border))

def clickInMenu():
	weapon = Menu.event
	Menu.menus = []
	
	if weaponMan.getCategory(weapon) == WEAPONS:
		weaponMan.switchWeapon(weapon)
		
	if weaponMan.getCategory(weapon) == UTILITIES:
		decrease = True
		if weapon == "moon gravity":
			global globalGravity
			globalGravity = 0.1
			Commentator.que.append(("", ("small step for wormanity", ""), HUDColor))
		elif weapon == "double damage":
			global damageMult, radiusMult
			damageMult += damageMult
			radiusMult *= 1.5
			Commentator.que.append(("", ("this gonna hurt", ""), HUDColor))
		elif weapon == "aim aid":
			global aimAid
			aimAid = True
			Commentator.que.append(("", ("snipe em'", ""), HUDColor))
		elif weapon == "teleport":
			weaponMan.switchWeapon(weapon)
			decrease = False
		elif weapon == "switch worms":
			global switchingWorms
			if switchingWorms:
				decrease = False
			switchingWorms = True
			Commentator.que.append(("", ("the ol' switcheroo", ""), HUDColor))
		elif weapon == "time travel":
			global timeTravel
			if not timeTravel:
				timeTravelInitiate()
			Commentator.que.append(("", ("no need for roads", ""), HUDColor))
		elif weapon == "jet pack":
			objectUnderControl.toggleJetpack()
		elif weapon == "flare":
			weaponMan.switchWeapon(weapon)
			decrease = False
		
		if decrease:
			currentTeam.ammo(weapon, -1)
	
	if weaponMan.getCategory(weapon) == ARTIFACTS:
		weaponMan.switchWeapon(weapon)

def weaponMenuInit():
	weaponsMenu = Menu()
	weaponsMenu.pos = Vector(winWidth - 100 - Menu.border, 1)
	Menu.menus.append(weaponsMenu)
	
	mode = WEAPONS
	menuUtilitiesExist = False
	menuArtifactsExist = False
	
	for i, w in enumerate(weaponMan.weapons):
		if mode == WEAPONS and i >= weaponMan.weaponCount:
			mode = UTILITIES
			utilitiesMenu = Menu()
			utilitiesMenu.pos = Vector(winWidth - 2 * 100 - 1 * Menu.border - 1, 1)
			Menu.menus.append(utilitiesMenu)
		if mode == UTILITIES and i >= weaponMan.weaponCount + weaponMan.utilityCount:
			mode = ARTIFACTS
			artifactsMenu = Menu()
			posY = 1
			if len(Menu.menus) > 1:
				posY = Menu.menus[-1].size.y + 1
			artifactsMenu.pos = Vector(winWidth - 2 * 100 - 1 * Menu.border - 1, posY)
			Menu.menus.append(artifactsMenu)
	
		if currentTeam.ammo(w[0]) != 0:
			secText = str(currentTeam.ammo(w[0])) if currentTeam.ammo(w[0]) > -1 else ""
			active = w[5] == 0
			if inUsedList(w[0]):
				active = False
		
		if currentTeam.ammo(w[0]) == 0:
			continue
	
		
		if mode == WEAPONS:
			newButton = weaponsMenu.addButton(w[0], secText, w[0], w[3], active)
		
		if mode == UTILITIES:
			newButton = utilitiesMenu.addButton(w[0], secText, w[0], w[3], active)
			menuUtilitiesExist = True
		
		if mode == ARTIFACTS:
			newButton = artifactsMenu.addButton(w[0], secText, w[0], w[3], active)
			menuArtifactsExist = True
			
	if not menuUtilitiesExist:
		Menu.menus.remove(utilitiesMenu)
	if not menuArtifactsExist:
		Menu.menus.remove(artifactsMenu)

def scrollMenu(up = True):
	menu = Menu.menus[0]
	if up: 
		menu.updatePosY((menu.elements[0].size.y + 0 * Menu.border) * 5, False)
	else:
		if menu.pos.y + menu.size.y <= winHeight:
			return
		menu.updatePosY(-(menu.elements[0].size.y + 0 * Menu.border) * 5, False)
	if menu.pos.y >= 1:
		menu.updatePosY(1, True)

waterAmp = 2
waterColor = [tuple((feelColor[0][i] + feelColor[1][i]) // 2 for i in range(3))]
waterColor.append(tuple(min(int(waterColor[0][i] * 1.5), 255) for i in range(3)))

class Water:
	level = initialWaterLevel
	quiet = 0
	rising = 1
	layersA = []
	layersB = []
	def __init__(self):
		self.points = [Vector(i * 20, 3 + waterAmp + waterAmp * (-1)**i) for i in range(-1,12)]
		self.speeds = [uniform(0.95, 1.05) for i in range(-1,11)]
		self.phase = [sin(timeOverall/(3 * self.speeds[i])) for i in range(-1,11)]
		
		self.surf = pygame.Surface((200, waterAmp * 2 + 6), pygame.SRCALPHA)
		self.state = Water.quiet
		self.amount = 0
	def getSplinePoint(self, t):
		p1 = int(t) + 1
		p2 = p1 + 1
		p3 = p2 + 1
		p0 = p1 - 1
			
		t = t - int(t)
		tt = t * t
		ttt = t * tt
		q1 = -ttt + 2 * tt - t
		q2 = 3 * ttt - 5 * tt + 2
		q3 = -3 * ttt + 4 * tt + t
		q4 = ttt - tt
		tx = (self.points[p0][0] * q1 + self.points[p1][0] * q2 + self.points[p2][0] * q3 + self.points[p3][0] * q4) /2
		ty = (self.points[p0][1] * q1 + self.points[p1][1] * q2 + self.points[p2][1] * q3 + self.points[p3][1] * q4) /2
		
		return (tx, ty)
	def rise(self, amount):
		self.amount = amount
		self.state = Water.rising
	def riseAll(self, amount):
		self.rise(amount)
	def step(self):
		self.surf.fill((0,0,0,0))
		self.points = [Vector(i * 20, 3 + waterAmp + self.phase[i % 10] * waterAmp * (-1)**i) for i in range(-1,12)]
		pygame.draw.polygon(self.surf, waterColor[0], self.points + [(200, waterAmp * 2 + 6), (0, waterAmp * 2 + 6)])
		for t in range(0,(len(self.points) - 3) * 20):
			point = self.getSplinePoint(t / 20)
			pygame.draw.circle(self.surf,  waterColor[1], (int(point[0]), int(point[1])), 1)
		
		self.phase = [sin(timeOverall/(3 * self.speeds[i])) for i in range(-1,11)]
	
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
		offset = (camPos.x)//width
		times = winWidth//width + 2
		for i in range(times):
			x = int(-camPos.x) + int(int(offset) * width + i * width)
			y =  int(mapHeight - Water.level - 3 - waterAmp - offsetY) - int(camPos.y)
			win.blit(self.surf, (x, y))
		
		pygame.draw.rect(win, waterColor[0], ((0,y + height), (winWidth, Water.level)))
	def createLayers(self):
		Water.layersA.append(Water())
		Water.layersB.append(Water())
	def stepAll(self):
		for w in Water.layersA:
			w.step()
		for w in Water.layersB:
			w.step()
	def drawLayers(self, layer):
		if layer == DOWN:
			offset = 2
			for w in Water.layersA:
				w.draw(offset)
				offset -= 10
		else:
			offset = 12
			for w in Water.layersB:
				w.draw(offset)
				offset -= 10

class Cloud:
	_reg = []
	cWidth = 170
	def __init__(self, pos):
		self._reg.append(self)
		self.pos = Vector(pos[0],pos[1])
		self.vel = Vector(0,0)
		self.acc = Vector(0,0)
		self.surf = renderCloud2()
		self.randomness = uniform(0.97, 1.02)
	def step(self):
		self.acc.x = wind
		self.vel += self.acc
		self.vel *= 0.85 * self.randomness
		self.pos += self.vel
		
		if self.pos.x > camPos.x + winWidth + 100 or self.pos.x < camPos.x - 100 - self.cWidth:
			self._reg.remove(self)
			del self
	def draw(self):
		win.blit(self.surf, point2world(self.pos))

def cloudManager():
	if mapHeight == 0:
		return
	if len(Cloud._reg) < 8 and randint(0,10) == 1:
		pos = Vector(choice([camPos.x - Cloud.cWidth - 100, camPos.x + winWidth + 100]), randint(5, mapHeight - 150))
		Cloud(pos)
	for cloud in Cloud._reg: cloud.step()

class Commentator:#(name, strings, color)
	que = []
	timer = 0 #0-wait, 1-render, 2-show
	WAIT = 0
	RENDER = 1
	SHOW = 2
	mode = 0
	textSurf = None
	name = None
	stringsDmg = [("", " is no more"), ("", " is an ex-worm"), ("", " bit the dust"), ("", " has been terminated"), ("poor ", ""), ("so long ", ""), ("", " will see you on the other side"), ("", " diededed")]
	stringsFlw = [(""," is swimming with the fishes"), ("there goes ", " again"), ("its bye bye for ", ""), ("", " has drowed"), ("", " swam like a brick"), ("", " has gone to marry a mermaid"), ("", " has divided by zero")]
	stringsCrt = [("a jewel from the heavens!", ""), ("its raining crates, halelujah!", ""), (" ","")]
	stringBaseBall = ("", " home run!")
	def step(self):
		if self.mode == Commentator.WAIT:
			if len(self.que) == 0:
				return
			else:
				self.mode = Commentator.RENDER
		elif self.mode == Commentator.RENDER:
			nameSurf = myfont.render(self.que[0][0], False, self.que[0][2])
				
			string1 = self.que[0][1][0]
			string2 = self.que[0][1][1]
			
			stringSurf1 = myfont.render(string1, False, HUDColor)
			stringSurf2 = myfont.render(string2, False, HUDColor)
			# combine strings
			self.textSurf = pygame.Surface((nameSurf.get_width() + stringSurf1.get_width() + stringSurf2.get_width(), nameSurf.get_height())).convert_alpha()
			self.textSurf.fill((0,0,0,0))
			self.textSurf.blit(stringSurf1, (0,0))
			self.textSurf.blit(nameSurf, (stringSurf1.get_width(),0))
			self.textSurf.blit(stringSurf2, (stringSurf1.get_width() + nameSurf.get_width() ,0))
			self.que.pop(0)
			self.mode = Commentator.SHOW
			self.timer = 2*fps + 1*fps/2
		elif self.mode == Commentator.SHOW:
			win.blit(self.textSurf, (int(winWidth/2 - self.textSurf.get_width()/2), 10))
			
			self.timer -= 1
			if self.timer == 0:
				self.mode = Commentator.WAIT

class Camera:
	def __init__(self, pos):
		self.pos = pos

class Toast:
	_toasts = []
	toastCount = 0
	bottom = 0
	middle = 1
	def __init__(self, surf, mode=0):
		Toast._toasts.append(self)
		self.surf = surf
		self.time = 0
		self.mode = mode
		if self.mode == Toast.bottom:
			self.anchor = Vector(winWidth/2, winHeight)
		else:
			self.anchor = Vector(winWidth//2, winHeight//2) - tup2vec(self.surf.get_size())/2
		self.pos = Vector()
		self.state = 0
		Toast.toastCount += 1
		
	def step(self):
		if self.mode == Toast.bottom:
			if self.state == 0:
				self.pos.y -= 3
				if self.pos.y < -self.surf.get_height():
					self.state = 1
			if self.state == 1:
				self.time += 1
				if self.time == fps * 3:
					self.state = 2
			if self.state == 2:
				self.pos.y += 3
				if self.pos.y > 0:
					Toast._toasts.remove(self)
					Toast.toastCount -= 1
		elif self.mode == Toast.middle:
			self.time += 1
			if self.time == fps * 3:
				Toast._toasts.remove(self)
				Toast.toastCount -= 1
			self.pos = uniform(0,2) * vectorUnitRandom()
				
	def draw(self):
		if self.mode == Toast.bottom:
			pygame.gfxdraw.box(win, (self.anchor + self.pos - Vector(1,1), tup2vec(self.surf.get_size()) + Vector(2,2)), (255,255,255,200))
		win.blit(self.surf, self.anchor + self.pos)
	def updateWinPos(self, pos):
		self.anchor[0] = pos[0]
		self.anchor[1] = pos[1]

def toastInfo():
	if gameMode < POINTS:
		return
	if Toast.toastCount > 0:
		Toast._toasts[0].time = 0
		if Toast._toasts[0].state == 2:
			Toast._toasts[0].state = 0
		return
	toastWidth = 100
	surfs = []
	for team in teams:
		name = myfont.render(team.name, False, team.color)
		points = myfont.render(str(team.points), False, HUDColor)
		surfs.append((name, points))
	surf = pygame.Surface((toastWidth, (surfs[0][0].get_height() + 3) * totalTeams), pygame.SRCALPHA)
	i = 0
	for s in surfs:
		surf.blit(s[0], (0, i))
		surf.blit(s[1], (toastWidth - s[1].get_width(), i))
		i += s[0].get_height() + 3
	Toast(surf)

class Arena:
	arena = None
	def __init__(self):
		self.size = Vector(200, 15)
		self.pos = Vector(mapWidth, mapHeight)//2 - self.size//2
	def step(self):
		pass
	def draw(self):
		pygame.draw.rect(gameMap, GRD,(self.pos, self.size))
		pygame.draw.rect(ground, (102, 102, 153), (self.pos, self.size))
	def wormsCheck(self):
		for worm in PhysObj._worms:
			checkPos = worm.pos + Vector(0, worm.radius * 2)
			addExtra(checkPos, (255,255,255), 3)
			if worm.pos.x > self.pos.x and worm.pos.x < self.pos.x + self.size.x and checkPos.y > self.pos.y and checkPos.y < self.pos.y + self.size.y:
				worm.team.points += 1

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
	startingWeapons = ["holy grenade", "gemino mine", "bee hive", "electro boom", "pokeball", "green shell", "guided missile"]
	if allowAirStrikes:
		startingWeapons.append("mine strike")
	if unlimitedMode: return
	for i in range(amount):
		for team in teams:
			effect = choice(startingWeapons)
			team.ammo(effect, 1)
			if randint(0,2) >= 1:
				effect = choice(["moon gravity", "teleport", "jet pack", "aim aid", "switch worms"])
				team.ammo(effect, 1)
			if randint(0,7) == 1:
				if randint(0,1) == 0:
					team.ammo("portal gun", 1)
				else:
					team.ammo("ender pearl", 3)

def randomWeaponsGive():
	for team in teams:
		for i, teamCount in enumerate(team.weaponCounter):
			if teamCount == -1:
				continue
			else:
				if randint(0,1) == 1:
					teamCount = randint(0,5)

def suddenDeath():
	global suddenDeathStyle
	string = "Sudden Death!"
	if len(suddenDeathStyle) == 0:
		suddenDeathStyle += [PLAGUE, TSUNAMI]
	if PLAGUE in suddenDeathStyle:
		string += " plague!"
		for worm in PhysObj._worms:
			worm.sicken()
			if not worm.health == 1:
				worm.health = worm.health // 2
	if TSUNAMI in suddenDeathStyle:
		string += " water rise!"
		global waterRise
		waterRise = True
	text = myfontbigger.render("sudden death", False, (220,0,0))
	Toast(pygame.transform.scale(text, tup2vec(text.get_size()) * 2), Toast.middle)
	
def isOnMap(vec):
	return not (vec[0] < 0 or vec[0] >= mapWidth or vec[1] < 0 or vec[1] >= mapHeight)

def cheatActive(code):
	code = code[:-1]
	if code == "gibguns":
		unlimitedMode = True
		for team in teams:
			for i, teamCount in enumerate(team.weaponCounter):
				team.weaponCounter[i] = -1
		for weapon in weaponMan.weapons:
			weapon[5] = 0
	if code == "suddendeath":
		suddenDeath()
	if code == "wind":
		global wind
		wind = uniform(-1,1)
	if code == "goodbyecruelworld":
		boom(objectUnderControl.pos, 100)
	if code == "armageddon":
		Armageddon()
	if code == "reset":
		global state, nextState
		state, nextState = RESET, RESET
	if code[0:5] == "gunme" and len(code) == 6:
		mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
		amount = int(code[5])
		for i in range(amount):
			WeaponPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
	if code[0:9] == "utilizeme" and len(code) == 10:
		mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
		amount = int(code[9])
		for i in range(amount):
			UtilityPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
	if code == "aspirin":
		mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
		HealthPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
	if code == "globalshift":
		for worm in PhysObj._worms:
			# if worm in currentTeam.worms:
				# continue
			worm.gravity = worm.gravity * -1
	if code == "gibpetrolcan":
		mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
		PetrolCan((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
	if code == "megaboom":
		global megaTrigger
		megaTrigger = True
	if code == "tsunami":
		global waterRise
		waterRise = True
		Commentator.que.append(("", ("", "water rising!"), HUDColor))
	if code == "comeflywithme":
		currentTeam.ammo("jet pack", 6)
		currentTeam.ammo("rope", 6)
		currentTeam.ammo("ender pearl", 6)
	
def gameDistable(): 
	global gameStable, gameStableCounter
	gameStable = False
	gameStableCounter = 0

killList = []
useList = []
def addToUseList(string):
	useList.append([myfont.render(string, False, HUDColor), string])
	if len(useList) > 4:
		useList.pop(0)

def addToKillList():
	"""add to kill list if points"""
	amount = 1
	if len(killList) > 0 and killList[0][1] == objectUnderControl.nameStr:
		amount += killList[0][2]
		killList.pop(0)
	string = objectUnderControl.nameStr + ": " + str(amount)
	killList.insert(0, (myfont.render(string, False, HUDColor), objectUnderControl.nameStr, amount))

def drawUseList():
	space = 0
	for i, usedWeapon in enumerate(useList):
		if i == 0:
			win.blit(usedWeapon[0], (30 + 80 * i,winHeight - 6))
		else:
			space += useList[i-1][0].get_width() + 10
			win.blit(usedWeapon[0], (30 + space, winHeight - 6))

def inUsedList(string):
	used = False
	for i in useList:
		if string == i[1]:
			used = True
			break
	return used

def pickVictim():
	global victim, terminatorHit
	terminatorHit = False
	worms = []
	for w in PhysObj._worms:
		if w in currentTeam.worms:
			continue
		worms.append(w)
	if len(worms) == 0:
		victim = None
		return
	victim = choice(worms)
	Commentator.que.append((victim.nameStr, choice([("", " is marked for death"), ("kill ", "!"), ("", " is the weakest link"), ("your target: ", "")]), victim.team.color))

def drawDirInd(pos):
	border = 20
	if not (pos[0] < camPos[0] - border/4 or pos[0] > (Vector(winWidth, winHeight) + camPos)[0] + border/4 or pos[1] < camPos[1] - border/4 or pos[1] > (Vector(winWidth, winHeight) + camPos)[1] + border/4):
		return

	cam = camPos + Vector(winWidth//2, winHeight//2)
	direction = pos - cam
	
	intersection = tup2vec(point2world((winWidth, winHeight))) + pos -  Vector(winWidth, winHeight)
	
	intersection[0] = min(max(intersection[0], border), winWidth - border)
	intersection[1] = min(max(intersection[1], border), winHeight - border)
	
	points = [Vector(0,2), Vector(0,-2), Vector(5,0)]
	angle = direction.getAngle()
	
	for point in points:
		point.rotate(angle)
	
	pygame.draw.polygon(win, (255,0,0), [intersection + i + normalize(direction) * 4 * sin(timeOverall / 5) for i in points])

lstep = 0
lstepmax = 1
def lstepper():
	global lstep
	lstep += 1
	pos = (winWidth/2 - loadingSurf.get_width()/2, winHeight/2 - loadingSurf.get_height()/2)
	width = loadingSurf.get_width()
	height = loadingSurf.get_height()
	pygame.draw.rect(win, (255,255,255), ((pos[0], pos[1] + 20), ((lstep/lstepmax)*width, height)))
	screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
	pygame.display.update()

def testerFunc():
	mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
	# m = Mjolnir()
	# m.pos = mouse
	# Covid19(mouse, Vector(), 0)
	print("worldArtifacts=", worldArtifacts)
	
################################################################################ State machine
if True:
	RESET = 0; GENERATE_TERRAIN = 1; PLACING_WORMS = 2; CHOOSE_STARTER = 3; PLAYER_CONTROL_1 = 4
	PLAYER_CONTROL_2 = 5; WAIT_STABLE = 6; FIRE_MULTIPLE = 7; WIN = 8
	state, nextState = RESET, RESET
	loadingSurf = myfontbigger.render("Simon's Worms Loading", False, WHITE)
	pauseSurf = myfontbigger.render("Game Paused", False, WHITE)
	gameStable = False; playerScrollAble = False; playerControl = False
	playerControlPlacing = False; playerShootAble = False; gameStableCounter = 0

def stateMachine():
	global state, nextState, gameStable, playerControl, playerControlPlacing, playerShootAble, playerScrollAble, currentTeam
	global objectUnderControl, camTrack, gameStableCounter, shotCount, fireWeapon, run, mapClosed, allowAirStrikes
	if state == RESET:
		gameStable = False
		playerActionComplete = False
		playerControl = False
		playerControlPlacing = False
		playerScrollAble = False
		
		nextState = GENERATE_TERRAIN
		state = nextState
	elif state == GENERATE_TERRAIN:
		playerControl = False
		playerControlPlacing = False
		playerScrollAble = False
		
		createWorld()
		currentTeam = teams[0]
		teamChoser = teams.index(currentTeam)
		# place stuff:
		if not diggingMatch:
			placeMines(randint(2,4))
		if manualPlace:
			placePetrolCan(randint(2,4))
			# place plants:
			if not diggingMatch:
				placePlants(randint(0,2))
		
		
		# check for sky opening for airstrikes
		closedSkyCounter = 0
		for i in range(100):
			if mapGetAt((randint(0, mapWidth-1), randint(0, 10))) == GRD:
				closedSkyCounter += 1
		if closedSkyCounter > 50:
			allowAirStrikes = False
			for team in teams:
				for i, w in enumerate(team.weaponCounter):
					if weaponMan.getBackColor(weaponMan.weapons[i][0]) == AIRSTRIKE:
						team.weaponCounter[i] = 0
		
		nextState = PLACING_WORMS
		state = nextState
	elif state == PLACING_WORMS: #modes
		playerControlPlacing = True #can move with mouse and place worms, but cant play them
		playerControl = False
		playerScrollAble = True
		
		# place worms:
		if not manualPlace:
			randomPlacing(wormsPerTeam)
			nextState = CHOOSE_STARTER
		if unlimitedMode:
			for weapon in weaponMan.weapons:
				weapon[5] = 0
		if nextState == CHOOSE_STARTER:
			if not manualPlace:
				placePetrolCan(randint(2,4))
				# place plants:
				if not diggingMatch:
					placePlants(randint(0,2))
			
			# targets:
			if gameMode == TARGETS:
				for i in range(ShootingTarget.numTargets):
					ShootingTarget()
			
			if diggingMatch:
				placeMines(80)
				# more digging
				for team in teams:
					team.ammo("minigun", 5)
					team.ammo("bunker buster", 3)
					team.ammo("laser gun", 3)
				mapClosed = True
				
			# give random legendary starting weapons:
			randomStartingWeapons(1)
			
			if gameMode == DAVID_AND_GOLIATH:
				global initialHealth
				for team in teams:
					length = len(team.worms)
					for i in range(length):
						if i == 0:
							team.worms[i].health = initialHealth + (length - 1) * (initialHealth//2)
							team.worms[i].healthStr = myfont.render(str(team.worms[i].health), False, team.worms[i].team.color)
						else:
							team.worms[i].health = (initialHealth//2)
							team.worms[i].healthStr = myfont.render(str(team.worms[i].health), False, team.worms[i].team.color)
				initialHealth = teams[0].worms[0].health
			if darkness:
				global HUDColor
				HUDColor = WHITE
				weaponMan.renderWeaponCount()
				for team in teams:
					team.ammo("flare", 3)
			if randomWeapons:
				randomWeaponsGive()
			if gameMode == CAPTURE_THE_FLAG:
				placeFlag()
			if gameMode == ARENA:
				Arena.arena = Arena()
			state = nextState
	elif state == CHOOSE_STARTER:
		playerControlPlacing = False
		playerControl = False
		playerScrollAble = False
		
		# choose the fisrt worm and rotate
		w = currentTeam.worms.pop(0)
		currentTeam.worms.append(w)
		
		global nWormsPerTeam
		nWormsPerTeam = 0
		for team in teams:
			if len(team) > nWormsPerTeam:
				nWormsPerTeam = len(team)
		
		# health calc:
		HealthBar.healthBar.calculateInit()
		
		if randomCycle:
			w = choice(currentTeam.worms)
		
		objectUnderControl = w
		if gameMode == TERMINATOR: pickVictim()
		camTrack = w
		timeReset()

		nextState = PLAYER_CONTROL_1
		state = nextState
	elif state == PLAYER_CONTROL_1:
		playerControlPlacing = False
		playerControl = True #can play
		playerShootAble = True
		if state == PLAYER_CONTROL_1:
			playerScrollAble = True
		else:
			playerScrollAble = False
		
		nextState = PLAYER_CONTROL_2
	elif state == PLAYER_CONTROL_2:
		playerControlPlacing = False
		playerControl = True #can play
		playerShootAble = False
		playerScrollAble = True
		
		gameStableCounter = 0
		nextState = WAIT_STABLE
	elif state == WAIT_STABLE:
		playerControlPlacing = False
		playerControl = False #can play
		playerShootAble = False
		playerScrollAble = True
		
		if gameStable:
			gameStableCounter += 1
			if gameStableCounter == 10:
				# next turn
				gameStableCounter = 0
				timeReset()
				cycleWorms()
				weaponMan.renderWeaponCount()
				state = nextState

		nextState = PLAYER_CONTROL_1
	elif state == FIRE_MULTIPLE:
		playerControlPlacing = False
		playerControl = True #can play
		playerShootAble = True
		playerScrollAble = True
		
		if weaponMan.currentWeapon in ["flame thrower", "minigun", "laser gun", "bubble gun"]:
			fireWeapon = True
			if not shotCount == 0:
				nextState = FIRE_MULTIPLE
	elif state == WIN:
		gameStableCounter += 1
		if gameStableCounter == 30*3:
			run = False
			subprocess.Popen("wormsLauncher.py -popwin", shell=True)

################################################################################ Keys action
def onKeyPressRight():
	global camTrack
	objectUnderControl.facing = RIGHT
	if objectUnderControl.shootAngle >= pi/2 and objectUnderControl.shootAngle <= (3/2)*pi:
		objectUnderControl.shootAngle = pi - objectUnderControl.shootAngle
	camTrack = objectUnderControl

def onKeyPressLeft():
	global camTrack
	objectUnderControl.facing = LEFT
	if objectUnderControl.shootAngle >= -pi/2 and objectUnderControl.shootAngle <= pi/2:
		objectUnderControl.shootAngle = pi - objectUnderControl.shootAngle
	camTrack = objectUnderControl

def onKeyPressSpace():
	global energising, energyLevel, fireWeapon
	if Sheep.trigger == False:
		Sheep.trigger = True
	if useListMode and inUsedList(weaponMan.currentWeapon):
		return
	if objectUnderControl and playerControl:
		if weaponMan.getCurrentStyle() == CHARGABLE and not currentTeam.ammo(weaponMan.currentWeapon) == 0:
			energising = True
			energyLevel = 0
			fireWeapon = False
			if weaponMan.currentWeapon in ["homing missile", "seeker"] and not HomingMissile.showTarget:
				energising = False

def onKeyHoldSpace():
	global energyLevel, energising, fireWeapon
	energyLevel += 0.05
	if energyLevel >= 1:
		if timeTravel:
			timeTravelPlay()
			energyLevel = 0
			energising = False
		else:
			energyLevel = 1
			fireWeapon = True

def onKeyReleaseSpace():
	global energyLevel, fireWeapon, playerShootAble, energising
	if playerShootAble:
		if timeTravel and not currentTeam.ammo(weaponMan.currentWeapon) == 0:
			timeTravelPlay()
			energyLevel = 0
		elif weaponMan.getCurrentStyle() == CHARGABLE and energising:
			fireWeapon = True
		# putable/gun weapons case
		elif (weaponMan.getCurrentStyle() in [PUTABLE, GUN]) and not currentTeam.ammo(weaponMan.currentWeapon) == 0 and not weaponMan.currentWeapon == "rope":
			if useListMode and inUsedList(weaponMan.currentWeapon): return
			fireWeapon = True
			playerShootAble = False
		# rope case:
		elif (weaponMan.getCurrentStyle() in [PUTABLE, GUN]) and not currentTeam.ammo(weaponMan.currentWeapon) == 0 and weaponMan.currentWeapon == "rope":
			# if not currently roping:
			fireWeapon = True
			playerShootAble = False
			# if currently roping:
			if objectUnderControl.rope: 
				objectUnderControl.toggleRope(None)
				fireWeapon = False
		energising = False
	elif objectUnderControl.rope:
		objectUnderControl.toggleRope(None)
	elif objectUnderControl.parachuting:
		objectUnderControl.toggleParachute()

def onKeyPressTab():
	if not state == PLAYER_CONTROL_1:
		if state == FIRE_MULTIPLE and switchingWorms:
			switchWorms()
		return
	if weaponMan.currentWeapon == "bunker buster":
		BunkerBuster.mode = not BunkerBuster.mode
		if BunkerBuster.mode:
			FloatingText(objectUnderControl.pos + Vector(0,-5), "drill mode", (20,20,20))
		else:
			FloatingText(objectUnderControl.pos + Vector(0,-5), "rocket mode", (20,20,20))
		weaponMan.renderWeaponCount()
	elif weaponMan.currentWeapon == "venus fly trap":
		PlantBomb.venus = not PlantBomb.venus
		if PlantBomb.venus:
			FloatingText(objectUnderControl.pos + Vector(0,-5), "venus fly trap", (20,20,20))
		else:
			FloatingText(objectUnderControl.pos + Vector(0,-5), "plant mode", (20,20,20))
	elif weaponMan.currentWeapon == "long bow":
		LongBow._sleep = not LongBow._sleep
		if LongBow._sleep:
			FloatingText(objectUnderControl.pos + Vector(0,-5), "sleeping", (20,20,20))
		else:
			FloatingText(objectUnderControl.pos + Vector(0,-5), "regular", (20,20,20))
	elif weaponMan.currentWeapon == "girder":
		global girderAngle, girderSize
		girderAngle += 45
		if girderAngle == 180:
			girderSize = 100
		if girderAngle == 360:
			girderSize = 50
			girderAngle = 0
	elif weaponMan.getFused(weaponMan.currentWeapon):
		global fuseTime
		fuseTime += fps
		if fuseTime > fps*4:
			fuseTime = fps
		string = "delay " + str(fuseTime//fps) + " sec"
		FloatingText(objectUnderControl.pos + Vector(0,-5), string, (20,20,20))
		weaponMan.renderWeaponCount()
	elif weaponMan.getBackColor(weaponMan.currentWeapon) == AIRSTRIKE:
		global airStrikeDir
		airStrikeDir *= -1
	elif switchingWorms:
		switchWorms()

def onKeyPressEnter():
	# jump
	if objectUnderControl.stable and objectUnderControl.health > 0:
		objectUnderControl.vel += Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle)) * 3
		objectUnderControl.stable = False

################################################################################ Setup
HealthBar.healthBar = HealthBar()
damageText = (damageThisTurn, myfont.render(str(int(damageThisTurn)), False, HUDColor))
commentator = Commentator()
water = Water()
Water.layersA.append(water)
water.createLayers()

def makeRandomTeams(teamQuantity, wormsPerTeam, names):
	global teams, totalTeams, currentTeam, teamChoser
	tempTeam = []
	shuffle(names)
	colorsChoice = [RED, YELLOW, BLUE, GREEN]
	shuffle(colorsChoice)
	for team in range(teamQuantity):
		teamNames = []
		for worm in range(wormsPerTeam):
			teamNames.append(names.pop())
		tempTeam.append(Team(teamNames, colorsChoice.pop()))
	teams = tempTeam
	totalTeams = teamQuantity
	currentTeam = choice(teams)
	teamChoser = randint(0,3) % totalTeams

namesCustom = ["eithan", "almog", "berry", "simon", "dor", "evgeny", "ted", "shahaf", "nakar", "dan", "yoni", "asi"]
namesCustom2 = ["Cenzor", "aliza", "naomi", "phathi", "yohai", "yulia", "rom", "lidia", "acasha", "ziv", "mario", "hagar"]
if False:
	makeRandomTeams(4, 4, namesCustom + namesCustom2)

################################################################################ Main Loop

if __name__ == "__main__":
	# pygame.mouse.set_visible(False)
	run = True
	pause = False
	while run:
		fpsClock.tick(fps)
		
		stateMachine()
		
		# events
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			# mouse click event
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # left click (main)
				#mouse position:
				mousePos = pygame.mouse.get_pos()
				if playerControlPlacing:
					teams[teamChoser].addWorm((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
					teamChoser = (teamChoser + 1) % totalTeams
				# CLICKABLE weapon check:
				if state == PLAYER_CONTROL_1 and weaponMan.getCurrentStyle() == CLICKABLE:
					fireClickable()
				if state == PLAYER_CONTROL_1 and weaponMan.currentWeapon in ["homing missile", "seeker"] and not len(Menu.menus) > 0:
					HomingMissile.Target.x, HomingMissile.Target.y = mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y
					HomingMissile.showTarget = True
				# cliking in menu
				if Menu.event:
					clickInMenu()
					
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)
				# testing mainly
				# testerFunc()
				pass
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
				# this is the next state after placing all worms
				if state == PLACING_WORMS:
					nextState = CHOOSE_STARTER
					# state = nextState
					weaponMan.renderWeaponCount()
				elif state == PLAYER_CONTROL_1:
					if len(Menu.menus) == 0:
						weaponMenuInit()
					else:
						Menu.menus.clear()
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll down
				if len(Menu.menus) > 0:
					scrollMenu()
				else:
					scalingFactor *= 1.1
					if scalingFactor >= 3: scalingFactor = 3
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll up
				if len(Menu.menus) > 0:
					scrollMenu(False)
				else:
					scalingFactor *= 0.9
					if scalingFactor <= 1: scalingFactor = 1
	
			# key press
			if event.type == pygame.KEYDOWN:
				# controll worm, jump and facing
					if objectUnderControl and playerControl:
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
					if state == PLAYER_CONTROL_1:
						weaponsSwitch = False
						if event.key == pygame.K_1:
							keyWeapons = ["missile", "gravity missile", "homing missile"]
							weaponsSwitch = True
						elif event.key == pygame.K_2:
							keyWeapons = ["grenade", "sticky bomb", "electric grenade"]
							weaponsSwitch = True
						elif event.key == pygame.K_3:
							keyWeapons = ["mortar", "raon launcher"]
							weaponsSwitch = True
						elif event.key == pygame.K_4:
							keyWeapons = ["petrol bomb", "flame thrower"]
							weaponsSwitch = True
						elif event.key == pygame.K_5:
							keyWeapons = ["TNT", "mine", "sheep"]
							weaponsSwitch = True
						elif event.key == pygame.K_6:
							keyWeapons = ["shotgun", "long bow", "gamma gun", "laser gun"]
							weaponsSwitch = True
						elif event.key == pygame.K_7:
							keyWeapons = ["girder", "baseball"]
							weaponsSwitch = True
						elif event.key == pygame.K_8:
							keyWeapons = ["bunker buster", "laser gun", "minigun"]
							weaponsSwitch = True
						elif event.key == pygame.K_9:
							keyWeapons = ["minigun"]
							weaponsSwitch = True
						elif event.key == pygame.K_0:
							keyWeapons = []
							for i, w in enumerate(currentTeam.weaponCounter):
								if w > 0 or w == -1:
									if weaponMan.weapons[i][3] == LEGENDARY:
										keyWeapons.append(weaponMan.weapons[i][0])
							weaponsSwitch = True
						elif event.key == pygame.K_MINUS:
							keyWeapons = ["rope"]
							weaponsSwitch = True
						elif event.key == pygame.K_EQUALS:
							keyWeapons = ["parachute"]
							weaponsSwitch = True
						if weaponsSwitch:
							if len(keyWeapons) > 0:
								if weaponMan.currentWeapon in keyWeapons:
									index = keyWeapons.index(weaponMan.currentWeapon)
									index = (index + 1) % len(keyWeapons)
									weaponSwitch = keyWeapons[index]
								else:
									weaponSwitch = keyWeapons[0]
							weaponMan.switchWeapon(weaponSwitch)
							weaponMan.renderWeaponCount()
					# misc
					if event.key == pygame.K_p:
						pause = not pause
					if event.key == pygame.K_TAB:
						onKeyPressTab()
					if event.key == pygame.K_t:
						testerFunc()
					if event.key == pygame.K_PAGEUP or event.key == pygame.K_KP9:
						if len(Menu.menus) > 0:
							scrollMenu()
					if event.key == pygame.K_PAGEDOWN or event.key == pygame.K_KP3:
						if len(Menu.menus) > 0:
							scrollMenu(False)
					if event.key == pygame.K_F1:
						toastInfo()
					if event.key == pygame.K_F2:
						Worm.healthMode = (Worm.healthMode + 1) % 2
						if Worm.healthMode == 1:
							for worm in PhysObj._worms:
								worm.healthStr = myfont.render(str(worm.health), False, worm.team.color)
					if event.key == pygame.K_F3:
						drawGroundSec = not drawGroundSec
					if event.key == pygame.K_RCTRL or event.key == pygame.K_LCTRL:
						scalingFactor = 3
						if camTrack == None:
							camTrack = objectUnderControl
					# if event.key == pygame.K_n:
						# pygame.image.save(win, "wormshoot" + str(timeOverall) + ".png")	
					cheatCode += event.unicode
					if event.key == pygame.K_EQUALS:
						cheatActive(cheatCode)
						cheatCode = ""
			if event.type == pygame.JOYBUTTONDOWN:
				if objectUnderControl and playerControl:
						if joystick.get_button(JOYSTICK_FOUR):
							onKeyPressEnter()
				if event.button == JOYSTICK_THREE:
					onKeyPressSpace()
			if event.type == pygame.KEYUP:
				# fire release
				if event.key == pygame.K_SPACE:
					onKeyReleaseSpace()
			if event.type == pygame.JOYBUTTONUP:
				if event.button == JOYSTICK_THREE:
					onKeyReleaseSpace()
		keys = pygame.key.get_pressed()
		if keys[pygame.K_ESCAPE]: run = False	
		#key hold:
		if objectUnderControl and playerControl:
			if keys[pygame.K_RIGHT]:# or joystick.get_axis(0) > 0.5:
				actionMove = True
			if keys[pygame.K_LEFT]:# or joystick.get_axis(0) < -0.5:
				actionMove = True
			# fire hold
			if playerShootAble and (keys[pygame.K_SPACE]) and weaponMan.getCurrentStyle() == CHARGABLE and energising:
				onKeyHoldSpace()
		
		if pause:
			pos = (winWidth/2 - pauseSurf.get_width()/2, winHeight/2 - pauseSurf.get_height()/2)
			win.blit(pauseSurf, pos)
			screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
			pygame.display.update()
			continue

		# use edge gameMap scroll
		mousePos = pygame.mouse.get_pos()
		if playerScrollAble and pygame.mouse.get_focused() and not len(Menu.menus) > 0:
			scroll = Vector()
			if mousePos[0] < edgeBorder:
				scroll.x -= mapScrollSpeed * (2.5 - scalingFactor/2)
			if mousePos[0] > screenWidth - edgeBorder:
				scroll.x += mapScrollSpeed * (2.5 - scalingFactor/2)
			if mousePos[1] < edgeBorder:
				scroll.y -= mapScrollSpeed * (2.5 - scalingFactor/2)
			if mousePos[1] > screenHeight - edgeBorder:
				scroll.y += mapScrollSpeed * (2.5 - scalingFactor/2)
			if scroll != Vector():
				camTrack = Camera(camPos + Vector(winWidth, winHeight)/2 + scroll)
		
		# handle scale:
		winWidth += (1280 / scalingFactor - winWidth) * 0.2
		winHeight += (720 / scalingFactor - (winHeight)) * 0.2
		winWidth = int(winWidth)
		winHeight = int(winHeight)
			
		win = pygame.Surface((winWidth, winHeight))
		
		# handle position:
		if camTrack:
			# actual position target:
			### camPos = camTrack.pos - Vector(winWidth, winHeight)/2
			# with smooth transition:
			camPos += ((camTrack.pos - Vector(int(1280 / scalingFactor), int(720 / scalingFactor))/2) - camPos) * 0.2
		
		# constraints:
		if camPos.y < 0: camPos.y = 0
		if camPos.y >= mapHeight - winHeight: camPos.y = mapHeight - winHeight
		if mapClosed or darkness:
			if camPos.x < 0:
				camPos.x = 0
			if camPos.x >= mapWidth - winWidth:
				camPos.x = mapWidth - winWidth
		
		if Earthquake.earthquake: camPos.x += 25*sin(timeOverall); camPos.y += 15*sin(timeOverall * 1.8)
		
		# Fire
		if fireWeapon and playerShootAble: fire()
		
		# step:
		gameStable = True
		for p in PhysObj._reg:
			p.step()
			if not p.stable:
				gameDistable()
		for f in nonPhys: f.step()
		for t in Toast._toasts: t.step()
		
		if timeTravel: timeTravelRecord()
			
		# camera for wait to stable:
		if state == WAIT_STABLE and timeOverall % 20 == 0:
			for worm in PhysObj._worms:
				if worm.stable:
					continue
				else:
					camTrack = worm
					break
		
		# advance timer
		timeOverall += 1
		if timeOverall % fps == 0 and state != PLACING_WORMS: timeStep()
		
		water.stepAll()
		cloudManager()
		
		if Arena.arena: Arena.arena.step()
		
		# reset actions
		actionMove = False
			
		# draw:
		win.fill(feelColor[0])
		win.blit(pygame.transform.scale(imageSky, (win.get_width(), mapHeight)), (0,0 - camPos[1]))
		for cloud in Cloud._reg: cloud.draw()
		drawBackGround(imageMountain2,4)
		drawBackGround(imageMountain,2)
		
		water.drawLayers(UP)
		drawLand()
		for p in PhysObj._reg: p.draw()
		for f in nonPhys: f.draw()
		water.drawLayers(DOWN)
		for t in Toast._toasts: t.draw()
		
		if weaponMan.currentWeapon in ["homing missile", "seeker"] and HomingMissile.showTarget: drawTarget(HomingMissile.Target)
		if gameMode == TERMINATOR and victim and victim.alive: drawTarget(victim.pos)
		if Arena.arena: Arena.arena.draw()
			
		# draw shooting indicator
		if objectUnderControl and state in [PLAYER_CONTROL_1, PLAYER_CONTROL_2, FIRE_MULTIPLE] and objectUnderControl.health > 0:
			objectUnderControl.drawCursor()
			if aimAid and weaponMan.getCurrentStyle() == GUN:
				p1 = vectorCopy(objectUnderControl.pos)
				p2 = p1 + Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle)) * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))
			i = 0
			while i < 20 * energyLevel:
				cPos = vectorCopy(objectUnderControl.pos)
				angle = objectUnderControl.shootAngle
				pygame.draw.line(win, (0,0,0), point2world(cPos), point2world(cPos + vectorFromAngle(angle) * i))
				i += 1
		if weaponMan.currentWeapon == "girder" and state == PLAYER_CONTROL_1: drawGirderHint()
		drawExtra()
		drawLayers()
		
		# HUD
		drawWindIndicator()
		timeDraw()
		if weaponMan.surf: win.blit(weaponMan.surf, ((int(25), int(8))))
		commentator.step()
		if weaponMan.getBackColor(weaponMan.currentWeapon) == AIRSTRIKE:
			mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
			win.blit(pygame.transform.flip(airStrikeSpr, False if airStrikeDir == RIGHT else True, False), point2world(mouse - tup2vec(airStrikeSpr.get_size())/2))
		if useListMode: drawUseList()
		# draw health bar
		if not state in [RESET, GENERATE_TERRAIN, PLACING_WORMS, CHOOSE_STARTER] and drawHealthBar: HealthBar.healthBar.step()
		if not state in [RESET, GENERATE_TERRAIN, PLACING_WORMS, CHOOSE_STARTER] and drawHealthBar: HealthBar.healthBar.draw() # teamHealthDraw()
		if gameMode == TERMINATOR and victim and victim.alive:
			drawDirInd(victim.pos)
		if gameMode == TARGETS and objectUnderControl:
			for target in ShootingTarget._reg:
				drawDirInd(target.pos)
		
		# weapon menu:
		# move menus
		if len(Toast._toasts) > 0:
			for t in Toast._toasts:
				if t.mode == Toast.bottom:
					t.updateWinPos((winWidth/2, winHeight))
				elif t.mode == Toast.middle:
					t.updateWinPos(Vector(winWidth/2, winHeight/2) - tup2vec(t.surf.get_size())/2)
		for i, menu in enumerate(Menu.menus):
			if i == 0: Menu.menus[0].updatePosX(winWidth - 100 - Menu.border)
			if i == 1: Menu.menus[1].updatePosX(winWidth - 2 * 100 - 1 * Menu.border - 1)
			
			if i == 2:
				posY = 1
				if len(Menu.menus) > 1:
					posY = Menu.menus[1].size.y + 1
				Menu.menus[2].updatePosX(winWidth - 2 * 100 - 1 * Menu.border - 1)
				Menu.menus[2].updatePosY(posY)
		# step menus
		Menu.event = None
		if len(Menu.menus) > 0:
			for menu in Menu.menus: menu.step()
			for menu in Menu.menus: menu.draw()
		# draw kill list
		if gameMode in [POINTS, TARGETS, TERMINATOR]:
			while len(killList) > 8:
				killList.pop(-1)
			for i, killed in enumerate(killList):
				win.blit(killed[0], (5, winHeight - 14 - i * 8))
		
		drawExtra()
		# debug:
		if damageText[0] != damageThisTurn: damageText = (damageThisTurn, myfont.render(str(int(damageThisTurn)), False, HUDColor))
		win.blit(damageText[1], ((int(5), int(winHeight-6))))
		
		if state == PLACING_WORMS: win.blit(myfont.render(str(len(PhysObj._worms)), False, HUDColor), ((int(20), int(winHeight-6))))
		
		# draw loading screen
		if state in [RESET, GENERATE_TERRAIN] or (state in [PLACING_WORMS, CHOOSE_STARTER] and not manualPlace):
			win.fill((0,0,0))
			pos = (winWidth/2 - loadingSurf.get_width()/2, winHeight/2 - loadingSurf.get_height()/2)
			win.blit(loadingSurf, pos)
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + 20), (pos[0] + loadingSurf.get_width(), pos[1] + 20))
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + loadingSurf.get_height() + 20), (pos[0] + loadingSurf.get_width(), pos[1] + loadingSurf.get_height() + 20))
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + 20), (pos[0], pos[1] + loadingSurf.get_height() + 20))
			pygame.draw.line(win, (255,255,255), (pos[0] + loadingSurf.get_width(), pos[1] + 20), (pos[0] + loadingSurf.get_width(), pos[1] + loadingSurf.get_height() + 20))
			pygame.draw.rect(win, (255,255,255), ((pos[0], pos[1] + 20), ((lstep/lstepmax)*loadingSurf.get_width(), loadingSurf.get_height())))
		
		# screen manegement
		screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
		
		pygame.display.update()
		
	pygame.quit()
