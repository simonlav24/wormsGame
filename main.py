from math import pi, cos, sin, atan2, sqrt, exp, degrees, radians, log
from random import shuffle ,randint, uniform, choice
from vector import *
from pygame import gfxdraw
import pygame
pygame.init()

if True:
	fpsClock = pygame.time.Clock()
	
	pygame.font.init()
	myfont = pygame.font.Font("fonts\pixelFont.ttf", 5)
	myfontbigger = pygame.font.Font("fonts\pixelFont.ttf", 10)
	
	scalingFactor = 3
	scalling = 3
	winWidth = int(1280 / scalingFactor)
	winHeight = int(720 / scalingFactor)
	# winWidth = int(640 / scalingFactor)
	# winHeight = int(480 / scalingFactor)
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
	
	RIGHT = 1
	LEFT = -1
	RED = (255,0,0)
	YELLOW = (255,255,0)
	BLUE = (0,0,255)
	GREEN = (0,255,0)
	BLACK = (0,0,0)
	WHITE = (255,255,255)
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
	LEGENDARY = (255, 255, 102)
	MISC = (224, 224, 235)
	AIRSTRIKE = (204, 255, 255)

# Game parameters
if True:
	turnTime = 45
	retreatTime = 5
	wormDieTime = 3
	shockRadius = 1.5
	burnRadius = 1.15
	globalGravity = 0.2
	mapScrollSpeed = 8
	initialHealth = 100
	deployPacks = True
	diggingMatch = False
	randomPlace = True
	drawHealthBar = True
	mapClosed = False
	unlimitedMode = False
	moreWindAffected = False
	fortsMode = False
	davidAndGoliathMode = False
	randomWeapons = False
	darkness = False
	drakRadius = 70
	pointsMode = False
	useListMode = False
	captureTheFlag = False
	targetsMode = False
	
	# Multipliers
	damageMult = 0.8
	fallDamageMult = 1
	windMult = 1.5
	radiusMult = 1
	packMult = 1
	dampMult = 1.5
	
	text = ""
	HUDColor = BLACK
webVer = True 

################################################################################ Map
if True:
	mapWidth = int(1024*1.5)
	mapHeight = 512
	map = pygame.Surface((mapWidth, mapHeight))
	wormCol = pygame.Surface((mapWidth, mapHeight))
	extraCol = pygame.Surface((mapWidth, mapHeight))
	
	ground = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	groundSec = pygame.Surface((mapWidth, mapHeight)).convert_alpha()#KILL
	mask = pygame.Surface((mapWidth, mapHeight)).convert_alpha()# for darkness
	lights = []
	
	camPos = Vector(0,0)
	camTarget = Vector(0,0)
	
	objectUnderControl = None
	camTrack = None # object to track
	
	energising = False
	energyLevel = 0
	fireWeapon = False
	currentWeapon = "missile"
	currentWeaponSurf = myfont.render(currentWeapon, False, HUDColor)
	weaponStyle = CHARGABLE
	
	wind = uniform(-1,1)
	actionMove = False
	aimAid = False
	switchingWorms = False
	timeTravel = False
	megaTrigger = False
	jetPackFuel = 100

def createMapImage(heightNorm = None):
	global mapImage
	if heightNorm:
		ratio = mapImage.get_width() / mapImage.get_height()
		mapImage = pygame.transform.scale(mapImage, (int(heightNorm * ratio), heightNorm))
		if randint(0,1) == 0:
			mapImage = pygame.transform.flip(mapImage, True, False)
	
	global map, mapWidth, mapHeight, ground, wormCol, extraCol, groundSec
	mapWidth = mapImage.get_width()
	mapHeight = mapImage.get_height()
	map = pygame.Surface((mapWidth, mapHeight))
	map.fill(SKY)
	wormCol = pygame.Surface((mapWidth, mapHeight))
	wormCol.fill(SKY)
	extraCol = pygame.Surface((mapWidth, mapHeight))
	extraCol.fill(SKY)
	global mask
	mask = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	
	ground = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	groundSec = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	global lstepmax
	lstepmax = mapWidth//10 + wormsPerTeam * len(teams) + 1
	for x in range(mapWidth):
		for y in range(mapHeight):
			if not mapImage.get_at((x, y)) == (0,0,0):
				map.set_at((x, y), GRD)
		if x % 10 == 0:
			lstepper()#
	mapImage.set_colorkey((0,0,0))

def createMapDigging():
	global map, wormCol, extraCol
	map.fill(GRD)
	wormCol.fill(SKY)
	extraCol.fill(SKY)
	
def drawLand():
	win.blit(groundSec, (-int(camPos.x), -int(camPos.y)))
	win.blit(ground, (-int(camPos.x), -int(camPos.y)))
	if darkness and not state == PLACING_WORMS:
		mask.fill((30,30,30))
		if objectUnderControl:
			pygame.draw.circle(mask, (0,0,0,0), objectUnderControl.pos.vec2tupint(), drakRadius)
	
		global lights
		for light in lights:
			pygame.draw.circle(mask, light[3], (int(light[0]), int(light[1])), int(light[2]))
		lights = []
	
		win.blit(mask, (-int(camPos.x), -int(camPos.y)))

def renderLand():
	global lstep
	ground.fill(SKY)
	if mapImage:
		ground.blit(mapImage, (0,0))
		groundSec.fill((91,149,209))
		mapImage.set_alpha(64)
		groundSec.blit(mapImage, (0,0))
		groundSec.set_colorkey((91,149,209))

	else:
		groundSec.fill(SKY)
		for x in range(0,mapWidth):
			for y in range(0,mapHeight):
				if map.get_at((x,y)) == GRD:
					ground.fill((randint(80, 120), randint(30, 70), 0), ((x,y), (1, 1)))

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
	size = (radius*burnRadius*2+2, radius*burnRadius*2+2)
	stain = pygame.Surface(size, pygame.SRCALPHA)
	patch = pygame.Surface(size, pygame.SRCALPHA)
	grounder = pygame.Surface(size, pygame.SRCALPHA)
	pygame.draw.circle(stain, (0,0,0,randint(100,180)), (radius*burnRadius+2, radius*burnRadius+2), radius * burnRadius+2)
	grounder.blit(ground, (0,0), (pos - tup2vec(size)/2, size))
	patch.blit(map, (0,0), (pos - tup2vec(size)/2, size))
	patch.set_colorkey(GRD)
	grounder.blit(stain, (0,0))
	grounder.blit(patch, (0,0))
	grounder.set_colorkey(SKY)
	ground.blit(grounder, pos - tup2vec(size)/2)

	
	pygame.draw.circle(map, SKY, pos.vec2tupint(), int(radius))
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
			d.radius = choice([1,2])

class Blast:
	_color = [(255,255,255), (255, 222, 3), (255, 109, 10), (254, 153, 35), (242, 74, 1), (93, 91, 86)]
	def __init__(self, pos, radius, smoke = 30):
		nonPhys.append(self)
		self.timeCounter = 0
		self.pos = pos
		self.radius = radius
		self.rad = 0
		self.timeCounter = 0
		self.smoke = smoke
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
		layersCircles[1].append((self._color[int(max(min(self.timeCounter-1, 5), 0))], self.pos, self.rad*0.6))
		layersCircles[2].append((self._color[int(max(min(self.timeCounter-2, 5), 0))], self.pos, self.rad*0.3))

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

def isVisibleInDarkness(self):
	if state == PLACING_WORMS:
		return True
	if isOnMap(self.pos):
		if mask.get_at(self.pos.vec2tupint())[3] < 255:
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
			if map.get_at((place.x, y + i)) == GRD or wormCol.get_at((place.x, y + i)) != (0,0,0) or extraCol.get_at((place.x, y + i)) != (0,0,0):
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
			pygame.draw.circle(map, SKY, place.vec2tup(), 5)
			pygame.draw.circle(ground, SKY, place.vec2tup(), 5)
	# print(counter)
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
def addExtra(pos, color = (255,255,255), delay = 5):
	extra.append((pos[0], pos[1], color, delay))

def drawExtra():
	global extra
	extraNext = []
	for i in extra:
		win.fill(i[2], ((int(i[0] - camPos.x), int(i[1] - camPos.y)),(1,1)))
		if i[3] > 0:
			extraNext.append((i[0], i[1], i[2], i[3]-1))
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

# sprites
if True:
	imageMountain = pygame.image.load("assets/mountain.png").convert_alpha()
	imageMountain2 = pygame.image.load("assets/mountain2.png").convert_alpha()
	imageSky = pygame.transform.scale(pygame.image.load("assets/sky.png"), (winWidth, winHeight))
	imageCloud = pygame.image.load("assets/cloud.png").convert_alpha()
	imageBat = pygame.image.load("assets/bat.png").convert_alpha()
	imageTurret = pygame.image.load("assets/turret.png").convert_alpha()
	imageParachute = pygame.image.load("assets/parachute.png").convert_alpha()
	imageVenus = pygame.image.load("assets/venus.png").convert_alpha()
	imagePokeball = pygame.image.load("assets/pokeball.png").convert_alpha()
	imageGreenShell = pygame.image.load("assets/greenShell.png").convert_alpha()
	imageMjolnir = pygame.image.load("assets/mjolnir.png").convert_alpha()

def drawBackGround(surf, parallax):
	width = surf.get_width()
	height = surf.get_height()
	offset = (camPos.x/parallax)//width
	times = winWidth//width + 2
	for i in range(times):
		x = int(-camPos.x/parallax) + int(int(offset) * width + i * width)
		y =  int(mapHeight - height) - int(camPos.y) - int((int(mapHeight - winHeight) - int(camPos.y))/parallax)
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
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0:
			if mapClosed:
				return False
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			r += pi /8
			continue
		
		getAt = testPos.vec2tupint()
		if map.get_at(getAt) == GRD:
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
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0:
			if mapClosed:
				return False
			else:
				r += pi /8
				continue
		if testPos.y < 0:
			r += pi /8
			continue
			
		if not map.get_at((int(testPos.x), int(testPos.y))) == (0,0,0):
			return False
		
		r += pi /8
	# check for falling
	groundUnder = False
	for i in range(int(obj.radius), 50):
		# extra.append((pos.x, pos.y + i, (255,255,255), 5))
		if map.get_at((int(pos.x), int(pos.y + i))) == GRD:
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
		if map.get_at(i.vec2tupint()) == (0,0,0):
			while map.get_at(i.vec2tupint()) == (0,0,0):
				if isOnMap((i[0], i[1] + 1)):
					i.y += 1
				else:
					break
		else:
			while map.get_at(i.vec2tupint()) == GRD:
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

def whiten(color):
	r = color[0]
	g = color[1]
	b = color[2]
	
	r = r/5 + 167
	g = g/5 + 167
	b = b/5 + 167
	
	return (r,g,b)

################################################################################ Objects
timeCounter = turnTime
timeOverall = 0
def timeStep():
	global timeCounter
	if timeCounter == 0:
		# timeCounter = turnTime
		timeOnTimer()
	if not timeCounter <= 0:
		timeCounter -= 1
def timeOnTimer():
	# onTime timeCounter end timeCounter
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
	win.blit(myfont.render(str(timeCounter), False, HUDColor) , ((int(10), int(8))))
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

Target = Vector(-1,-1)
showTarget = False
def drawTarget():
	if showTarget:
		pygame.draw.line(win, (180,0,0), point2world((Target.x - 10, Target.y - 8)) , point2world((Target.x + 10, Target.y + 8)), 2)
		pygame.draw.line(win, (180,0,0), point2world((Target.x + 10, Target.y - 8)) , point2world((Target.x - 10, Target.y + 8)), 2)

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
		self.damp = 0.8
		
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
			
			# collission with map:
			if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
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
			self.stable = True
			
			response.normalize()
			
			fdot = self.vel.dot(response)
			if not self.bounceBeforeDeath == 1:
				
				# damp formula 1 - logarithmic
				dampening = max(self.damp, self.damp * log(magVel) if magVel > 0.001 else 1)
				dampening = min(dampening, min(self.damp * 2, 0.9))
				newVel = ((response * -2 * fdot) + self.vel) * dampening
				
				# legacy formula
				newVel = ((response * -2 * fdot) + self.vel) * self.damp * dampMult
				
				# if newVel.getMag() > magVel:
					# newVel.setMag(magVel)
					
				self.vel = newVel
				# max speed recorded ~ 25
			
			if self.bounceBeforeDeath > 0:
				self.bounceBeforeDeath -= 1
				self.dead = self.bounceBeforeDeath == 0
				
		else:
			self.pos = ppos
			# flew out map but not worms !
			if self.pos.y > mapHeight and not self in self._worms:
				self.outOfMapResponse()
				self._reg.remove(self)
				return
		
		if magVel < 0.1: # creates a double jump problem
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self._reg.remove(self)
			self.deathResponse()
			del self
	def applyForce(self):
		# gravity:
		self.acc.y += globalGravity
		if self.windAffected:
			self.acc.x += wind * 0.1 * windMult
	def deathResponse(self):
		pass
	def secondaryStep(self):
		pass
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
	def __init__(self, pos, blast, colors):
		Debrie._debries.append(self)
		self.initialize()
		self.vel = Vector(cos(uniform(0,1) * 2 *pi), sin(uniform(0,1) * 2 *pi)) * blast
		self.pos = Vector(pos[0],pos[1])
		
		self.boomAffected = False
		self.bounceBeforeDeath = 2
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
		self.windAffected = True
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
		Blast(self.pos + vectorUnitRandom()*2, randint(5,8))
fuseTime = 60
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
					k.windAffected = False
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
			m.windAffected = False
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
		self.cpu = False
		self.wormCollider = True
		self.flagHolder = False
		self.sleep = False
	def applyForce(self):
		# gravity:
		if self.gravity == DOWN:
			### JETPACK
			if self.jetpacking and playerControl and objectUnderControl == self:
				global jetPackFuel
				if pygame.key.get_pressed()[pygame.K_UP]:
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
			
			FloatingText(self.pos.vec2tup(), str(dmg))
			self.health -= dmg
			if self.health < 0:
				self.health = 0
			if Worm.healthMode == 1:
				self.healthStr = myfont.render(str(self.health), False, self.team.color)
			global damageThisTurn
			if not self == objectUnderControl:
				if not sentring and not raoning and not self in currentTeam.worms:
					damageThisTurn += dmg
			if captureTheFlag and damageType != 2:
				if self.flagHolder:
					self.team.flagHolder = False
					self.flagHolder = False
					Flag(self.pos)
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
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		win.blit(self.name , ((int(self.pos.x) - int(camPos.x) - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(camPos.y) - 21)))
		if self.rope:
			rope = [point2world(x) for x in self.rope[0]]
			rope.append(point2world(self.pos))
			pygame.draw.lines(win, (250,250,0), False, rope)
		if self.cpu:
			pygame.draw.circle(win, (200,0,0), point2world(self.pos + Vector(0,-5)), 2)
			cpuDraw()
		if self.alive and drawHealthBar:
			self.drawHealth()
		if self.pos.y < 0:
			width = 25
			height = 10
			pygame.draw.rect(win, (0,0,0), (point2world((self.pos.x - width/2,10)), (width, height)))
			num = myfont.render(str(int(-self.pos.y)), False, self.team.color)
			win.blit(num, point2world((self.pos.x - num.get_width()/2, 12)))
		if self.sleep and self.alive:
			if timeOverall % 30 == 0:
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
		self.name = myfont.render(self.nameStr, False, whiten(self.team.color))

		# insert to kill list:
		if not sentring and not raoning and not self in currentTeam.worms:
			damageThisTurn += self.health
			currentTeam.killCount += 1
			if pointsMode:
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
			Commentator.que.append((self.nameStr, choice(Commentator.stringsFlw), self.team.color))
		
		# if self in PhysObj._worms:
		
		# remove from regs:
		PhysObj._worms.remove(self)
		self.team.worms.remove(self)
		if cause == Worm.causeFlew or cause == Worm.causeVenus:
			PhysObj._reg.remove(self)
		
		# if under control 
		if objectUnderControl == self:
			if state == FIRE_MULTIPLE:
				if weaponStyle == GUN:
					self.team.weaponCounter[weaponDict[currentWeapon]] -= 1
					renderWeaponCount()
			nextState = PLAYER_CONTROL_2
			# unclear what will happen if dies in WAIT_STABLE
			state = nextState
			timeRemaining(wormDieTime)
	def drawHealth(self):
		if Worm.healthMode == 0:
			pygame.draw.rect(win, (220,220,220),(int(self.pos.x) -10 -int(camPos.x), int(self.pos.y) -15 -int(camPos.y), 20,3))
			value = 20 * min(self.health/initialHealth, 1)
			if value < 1:
				value = 1
			pygame.draw.rect(win, (0,220,0),(int(self.pos.x) -10 -int(camPos.x), int(self.pos.y) -15 -int(camPos.y), int(value),3))
		else:
			win.blit(self.healthStr , ((int(self.pos.x) - int(camPos.x) - int(self.healthStr.get_size()[0]/2)), (int(self.pos.y) - int(camPos.y) - 15)))
		# draw jetpack fuel
		if self.jetpacking:
			pygame.draw.rect(win, (220,220,220),(int(self.pos.x) -10 -int(camPos.x), int(self.pos.y) -25 -int(camPos.y), 20,3))
			value = 20 * (jetPackFuel/100)
			if value < 1:
				value = 1
			pygame.draw.rect(win, (0,0,220),(int(self.pos.x) -10 -int(camPos.x), int(self.pos.y) -25 -int(camPos.y), int(value),3))
	def secondaryStep(self):
		global state, nextState
		if objectUnderControl == self and playerControl and self.alive:
			self.damp = 0.1
		
			if keys[pygame.K_UP]:
				self.shootAcc = -0.04
			elif keys[pygame.K_DOWN]:
				self.shootAcc = 0.04
			else:
				self.shootAcc = 0
				self.shootVel = 0
		else:
			self.damp = 0.2
			self.shootAcc = 0
			self.shootVel = 0
		
		## CPU
		if state == PLAYER_CONTROL_1 and objectUnderControl == self and playerControl and self.cpu:
			CpuHolder.team = self.team
					
			if CpuHolder.mode == CpuHolder.CHECK_SURROUNDING:
				CpuHolder.targetMove = cpuTakeALook(self)
				if CpuHolder.targetMove:
					print("desided to move, worm:", CpuHolder.closeToWorm, "petrol:", CpuHolder.closeToPetrol)
					CpuHolder.mode = CpuHolder.MOVE
					
				else:
					CpuHolder.mode = CpuHolder.DUMMY
					print("desided to stay")
			
			if CpuHolder.mode == CpuHolder.MOVE:
				moved = cpuMove(self, CpuHolder.targetMove)
				if not moved:
					CpuHolder.mode = CpuHolder.CHECK_SURROUNDING
				
			if CpuHolder.mode == CpuHolder.DUMMY:
				print("gathering shot info")
				cpuGather()
			
			cpuProccess(self)
			
			if CpuHolder.mode == CpuHolder.READY:
				global energyLevel
				direction = CpuHolder.direction
				energy = CpuHolder.energy
			
				# calculate needed facing
				if not CpuHolder.checkList["facing"]:
					if direction.x >= 0:
						onKeyPressRight()
					else:
						onKeyPressLeft()
					CpuHolder.checkList["facing"] = True
				
				# calculate needed shootAngle
				if CpuHolder.checkList["facing"] and not CpuHolder.checkList["angle"]:
					needed = direction
					current = vectorFromAngle(self.shootAngle)
					current.x = needed.x
					if needed.y > current.y:
						# down
						self.shootAcc = 0.04
					else:
						self.shootAcc = -0.04
					if needed.y - 0.04 < current.y and current.y < needed.y + 0.04:
						# print("mine:", self.shootAngle, "needed:", direction.getAngle(), "facing:", self.facing)
						# if self.facing == RIGHT:
							# self.shootAngle = direction.getAngle()
						# else:
							# self.shootAngle = direction.getAngle() + 2*pi
						# print("correction: mine:", self.shootAngle, "needed:", direction.getAngle(), "facing:", self.facing)
						CpuHolder.checkList["angle"] = True
						
				if CpuHolder.checkList["facing"] and CpuHolder.checkList["angle"] and not CpuHolder.checkList["pressed"]:
					onKeyPressSpace()
					CpuHolder.checkList["pressed"] = True
				
				if CpuHolder.checkList["facing"] and CpuHolder.checkList["angle"] and CpuHolder.checkList["pressed"] and not CpuHolder.checkList["hold"]:
					onKeyHoldSpace()
					if energyLevel >= CpuHolder.energy:			
						CpuHolder.checkList["hold"] = True
				if CpuHolder.checkList["facing"] and CpuHolder.checkList["angle"] and CpuHolder.checkList["pressed"] and CpuHolder.checkList["hold"] and not CpuHolder.checkList["release"]:
					onKeyReleaseSpace()
					energyLevel = CpuHolder.energy
					CpuHolder.checkList["release"] = True
					CpuHolder.mode = CpuHolder.DUMMY
					
			if CpuHolder.mode == CpuHolder.STUCK:
				pass
		
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
				if map.get_at(testPos.vec2tupint()) == GRD:
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
					if map.get_at(testPos.vec2tupint()) == GRD:
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
		
		# check if killed:
		if self.health <= 0 and self.alive:
			self.dieded()
		
		# check if on map:
		if self.pos.y >= mapHeight:
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

##########################<CPU>
class CpuHolder:
	index = 0
	
	DUMMY = 0 #nothing to do
	RESET = 1 #ready to calculate shot from 0
	CHECK = 2 #check worms
	CALCULATE = 3 #calculate shot
	CHECK_PATH = 4 #check if shot hits ground
	READY = 5 #ready to shoot
	STUCK = 6 #cant shoot
	TRYAGAIN = 7 #try again with longer shot
	SETTLE = 10 #ready to calculate shot
	
	CHECK_SURROUNDING = 8 #check personal area to see if need to move
	MOVE = 9
	
	long = 0
	
	team = None
	
	mode = CHECK_SURROUNDING
	targets = []
	velCount = 0

	initialPos = None
	direction = None
	energy = None
	
	checkList = {"facing":False, "angle":False, "pressed":False, "hold":False, "release":False}
	weaponsCheckList = {"missile":False, "grenade":False}
	weapons = ["missile", "grenade"]
	weapon = None
	
	closeToWorm = None
	closeToPetrol = None
	
	potRight = []
	potLeft = []
	
	targetMove = None

def cpuPotential(self):
	walkLeft = 0
	walkRight = 0
	if CpuHolder.closeToWorm:
		directionToWorm = CpuHolder.closeToWorm.pos - self.pos
		if directionToWorm.x > 0: #worm is to the right
			walkLeft += 1
		else:
			walkRight += 1
	if CpuHolder.closeToPetrol:
		directionToPetrol = CpuHolder.closeToPetrol.pos - self.pos
		if directionToPetrol.x > 0: #worm is to the right
			walkLeft += 1
		else:
			walkRight += 1
	
	if walkLeft == 0 and walkRight == 0:
		return None
	
	if walkRight > walkLeft:
		return CpuHolder.potRight[-1]
	else:
		return CpuHolder.potLeft[-1]
		
def cpuMove(self, posToMove):
	if (posToMove - self.pos).x > 0:
		onKeyPressRight()
	else:
		onKeyPressLeft()
	
	if dist(self.pos, posToMove) > 5:
		return moveFallProof(self)
	else:
		CpuHolder.closeToWorm = None
		CpuHolder.closeToPetrol = None
		CpuHolder.targetMove = None
		return False

def cpuTakeALook(self):
	# if too close to same\other worms\petrol can
	for worm in PhysObj._worms:
		if worm == self:
			continue
		if dist(self.pos, worm.pos) < 30:
			CpuHolder.closeToWorm = worm
	for can in PetrolCan._cans:
		if dist(self.pos, can.pos) < 30:
			CpuHolder.closeToPetrol = can
	
	# check potentials:
	onKeyPressRight()
	CpuHolder.potRight = checkPotential(self, 50)
	onKeyPressLeft()
	CpuHolder.potLeft = checkPotential(self, 50)
	
	if CpuHolder.closeToWorm or CpuHolder.closeToPetrol:
		return cpuPotential(self)

def cpuLonger():
	CpuHolder.long += 1
	if CpuHolder.long == 5:
		CpuHolder.mode = CpuHolder.STUCK
	else:
		print("cant find path, checking long = ", CpuHolder.long)
		CpuHolder.mode = CpuHolder.TRYAGAIN

def cpuGather():
	if CpuHolder.mode == CpuHolder.DUMMY:
		CpuHolder.long = 0
		CpuHolder.mode = CpuHolder.RESET

def cpuProccess(self):
	# print(CpuHolder.mode)
	if CpuHolder.mode == CpuHolder.RESET:
		CpuHolder.targets = []
		CpuHolder.direction = None
		CpuHolder.energy = None
		CpuHolder.index = 0
		CpuHolder.velCount = 0
		CpuHolder.mode = CpuHolder.CHECK
		CpuHolder.checkList = {"facing":False, "angle":False, "pressed":False, "hold":False, "release":False}
		CpuHolder.weaponsCheckList = {"missile":False, "grenade":False}
		CpuHolder.long = 0
		CpuHolder.weapon = None
	
	if CpuHolder.mode == CpuHolder.TRYAGAIN:
		CpuHolder.targets = []
		CpuHolder.direction = None
		CpuHolder.energy = None
		CpuHolder.index = 0
		CpuHolder.velCount = 0
		CpuHolder.mode = CpuHolder.CHECK
		CpuHolder.checkList = {"facing":False, "angle":False, "pressed":False, "hold":False, "release":False}
	
	elif CpuHolder.mode == CpuHolder.CHECK:
		# print("check")
		worm2check = PhysObj._worms[CpuHolder.index]
		if not worm2check.team == CpuHolder.team:
			distance = dist(worm2check.pos, self.pos)
			if distance < 400:
				# if too close than ignore
				if not distance < 50:
					CpuHolder.targets.append([worm2check, None, 0, False]) # 0:target, 1:velInitial, 2:steps, 3:good_path
		
		CpuHolder.index += 1
		if CpuHolder.index == len(PhysObj._worms):
			CpuHolder.index = 0
			CpuHolder.mode = CpuHolder.CALCULATE
			if len(CpuHolder.targets) == 0:
				print("cant find worms")
				CpuHolder.mode = CpuHolder.STUCK
			
	elif CpuHolder.mode == CpuHolder.CALCULATE:
		worm2check = CpuHolder.targets[CpuHolder.index][0]
		# print("calculate", worm2check)
		posFinal = worm2check.pos + Vector(0, worm2check.radius)
		CpuHolder.initialPos = self.pos
		# missile acc
		if currentWeapon == "missile":
			acc = Vector(wind * 0.1 * windMult, globalGravity)
		else:
			acc = Vector(0, globalGravity)

		rang = (CpuHolder.long * 30, CpuHolder.long * 30 + 30)
		
		for i in range(rang[0], rang[1]):
			velInitial = (posFinal - CpuHolder.initialPos - acc * (i*(i+1)/2) )/i
			if velInitial.getMag() <= 10:
				# print("found")
				CpuHolder.targets[CpuHolder.index][1] = velInitial
				CpuHolder.targets[CpuHolder.index][2] = i
				CpuHolder.velCount += 1
				break
		
		# if we find velocity then velocity is inserted to target
		# if not velocity is None
		
		CpuHolder.index += 1
		if CpuHolder.index == len(CpuHolder.targets):
			CpuHolder.index = 0
			CpuHolder.mode = CpuHolder.CHECK_PATH
			if CpuHolder.velCount == 0:
				print("cant find vel")
				cpuLonger()
	
	elif CpuHolder.mode == CpuHolder.CHECK_PATH:
		# print("check path")
		# print(CpuHolder.targets)
		target = CpuHolder.targets[CpuHolder.index]
		
		if currentWeapon == "missile":
			acc = Vector(wind * 0.1 * windMult, globalGravity)
		else:
			acc = Vector(0, globalGravity)
		
		if target[1]: # if has velocity
			# print("has velocity,", target)
			target[3] = True
			for i in range(target[2]):
				# print("inside", target[1])
				posCurrent = CpuHolder.initialPos + target[1] * i + acc * (i*(i+1)/2)
				extra.append((posCurrent.x, posCurrent.y, (255,255,255), 10))
				if map.get_at(posCurrent.vec2tupint()) == GRD:
					target[3] = False
					break
			
		
		CpuHolder.index += 1
		if CpuHolder.index == len(CpuHolder.targets):
			CpuHolder.index = 0
			
			# pick currect fuseTime:
			global fuseTime
			fuseTime = CpuHolder.long * 30 + 30
			
			
			# pick first to fire:
			picked = False
			
			pick = 1
			
			# pick from strongest team:
			if pick == 1:
				strongestTeamIndex = teamsInfo.index(max(teamsInfo))
				# print(strongestTeamIndex)
				for tar in CpuHolder.targets:
					if tar[3] and tar[0].team == teams[strongestTeamIndex]:
						print("choosed", tar[0].nameStr, "by strongest team")
						picked = True
						CpuHolder.direction = normalize(tar[1])
						CpuHolder.energy = tar[1].getMag()/10
						break
					
					
			# pick first in order, defult:
			if not picked:
				for tar in CpuHolder.targets:
					if tar[3]:
						picked = True
						CpuHolder.direction = normalize(tar[1])
						CpuHolder.energy = tar[1].getMag()/10
						break
					
			if picked:
				CpuHolder.mode = CpuHolder.READY
			else:
				cpuLonger()

def cpuDraw():
	for target in CpuHolder.targets:
		pygame.draw.circle(win, (255,255,255), point2world(target[0].pos + Vector(0, -10)), 3)
	if CpuHolder.initialPos and CpuHolder.direction:
		pygame.draw.line(win, (255,255,255), point2world(CpuHolder.initialPos), point2world(CpuHolder.initialPos + CpuHolder.direction * 10))

def cpuUpdateCycle():
	if CpuHolder.mode == CpuHolder.STUCK:
		CpuHolder.mode = CpuHolder.CHECK_SURROUNDING

class CPU:#redundent
	only = None
	def __init__(self, pos):
		CPU.only = self
		self.pos = pos
		nonPhys.append(self)
		CpuHolder.initialPos = self.pos
		
		self.data = None
		
		self.firing = False
	def step(self):
		cpuProccess(self)
		if CpuHolder.mode == CpuHolder.READY:
			CpuHolder.mode = CpuHolder.DUMMY
			# self.fireAnim()
			self.data = (CpuHolder.direction, CpuHolder.energy)
	def fireAnim(self):
		Missile(self.pos, CpuHolder.direction, CpuHolder.energy)
	def draw(self):
		pygame.draw.circle(win, (255,255,255), point2world(self.pos), 2)
		for target in CpuHolder.targets:
			pygame.draw.circle(win, (255,255,255), point2world(target[0].pos + Vector(0, -10)), 3)
	def changePos(self, pos):
		self.pos = pos
		CpuHolder.initialPos = self.pos
	def gather(self):
		CpuHolder.long = 0
		CpuHolder.mode = CpuHolder.RESET

class CpuProbe:
	def __init__(self, pos, facing):
		nonPhys.append(self)
		self.radius = 3.5
		self.pos = pos
		self.facing = facing
	def step(self):
		if actionMove:
			moveFallProof(self)
	def draw(self):
		pygame.draw.circle(win, (255,255,255), point2world(self.pos), int(self.radius)+1, 1)
##########################</CPU>

class Fire(PhysObj):
	# _fires = []
	def __init__(self, pos, delay = 0):
		self.initialize()
		Debrie._debries.append(self)
		# Fire._fires.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.damp = 0
		self.red = 255
		self.yellow = 106
		self.phase = uniform(0,2)
		self.radius = 2
		self.windAffected = True
		self.life = randint(50,70)
		self.fallen = False
		self.delay = delay
		self.timer = 0
		self.wormCollider = True
	def collisionRespone(self, ppos):
		self.fallen = True
	def secondaryStep(self):
		self.stable = False
		if randint(0,10) == 1:
			Blast(self.pos + vectorUnitRandom(), randint(self.radius,7), 150)
		self.timer += 1
		if self.fallen:
			self.life -= 1
		if darkness:
			lights.append((self.pos[0], self.pos[1], 20, (0,0,0,0)))
		if self.life == 0:
			self._reg.remove(self)
			# Fire._fires.remove(self)
			del self
			return
		if randint(0,1) == 1 and self.timer > self.delay:
			boom(self.pos + Vector(randint(-1,1),randint(-1,1)), 3, False, False, True)
		# if randint(0,100) == 0 and Smoke.smokeCount < 30:
			# Smoke(self.pos)
	def draw(self):
		radius = 1
		if self.life > 20:
			radius += 1
		if self.life > 10:
			radius += 1
		# self.red = self.red
		self.yellow = int(sin(0.3*timeOverall + self.phase) * ((255-106)/4) + 255 - ((255-106)/2))
		# print(self.yellow)
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
		self.stable = False
		self.boomAffected = False
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
		if self.timer == 120:
			self.dead = True
	def deathResponse(self):
		global camTrack, grenadeThrown, grenadeTimer
		boom(self.pos, 40)
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -2) - int(camPos.x),int(self.pos.y -4) - int(camPos.y) , 3,8))
		pygame.draw.line(win, (90,90,90), point2world(self.pos + Vector(-1,-4)), point2world(self.pos + Vector(-1, -5*(120 - self.timer)/120 - 4)), 1)
		if randint(0,10) == 1:
			Blast(self.pos + Vector(-1, -5*(120 - self.timer)/120 - 4), randint(3,6), 150)

shotCount = 0
def fireShotgun(start, direction, power=15):#6
	hit = False

	for t in range(5,500):
		testPos = start + direction * t
		extra.append((testPos.x, testPos.y, (255, 204, 102), 3))
		
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue
		# hit worms or ground:
		at = (int(testPos.x), int(testPos.y))
		if map.get_at(at) == GRD or wormCol.get_at(at) != (0,0,0) or extraCol.get_at(at) != (0,0,0):
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
	map.blit(surfMap, (int(pos[0] - surfMap.get_width()/2), int(pos[1] - surfMap.get_height()/2)) )
	
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
		self.windAffected = False
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
		self.windAffected = False
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
		self.windAffected = False
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
			worm.team.weaponCounter[weaponDict[self.box]] += 1
			return
		elif self.box == "travel kit":
			worm.team.weaponCounter[weaponDict["rope"]] += 3
			worm.team.weaponCounter[weaponDict["parachute"]] += 3
			return
		elif self.box == "ender pearls":
			worm.team.weaponCounter[weaponDict["ender pearl"]] += 5
			return
		
		worm.team.utilityCounter[utilityDict[self.box]] += 1

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
		self.windAffected = False
		weaponsInBox = ["banana", "holy grenade", "earthquake", "gemino mine", "sentry turret", "bee hive", "vortex grenade", "chilli pepper", "covid 19", "raging bull", "electro boom", "pokeball", "green shell", "guided missile"]
		if not mapClosed:
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
		worm.team.weaponCounter[weaponDict[self.box]] += 1

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
			if y + i >= mapHeight:
				# no ground bellow
				goodPlace = False
				continue
			if map.get_at((x, y + i)) == GRD:
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
		extra.append((testPos.x, testPos.y, (0,255,255), 10))
		
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
		if self.timer == fuseTime + 60:
			self.dead = True
		if self.timer == fuseTime + 30:
			Commentator.que.append(choice([("hand grenade",("o lord bless this thy ",""),(210,210,0)), ("",("blow thine enemy to tiny bits ",""),(210,210,0)), ("",("feast upon the lambs and sloths and carp",""),(210,210,0)), ("",("three shall be the number thous shalt count",""),(210,210,0)), ("",("thou shall snuff that",""),(210,210,0))]))

class Banana(Grenade):
	def __init__(self, pos, direction, energy, used = False):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255, 204, 0)
		self.damp = 0.6
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
		pygame.draw.circle(map, GRD, (int(self.pos[0]), int(self.pos[1])), int(self.radius))
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
	def collisionRespone(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0:
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
			
			if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
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
		
		# if not self.target:
		self.angle += (self.angle2for - self.angle)*0.2
		if not self.target and timeOverall % 60 == 0:
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
			if map.get_at((ppos.vec2tupint())) == GRD:
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
		self.damp = 0.5
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
			if map.get_at(checkPos) == GRD:
				self.inGround = True
				self.drillVel = vectorCopy(self.vel)
		if self.inGround:
			self.timer += 1
					
		checkPos = (self.pos + direction*(self.radius + 2)).vec2tupint()
		if not(checkPos[0] >= mapWidth or checkPos[0] < 0 or checkPos[1] >= mapHeight or checkPos[1] < 0):
			if not map.get_at(checkPos) == GRD and self.inGround:
				self.dead = True
				
		if self.timer == 60:
			self.dead = True
			
		self.lastPos.x, self.lastPos.y = self.pos.x, self.pos.y
		self.pos = ppos
		
		if self.inGround:
			boom(self.pos, self.radius, False)
		self.lineOut((self.lastPos.vec2tupint(), self.pos.vec2tupint()))
		
		# flew out map but not worms !
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
		pygame.draw.line(map, SKY, line[0], line[1], self.radius*2)
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
	pygame.draw.circle(win, color, (int(end.x) - int(camPos.x), int(end.y) - int(camPos.y)), int(PhysObj._worms[0].radius) + 3)

class ElectricGrenade(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0,self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (120, 230, 230)
		self.damp = 0.55
		self.timer = 0
		self.worms = []
		self.raons = []
		self.electrifying = False
		self.emptyCounter = 0
		self.lifespan = 300
	def deathResponse(self):
		rad = 20
		boom(self.pos, rad)
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
			for worm in PhysObj._worms:
				if dist(self.pos, worm.pos) < 100:
					self.worms.append(worm)
			for raon in Raon._raons:
				if dist(self.pos, raon.pos) < 100:
					self.raons.append(raon)
			if len(self.worms) == 0 and len(self.raons) == 0:
				self.emptyCounter += 1
				if self.emptyCounter == 30:
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
	def draw(self):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		for worm in self.worms:
			drawLightning(self.pos, worm.pos)
		for raon in self.raons:
			drawLightning(self.pos, raon.pos)

class HomingMissile(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0, 51, 204)
		self.bounceBeforeDeath = 1
		self.windAffected = True
		self.boomRadius = 30
		self.activated = False
		self.timer = 0
	def applyForce(self):
		# gravity:
		global Target
		if self.activated:
			desired = Target - self.pos
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
		if self.timer == 20 + 30*5:
			self.activated = False
	def limitVel(self):
		self.vel.limit(15)
	def outOfMapResponse(self):
		global showTarget
		showTarget = False
	def collisionRespone(self, ppos):
		global showTarget
		showTarget = False
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
	timeTravelList["weapon"] = currentWeapon
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
		self.damp = 0.8
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

class Covid19:
	def __init__(self, pos, angle = vectorUnitRandom().getAngle()):
		PhysObj._reg.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.stable = False
		self.boomAffected = False
		self.radius = 1
		self.angle = angle
		self.target = None
		self.lifespan = 430
		self.unreachable = []
		self.bitten = []
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
			if map.get_at((ppos.vec2tupint())) == GRD:
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
				m.windAffected = False
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
	def step(self):
		if not self.stuck:
			ppos = self.pos + self.vel
			iterations = 15
			for t in range(iterations):
				value = t/iterations
				testPos = (self.pos * value) + (ppos * (1-value))
				if not isOnMap(testPos.vec2tupint()):
					PhysObj._reg.remove(self)
					return
				# check map collision
				if map.get_at(testPos.vec2tupint()) == GRD:
					self.stuck = vectorCopy(testPos)
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
						worm.damage(randint(15,25) if self.sleep else randint(10,20))
						global camTrack
						camTrack = worm
						if self.sleep: worm.sleep = True
						self.destroy()
						return
				# check target collision:
				for target in ShootingTarget._reg:
					if dist(testPos, target.pos) < target.radius:
						target.explode()
						self.destroy()
						return
			self.pos = ppos
		if self.stuck:
			self.pos = self.stuck
			
			points = [(self.pos - self.direction * 10 + i).vec2tupint() for i in self.triangle]
			pygame.draw.polygon(ground, (230,235,240), points)
			pygame.draw.polygon(map, GRD, points)
			
			pygame.draw.line(map, GRD, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
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
		self.windAffected = False
	def secondaryStep(self):
		self.timer += 1
		self.stable = False
		moved = move(self)
		if self.timer % 3 == 0:
			moved = move(self)
		if not moved:
			if isGroundAround(self.pos, self.radius+1):
				self.facing *= -1
		if self.timer % 15 == 0 and isGroundAround(self.pos, self.radius+1):
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
		if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
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
				m.windAffected = False
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
		if self.timer == fuseTime + 60:
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
			drawLightning(self.pos, worm.pos)
		for net in self.network:
			for worm in net[1]:
				drawLightning(net[0].pos, worm.pos)

def firePortal(start, direction):
	steps = 500
	for t in range(5,steps):
		testPos = start + direction * t
		extra.append((testPos.x, testPos.y, (255,255,255), 3))
		
		# missed
		if t == steps - 1:
			if len(Portal._reg) % 2 == 1:
				p = Portal._reg.pop(-1)
				PhysObj._reg.remove(p)

		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue

		# if hits map:
		if map.get_at(testPos.vec2tupint()) == GRD:
			
			response = Vector(0,0)
			
			for i in range(12):
				ti = (i/12) * 2 * pi
				
				check = testPos + Vector(8 * cos(ti), 8 * sin(ti))
				
				if check.x >= mapWidth or check.y >= mapHeight or check.x < 0 or check.y < 0:
					continue
				if map.get_at(check.vec2tupint()) == GRD:
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
		if not map.get_at(self.holdPos.vec2tupint()) == GRD:
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
				map.set_at(self.pos.vec2tupint(), GRD)
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
						
			for worm in PhysObj._reg:
				if worm in Debrie._debries or worm in Portal._reg or worm in Flag.flags:
					continue
				if dist(worm.pos, pos) <= 25:
					
					self.mode = Venus.catch
					if worm in PhysObj._worms:
						global damageThisTurn
						# if not worm == objectUnderControl:
							# if not sentring and not worm in objectUnderControl.team.worms:
								# damageThisTurn += worm.health
						worm.dieded(Worm.causeVenus)
						Commentator.que.append(choice([("", ("yummy",""), worm.team.color), (worm.nameStr, ("", " was delicious"), worm.team.color), (worm.nameStr, ("", " is good protein"), worm.team.color), (worm.nameStr, ("", " is some serious gourmet s**t"), worm.team.color)]))
					else:
						self.explossive = True
						PhysObj._reg.remove(worm)
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
			if self.timer == 30:
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
			if not map.get_at(self.pos.vec2tupint()) == GRD:
				nonPhys.remove(self)
				Venus._reg.remove(self)
		else:
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
			
			if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
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
			# flew out map but not worms !
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
		
		if self.timer >= fuseTime and self.timer <= fuseTime + 60 and not self.hold:
			self.stable = False
			closer = [None, 7000]
			for worm in PhysObj._worms:
				distance = dist(self.pos, worm.pos)
				if distance < closer[1]:
					closer = [worm, distance]
			if closer[1] < 50:
				self.hold = closer[0]
				
		if self.timer == fuseTime + 60:
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
		
		if self.timer <= fuseTime + 60 + 15:
			gameDistable()
		
		# print(self.vel.getMag())
		if self.vel.getMag() < 0.14:
			self.vel *= 0
		self.angle -= self.vel.x*4
	def draw(self):
		if darkness and not isVisibleInDarkness(self):
			return
		surf = pygame.transform.rotate(imagePokeball, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		if self.timer >= fuseTime and self.timer < fuseTime + 60 and self.hold:
			drawLightning(self.pos, self.hold.pos, (255, 255, 204))
		if self.name:
			win.blit(self.name , point2world(self.pos + Vector(-self.name.get_width()/2, -21)))
	
class GreenShell(PhysObj):
	def __init__(self, pos):
		self.ignore = []
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

def fireLaser(start, direction, power=15):
	hit = False
	color = (254, 153, 35)
	square = [Vector(1,5), Vector(1,-5), Vector(-10,-5), Vector(-10,5)]
	for i in square:
		i.rotate(direction.getAngle())
	
	# print(square)
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
		
		# if hits map:
		if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
			if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
			layersCircles[0].append((color, start + direction * 5, 5))
			layersCircles[0].append((color, testPos, 5))
			layersLines.append((color, start + direction * 5, testPos, 10, 1))
			points = []
			for i in square:
				points.append((testPos + i).vec2tupint())
			
			pygame.draw.polygon(map, SKY, points)
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
			if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0:
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
			
			if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				collision = True
			
			r += pi /8
		
		if collision:
			boom(self.pos, 35)
			if randint(0,30) == 1:
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
		self.damp = 0.5
		self.surf = pygame.Surface((3, 8)).convert_alpha()
		self.surf.fill(self.color)
		self.angle = 0
		self.lightRadius = 50
	def secondaryStep(self):
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
			if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0:
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
			
			if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		PhysObj._reg.remove(self)
		
		response.normalize()
		pos = self.pos + response * (objectUnderControl.radius + 2)
		objectUnderControl.pos = pos

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
		# print("im out")
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
		pygame.draw.circle(map, GRD, self.pos, self.radius)
		self.points = [self.pos + vectorFromAngle((i / 11) * 2 * pi) * (self.radius - 2) for i in range(10)]
	def step(self):
		for point in self.points:
			if map.get_at(point.vec2tupint()) != GRD:
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
		amount = 1
		if len(killList) > 0 and killList[0][1] == objectUnderControl.nameStr:
			amount += killList[0][2]
			killList.pop(0)
		string = objectUnderControl.nameStr + ": " + str(amount)
		killList.insert(0, (myfont.render(string, False, HUDColor), objectUnderControl.nameStr, amount))
	def draw(self):
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius))
		pygame.draw.circle(win, RED, point2world(self.pos), int(self.radius - 4))
		pygame.draw.circle(win, WHITE, point2world(self.pos), int(self.radius - 8))

class Distorter(Grenade):
	def deathResponse(self):
		global ground
		width = 150
		arr = []
		for x in range(int(self.pos.x) - width//2, int(self.pos.x) + width//2):
			for y in range(int(self.pos.y) - width//2, int(self.pos.y) + width//2):
				if dist(Vector(x,y), self.pos) > width//2:
					continue
				rot = (dist(Vector(x,y), self.pos) - width//2) * 0.1
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
					map.set_at((x,y), SKY)
				else:
					map.set_at((x,y), GRD)
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
		if self.target:
			self.facing = RIGHT if self.target.pos.x > self.pos.x else LEFT
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
		closest = [PhysObj._worms[0], dist(self.pos, PhysObj._worms[0].pos)]
		for worm in PhysObj._worms:
			distance = dist(worm.pos, self.pos)
			if distance < closest[1]:
				closest = [worm, distance]
		if closest[1] < 100:
			self.target = closest[0]
			self.state = Raon.pointing
		else:
			self.state = Raon.idle
	def advance(self):
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

################################################################################ Create World

maps = []
for i in range(1,101 + 1):
	string = "wormsMaps/wMap" + str(i) + ".png"
	maps.append((string, 512))
if True:
	maps.append(("wormsMaps/wMapbig1.png", 1000))
	maps.append(("wormsMaps/wMapbig2.png", 800))
	maps.append(("wormsMaps/wMapbig3.png", 800))
	maps.append(("wormsMaps/wMapbig4.png", 800))
	maps.append(("wormsMaps/wMapbig5.png", 800))
	maps.append(("wormsMaps/wMapbig6.png", 700))
	maps.append(("wormsMaps/wMapbig7.png", 800))
	maps.append(("wormsMaps/wMapbig8.png", 800))
	maps.append(("wormsMaps/wMapbig9.png", 800))
	maps.append(("wormsMaps/wMapbig10.png", 800))
	maps.append(("wormsMaps/wMapbig11.png", 800))
	maps.append(("wormsMaps/wMapbig12.png", 800))
	maps.append(("wormsMaps/wMapbig13.png", 1000))
	maps.append(("wormsMaps/wMapbig14.png", 800))
	maps.append(("wormsMaps/wMapbig15.png", 800))
	maps.append(("wormsMaps/wMapbig16.png", 2000))
if webVer:
	maps = [("wormsMaps/wMapbig1.png", 1000),("wormsMaps/wMap18.png", 512),("wormsMaps/wMap11.png", 512),("wormsMaps/wMap12.png", 512)]

def createWorld():
	global mapClosed
	if mapChoice == -555:
		imageChoice = choice(maps)
	else:
		imageChoice = maps[mapChoice - 1]
	# imageChoice = ("wormsMaps/race2.png", 900)
	
	if not webVer:
		if imageChoice in [maps[i] for i in [19-1, 26-1, 40-1, 41-1, 64-1]]: mapClosed = True
		if imageChoice[0] == "wormsMaps/wMapbig8.png": mapClosed = True
	imageFile, heightNorm = imageChoice
	
	global mapImage
	mapImage = pygame.image.load(imageFile)
	if not diggingMatch: createMapImage(heightNorm)
	else: mapImage = None; createMapDigging()
	renderLand()

import argparse
if True:
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-f", "--forts", type=bool, nargs='?', const=True, default=False, help="Activate forts mode.")
	parser.add_argument("-dvg", "--dvg", type=bool, nargs='?', const=True, default=False, help="Activate DvG mode.")
	parser.add_argument("-ih", "--initial_health", default=100, help="Initial health", type=int)
	parser.add_argument("-dig", "--digging", type=bool, nargs='?', const=True, default=False, help="Activate Digging mode.")
	parser.add_argument("-dark", "--darkness", type=bool, nargs='?', const=True, default=False, help="Activate Darkness mode.")
	parser.add_argument("-pm", "--pack_mult", default=1, help="Number of packs", type=int)
	parser.add_argument("-wpt", "--worms_per_team", default=8, help="Worms per team", type=int)
	parser.add_argument("-map", "--map_choice", default=-555, help="world map", type=int)
	parser.add_argument("-points", "--points_mode", type=bool, nargs="?", const=True, default=False, help="Activate Points mode.")
	parser.add_argument("-used", "--used_list", type=bool, nargs="?", const=True, default=False, help="Activate Used List mode.")
	parser.add_argument("-closed", "--closed_map", type=bool, nargs="?", const=True, default=False, help="Activate closed map mode.")
	parser.add_argument("-ctf", "--ctf", type=bool, nargs='?', const=True, default=False, help="Activate captureTheFlag mode.")
	parser.add_argument("-targets", "--targets", type=bool, nargs='?', const=True, default=False, help="Activate shooting targets mode.")
	
	args = parser.parse_args()
	
	davidAndGoliathMode = args.dvg
	fortsMode = args.forts
	initialHealth = args.initial_health
	diggingMatch = args.digging
	darkness = args.darkness
	packMult = args.pack_mult
	wormsPerTeam = args.worms_per_team
	mapChoice = args.map_choice
	pointsMode = args.points_mode
	useListMode = args.used_list
	mapClosed = args.closed_map
	captureTheFlag = args.ctf
	targetsMode = args.targets

# drawHealthBar = False
# randomPlace = False
# moreWindAffected = True

################################################################################ Weapons setup

weapons = []
if True:
	weapons.append(["missile", CHARGABLE, -1, MISSILES, False, 0])
	weapons.append(["gravity missile", CHARGABLE, 5, MISSILES, False, 0])
	weapons.append(["bunker buster", CHARGABLE, 2, MISSILES, False, 0])
	weapons.append(["homing missile", CHARGABLE, 2, MISSILES, False, 0])
	weapons.append(["artillery assist", CHARGABLE, 1, MISSILES, False, 0])
	weapons.append(["grenade", CHARGABLE, 5, GRENADES, True, 0])
	weapons.append(["mortar", CHARGABLE, 3, GRENADES, True, 0])
	weapons.append(["sticky bomb", CHARGABLE, 3, GRENADES, True, 0])
	weapons.append(["gas grenade", CHARGABLE, 5, GRENADES, True, 0])
	weapons.append(["electric grenade", CHARGABLE, 3, GRENADES, True, 0])
	weapons.append(["raon launcher", CHARGABLE, 2, GRENADES, False, 0])
	weapons.append(["shotgun", GUN, 5, GUNS, False, 0])
	weapons.append(["minigun", GUN, 6, GUNS, False, 0])
	weapons.append(["gamma gun", GUN, 3, GUNS, False, 0])
	weapons.append(["long bow", GUN, 3, GUNS, False, 0])
	weapons.append(["laser gun", GUN, 3, GUNS, False, 0])
	weapons.append(["portal gun", GUN, 0, GUNS, False, 0])
	weapons.append(["petrol bomb", CHARGABLE, 5, FIREY, False, 0])
	weapons.append(["flame thrower", PUTABLE, 5, FIREY, False, 0])
	weapons.append(["mine", PUTABLE, 5, GRENADES, False, 0])
	weapons.append(["TNT", PUTABLE, 1, GRENADES, False, 0])
	weapons.append(["covid 19", PUTABLE, 0, GRENADES, False, 0])
	weapons.append(["sheep", PUTABLE, 1, GRENADES, False, 0])
	weapons.append(["baseball", PUTABLE, 3, MISC, False, 0])
	weapons.append(["girder", CLICKABLE, -1, MISC, False, 0])
	weapons.append(["rope", PUTABLE, 3, MISC, False, 0])
	weapons.append(["parachute", PUTABLE, 3, MISC, False, 0])
	weapons.append(["venus fly trap", CHARGABLE, 1, MISC, False, 0])
	weapons.append(["sentry turret", PUTABLE, 0, MISC, False, 0])
	weapons.append(["ender pearl", CHARGABLE, 0, MISC, False, 0])
	weapons.append(["airstrike", CLICKABLE, 1, AIRSTRIKE, False, 8])
	weapons.append(["napalm strike", CLICKABLE, 1, AIRSTRIKE, False, 8])
	weapons.append(["mine strike", CLICKABLE, 0, AIRSTRIKE, False, 8])
	weapons.append(["holy grenade", CHARGABLE, 0, LEGENDARY, True, 1])
	weapons.append(["banana", CHARGABLE, 0, LEGENDARY, True, 1])
	weapons.append(["earthquake", PUTABLE, 0, LEGENDARY, False, 1])
	weapons.append(["gemino mine", CHARGABLE, 0, LEGENDARY, False, 1])
	weapons.append(["bee hive", CHARGABLE, 0, LEGENDARY, False, 1])
	weapons.append(["vortex grenade", CHARGABLE, 0, LEGENDARY, True, 1])
	weapons.append(["chilli pepper", CHARGABLE, 0, LEGENDARY, False, 1])
	weapons.append(["raging bull", PUTABLE, 0, LEGENDARY, False, 1])
	weapons.append(["electro boom", CHARGABLE, 0, LEGENDARY, True, 1])
	weapons.append(["pokeball", CHARGABLE, 0, LEGENDARY, True, 1])
	weapons.append(["green shell", PUTABLE, 0, LEGENDARY, False, 1])
	weapons.append(["guided missile", PUTABLE, 0, LEGENDARY, False, 1])

weaponDict = {}
basicSet = []

def fire(weapon = None):
	global decrease, shotCount, nextState, state, camTrack, fireWeapon, energyLevel, energising, timeTravelFire, currentWeapon
	if not weapon:
		weapon = currentWeapon
	decrease = True
	if objectUnderControl:
		weaponOrigin = vectorCopy(objectUnderControl.pos)
		weaponDir = vectorFromAngle(objectUnderControl.shootAngle)
		#weaponOrigin += weaponDir * (objectUnderControl.radius + 3)
		energy = energyLevel
		# cheating
		if objectUnderControl.cpu:
			energy = CpuHolder.energy
			weaponDir = CpuHolder.direction
		
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
		currentTeam.utilityCounter[utilityDict["flare"]] -= 1
		nextState = PLAYER_CONTROL_1
		decrease = False
		renderWeaponCount(True)
	elif weapon == "ender pearl":
		w = EndPearl(weaponOrigin, weaponDir, energy)
		nextState = PLAYER_CONTROL_1
	elif weapon == "raon launcher":
		w = Raon(weaponOrigin, weaponDir, energy * 0.95)
		w = Raon(weaponOrigin, weaponDir, energy * 1.05)
		if randint(0, 10) == 0 or megaTrigger:
			w = Raon(weaponOrigin, weaponDir, energy * 1.08)
			w = Raon(weaponOrigin, weaponDir, energy * 0.92)
	
	if w and not timeTravelFire: camTrack = w	
	
	# position to available position
	if w and avail:
		availpos = getClosestPosAvail(w)
		if availpos:
			w.pos = availpos
	
	if decrease:
		currentTeam.weaponCounter[weaponDict[weapon]] -= 1
		renderWeaponCount()

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
		addToUseList(currentWeapon)

def fireClickable():
	global currentWeapon, state
	decrease = True
	if len(Menu.menus) > 0 or inUsedList(currentWeapon) :
		return
	
	if currentWeapon == "girder":
		girder((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))

	elif currentWeapon == "teleport":
		currentTeam.utilityCounter[utilityDict["teleport"]] -= 1
		currentWeapon = "missile"
		weaponStyle = weapons[weaponDict[currentWeapon]][1]
		objectUnderControl.pos = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
		timeRemaining(retreatTime)
		state = nextState
		return
	
	elif currentWeapon == "airstrike" and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
		fireAirstrike((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
	elif currentWeapon == "mine strike" and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
		fireMineStrike((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
	elif currentWeapon == "napalm strike" and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
		fireNapalmStrike((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
	
	if decrease:
		currentTeam.weaponCounter[weaponDict[currentWeapon]] -= 1
	
	if useListMode and (nextState == PLAYER_CONTROL_2 or nextState == WAIT_STABLE):
		addToUseList(currentWeapon)
	
	renderWeaponCount()
	timeRemaining(retreatTime)
	state = nextState

for i in range(len(weapons)):
	weaponDict[weapons[i][0]] = i
	weaponDict[i] = weapons[i][0]
	if not unlimitedMode: basicSet.append(weapons[i][2])
	else: basicSet.append(-1)
	
utilities = []
if True:
	utilities.append(["moon gravity"])
	utilities.append(["double damage"])
	utilities.append(["aim aid"])
	utilities.append(["teleport"])
	utilities.append(["switch worms"])
	utilities.append(["time travel"])
	utilities.append(["jet pack"])
	utilities.append(["flare"])

utilityDict = {}
for i in range(len(utilities)):
	utilityDict[utilities[i][0]] = i
	utilityDict[i] = utilities[i][0]

################################################################################ Teams
class Team:
	def __init__(self, namesList, color, name = "", cpu = False):
		self.nameList = namesList
		self.color = color
		self.weaponCounter = basicSet.copy()
		self.utilityCounter = [0] * len(utilities)
		self.worms = []
		self.name = name
		self.cpu = cpu
		self.damage = 0
		self.killCount = 0
		self.points = 0
		self.flagHolder = False
	def __len__(self):
		return len(self.worms)
	def addWorm(self, pos):
		if len(self.nameList) > 0:
			w = Worm(pos, self.nameList.pop(0), self)
			self.worms.append(w)
			w.cpu = self.cpu
	def saveStr(self):
		string = ""
		string += "color" + list2str(self.color) + "\n"
		string += "weaponCounter" + list2str(self.weaponCounter) + "\n"
		string += "utilityCounter" + list2str(self.utilityCounter) + "\n"
		string += "worms:" + "\n"
		for worm in self.worms:
			string += worm.saveStr()
		return string

blues = Team(["red lion", "commercial", "swan", "brewers", "fred", "sparrow", "eithan", "reed"], BLUE, "blue")
reds = Team(["fix delux r", "vamp b", "birdie", "lordie", "pinkie", "katie", "angie", "miya"], RED, "red")
greens = Team(["blair", "major", "thatcher", "chellenge", "george", "mark", "mercury", "philip"], GREEN, "green")
yellows = Team(["colan", "GT", "jettets", "chevan", "jonie", "murph", "silvia", "flur"], YELLOW, "yellow")

# choose teams:
teams = [blues, greens, reds, yellows]

totalTeams = len(teams)

currentTeam = None
teamChoser = 0
roundCounter = 0
mostDamage = (0,None)
damageThisTurn = 0

nWormsPerTeam = 0
teamsInfo = []
if unlimitedMode:
	for team in teams:
		team.utilityCounter = [99] * len(utilities)
	for weapon in weapons:
		weapon[5] = 0

def renderWeaponCount(special = False):
	global currentTeam, currentWeapon, currentWeaponSurf
	if not special:
		try:
			if currentTeam.weaponCounter[weaponDict[currentWeapon]] < 0:
				currentWeaponSurf = myfont.render(currentWeapon, False, HUDColor)
			else:
				currentWeaponSurf = myfont.render(currentWeapon + " " + str(currentTeam.weaponCounter[weaponDict[currentWeapon]]), False, HUDColor)
		except KeyError:
			currentWeapon = "missile"
			currentWeaponSurf = myfont.render(currentWeapon, False, HUDColor)
		
		if weapons[weaponDict[currentWeapon]][4]:
			delayAdd = myfont.render("delay: " + str(fuseTime//30), False, HUDColor)
			surf = pygame.Surface((currentWeaponSurf.get_width() + delayAdd.get_width() + 10, currentWeaponSurf.get_height()), pygame.SRCALPHA)
			surf.blit(currentWeaponSurf, (0,0))
			surf.blit(delayAdd, (currentWeaponSurf.get_width() + 10,0))
			currentWeaponSurf = surf
		
		return
	if currentWeapon == "teleport":
		currentWeaponSurf = myfont.render(currentWeapon + " " + str(currentTeam.utilityCounter[utilityDict["teleport"]]), False, HUDColor)
	if currentWeapon == "flare":
		currentWeaponSurf = myfont.render(currentWeapon + " " + str(currentTeam.utilityCounter[utilityDict["flare"]]), False, HUDColor)
	
def calculateTeamHealth():
	global teamsInfo
	teamsInfo = []
	maxHealth = nWormsPerTeam * initialHealth
	if davidAndGoliathMode:
		maxHealth = int(initialHealth/(1+0.5*(nWormsPerTeam - 1))) * nWormsPerTeam
	for i in range(totalTeams):
		team = teams[i]
		health = 0
		for worm in team.worms:
			health += worm.health
		teamsInfo.append(health)
	
def teamHealthDraw():
	if diggingMatch:
		return
	maxHealth = nWormsPerTeam * initialHealth
	if davidAndGoliathMode:
		maxHealth = int(initialHealth/(1+0.5*(nWormsPerTeam - 1))) * nWormsPerTeam
		
	maxPoints = sum([i.points for i in teams])
	
	for i in range(totalTeams):
		pygame.draw.rect(win, (220,220,220), (int(winWidth-50),int(10+i*3) , 40,2))
		value = min(teamsInfo[i]/maxHealth, 1)*40
		if value < 1 and value > 0:
			value = 1
		if not value <= 0:
			pygame.draw.rect(win, teams[i].color, (int(winWidth-50), int(10+i*3), int(value),2))
		
		if pointsMode or captureTheFlag or targetsMode:
			if maxPoints == 0:
				continue
			value = (teams[i].points / maxPoints) * 40
			if value < 1 and value > 0:
				value = 1
			if not value == 0:
				pygame.draw.rect(win, (220,220,220), (int(winWidth-50) - 1 - int(value), int(10+i*3), int(value), 2))
			if captureTheFlag:
				if teams[i].flagHolder:
					pygame.draw.circle(win, (220,0,0), (int(winWidth-50) - 1 - int(value) - 4, int(10+i*3) + 1) , 2)

def checkWinners():
	global mostDamage, run, camTrack, nextState
	count = 0
	end = False
	winningTeam = None
	for team in teams:
		if len(team.worms) == 0:
			count += 1
	if count == totalTeams:
		# all dead
		end = True
		print("everyone dead")
		run = False
		return end
	elif count == totalTeams - 1:
		# someone won
		
		if captureTheFlag:
			for team in teams:
				if team.flagHolder:
					team.points += 1 + 3 #3 points bonus for surviving team
					break
		
		end = True
		adding = ""
					 
		# won in points mode:
		if pointsMode:
			lastTeam = None
			for team in teams:
				if not len(team.worms) == 0:
					lastTeam = team
			if lastTeam:
				lastTeam.points += 150
				# find winners:
				teamsFinals = sorted(teams, key = lambda x: x.points)
				winningTeam = teamsFinals[-1]
			adding += "points: " + str(winningTeam.points)
		
		# won in capture the flag mode:
		elif captureTheFlag:
			teamsFinals = sorted(teams, key = lambda x: x.points)
			if teamsFinals[-1].points == teamsFinals[-2].points:
				# tie. pick one at chance
				winningTeam = teamsFinals[-1]
			else:
				winningTeam = teamsFinals[-1]
			adding += "CTF mode"
				
		# regular win:
		else:
			for team in teams:
				if not len(team.worms) == 0:
					winningTeam = team
					if davidAndGoliathMode:
						adding += "_dVg_"
					
	if targetsMode:
		if len(ShootingTarget._reg) == 0 and ShootingTarget.numTargets <= 0:
			end = True
			currentTeam.points += 3
			teamsFinals = sorted(teams, key = lambda x: x.points)
			winningTeam = teamsFinals[-1]
			adding = "Targets mode"
	
	if end:
		string = "time taken: " + '{:6}'.format(str(int(timeOverall/30))) + " winner: " + '{:10}'.format(winningTeam.name)
		if mostDamage[1]:
			string += "most damage: " + '{:6}'.format(int(mostDamage[0])) +" by " + '{:20}'.format(mostDamage[1])
		string += adding + "\n"
	
		file = open('wormsRecord.txt', 'a')
		file.write(string)
		file.close()
		
		commentator.que.append((winningTeam.name, ("taem "," won!"), winningTeam.color))
		print("team", winningTeam.name, "won!")
		if len(winningTeam.worms) > 0:
			camTrack = winningTeam.worms[0]
		nextState = WIN
		pygame.image.save(ground, "lastWormsGround.png")
	return end

def cycleWorms():
	global objectUnderControl, camTrack, currentTeam, run, nextState, roundCounter, mostDamage, damageThisTurn, currentWeapon
	global deploying, sentring, deployPacks, showTarget, switchingWorms, raoning

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
		objectUnderControl.team.weaponCounter[weaponDict["rope"]] -= 1
		Worm.roped = False
	
	# update cpu:
	#cpuUpdateCycle()
	
	# update damage:
	if damageThisTurn > mostDamage[0]:
		mostDamage = (damageThisTurn, objectUnderControl.nameStr)	
	if damageThisTurn > int(initialHealth * 2.5):
		Commentator.que.append((objectUnderControl.nameStr, choice([("awesome shot ", "!"), ("", " is on fire!"), ("", " shows no mercy")]), objectUnderControl.team.color))
	elif damageThisTurn > int(initialHealth * 1.5):
		Commentator.que.append((objectUnderControl.nameStr, choice([("good shot ", "!"), ("nicely done ","")]), objectUnderControl.team.color))
	
	currentTeam.damage += damageThisTurn
	if pointsMode:
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
				team.utilityCounter[utilityDict["flare"]] += 1
				if team.utilityCounter[utilityDict["flare"]] > 3:
					team.utilityCounter[utilityDict["flare"]] = 3
		return
		
	raoning = False
	deploying = False
	sentring = False
	
	if captureTheFlag:
		for team in teams:
			if team.flagHolder:
				team.points += 1
				break
	
	# update weapons delay (and targets)
	if roundCounter % totalTeams == 0:
		for weapon in weapons:
			if not weapon[5] == 0:
				weapon[5] -= 1
		if targetsMode:
			ShootingTarget.numTargets -= 1
			if ShootingTarget.numTargets == 0:
				commentator.que.append(("", ("final targets round",""), (0,0,0)))
	
	# update debries
	Debrie._debries = []
	
	showTarget = False
	# change wind:
	global wind
	wind = uniform(-1,1)
	
	# flares reduction
	if darkness:
		for flare in Flare._flares:
			if not flare in PhysObj._reg:
				Flare._flares.remove(flare)
			flare.lightRadius -= 10
	
	index = teams.index(currentTeam)
	index = (index + 1) % totalTeams
	currentTeam = teams[index]
	
	while not len(currentTeam.worms) > 0:
		index = teams.index(currentTeam)
		index = (index + 1) % totalTeams
		currentTeam = teams[index]
	
	# sick:
	for worm in PhysObj._worms:
		if not worm.sick == 0 and worm.health > 5:
			worm.damage(min(int(5/damageMult)+1, int((worm.health-5)/damageMult) +1), 2)
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
			if map.get_at(at) == GRD or wormCol.get_at(at) != (0,0,0) or extraCol.get_at(at) != (0,0,0):
				return True
		except IndexError:
			print("isGroundAround index error")
			
	return False

def randomPlacing(wormsPerTeam):
	global lstep
	for i in range(wormsPerTeam * len(teams)):
		if fortsMode:
			place = giveGoodPlace(i)
		else:
			place = giveGoodPlace()
		if diggingMatch:
			pygame.draw.circle(map, SKY, place, 35)
			pygame.draw.circle(ground, SKY, place, 35)
		global teamChoser
		teams[teamChoser].addWorm(place.vec2tup())
		teamChoser = (teamChoser + 1) % totalTeams
		lstepper()#
	global state
	state = nextState

class Menu:
	menus = []
	border = 1
	textColor = BLACK
	TextColorInnactive = (170,170,170)
	backColor = BLACK
	width = 100
	def __init__(self, winPos):
		Menu.menus.append(self)
		self.winPos = vectorCopy(winPos)
		self.elements = []
		self.buttons = []
		self.currentHeight = 1
		self.dims = [0,0]
	def updateWinPos(self, pos):
		self.winPos[0] = pos[0]
		self.winPos[1] = pos[1]
	def addString(self, string):
		self.elements.append(MenuString(string, self.winPos + Vector(Menu.border, self.currentHeight)))
		self.currentHeight += self.elements[-1].height + Menu.border
		self.dims[0] = max(self.dims[0], self.elements[-1].width + 2 * Menu.border)
		self.dims[1] = self.currentHeight + Menu.border
	def addButton(self, text, secText, bColor, active, action):
		b = Button(text, secText, bColor, self.winPos, Vector(Menu.border, self.currentHeight), active, action)
		self.elements.append(b)
		self.buttons.append(b)
		self.currentHeight += self.elements[-1].height + Menu.border
		self.dims[0] = max(self.dims[0], self.elements[-1].width + 2 * Menu.border)
		self.dims[1] = self.currentHeight
	def step(self):
		for element in self.elements:
			element.step()
	def draw(self):
		pygame.draw.rect(win, Menu.backColor, (self.winPos, self.dims))
		for e in self.elements:
			e.draw()
	def destroy(self):
		Menu.menus.remove(self)
	
class MenuString:
	def __init__(self, string, winPos):
		self.winPos = winPos
		self.surf = myfont.render(string, False, BLACK)
		self.width = self.surf.get_width()
		self.height = self.surf.get_height()
	def draw(self):
		win.blit(self.surf, self.winPos)
	
class Button:
	globalButtonHeight = 8
	def __init__(self, text, secText, bColor, winPos, offset, active, action):
		self.text = text
		self.selected = False
		self.secText = secText
		self.surf = myfont.render(text, False, Menu.textColor if active else Menu.TextColorInnactive)
		self.secSurf = myfont.render(secText, False, Menu.textColor if active else Menu.TextColorInnactive)
		self.width = Menu.width + Menu.border * 2
		self.height = self.surf.get_height() + Menu.border * 2
		self.winPos = winPos
		self.offset = offset
		self.bColor = bColor
		self.active = active
		self.action = action
	def activate(self):
		self.action(self)
	def step(self):
		mousePos = (pygame.mouse.get_pos()[0]/scalingFactor, pygame.mouse.get_pos()[1]/scalingFactor)
		if mousePos[0] > self.winPos[0] + self.offset[0] and mousePos[0] < self.winPos[0] + self.offset[0] + self.width and mousePos[1] > self.winPos[1] + self.offset[1] and mousePos[1] < self.winPos[1] + self.offset[1] + self.height:
			self.selected = True
		else:
			self.selected = False
	def draw(self):
		pygame.draw.rect(win, RED if self.selected else self.bColor, (self.winPos + self.offset, (self.width, self.height)))
		win.blit(self.surf, self.winPos + self.offset + Vector(Menu.border,Menu.border))
		win.blit(self.secSurf, self.winPos + self.offset + Vector(Menu.width - 10, Menu.border))

def actionWeaponButton(button):
	global currentWeapon, weaponStyle
	currentWeapon = weapons[weaponDict[button.text]][0]
	renderWeaponCount()
	weaponStyle = weapons[weaponDict[currentWeapon]][1]

def actionUtilityButton(button):
	global currentWeapon, weaponStyle
	utility = button.text
	decrease = True
	
	if utility == "moon gravity":
		global globalGravity
		globalGravity = 0.1
	elif utility == "double damage":
		global damageMult, radiusMult
		damageMult += damageMult
		radiusMult *= 1.5
	elif utility == "aim aid":
		global aimAid
		aimAid = True
	elif utility == "teleport":
		currentWeapon = "teleport"
		weaponStyle = CLICKABLE
		decrease = False
		renderWeaponCount(True)
	elif utility == "switch worms":
		global switchingWorms
		if switchingWorms:
			decrease = False
		switchingWorms = True
	elif utility == "time travel":
		global timeTravel
		if not timeTravel:
			timeTravelInitiate()
	elif utility == "jet pack":
		objectUnderControl.toggleJetpack()
	elif utility == "flare":
		currentWeapon = "flare"
		weaponStyle = CHARGABLE
		decrease = False
		renderWeaponCount(True)
		
	if decrease:
		currentTeam.utilityCounter[utilityDict[utility]] -= 1

def weaponMenuInit():
	count = 0
	m = Menu((winWidth - Menu.width - 2 * Menu.border, 0))
	for i in range(len(weapons)):
		if currentTeam.weaponCounter[i] != 0:
			secText = str(currentTeam.weaponCounter[i]) if currentTeam.weaponCounter[i] > -1 else ""
			active = weapons[i][5] == 0
			if inUsedList(weapons[i][0]):
				active = False
			m.addButton(weapons[i][0], secText, weapons[i][3], active, actionWeaponButton)
	
	if sum(currentTeam.utilityCounter) == 0:
		return
	m2 = Menu((winWidth - 2 * Menu.width - 4 * Menu.border - 1, 0))
	for i in range(len(utilities)):
		if currentTeam.utilityCounter[i] != 0:
			secText = str(currentTeam.utilityCounter[i])
			m2.addButton(utilities[i][0], secText, WHITE, True, actionUtilityButton)

def scrollMenu(up = True):
	menu = Menu.menus[0]
	if up:
		if menu.winPos[1] >= 0:
			return
	else:
		if menu.winPos[1] + menu.dims[1] <= winHeight:
			return
	menu.winPos[1] += Button.globalButtonHeight * 5 if up else -Button.globalButtonHeight * 5

class Cloud:
	_reg = []
	cWidth = imageCloud.get_width()
	def __init__(self, pos):
		self._reg.append(self)
		self.pos = Vector(pos[0],pos[1])
		self.vel = Vector(0,0)
		self.acc = Vector(0,0)
	def step(self):
		self.acc.x = wind
		self.vel += self.acc
		self.vel *= 0.85
		self.pos += self.vel
		
		if self.pos.x > camPos.x + winWidth + 100 or self.pos.x < camPos.x - 100 - self.cWidth:
			self._reg.remove(self)
			del self
	def draw(self):
		win.blit(imageCloud, (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)))

def cloud_maneger():
	if len(Cloud._reg) < 8 and randint(0,10) == 1:
		pos = Vector(choice([camPos.x - Cloud.cWidth - 100, camPos.x + winWidth + 100]), randint(5, mapHeight - 150))
		Cloud(pos)

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
			self.timer = 2*30 + 1*15
		elif self.mode == Commentator.SHOW:
			win.blit(self.textSurf, (int(winWidth/2 - self.textSurf.get_width()/2), 10))
			
			self.timer -= 1
			if self.timer == 0:
				self.mode = Commentator.WAIT
commentator = Commentator()

def saveGame():
	file = open("wormsSave.txt", 'w')
	# team parameters:
	for team in teams:
		file.write("team:\n")
		string = team.saveStr()
		file.write(string + "\n")
	# world parameters:
	file.write(str(camPos) + "\n")
	file.write(str(camTarget) + "\n")
	# object under controll
	# camTrack
	file.write(str(currentWeapon) + "\n")
	file.write(str(weaponStyle) + "\n")
	file.write(str(wind) + "\n")
	file.write(str(aimAid) + "\n")
	
	file.write("map:\n")
	file.write(str(mapWidth) + " " + str(mapHeight))
	mapSave = pygame.image.tostring(map, 'RGBA')
	file.write(str(mapSave) + "\n")
	groundSave = pygame.image.tostring(ground, 'RGBA')
	file.write(str(groundSave) + "\n")
	
	file.write("state:\n")
	file.write(str(state) + "\n")
	file.write(str(nextState) + "\n")
	file.write(str(gameStable) + "\n")
	file.write(str(playerScrollAble) + "\n")
	file.write(str(playerControlPlacing) + "\n")
	file.write(str(playerShootAble) + "\n")
	
	file.write("\n")
	file.write(str(totalTeams) + "\n")
	file.write(str(teamChoser) + "\n")
	file.write(str(roundCounter) + "\n")
	file.write(str(mostDamage) + "\n")
	file.write(str(damageThisTurn) + "\n")
	file.write(str(timeOverall) + "\n")
	file.write(str(timeCounter) + "\n")
	
	file.close()

def list2str(_list):
	string = ""
	for i in range(len(_list)):
		string += str(_list[i])
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
	if not mapClosed:
		startingWeapons.append("mine strike")
	if unlimitedMode: return
	for i in range(amount):
		for team in teams:
			effect = choice(startingWeapons)
			team.weaponCounter[weaponDict[effect]] += 1
			if randint(0,2) >= 1:
				effect = choice(["moon gravity", "teleport", "jet pack", "aim aid", "switch worms"])
				team.utilityCounter[utilityDict[effect]] += 1
			if randint(0,7) == 1:
				if randint(0,1) == 0:
					team.weaponCounter[weaponDict["portal gun"]] += 1
				else:
					team.weaponCounter[weaponDict["ender pearl"]] += 3

def randomWeaponsGive():
	for team in teams:
		for i in range(len(team.weaponCounter)):
			if team.weaponCounter[i] == -1:
				continue
			else:
				if randint(0,1) == 1:
					team.weaponCounter[i] = randint(0,5)

def suddenDeath():
	for worm in PhysObj._worms:
		worm.sicken()
		if not worm.health == 1:
			worm.health = worm.health // 2

def moreDigging():
	for team in teams:
		team.weaponCounter[weaponDict["minigun"]] += 5
		team.weaponCounter[weaponDict["bunker buster"]] += 3
		team.weaponCounter[weaponDict["laser gun"]] += 3

def isOnMap(vec):
	return not (vec[0] < 0 or vec[0] >= mapWidth or vec[1] < 0 or vec[1] >= mapHeight)

class Cam:
	pos = Vector()

def cheatActive(code):
	code = code[:-1]
	if code == "gibguns":
		unlimitedMode = True
		for team in teams:
			for i in range(len(team.weaponCounter)):
				team.weaponCounter[i] = -1
			team.utilityCounter = [99] * len(utilities)
		for weapon in weapons:
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
def drawUseList():
	space = 0
	for i in range(len(useList)):
		if i == 0:
			win.blit(useList[i][0], (30 + 80 * i,winHeight - 6))
		else:
			space += useList[i-1][0].get_width() + 10
			win.blit(useList[i][0], (30 + space, winHeight - 6))
def inUsedList(string):
	used = False
	for i in useList:
		if string == i[1]:
			used = True
			break
	return used

damageText = (damageThisTurn, myfont.render(str(int(damageThisTurn)), False, HUDColor))

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
	if state == PLAYER_CONTROL_1:
		mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
		# Ball(mouse)
		
		# for worm in PhysObj._worms:
			# if dist(mouse, worm.pos) < 10:
				# print(worm.nameStr, "sleep")
				# worm.sleep = True
				# break
		p = Path(mouse)
		# print("test")
		pass

################################################################################ State machine
if True:
	RESET = 0; GENERATE_TERRAIN = 1; PLACING_WORMS = 2; CHOOSE_STARTER = 3; PLAYER_CONTROL_1 = 4
	PLAYER_CONTROL_2 = 5; WAIT_STABLE = 6; FIRE_MULTIPLE = 7; WIN = 8
	
	state, nextState = RESET, RESET
	loadingSurf = myfontbigger.render("simon's worms Loading", False, WHITE)
	gameStable = False; playerScrollAble = False; playerControl = False
	playerControlPlacing = False; playerShootAble = False; gameStableCounter = 0

def stateMachine():
	global state, nextState, gameStable, playerControl, playerControlPlacing, playerShootAble, playerScrollAble, currentTeam
	global objectUnderControl, camTrack, gameStableCounter, shotCount, fireWeapon, currentWeapon, run, mapClosed
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
		
		shuffle(teams)
		currentTeam = teams[0]
		teamChoser = teams.index(currentTeam)
		
		# place stuff:
		if not diggingMatch:
			placeMines(randint(2,4))
		if not randomPlace:
			placePetrolCan(randint(2,4))
			# place plants:
			if not diggingMatch:
				placePlants(randint(0,2))
		
		nextState = PLACING_WORMS
		state = nextState
	elif state == PLACING_WORMS: #modes
		playerControlPlacing = True #can move with mouse and place worms, but cant play them
		playerControl = False
		playerScrollAble = True
		
		# place worms:
		if randomPlace:
			randomPlacing(wormsPerTeam)
			nextState = CHOOSE_STARTER
		
		if nextState == CHOOSE_STARTER:
			if randomPlace:
				placePetrolCan(randint(2,4))
				# place plants:
				if not diggingMatch:
					placePlants(randint(0,2))
			
			# targets:
			if targetsMode:
				for i in range(ShootingTarget.numTargets):
					ShootingTarget()
			
			if diggingMatch:
				placeMines(80)
				moreDigging()
				mapClosed = True
				
			# give random legendary starting weapons:
			randomStartingWeapons(1)
			
			if davidAndGoliathMode:
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
				for team in teams:
					team.utilityCounter[utilityDict["flare"]] += 3
			if randomWeapons:
				randomWeaponsGive()
			if captureTheFlag:
				placeFlag()
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
		
		objectUnderControl = w
		camTrack = w
		timeReset()
		calculateTeamHealth()
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
				calculateTeamHealth()
				timeReset()
				cycleWorms()
				renderWeaponCount()
				state = nextState

		nextState = PLAYER_CONTROL_1
	elif state == FIRE_MULTIPLE:
		playerControlPlacing = False
		playerControl = True #can play
		playerShootAble = True
		playerScrollAble = True
		
		if currentWeapon == "flame thrower" or currentWeapon == "minigun" or currentWeapon == "laser gun":
			fireWeapon = True
			if not shotCount == 0:
				nextState = FIRE_MULTIPLE
	elif state == WIN:
		gameStableCounter += 1
		if gameStableCounter == 30*3:
			run = False

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
	if useListMode and inUsedList(currentWeapon):
		return
	if objectUnderControl and playerControl:
		if currentWeapon == "flare":
			if currentTeam.utilityCounter[utilityDict["flare"]] == 0: return
			energising = True
			energyLevel = 0
			fireWeapon = False
			return
		if weaponStyle == CHARGABLE and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
			energising = True
			energyLevel = 0
			fireWeapon = False
			if currentWeapon == "homing missile" and not showTarget:
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
		if timeTravel and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
			timeTravelPlay()
			energyLevel = 0
		elif weaponStyle == CHARGABLE and energising:
			fireWeapon = True
		# putable/gun weapons case
		elif (weaponStyle in [PUTABLE, GUN]) and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0 and not currentWeapon == "rope":
			if useListMode and inUsedList(currentWeapon): return
			fireWeapon = True
			# if objectUnderControl.rope: #rope
				# objectUnderControl.toggleRope(None)
				# fireWeapon = False
			playerShootAble = False
		# rope case:
		elif (weaponStyle in [PUTABLE, GUN]) and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0 and currentWeapon == "rope":
			# if not currently roping:
			fireWeapon = True
			playerShootAble = False
			# if currently roping:
			if objectUnderControl.rope: #rope
				objectUnderControl.toggleRope(None)
				fireWeapon = False
		energising = False
	elif objectUnderControl.rope:
		objectUnderControl.toggleRope(None)
	elif objectUnderControl.parachuting:
		objectUnderControl.toggleParachute()

################################################################################ Setup

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
if webVer:
	makeRandomTeams(4, 4, namesCustom + namesCustom2)

################################################################################ Main Loop

if __name__ == "__main__":

	run = True
	pause = False
	while run:
		fpsClock.tick(30)
		
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
				if state == PLAYER_CONTROL_1 and weaponStyle == CLICKABLE:
					fireClickable()
				if state == PLAYER_CONTROL_1 and currentWeapon == "homing missile":
					Target.x, Target.y = mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y
					showTarget = True
				# cliking in menu
				if len(Menu.menus) > 0:
					buttonPressed = False
					for menu in Menu.menus:
						for button in menu.buttons:
							if button.selected and button.active:
								button.activate()
								buttonPressed = True
								break
					if buttonPressed:
						while len(Menu.menus) > 0:
							Menu.menus[0].destroy()
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)\
				# testing mainly
				testerFunc()
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
				# this is the next state after placing all worms
				if state == PLACING_WORMS:
					nextState = CHOOSE_STARTER
					# state = nextState
					renderWeaponCount()
				elif state == PLAYER_CONTROL_1:
					if len(Menu.menus) == 0:
						weaponMenuInit()
					else:
						while len(Menu.menus) > 0:
							Menu.menus[0].destroy()
						
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll up
				if len(Menu.menus) > 0:
					scrollMenu()
				else:
					scalingFactor *= 1.1
					if scalingFactor >= 3: scalingFactor = 3
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll down
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
						# jump
						if objectUnderControl.stable and objectUnderControl.health > 0:
							objectUnderControl.vel += Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle)) * 3
							objectUnderControl.stable = False
					if event.key == pygame.K_RIGHT:
						# objectUnderControl.facing = RIGHT
						# if objectUnderControl.shootAngle >= pi/2 and objectUnderControl.shootAngle <= (3/2)*pi:
							# objectUnderControl.shootAngle = pi - objectUnderControl.shootAngle
						# camTrack = objectUnderControl
						onKeyPressRight()
					if event.key == pygame.K_LEFT:
						# objectUnderControl.facing = LEFT
						# if objectUnderControl.shootAngle >= -pi/2 and objectUnderControl.shootAngle <= pi/2:
							# objectUnderControl.shootAngle = pi - objectUnderControl.shootAngle
						# camTrack = objectUnderControl
						onKeyPressLeft()
				# fire on key press
				if event.key == pygame.K_SPACE:
					# if objectUnderControl and playerControl:
						# if weaponStyle == CHARGABLE and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
							# energising = True
							# energyLevel = 0
							# fireWeapon = False
							# if currentWeapon == "homing missile" and not showTarget:
								# energising = False
					# if Sheep.trigger == False:
						# Sheep.trigger = True
					onKeyPressSpace()
				# weapon change by keyboard
				if state == PLAYER_CONTROL_1:
					weaponsSwitch = False
					if event.key == pygame.K_1:
						currentWeapon = "missile"
						weaponsSwitch = True
					elif event.key == pygame.K_2:
						currentWeapon = "grenade"
						weaponsSwitch = True
					elif event.key == pygame.K_3:
						currentWeapon = "mortar"
						weaponsSwitch = True
					elif event.key == pygame.K_4:
						currentWeapon = "petrol bomb"
						weaponsSwitch = True
					elif event.key == pygame.K_5:
						currentWeapon = "TNT"
						weaponsSwitch = True
					elif event.key == pygame.K_6:
						currentWeapon = "shotgun"
						weaponsSwitch = True
					elif event.key == pygame.K_7:
						currentWeapon = "girder"
						weaponsSwitch = True
					elif event.key == pygame.K_8:
						currentWeapon = "flame thrower"
						weaponsSwitch = True
					elif event.key == pygame.K_9:
						currentWeapon = "sticky bomb"
						weaponsSwitch = True
					elif event.key == pygame.K_0:
						currentWeapon = "minigun"
						weaponsSwitch = True
					elif event.key == pygame.K_MINUS:
						currentWeapon = "rope"
						weaponsSwitch = True
					elif event.key == pygame.K_EQUALS:
						currentWeapon = "parachute"
						weaponsSwitch = True
					if weaponsSwitch:
						weaponStyle = weapons[weaponDict[currentWeapon]][1]
						renderWeaponCount()
				# misc
				if event.key == pygame.K_p:
					pause = not pause
				if event.key == pygame.K_TAB:
					if state == PLAYER_CONTROL_1 and currentWeapon == "bunker buster":
						BunkerBuster.mode = not BunkerBuster.mode
						if BunkerBuster.mode:
							FloatingText(objectUnderControl.pos + Vector(0,-5), "drill mode", (20,20,20))
						else:
							FloatingText(objectUnderControl.pos + Vector(0,-5), "rocket mode", (20,20,20))
					elif state == PLAYER_CONTROL_1 and currentWeapon == "venus fly trap":
						PlantBomb.venus = not PlantBomb.venus
						if PlantBomb.venus:
							FloatingText(objectUnderControl.pos + Vector(0,-5), "venus fly trap", (20,20,20))
						else:
							FloatingText(objectUnderControl.pos + Vector(0,-5), "plant mode", (20,20,20))
					elif state == PLAYER_CONTROL_1 and currentWeapon == "long bow":
						LongBow._sleep = not LongBow._sleep
						if LongBow._sleep:
							FloatingText(objectUnderControl.pos + Vector(0,-5), "sleeping", (20,20,20))
						else:
							FloatingText(objectUnderControl.pos + Vector(0,-5), "regular", (20,20,20))
					elif state == PLAYER_CONTROL_1 and weapons[weaponDict[currentWeapon]][4]:
						fuseTime += 30
						if fuseTime > 120:
							fuseTime = 30
						string = "delay " + str(fuseTime//30) + " sec"
						FloatingText(objectUnderControl.pos + Vector(0,-5), string, (20,20,20))
						renderWeaponCount()
					elif state == PLAYER_CONTROL_1 and currentWeapon == "girder":
						girderAngle += 45
						if girderAngle == 180:
							girderSize = 100
						if girderAngle == 360:
							girderSize = 50
							girderAngle = 0
					elif state == PLAYER_CONTROL_1 and weapons[weaponDict[currentWeapon]][3] == AIRSTRIKE:
						airStrikeDir *= -1
					elif (state == PLAYER_CONTROL_1 or state == FIRE_MULTIPLE) and switchingWorms:
						switchWorms()
				if event.key == pygame.K_t:
					# checkPotential(objectUnderControl, 100)
					# for i in range(2500):
						# extra.append((randint(0,mapWidth-1), randint(0,mapHeight-1), (255,0,0), 5))
					# print(len(Flare._flares))
					print(roundCounter)
					pass
				if event.key == pygame.K_y:
					# objectUnderControl.cpu = not objectUnderControl.cpu
					# CpuHolder.mode = CpuHolder.CHECK_SURROUNDING
					pass
				if event.key == pygame.K_PAGEUP or event.key == pygame.K_KP9:
					if len(Menu.menus) > 0:
						scrollMenu()
				if event.key == pygame.K_PAGEDOWN or event.key == pygame.K_KP3:
					if len(Menu.menus) > 0:
						scrollMenu(False)
				if event.key == pygame.K_F2:
					Worm.healthMode = (Worm.healthMode + 1) % 2
					if Worm.healthMode == 1:
						for worm in PhysObj._worms:
							worm.healthStr = myfont.render(str(worm.health), False, worm.team.color)
				if event.key == pygame.K_RCTRL or event.key == pygame.K_LCTRL:
					scalingFactor = 3
				# if event.key == pygame.K_n:
					# pygame.image.save(win, "wormshoot" + str(timeOverall) + ".png")	
				text += event.unicode
				if event.key == pygame.K_EQUALS:
					cheatActive(text)
					text = ""
			# key release
			if event.type == pygame.KEYUP:
				# fire release
				if event.key == pygame.K_SPACE:
					# if playerShootAble:
						# if timeTravel:
							# timeTravelPlay()
							# energyLevel = 0
						# elif weaponStyle == CHARGABLE and energising:
							# fireWeapon = True
						##putable/gun weapons case
						# elif (weaponStyle in [PUTABLE, GUN]) and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0 and not currentWeapon == "rope":
							# fireWeapon = True
							##if objectUnderControl.rope: #rope
							##	objectUnderControl.toggleRope(None)
							##	fireWeapon = False
							# playerShootAble = False
						##rope case:
						# elif (weaponStyle in [PUTABLE, GUN]) and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0 and currentWeapon == "rope":
							##if not currently roping:
							# fireWeapon = True
							# playerShootAble = False
							##if currently roping:
							# if objectUnderControl.rope: #rope
								# objectUnderControl.toggleRope(None)
								# fireWeapon = False
						# energising = False
					# elif objectUnderControl.rope:
						# objectUnderControl.toggleRope(None)
					# elif objectUnderControl.parachuting:
						# objectUnderControl.toggleParachute()
					onKeyReleaseSpace()
					
		keys = pygame.key.get_pressed()
		if keys[pygame.K_ESCAPE]: run = False	
		#key hold:
		if objectUnderControl and playerControl:
			if keys[pygame.K_RIGHT]:
				actionMove = True
			if keys[pygame.K_LEFT]:
				actionMove = True
			# fire hold
			if playerShootAble and keys[pygame.K_SPACE] and weaponStyle == CHARGABLE and energising:
				# energyLevel += 0.05
				# if energyLevel >= 1:
					# if timeTravel:
						# timeTravelPlay()
						# energyLevel = 0
						# energising = False
					# else:
						# energyLevel = 1
						# fireWeapon = True
				onKeyHoldSpace()
		
		if pause: continue
	
		# set camera target
		if camTrack:
			camTarget.x = camTrack.pos.x - winWidth /2
			camTarget.y = camTrack.pos.y - winHeight /2
			camPos += (camTarget - camPos) * 0.2
		
		# set scalling
		if not scalling == scalingFactor:
			scalling += (scalingFactor - scalling) * 0.2
			if abs(scalling - scalingFactor) <= 0.001:
				scalling = scalingFactor
			if not camTrack:
				Cam.pos = Vector((screenWidth/2)/scalingFactor + camPos.x, (screenHeight/2)/scalingFactor + camPos.y)
				camTrack = Cam
			
			winWidth = int(1280 / scalling)
			winHeight = int(720 / scalling)
			win = pygame.Surface((winWidth, winHeight))
			
			camTarget.x = camTrack.pos.x - winWidth /2
			camTarget.y = camTrack.pos.y - winHeight /2
			camPos = vectorCopy(camTarget)
			
			if len(Menu.menus) > 0:
				Menu.menus[0].updateWinPos((winWidth - Menu.width - 2 * Menu.border, 0))
				if len(Menu.menus) > 1:
					Menu.menus[1].updateWinPos((winWidth - 2 * Menu.width - 4 * Menu.border - 1, 0))
		
		# use edge map scroll
		mousePos = pygame.mouse.get_pos()
		if playerScrollAble and pygame.mouse.get_focused() and not len(Menu.menus) > 0:
			edgeBorder = 65
			if mousePos[0] < edgeBorder:
				camTrack = None
				camPos.x -= mapScrollSpeed
			if mousePos[0] > screenWidth - edgeBorder:
				camTrack = None
				camPos.x += mapScrollSpeed
			if mousePos[1] < edgeBorder:
				camTrack = None
				camPos.y -= mapScrollSpeed
			if mousePos[1] > screenHeight - edgeBorder:
				camTrack = None
				camPos.y += mapScrollSpeed
		
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
		
		if timeTravel:
			timeTravelRecord()
		
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
		if timeOverall % 30 == 0:
			if not state in [PLACING_WORMS]:
				timeStep()
				
		cloud_maneger()
		for cloud in Cloud._reg: cloud.step()
			
		# draw:
		win.blit(pygame.transform.scale(imageSky, win.get_rect().size), (0,0))
		for cloud in Cloud._reg: cloud.draw()
		drawBackGround(imageMountain2,4)
		drawBackGround(imageMountain,2)
		
		drawLand()
		wormCol.fill(SKY)##
		extraCol.fill(SKY)##
		for p in PhysObj._reg: p.draw()
		for f in nonPhys: f.draw()
		drawTarget()
		# draw shooting indicator
		if objectUnderControl and state in [PLAYER_CONTROL_1, PLAYER_CONTROL_2, FIRE_MULTIPLE] and objectUnderControl.health > 0:
			objectUnderControl.drawCursor()
			if aimAid and weaponStyle == GUN:
				p1 = vectorCopy(objectUnderControl.pos)
				p2 = p1 + Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle)) * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))
			i = 0
			while i < 20 * energyLevel:
				cPos = vectorCopy(objectUnderControl.pos)
				angle = objectUnderControl.shootAngle
				pygame.draw.line(win, (0,0,0), point2world(cPos), point2world(cPos + vectorFromAngle(angle) * i))
				i += 1
		if currentWeapon == "girder" and state == PLAYER_CONTROL_1: drawGirderHint()
		drawExtra()
		drawLayers()
		
		# HUD
		drawWindIndicator()
		timeDraw()
		win.blit(currentWeaponSurf, ((int(25), int(8))))
		commentator.step()
		if not currentWeapon in ["flare", "teleport"]:
			if weapons[weaponDict[currentWeapon]][3] == AIRSTRIKE:
				mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
				win.blit(pygame.transform.flip(airStrikeSpr, False if airStrikeDir == RIGHT else True, False), point2world(mouse - tup2vec(airStrikeSpr.get_size())/2))
		if useListMode: drawUseList()
		
		if not state in [RESET, GENERATE_TERRAIN, PLACING_WORMS, CHOOSE_STARTER] and drawHealthBar: teamHealthDraw()
		# weapon menu:
		if len(Menu.menus) > 0:
			for menu in Menu.menus:
				menu.step()
			for menu in Menu.menus:
				menu.draw()
		
		if pointsMode or targetsMode:
			while len(killList) > 8:
				killList.pop(-1)
			for i in range(len(killList)):
				win.blit(killList[i][0], (5, winHeight - 14 - i * 8))
		
		# debug:
		if damageText[0] != damageThisTurn:
			damageText = (damageThisTurn, myfont.render(str(int(damageThisTurn)), False, HUDColor))
		win.blit(damageText[1], ((int(5), int(winHeight-6))))
		
		if state == PLACING_WORMS:
			win.blit(myfont.render(str(len(PhysObj._worms)), False, HUDColor), ((int(20), int(winHeight-6))))
		
		if state in [RESET, GENERATE_TERRAIN] or (state in [PLACING_WORMS, CHOOSE_STARTER] and randomPlace):
			win.fill((0,0,0))
			pos = (winWidth/2 - loadingSurf.get_width()/2, winHeight/2 - loadingSurf.get_height()/2)
			win.blit(loadingSurf, pos)
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + 20), (pos[0] + loadingSurf.get_width(), pos[1] + 20))
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + loadingSurf.get_height() + 20), (pos[0] + loadingSurf.get_width(), pos[1] + loadingSurf.get_height() + 20))
			pygame.draw.line(win, (255,255,255), (pos[0], pos[1] + 20), (pos[0], pos[1] + loadingSurf.get_height() + 20))
			pygame.draw.line(win, (255,255,255), (pos[0] + loadingSurf.get_width(), pos[1] + 20), (pos[0] + loadingSurf.get_width(), pos[1] + loadingSurf.get_height() + 20))
			pygame.draw.rect(win, (255,255,255), ((pos[0], pos[1] + 20), ((lstep/lstepmax)*loadingSurf.get_width(), loadingSurf.get_height())))
		
		# reset actions
		actionMove = False
		
		# screen manegement
		screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
		
		pygame.display.update()
		
	pygame.quit()

