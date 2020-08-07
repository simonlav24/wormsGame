from math import pi, cos, sin, atan2, sqrt, exp, degrees, radians
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
	DOWN = 1
	UP = -1
	
	HEALTH_PACK = 0
	UTILITY_PACK = 1
	WEAPON_PACK = 2
	
	MOON_GRAVITY = 0
	DOUBLE_DAMAGE = 1
	AIM_AID = 2
	TELEPORT = 3
	SWITCH_WORMS = 4
	TIME_TRAVEL = 5
	JETPACK = 6
	
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
	shockRadius = 1.5
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
	
	# Multipliers
	damageMult = 0.8
	fallDamageMult = 1
	windMult = 1.5
	radiusMult = 1
	packMult = 1
	
	text = ""
webVer = True 

################################################################################ Map
if True:
	mapWidth = int(1024*1.5)
	mapHeight = 512
	map = pygame.Surface((mapWidth, mapHeight))
	
	ground = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	
	camPos = Vector(0,0)
	camTarget = Vector(0,0)
	
	objectUnderControl = None
	camTrack = None
	
	energising = False
	energyLevel = 0
	fireWeapon = False
	currentWeapon = "missile"
	currentWeaponSurf = myfont.render(currentWeapon, False, (0,0,0))
	weaponStyle = CHARGABLE
	
	wind = uniform(-1,1)
	actionMove = False
	aimAid = False
	switchingWorms = False
	timeTravel = False
	jetPackFuel = 100

def createMapImage(heightNorm = None):
	global mapImage
	if heightNorm:
		ratio = mapImage.get_width() / mapImage.get_height()
		mapImage = pygame.transform.scale(mapImage, (int(heightNorm * ratio), heightNorm))
		if randint(0,1) == 0:
			mapImage = pygame.transform.flip(mapImage, True, False)
	
	global map, mapWidth, mapHeight, ground
	mapWidth = mapImage.get_width()
	mapHeight = mapImage.get_height()
	map = pygame.Surface((mapWidth, mapHeight))
	map.fill((0,0,0))
	ground = pygame.Surface((mapWidth, mapHeight)).convert_alpha()
	
	for x in range(mapWidth):
		for y in range(mapHeight):
			if not mapImage.get_at((x, y)) == (0,0,0):
				map.set_at((x, y), GRD)

def createMapDigging():
	global map
	map.fill((255,255,255))
	
def drawLand():
	win.blit(ground, (-int(camPos.x), -int(camPos.y)))

def renderLand():
	ground.fill(SKY)
	if mapImage:
		for x in range(0,mapWidth):
			for y in range(0,mapHeight):
				if map.get_at((x,y)) == GRD:
					ground.fill(mapImage.get_at((x,y)), ((x,y), (1, 1)))
		
	else:
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
			colors.append((255,255,0))
	# ground delete
	if not fire:
		Explossion(pos, radius)
	
	pygame.draw.circle(map, SKY, (int(pos[0]), int(pos[1])), int(radius))
	pygame.draw.circle(ground, SKY, (int(pos[0]), int(pos[1])), int(radius))
	
	
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
		self.time = 0
		self.pos = pos
		self.radius = radius
		self.rad = 0
		self.time = 0
		self.smoke = smoke
	def step(self):
		if randint(0,self.smoke) == 0:
			Smoke(self.pos)
		self.time += 0.5
		self.rad = 1.359 * self.time * exp(- 0.5 * self.time) * self.radius
		if self.time >= 10:
			nonPhys.remove(self)
			del self
	def draw(self):
		# pygame.draw.circle(win, self._color[int(max(min(self.time, 5), 0))], point2world(self.pos), int(self.rad))
		# pygame.draw.circle(win, self._color[int(max(min(self.time-1,5), 0))], point2world(self.pos), int(self.rad*0.6))
		# pygame.draw.circle(win, self._color[int(max(min(self.time-2,5), 0))], point2world(self.pos), int(self.rad*0.3))
		layers[0].append((self._color[int(max(min(self.time, 5), 0))], self.pos, self.rad))
		layers[1].append((self._color[int(max(min(self.time-1, 5), 0))], self.pos, self.rad*0.6))
		layers[2].append((self._color[int(max(min(self.time-2, 5), 0))], self.pos, self.rad*0.3))

class Explossion:
	def __init__(self, pos, radius):	
		nonPhys.append(self)
		self.pos = pos
		self.radius = radius
		self.times = radius//5
		self.time = 0
	def step(self):
		Blast(self.pos + vectorUnitRandom() * uniform(0,self.radius/2), uniform(10, self.radius*0.7))
		self.time += 1
		if self.time == self.times:
			nonPhys.remove(self)
			del self
	def draw(self):
		pass

def drawWindIndicator():
	pygame.draw.line(win, (100,100,255), (20, 15), (int(20 + wind * 20),15))
	pygame.draw.line(win, (0,0,255), (20, 10), (20,20))

def giveGoodPlace(div = 0):
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
	
	if not diggingMatch:
		while not goodPlace:

			counter += 1
			goodPlace = True
			place = Vector(randint(int(left), int(right)), randint(6, mapHeight - 6))
			# check circle around
			if isGroundAround(place):
				goodPlace = False
			if  not goodPlace:
				continue
			
			if counter > 8000:
				# check only worms around
				for worm in PhysObj._worms:
					if dist(worm.pos, place) < 50:
						goodPlace = False
						break
				if  not goodPlace:
					continue
				# girder down 
				girder(place + Vector(0,20))
				return place
			
			# put place down
			y = place.y
			for i in range(mapHeight):
				if y + i >= mapHeight:
					goodPlace = False
					break
				if map.get_at((place.x, y + i)) == GRD:
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
					# print("F2")
			if  not goodPlace:
				continue
			for mine in PhysObj._mines:
				if dist(mine.pos, place) < 40:
					goodPlace = False
					break
			if  not goodPlace:
				continue
			if isGroundAround(place):
				pygame.draw.circle(map, SKY, place.vec2tup(), 5)
				pygame.draw.circle(ground, SKY, place.vec2tup(), 5)
	else:
		while not goodPlace:
			place = Vector(randint(int(left), int(right)), randint(6, mapHeight - 50))
			goodPlace = True
			for worm in PhysObj._worms:
				if dist(worm.pos, place) < 75:
					goodPlace = False
					break
				if  not goodPlace:
					continue
	
	if counter >= 8000: # will never get here :)
		print("above 8000:", counter)
	return place

def placePetrolCan(quantity = 1):
	noPlace = []
	
	for times in range(quantity):
		place = giveGoodPlace(-1)
		PetrolCan((place.x, place.y - 2))

def placeMines(quantity = 1):
	noPlace = []
	
	for times in range(quantity):
		place = giveGoodPlace(-1)
		m = Mine((place.x, place.y - 2))
		m.damp = 0.1

extra = [] #posx, posy, color, repeat
def drawExtra():
	global extra
	extraNext = []
	for i in extra:
		win.fill(i[2], ((int(i[0] - camPos.x), int(i[1] - camPos.y)),(1,1)))
		if i[3] > 0:
			extraNext.append((i[0], i[1], i[2], i[3]-1))
	extra = extraNext

layers = [[],[],[]]
def drawLayers():
	global layers
	for j in layers:
		for i in j:
			pygame.draw.circle(win, i[0], point2world(i[1]), int(i[2]))
	layers = [[],[],[]]

def clamp(value, upper, lower):
	if value > upper:
		value = upper
	if value < lower:
		value = lower
	return value

# sprites
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

def drawBackGround(surf, parallax):
	width = surf.get_width()
	height = surf.get_height()
	offset = (camPos.x/parallax)//width
	times = winWidth//width + 2
	for i in range(times):
		x = int(-camPos.x/parallax) + int(int(offset) * width + i * width)
		y =  int(mapHeight - height) - int(camPos.y) - int((int(mapHeight - winHeight)  - int(camPos.y))/parallax)
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

def checkFreePos(obj, pos):
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
	return True

def whiten(color):
	r = color[0]
	g = color[1]
	b = color[2]
	
	r = r/5 + 167
	g = g/5 + 167
	b = b/5 + 167
	
	return (r,g,b)

################################################################################ Objects
time = turnTime
timeOverall = 0
def timeStep():
	global time
	if time == 0:
		# time = turnTime
		timeOnTimer()
	if not time <= 0:
		time -= 1
def timeOnTimer():
	# onTime time end time
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
	win.blit(myfont.render(str(time), False, (0,0,0)) , ((int(10), int(8))))
def timeReset():
	global time
	time = turnTime
def timeRemaining(amount):
	global time
	time = amount

nonPhys = []
class FloatingText: #pos, text, color
	def __init__(self, pos, text, color = (255,0,0)):
		nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.surf = myfont.render(str(text), False, color)
		self.time = 0
	def step(self):
		self.time += 1
		self.pos.y -= 0.5
		if self.time == 50:
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
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0],pos[1])
		
		self.radius = 4
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
				# if response.x > 0:
					# self.vel.x += 0.4
				# else:
					# self.vel.x -= 0.4
			
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
	def applyForce(self):
		# gravity:
		self.acc.y += globalGravity
		if self.windAffected:
			self.acc.x += wind * 0.1 * windMult
	def deathResponse(self):
		pass
	def secondaryStep(self):
		pass
	def damage(self, value):
		pass
	def collisionRespone(self, ppos):
		pass
	def outOfMapResponse(self):
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
		self.megaBoom = False
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
		self.damp = 0.5
		self.timer = 0
	def deathResponse(self):
		rad = 30
		if randint(0,50) == 1:
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
		self.damp = 0.5
		self.timer = 0
	def deathResponse(self):
		global camTrack
		megaBoom = False
		boom(self.pos, 25)
		if randint(0,50) == 1:
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
		if randint(0,50) == 1:
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
	def damage(self, value):
		if self.health > 0: # if alive
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
				if not sentring and not self in objectUnderControl.team.worms:
					damageThisTurn += dmg
	def draw(self):
		if self.parachuting:
			win.blit(imageParachute, point2world(self.pos - tup2vec(imageParachute.get_size())/2 + Vector(0,-15)))
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		win.blit(self.name , ((int(self.pos.x) - int(camPos.x) - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(camPos.y) - 21)))
		if self.rope:
			# rope = [point2world(self.pos)]
			rope = [point2world(x) for x in self.rope[0]]
			rope.append(point2world(self.pos))
			pygame.draw.lines(win, (250,250,0), False, rope)
		if self.cpu:
			pygame.draw.circle(win, (200,0,0), point2world(self.pos + Vector(0,-5)), 2)
			cpuDraw()
		if self.health > 0 and drawHealthBar:
			self.drawHealth()
		if self.pos.y < 0:
			width = 25
			height = 10
			pygame.draw.rect(win, (0,0,0), (point2world((self.pos.x - width/2,10)), (width, height)))
			num = myfont.render(str(int(-self.pos.y)), False, self.team.color)
			win.blit(num, point2world((self.pos.x - num.get_width()/2, 12)))
	def __str__(self):
		return self.nameStr
	def __repr__(self):
		return str(self)
	def dieded(self):
		global state, nextState, teams
		self.color = (167,167,167)
		self.name = myfont.render(self.nameStr, False, whiten(self.team.color))
		if self in self._worms:
			self._worms.remove(self)
			self.team.worms.remove(self)
			if objectUnderControl == self:
				# self died and is objectUnderControl
				if state == FIRE_MULTIPLE:
					nextState = PLAYER_CONTROL_2
					# remove shotgun if current
					if weaponStyle == GUN:
						self.team.weaponCounter[weaponDict[currentWeapon]] -= 1
						renderWeaponCount()
				state = nextState
				timeRemaining(5)
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
		if objectUnderControl == self and playerControl and self.health > 0:
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
			# gather fire information
			CpuHolder.team = self.team
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
						# CpuHolder.mode = CpuHolder.DUMMY
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
		
		self.shootVel = clamp(self.shootVel + self.shootAcc, 0.1, -0.1)
		self.shootAngle += self.shootVel * self.facing
		if self.facing == RIGHT:
			self.shootAngle = clamp(self.shootAngle, pi/2, -pi/2)
		elif self.facing == LEFT:
			self.shootAngle = clamp(self.shootAngle, pi + pi/2, pi/2)

		if self.health <= 0 and not self.color == (167,167,167):
			self.dieded()
			Commentator.que.append((self.nameStr, choice(Commentator.stringsDmg), self.team.color))
		# check if on map:
		if self.pos.y >= mapHeight:
			global damageThisTurn
			if not self == objectUnderControl:
				if not sentring and not self in objectUnderControl.team.worms:
					damageThisTurn += self.health
			self.health = 0
			self.dieded()
			Commentator.que.append((self.nameStr, choice(Commentator.stringsFlw), self.team.color))
			self._reg.remove(self)
		if self.pos.y < 0:
			self.gravity = DOWN
		if actionMove or actionMove:
			# self.move()
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

##########################CPU
class CpuHolder:
	index = 0
	
	DUMMY = 0
	RESET = 1
	CHECK = 2
	CALCULATE = 3
	CHECK_PATH = 4
	FIRE = 5
	READY = 6
	STUCK = 7
	TRYAGAIN = 8
	
	long = 0
	
	team = None
	
	mode = DUMMY
	targets = []
	velCount = 0

	initialPos = None
	direction = None
	energy = None
	
	checkList = {"facing":False, "angle":False, "pressed":False, "hold":False, "release":False}
	weaponsCheckList = {"missile":False, "grenade":False}
	weapons = ["missile", "grenade"]
	weapon = None
	
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
		CpuHolder.mode = CpuHolder.DUMMY

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
		
##########################CPU

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
		self.windAffected = True
		self.life = randint(50,70)
		self.fallen = False
		self.delay = delay
		self.timer = 0
	def collisionRespone(self, ppos):
		self.fallen = True
	def secondaryStep(self):
		if randint(0,10) == 1:
			Blast(self.pos + vectorUnitRandom(), randint(self.radius,7), 150)
		self.timer += 1
		if self.fallen:
			self.life -= 1
		if self.life == 0:
			self._reg.remove(self)
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
		self.time = 0
	def draw(self):
		pygame.gfxdraw.filled_circle(win, int(self.pos.x - camPos.x), int(self.pos.y - camPos.y), self.radius, self.color)
	def step(self):
		self.time += 1
		if self.time % 5 == 0:
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
		extra.append((testPos.x, testPos.y, (255,255,0), 3))
		
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue
		# if hits worm:
		for worm in PhysObj._worms:
			if dist(testPos, worm.pos) < worm.radius + 1:
				boom(testPos, power)
				worm.vel += direction*2
				hit = True
				break
		# if hits can:
		for can in PetrolCan._cans:
			if dist(testPos, can.pos) < can.radius + 1:
				boom(testPos, power)
				can.deathResponse()
				hit = True
				break
		if hit:
			break
		# if hits map:
		if map.get_at((int(testPos.x), int(testPos.y))) == GRD:
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
	fireShotgun(start, direction, 8)

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
	def deathResponse(self):
		boom(self.pos, 20)
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
	def damage(self, value):
		dmg = value * damageMult
		if self.health > 0:
			self.health -= int(dmg)
			if self.health < 0:
				self.health = 0
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -3) - int(camPos.x),int(self.pos.y -5) - int(camPos.y) , 7,10))
		pygame.draw.circle(win, (218, 238, 44), (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), 3)

class Mine(PhysObj):
	def __init__(self, pos, delay=0):
		self.initialize()
		self._mines.append(self)
		self.pos = tup2vec(pos)
		self.radius = 2
		self.color = (52,66,71)
		self.damp = 0.55
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
	for t in range(5, 20):
		testPos = start + direction * t
		extra.append((testPos.x, testPos.y, (255,255,0), 10))
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
		self.time = 0
		self.sickness = sickness
	def draw(self):
		pygame.gfxdraw.filled_circle(win, int(self.pos.x - camPos.x), int(self.pos.y - camPos.y), self.radius, self.color)
	def step(self):
		self.time += 1
		if self.time % 8 == 0:
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
		Commentator.que.append(("", choice(Commentator.stringsCrt), (0,0,0)))
	def draw(self):
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
		Commentator.que.append(("", choice(Commentator.stringsCrt), (0,0,0)))
		self.box = choice([MOON_GRAVITY, DOUBLE_DAMAGE, AIM_AID, TELEPORT, SWITCH_WORMS, TIME_TRAVEL, JETPACK, "portal gun"])
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -5) - int(camPos.x),int(self.pos.y -5) - int(camPos.y) , 10,10))
		win.blit(self.surf, (int(self.pos.x) - int(camPos.x)-1, int(self.pos.y) - int(camPos.y)-2))
	def effect(self, worm):
		if unlimitedMode:
			return
		
		if self.box == MOON_GRAVITY:
			FloatingText(self.pos, "moon gravity", (0,200,200))
		elif self.box == DOUBLE_DAMAGE:
			FloatingText(self.pos, "double damage", (0,200,200))
		elif self.box == AIM_AID:
			FloatingText(self.pos, "aim aid", (0,200,200))
		elif self.box == TELEPORT:
			FloatingText(self.pos, "teleport", (0,200,200))
		elif self.box == SWITCH_WORMS:
			FloatingText(self.pos, "switch worms", (0,200,200))
		elif self.box == TIME_TRAVEL:
			FloatingText(self.pos, "time travel", (0,200,200))
		elif self.box == JETPACK:
			FloatingText(self.pos, "jet pack", (0,200,200))
		elif self.box == "portal gun":#portal gun
			FloatingText(self.pos, self.box, (0,200,200))
			worm.team.weaponCounter[weaponDict[self.box]] += 1
			return
		
		worm.team.hasSpecial = True
		worm.team.specialCounter[self.box] += 1

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
		Commentator.que.append(("", choice(Commentator.stringsCrt), (0,0,0)))
		self.box = choice(["banana", "holy grenade", "earthquake", "gemino mine", "sentry turret", "bee hive", "vortex grenade", "chilli pepper", "covid 19", "mine strike", "raging bull", "electro boom", "pokeball", "green shell"])
	def draw(self):
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
	if pack == UTILITY_PACK:
		p = UtilityPack((x, y))
	if pack == WEAPON_PACK:
		p = WeaponPack((x, y))
	return p
	
def fireAirstrike(pos):
	global camTrack
	x = pos[0]
	y = 5
	for i in range(5):
		f = Missile((x - 40 + 20*i, y - i), (0,0), 0)
		f.megaBoom = False
		f.boomAffected = False
		f.radius = 1
		f.boomRadius = 18
		if i == 2:
			camTrack = f

def fireMineStrike(pos):
	megaBoom = False
	if randint(0,50) == 1:
		megaBoom = True
	global camTrack
	x = pos[0]
	y = 5
	if megaBoom:
		for i in range(20):
			m = Mine((x - 40 + 4*i, y - i))
			m.vel.x = 1
			if i == 10:
				camTrack = m
	else:
		for i in range(5):
			m = Mine((x - 40 + 20*i, y - i))
			m.vel.x = 1
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

def fireBusterStrike(pos): # deleted
	global camTrack
	x = pos[0]
	y = 5
	BunkerBuster.mode = True
	for i in range(3):
		b = BunkerBuster((x - 40 + 40*i, y - i), (0,0), 0)
		if i == 1:
			camTrack = b

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
		testPos = start + direction * t + normal * 1.5 * sin(t * 0.6)
		extra.append((testPos.x, testPos.y, (0,255,255), 10))
		
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			continue
		# if hits worm:
		for worm in PhysObj._worms:
			if dist(testPos, worm.pos) < worm.radius and not worm in hitted:
				worm.damage(int(10/damageMult)+1)
				worm.sicken()
				hitted.append(worm)

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
		self.damp = 0.7
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
		PhysObj._reg.append(self)
		self.stable = False
		self.boomAffected = False
		Earthquake.earthquake = True
	def step(self):
		for obj in PhysObj._reg:
			if obj == self:
				continue
			if randint(0,5) == 1:
				obj.vel += Vector(randint(-1,1), -uniform(0,1))
		self.timer -= 1
		if self.timer == 0:
			PhysObj._reg.remove(self)
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
		self.time = 0
		self.green = 135
		self.venus = venus
	def step(self):
		self.pos += vectorFromAngle(self.angle + uniform(-1,1))
		if randint(1,100) <= 2 and not self.venus:
			Plant(self.pos, self.radius, self.angle + choice([pi/3, -pi/3]))
		self.time += 1
		if self.time % 10 == 0:
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
	venus = False
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
		# point1 = self.pos + vectorFromAngle(-5*pi/4, self.radius+2)
		# point3 = self.pos + vectorFromAngle(pi/4, self.radius+2)
		# pygame.draw.lines(win, self.color, False, [point2world(point1), point2world(self.pos), point2world(point3)], 3)
		# pygame.draw.rect(win, (0, 51, 0), (point2world((self.pos.x - 3, self.pos.y - 2)), (6, 4)) )
		# pygame.draw.circle(win, self.teamColor, point2world(self.pos + Vector(2,0)), 1)
		size = Vector(4*2,10*2)
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))
		pygame.draw.line(win, self.teamColor, point2world(self.pos), point2world(self.pos + vectorFromAngle(self.angle) * 18))
		
	def damage(self, value):
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
	def step(self):
		self.lifespan -= 1
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
		pygame.draw.circle(win, self.color, point2world(self.pos), self.radius)

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
	def secondaryStep(self):
		if self.beeCount <= 0:
			self.dead = True
	def deathResponse(self):
		# boom(self.pos, 15)
		pass
	def collisionRespone(self, ppos):
		out = randint(1,3)
		for i in range(out):
			Bee(self.pos, uniform(0,2*pi))
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
				# self.drillVel.setMag(5)
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
		
def drawLightning(start, end):
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
		pygame.draw.lines(win, (153, 255, 255), False, points, 2)
	else:
		pygame.draw.lines(win, (153, 255, 255), False, [point2world(start), point2world(end)], 2)
	pygame.draw.circle(win, (153, 255, 255), (int(end.x) - int(camPos.x), int(end.y) - int(camPos.y)), int(PhysObj._worms[0].radius) + 3)

class ElectricGrenade(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		PhysObj._reg.remove(self)
		PhysObj._reg.insert(0,self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (120, 230, 230)
		self.damp = 0.7
		self.timer = 0
		self.worms = []
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
			for worm in PhysObj._worms:
				if dist(self.pos, worm.pos) < 100:
					self.worms.append(worm)
			if len(self.worms) == 0:
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
	def draw(self):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)
		for worm in self.worms:
			drawLightning(self.pos, worm.pos)

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
	def step(self):
		self.applyForce()
		
		# velocity
		self.vel += self.acc
		self.vel.limit(15)
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
		
		if magVel < 0.1:
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self._reg.remove(self)
			self.deathResponse()
			del self
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
	def __init__(self, pos):
		PhysObj._reg.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.rot = 0
		self.inhale = True
		self.boomAffected = False
		self.stable = False
	def step(self):
		self.stable = False
		if self.inhale:
			self.rot += 0.001
			if self.rot > 0.1:
				self.rot = 0.1
				self.inhale = False
		else:
			self.rot -= 0.001
		
		if self.inhale:
			for worm in PhysObj._reg:
				if worm == self:
					continue
				if dist(self.pos, worm.pos) < 130:
					worm.acc += (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
					if randint(0,20) == 1:
						worm.vel.y -= 2
				if worm in PhysObj._worms and dist(self.pos, worm.pos) < 50:
					if randint(0,20) == 1:
						worm.damage(randint(1,8))
		else:
			for worm in PhysObj._reg:
				if worm == self:
					continue
				if dist(self.pos, worm.pos) < 130:
					worm.acc -= (self.pos - worm.pos) * 1/dist(self.pos, worm.pos)
			
		if not self.inhale and self.rot < 0:
			PhysObj._reg.remove(self)
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
		self.time = 0
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
			
		self.time += 1
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
	global timeTravel, timeTravelList, time
	timeTravel = True
	timeTravelList = {}
	timeTravelList["color"] = objectUnderControl.color
	timeTravelList["name"] = objectUnderControl.name
	timeTravelList["health"] = objectUnderControl.health
	timeTravelList["initial pos"] = vectorCopy(objectUnderControl.pos)
	timeTravelList["time in turn"] = time
	timeTravelList["jet pack"] = jetPackFuel
def timeTravelRecord():
	timeTravelPositions.append(objectUnderControl.pos.vec2tup())
def timeTravelPlay():
	global timeTravel, time, timeTravelList, jetPackFuel
	time = timeTravelList["time in turn"]
	timeTravel = False
	timeTravelList["weapon"] = currentWeapon
	timeTravelList["weaponOrigin"] = vectorCopy(objectUnderControl.pos)
	timeTravelList["energy"] = energyLevel
	timeTravelList["weaponDir"] = Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle))
	objectUnderControl.health = timeTravelList["health"]
	if Worm.healthMode == 1:
		objectUnderControl.healthStr = myfont.render(str(objectUnderControl.health), False, objectUnderControl.team.color)
	objectUnderControl.pos = timeTravelList["initial pos"]
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
			print("bee index error")
		self.pos = ppos
		
		if self.lifespan % 40 == 0:
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
		self.boomCount = 3
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
				# boom(self.pos + vectorUnitRandom()*10, 30)
				m = Missile((self.pos[0] + randint(-20,20), 0),(0,0),0 )
				m.windAffected = False
				m.boomAffected = False
				m.megaBoom = False
				if self.boomCount == 3:
					global camTrack
					camTrack = m
				self.boomCount -= 1
			if self.boomCount == 0:
				self.dead = True

class LongBow:
	def __init__(self, pos, direction):
		PhysObj._reg.append(self)
		self.pos = vectorCopy(pos)
		self.direction = direction
		self.vel = direction.normalize() * 20
		self.stable = False
		self.boomAffected = False
		self.stuck = None
		self.color = (204, 102, 0)
		self.ignore = None
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
						worm.damage(randint(20,30))
						self.destroy()
						return
			self.pos = ppos
		if self.stuck:
			self.pos = self.stuck
			pygame.draw.line(map, GRD, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
			pygame.draw.line(ground, self.color, self.pos.vec2tupint(), (self.pos - self.direction*8).vec2tupint(), 3)
			self.destroy()
			
	def draw(self):
		pygame.draw.line(win, self.color, point2world(self.pos), point2world(self.pos - self.direction*8), 3)

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
		PhysObj._reg.append(self)
		self.stable = False
		self.boomAffected = False
		self.timer = 700
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			PhysObj._reg.remove(self)
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
		self.damp = 0.7
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
		
		# pygame.draw.circle(map, SKY, self.pos.vec2tupint(), 8)
		# pygame.draw.circle(ground, SKY, self.pos.vec2tupint(), 8)
		
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
		win.blit(self.surf, point2world(self.pos - tup2vec(self.surf.get_size())/2))

class Venus:
	# _reg = []
	grow = -1
	catch = 0
	idle = 1
	hold = 2
	release = 3
	def __init__(self, pos, angle = -1):
		nonPhys.append(self)
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
	def step(self):
	
		self.gap = 5*(self.snap + pi/2)/(pi/2)
		self.p1 = self.pos + self.d1 * self.gap
		self.p2 = self.pos + self.d2 * self.gap
		
		if self.mode == Venus.grow:
			self.scale += 0.1
			if self.scale >= 1:
				self.scale = 1
				self.mode = Venus.hold
			return
			
		self.timer += 1
		
		if self.mode == Venus.idle:
			pos = self.pos + self.direction * 25
			for worm in PhysObj._reg:
				if worm in Debrie._debries:
					continue
				if dist(worm.pos, pos) <= 25:
					
					self.mode = Venus.catch
					if worm in PhysObj._worms:
						global damageThisTurn
						if not worm == objectUnderControl:
							if not sentring and not worm in objectUnderControl.team.worms:
								damageThisTurn += worm.health
						worm.health = 0
						worm.dieded()
						Commentator.que.append(choice([("", ("yummy",""), worm.team.color), (worm.nameStr, ("", " was delicious"), worm.team.color), (worm.nameStr, ("", " is good protein"), worm.team.color), (worm.nameStr, ("", " is some serious gourmet s**t"), worm.team.color)]))
					else:
						self.explossive = True
					PhysObj._reg.remove(worm)
					break
					
		elif self.mode == Venus.catch:
			self.snap += 0.5
			if self.snap >= 0:
				self.snap = 0
				self.mode = Venus.hold
				self.timer = 0
		elif self.mode == Venus.hold:
			if self.timer == 30:
				self.mode = Venus.release
				if self.explossive:
					self.explossive = False
					for i in range(randint(6,14)):
						s = Smoke(self.pos + self.direction * 25 + vectorUnitRandom() * randint(3,10))
						nonPhys.remove(s)
						nonPhys.insert(0,s)
		elif self.mode == Venus.release:
			self.snap -= 0.1
			if self.snap <= self.opening:
				self.snap = self.opening
				self.mode = Venus.idle
		if not map.get_at(self.pos.vec2tupint()) == GRD:
			nonPhys.remove(self)		
	def draw(self):
		# pygame.draw.circle(win, (255,255,255), point2world(self.pos), 2)
		# pygame.draw.circle(win, (255,255,255), point2world(self.p1), 2)
		# pygame.draw.circle(win, (255,255,255), point2world(self.p2), 2)
		
		# pygame.draw.circle(win, (255,255,255), point2world(self.pos + self.direction * 25), 25, 1)
		if self.scale < 1:
			image = pygame.transform.scale(imageVenus, (tup2vec(imageVenus.get_size()) * self.scale).vec2tupint())
		else:
			image = imageVenus
		
		rotated_image = pygame.transform.rotate(image, -degrees(self.angle - self.snap))
		rotated_offset = rotateVector(self.offset, self.angle - self.snap)
		rect = rotated_image.get_rect(center=(self.p2 + rotated_offset).vec2tupint())
		win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))
		
		rotated_image = pygame.transform.rotate(pygame.transform.flip(image, False, True), -degrees(self.angle + self.snap))
		rotated_offset = rotateVector(self.offset, self.angle + self.snap)
		rect = rotated_image.get_rect(center=(self.p1 + rotated_offset).vec2tupint())
		win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))

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
		self.damp = 0.5
		self.timer = 0
		self.hold = None
		self.health = 30
		self.name = None
		self.angle = 0
	def damage(self, value):
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
		if self.timer == fuseTime:
			closer = [None, 7000]
			for worm in PhysObj._worms:
				distance = dist(self.pos, worm.pos)
				if distance < closer[1]:
					closer = [worm, distance]
			if closer[1] < 50:
				self.hold = closer[0]
		if self.timer == fuseTime + 30:
			if self.hold:
				# store worm
				# print(self.hold.nameStr)
				# print("reg:", PhysObj._reg)
				PhysObj._reg.remove(self.hold)
				# print("worms:", PhysObj._worms)
				PhysObj._worms.remove(self.hold)
				self.hold.team.worms.remove(self.hold)
				self.name = myfont.render(self.hold.nameStr, False, self.hold.team.color)
			else:
				self.dead = True
		self.angle -= self.vel.x*4
	def draw(self):
		surf = pygame.transform.rotate(imagePokeball, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		if self.timer >= fuseTime and self.timer < fuseTime + 30 and self.hold:
			drawLightning(self.pos, self.hold.pos)
		if self.name:
			win.blit(self.name , ((int(self.pos.x) - int(camPos.x) - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(camPos.y) - 21)))
	
class GreenShell(PhysObj):
	def __init__(self, pos):
		self.ignore = []
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(0,-2)
		self.radius = 6
		self.damp = 0.01
		self.timer = 0
		self.boomAffected = False
		self.facing = RIGHT
		self.ignore = []
	def secondaryStep(self):
		self.stable = False
		self.timer += 1
		moved = move(self)
		moved = move(self)
		moved = move(self)
		if not moved:
			self.facing *= -1
		for worm in PhysObj._reg:
			if worm == self:
				continue
			if worm in self.ignore:
				continue
			if dist(worm.pos, self.pos) < self.radius + worm.radius:
				self.ignore.append(worm)
				worm.vel = Vector(self.facing * randint(1,2),-randint(2,4))
				if worm in PhysObj._worms:
					worm.damage(randint(10,25))
				
		if self.timer % 20 == 0:
			self.ignore = []
		if self.timer >= 300:
			boom(self.pos, 25)
			self.dead = True
	def draw(self):
		index = int((self.timer % 12)/3)
		win.blit(imageGreenShell, point2world(self.pos - Vector(16,16)/2), ((index*16, 0), (16,16)))

################################################################################ Create World

maps = []
for i in range(1,79):
	string = "wormsMaps/wMap" + str(i) + ".png"
	maps.append((string, 512))
maps.append(("wormsMaps/wMapbig1.png", 1000))
maps.append(("wormsMaps/wMapbig2.png", 800))
maps.append(("wormsMaps/wMapbig3.png", 800))
maps.append(("wormsMaps/wMapbig4.png", 800))
maps.append(("wormsMaps/wMapbig5.png", 800))
maps.append(("wormsMaps/wMapbig6.png", 700))
if webVer:
	maps = [("wormsMaps/wMapbig1.png", 1000),("wormsMaps/wMap18.png", 512),("wormsMaps/wMap11.png", 512),("wormsMaps/wMap12.png", 512)]

def createWorld():
	global mapClosed
	# imageFile = ("lastWormsGround.png", 512)
	imageChoice = choice(maps)
	# imageChoice = maps[11 - 1]
	# imageChoice = maps[-3]
	
	if not webVer:
		if imageChoice in [maps[i] for i in [19-1, 26-1, 40-1, 41-1, 64-1]]: mapClosed = True
	imageFile, heightNorm = imageChoice
	
	global mapImage
	mapImage = pygame.image.load(imageFile)
	
	if not diggingMatch: createMapImage(heightNorm)
	else:
		mapImage = None
		createMapDigging()
	placePetrolCan(randint(2,4))
	if not diggingMatch: placeMines(randint(2,4))
	randomStartingWeapons(1)
	if diggingMatch:
		moreDigging()
		mapClosed = True
	renderLand()

# drawHealthBar = False
# randomPlace = False
# mapClosed = True
# diggingMatch = True
# moreWindAffected = True
# davidAndGoliathMode = True
# fortsMode = True
# randomWeapons = True
# initialHealth = 200
wormsPerTeam = 8

################################################################################ Weapons setup

weapons = []
if True:
	weapons.append(("missile", CHARGABLE, -1, MISSILES))
	weapons.append(("gravity missile", CHARGABLE, 10, MISSILES))
	weapons.append(("bunker buster", CHARGABLE, 2, MISSILES))
	weapons.append(("homing missile", CHARGABLE, 2, MISSILES))
	weapons.append(("artillery assist", CHARGABLE, 1, MISSILES))
	weapons.append(("grenade", CHARGABLE, 10, GRENADES))
	weapons.append(("mortar", CHARGABLE, 3, GRENADES))
	weapons.append(("sticky bomb", CHARGABLE, 3, GRENADES))
	weapons.append(("gas grenade", CHARGABLE, 5, GRENADES))
	weapons.append(("electric grenade", CHARGABLE, 3, GRENADES))
	weapons.append(("shotgun", GUN, 5, GUNS))
	weapons.append(("minigun", GUN, 6, GUNS))
	weapons.append(("gamma gun", GUN, 3, GUNS))
	weapons.append(("long bow", GUN, 3, GUNS))
	weapons.append(("portal gun", GUN, 0, GUNS))
	weapons.append(("petrol bomb", CHARGABLE, 5, FIREY))
	weapons.append(("flame thrower", PUTABLE, 5, FIREY))
	weapons.append(("mine", PUTABLE, 5, GRENADES))
	weapons.append(("TNT", PUTABLE, 1, GRENADES))
	weapons.append(("covid 19", PUTABLE, 0, GRENADES))
	weapons.append(("sheep", PUTABLE, 1, GRENADES))
	weapons.append(("baseball", PUTABLE, 3, MISC))
	weapons.append(("girder", CLICKABLE, -1, MISC))
	weapons.append(("rope", PUTABLE, 3, MISC))
	weapons.append(("parachute", PUTABLE, 3, MISC))
	weapons.append(("plant seed", CHARGABLE, 2, MISC))
	weapons.append(("sentry turret", PUTABLE, 0, MISC))
	weapons.append(("airstrike", CLICKABLE, 1, AIRSTRIKE))
	weapons.append(("napalm strike", CLICKABLE, 1, AIRSTRIKE))
	weapons.append(("mine strike", CLICKABLE, 0, AIRSTRIKE))
	weapons.append(("holy grenade", CHARGABLE, 0, LEGENDARY))
	weapons.append(("banana", CHARGABLE, 0, LEGENDARY))
	weapons.append(("earthquake", PUTABLE, 0, LEGENDARY))
	weapons.append(("gemino mine", CHARGABLE, 0, LEGENDARY))
	weapons.append(("bee hive", CHARGABLE, 0, LEGENDARY))
	weapons.append(("vortex grenade", CHARGABLE, 0, LEGENDARY))
	weapons.append(("chilli pepper", CHARGABLE, 0, LEGENDARY))
	weapons.append(("raging bull", PUTABLE, 0, LEGENDARY))
	weapons.append(("electro boom", CHARGABLE, 0, LEGENDARY))
	weapons.append(("pokeball", CHARGABLE, 0, LEGENDARY))
	weapons.append(("green shell", PUTABLE, 0, LEGENDARY))

weaponDict = {} # str => int
weaponDictI = {} # int => str
weaponStyleTup = []
basicSet = []

def fire(weapon = None):
	global decrease, shotCount, nextState, state, camTrack, fireWeapon, energyLevel, energising, timeTravelFire, currentWeapon
	if not weapon:
		weapon = currentWeapon
	decrease = True
	if objectUnderControl:
		weaponOrigin = vectorCopy(objectUnderControl.pos)
		weaponDir = Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle))
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
			timeRemaining(5)
	elif weapon == "sticky bomb":
		w = StickyBomb(weaponOrigin, weaponDir, energy)
	elif weapon == "minigun":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 20
			if randint(0,50) == 1:
				shotCount = 60
		
		fireMiniGun(weaponOrigin, weaponDir)
		if not shotCount == 0:
			shotCount -= 1
			nextState = FIRE_MULTIPLE
		else:
			nextState = PLAYER_CONTROL_2
			decrease = True
			timeRemaining(5)
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
	elif weapon == "plant seed":
		w = PlantBomb(weaponOrigin, weaponDir, energy)
	elif weapon == "sentry turret":
		w = SentryGun(weaponOrigin, currentTeam.color)
		w.pos.y -= objectUnderControl.radius + w.radius
	elif weapon == "bee hive":
		w = BeeHive(weaponOrigin, weaponDir, energy)
	elif weapon == "bunker buster":
		w = BunkerBuster(weaponOrigin, weaponDir, energy)
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
		
		"artillery assistance"
	elif weapon == "artillery assist":
		w = Artillery(weaponOrigin, weaponDir, energy)
	elif weapon == "long bow":
		decrease = False
		if state == PLAYER_CONTROL_1:
			shotCount = 3 # three shots
		w = LongBow(weaponOrigin, weaponDir) # fire
		w.ignore = objectUnderControl
		shotCount -= 1
		if shotCount > 0:
			nextState = FIRE_MULTIPLE
		if shotCount == 0:
			decrease = True
			nextState = PLAYER_CONTROL_2
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
	if w and not timeTravelFire: camTrack = w	
	
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
	if state == PLAYER_CONTROL_2: timeRemaining(5)

for i in range(len(weapons)):
	weaponDict[weapons[i][0]] = i
	weaponDictI[i] = weapons[i][0]
	weaponStyleTup.append(weapons[i][1])
	if not unlimitedMode: basicSet.append(weapons[i][2])
	else: basicSet.append(-1)

wRects = []
for i in range(len(weaponDict)):
	index = i
	textSurf = myfont.render(weaponDictI[i], False, (0,0,0))
	rect = None #[winWidth - 100 + 2, 2 + i * 10 - 10, 100 - 4 ,8]
	selected = False
	color = weapons[i][3]
	if weapons[i][3] == AIRSTRIKE:
		delay = 8
	elif weapons[i][3] == LEGENDARY:
		delay = 1
	else:
		delay = 0
	wRects.append( [index, textSurf, rect, selected, color, delay] )
specialStr = ["moon gravity", "double damage", "aim aid", "teleport", "switch worms", "time travel", "jet pack"]
sRects = []
for i in range(len(specialStr)):
	textSurf = myfont.render(specialStr[i], False, (0,0,0))
	rect = [winWidth - 200, 2 + i * 10, 100 - 4, 8]
	selected = False
	sRects.append( [i, textSurf, rect, selected] )

################################################################################ Teams
class Team:
	def __init__(self, namesList, color, name = "", cpu = False):
		self.nameList = namesList
		self.color = color
		self.weaponCounter = basicSet.copy()
		self.specialCounter = [0] * len(specialStr)
		self.hasSpecial = False
		self.worms = []
		self.name = name
		self.cpu = cpu
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
		string += "specialCounter" + list2str(self.specialCounter) + "\n"
		string += "hasSpecial" + str(self.hasSpecial) + "\n"
		string += "worms:" + "\n"
		for worm in self.worms:
			string += worm.saveStr()
		return string

blues = Team(["red lion", "commercial", "swan", "brewers", "fred", "sparrow", "eithan", "reed"], BLUE, "blue")
reds = Team(["fix delux r", "vamp b", "birdie", "lordie", "pinkie", "katie", "angie", "miya"], RED, "red")
greens = Team(["blair", "major", "thatcher", "chellenge", "george", "mark", "mercury", "philip"], GREEN, "green")
yellows = Team(["colan", "GT", "jettets", "chevan", "jonie", "murph", "silvia", "flur"], YELLOW, "yellow")

teams = [blues, greens, reds, yellows]
shuffle(teams)
totalTeams = len(teams)

currentTeam = choice(teams)
teamChoser = randint(0,3) % totalTeams
roundCounter = 0
mostDamage = (0,None)
damageThisTurn = 0

nWormsPerTeam = 0
teamsInfo = []
if unlimitedMode:
	for team in teams:
		team.specialCounter = [99] * len(specialStr)
		team.hasSpecial = True
	for wRect in wRects:
		wRect[5] = 0

def renderWeaponCount(special = False):
	global currentTeam, currentWeapon, currentWeaponSurf
	if not special:
		if currentTeam.weaponCounter[weaponDict[currentWeapon]] < 0:
			currentWeaponSurf = myfont.render(currentWeapon, False, (0,0,0))
		else:
			currentWeaponSurf = myfont.render(currentWeapon + " " + str(currentTeam.weaponCounter[weaponDict[currentWeapon]]), False, (0,0,0))
		return
	if currentWeapon == "teleport":
		currentWeaponSurf = myfont.render(currentWeapon + " " + str(currentTeam.specialCounter[TELEPORT]), False, (0,0,0))
	
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
	for i in range(totalTeams):
		pygame.draw.rect(win, (220,220,220), (int(winWidth-50),int(10+i*3) , 40,2))
		value = min(teamsInfo[i]/maxHealth, 1)*40
		if value == 0:
			continue
		if value < 1:
			value = 1
		pygame.draw.rect(win, teams[i].color, (int(winWidth-50),int(10+i*3) , int(value),2))

def cycleWorms():
	global objectUnderControl, camTrack, currentTeam, run, nextState, roundCounter, mostDamage, damageThisTurn, currentWeapon
	global deploying, sentring, deployPacks, showTarget, switchingWorms

	# reset special effects:
	global globalGravity
	globalGravity = 0.2
	global damageMult
	global radiusMult
	damageMult = 0.8
	radiusMult = 1
	global aimAid, timeTravel
	aimAid = False
	if timeTravel: timeTravelReset()
	if objectUnderControl.jetpacking: objectUnderControl.toggleJetpack()
	switchingWorms = False
	if Worm.roped:
		objectUnderControl.team.weaponCounter[weaponDict["rope"]] -= 1
		Worm.roped = False
	
	# update cpu:
	cpuUpdateCycle()
	
	# update damage:
	if damageThisTurn > mostDamage[0]:
		mostDamage = (damageThisTurn, objectUnderControl.nameStr)
	if damageThisTurn > int(initialHealth * 2.5):
		Commentator.que.append((objectUnderControl.nameStr, choice([("awesome shot ", "!"), ("", " is on fire!"), ("", " shows no mercy")]), objectUnderControl.team.color))
	elif damageThisTurn > int(initialHealth * 1.5):
		Commentator.que.append((objectUnderControl.nameStr, choice([("good shot ", "!"), ("nicely done ","")]), objectUnderControl.team.color))
		
	damageThisTurn = 0
	
	# check winners
	count = 0
	for team in teams:
		if len(team.worms) == 0:
			count += 1
	if count == totalTeams:
		pygame.image.save(ground, "lastWormsGround.png")
		# all dead
		print("everyone dead")
		run = False
		return
	elif count == totalTeams - 1:
		pygame.image.save(ground, "lastWormsGround.png")
		# someone won
		for team in teams:
			if not len(team.worms) == 0:
				print("team", team.name, "won!")
				file = open('wormsRecord.txt', 'a')
				adding = ""
				if davidAndGoliathMode:
					adding += "_dVg_"
				file.write("time taken: " + '{:6}'.format(str(int(timeOverall/30))) + " winner: " + '{:10}'.format(team.name) \
					 + "most damage: " + '{:6}'.format(int(mostDamage[0])) +" by " + '{:6}'.format(mostDamage[1]+adding) + "\n")
				file.close()
				commentator.que.append((team.name, ("taem "," won!"), team.color))
				camTrack = team.worms[0]
				nextState = WIN
				# run = False
				return
	
	roundCounter += 1
	
	# deploy pack:
	if deployPacks and roundCounter % totalTeams == 0 and not deploying:
		deploying = True
		roundCounter -= 1
		nextState = WAIT_STABLE
		for i in range(packMult):
			w = deployPack(choice([HEALTH_PACK,UTILITY_PACK, WEAPON_PACK]))
			camTrack = w
		return
	
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
			
	deploying = False
	sentring = False
	
	# update weapons delay
	if roundCounter % totalTeams == 0:
		for wRect in wRects:
			if not wRect[5] == 0:
				wRect[5] -= 1
	
	# update debries
	Debrie._debries = []
	
	showTarget = False
	# change wind:
	global wind
	wind = uniform(-1,1)
	
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
			worm.damage(min(int(5/damageMult)+1, int((worm.health-5)/damageMult) +1))
	damageThisTurn = 0
	if nextState == PLAYER_CONTROL_1:
	
		# sort worms by health for drawing purpuses
		PhysObj._reg.sort(key = lambda worm: worm.health if worm.health else 0)
		
		# actual worm switch
		w = currentTeam.worms.pop(0)
		currentTeam.worms.append(w)
	
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
			if map.get_at((int(checkPos.x), int(checkPos.y))) == GRD:
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
			pygame.draw.circle(map, SKY, place, 35)
			pygame.draw.circle(ground, SKY, place, 35)
		global teamChoser
		teams[teamChoser].addWorm(place.vec2tup())
		teamChoser = (teamChoser + 1) % totalTeams
	global state
	state = nextState

def rectOffset(rect, y):
	return ( rect[0], rect[1] - y, rect[2], rect[3])

def weaponMenuInit():
	# print(wRects)
	count = 0
	for i in range(len(weaponDict)):
		# if > 0 in current team
		if currentTeam.weaponCounter[i] == 0:
			rect = None
		else:
			rect = [winWidth - 100 + 2, 2 + count * 10, 100 - 4 ,8]
			count += 1
		wRects[i][2] = rect

def weaponMenuStep():
	mousePos = pygame.mouse.get_pos()
	mousePos = (mousePos[0]/scalingFactor, mousePos[1]/scalingFactor)
	for wRect in wRects:
		if not wRect[2]:
			continue
		wRect[2][0] = winWidth - 100 + 2
		if mousePos[0] > wRect[2][0] and mousePos[0] < wRect[2][0] + wRect[2][2] and mousePos[1] > wRect[2][1] - menuOffset and mousePos[1] < wRect[2][1] + wRect[2][3] - menuOffset:
			wRect[3] = True
		else:
			wRect[3] = False
	if not currentTeam.hasSpecial:
		return
	for sRect in sRects:
		sRect[2][0] = winWidth - 200
		if mousePos[0] > sRect[2][0] and mousePos[0] < sRect[2][0] + sRect[2][2] and mousePos[1] > sRect[2][1] - menuOffset*0 and mousePos[1] < sRect[2][1] + sRect[2][3] - menuOffset*0:
			sRect[3] = True
		else:
			sRect[3] = False
menuOffset = 0
def weaponMenuDraw():
	# black background
	pygame.draw.rect(win, (10,10,10), (int(winWidth - 100),int(0) ,100 ,winHeight))
	# draw main weapons
	for i in wRects:
		if not i[2]:
			continue
		if i[3]:# selected
			pygame.draw.rect(win, (255,0,0), rectOffset(i[2], menuOffset))
		else:
			pygame.draw.rect(win, i[4], rectOffset(i[2], menuOffset))
		# text
		win.blit(i[1], ((i[2][0] +1, i[2][1] +1 - menuOffset)))
		# amount
		if currentTeam.weaponCounter[i[0]] > 0:
			color = (0,0,0) if i[5] == 0 else (170,170,170)
			win.blit(myfont.render(str(currentTeam.weaponCounter[i[0]]), False, color), ((winWidth - 20, i[2][1] +1 - menuOffset)))
	if not currentTeam.hasSpecial:
		return
	for i in sRects:
		if i[3]:
			pygame.draw.rect(win, (255,255,0), i[2])
		else:
			pygame.draw.rect(win, (255,255,255), i[2])
		win.blit(i[1], ((i[2][0] +1, i[2][1] +1)))
		if currentTeam.specialCounter[i[0]] >= 0:
			win.blit(myfont.render(str(currentTeam.specialCounter[i[0]]), False, (0,0,0)), ((winWidth - 100 -20, i[2][1] +1)))

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
	timer = 0
	mode = 0 #0-wait, 1-render, 2-show
	textSurf = None
	name = None
	stringsDmg = [("", " is no more"), ("", " is an ex-worm"), ("", " bit the dust"), ("", " has been terminated"), ("poor ", ""), ("so long ", ""), ("", " will see you on the other side"), ("", " diededed")]
	stringsFlw = [(""," is swimming with the fishes"), ("there goes ", " again"), ("its bye bye for ", ""), ("", " has drowed"), ("", " swam like a brick"), ("", " has gone to marry a mermaid"), ("", " went to ort braude"), ("", " has divided by zero")]
	stringsCrt = [("a jewel from the heavens!", ""), ("its raining crates, halelujah!", ""), (" ","")]
	def step(self):
		if self.mode == 0:
			if len(self.que) == 0:
				return
			else:
				self.mode = 1
		elif self.mode == 1:
			nameSurf = myfont.render(self.que[0][0], False, self.que[0][2])
				
			string1 = self.que[0][1][0]
			string2 = self.que[0][1][1]
			
			stringSurf1 = myfont.render(string1, False, (0,0,0))
			stringSurf2 = myfont.render(string2, False, (0,0,0))
			# combine strings
			self.textSurf = pygame.Surface((nameSurf.get_width() + stringSurf1.get_width() + stringSurf2.get_width(), nameSurf.get_height())).convert_alpha()
			self.textSurf.fill((0,0,0,0))
			self.textSurf.blit(stringSurf1, (0,0))
			self.textSurf.blit(nameSurf, (stringSurf1.get_width(),0))
			self.textSurf.blit(stringSurf2, (stringSurf1.get_width() + nameSurf.get_width() ,0))
			# print(self.que)
			self.que.pop(0)
			self.mode = 2
			self.timer = 2*30 + 1*15
		elif self.mode == 2:
			win.blit(self.textSurf, (int(winWidth/2 - self.textSurf.get_width()/2), 10))
			
			self.timer -= 1
			if self.timer == 0:
				self.mode = 0
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
	file.write(str(time) + "\n")
	
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
	if unlimitedMode: return
	for i in range(amount):
		for team in teams:
			effect = choice(["holy grenade", "gemino mine", "bee hive", "mine strike", "electro boom", "pokeball", "green shell"])
			team.weaponCounter[weaponDict[effect]] += 1
			if randint(0,2) >= 1:
				effect = choice([MOON_GRAVITY, TELEPORT, JETPACK, AIM_AID, SWITCH_WORMS])
				team.specialCounter[effect] += 1
				team.hasSpecial = True
			if randint(0,7) == 1:
				team.weaponCounter[weaponDict["portal gun"]] += 1

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

def scrollMenu(up = True):
	length = len([i for i in currentTeam.weaponCounter if not i == 0]) + 1
	max = (length - 24)*10
	global menuOffset
	if up:
		menuOffset -= 50
		if menuOffset < 0:
			menuOffset = 0
	else:
		menuOffset += 50
		if menuOffset > max:
			menuOffset = max

def isOnMap(vec):
	return not (vec[0] < 0 or vec[0] >= mapWidth or vec[1] < 0 or vec[1] >= mapHeight)

class Cam:
	pos = Vector()

def cheatActive(code):
	if code == "gibguns=":
		unlimitedMode = True
		for team in teams:
			for i in range(len(team.weaponCounter)):
				team.weaponCounter[i] = -1
			team.specialCounter = [99] * len(specialStr)
			team.hasSpecial = True
		for wRect in wRects:
			wRect[5] = 0
	if code == "suddendeath=":
		suddenDeath()
	if code == "wind=":
		global wind
		wind = uniform(-1,1)
	if code == "goodbyecruelworld=":
		boom(objectUnderControl.pos, 100)
	if code == "armageddon=":
		Armageddon()
	if code == "reset=":
		global state, nextState
		state, nextState = RESET, RESET
################################################################################ State machine
if True:
	RESET = 0; GENERATE_TERRAIN = 1; PLACING_WORMS = 2; CHOOSE_STARTER = 3; PLAYER_CONTROL_1 = 4
	PLAYER_CONTROL_2 = 5; WAIT_STABLE = 6; FIRE_MULTIPLE = 7; OPEN_MENU = 8; WIN = 9
	
	state, nextState = RESET, RESET

	gameStable = False; playerScrollAble = False; playerControl = False
	playerControlPlacing = False; playerShootAble = False; gameStableCounter = 0

def stateMachine():
	global state, nextState, gameStable, playerControl, playerControlPlacing, playerShootAble, playerScrollAble
	global objectUnderControl, camTrack, gameStable, gameStableCounter, shotCount, fireWeapon, currentWeapon, run
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
		
		nextState = PLACING_WORMS
		state = nextState
	elif state == PLACING_WORMS:
		playerControlPlacing = True #can move with mouse and place worms, but cant play them
		playerControl = False
		playerScrollAble = True
		
		nextState = CHOOSE_STARTER
		if randomPlace:
			randomPlacing(wormsPerTeam)
		if diggingMatch:
			placeMines(100)
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
		
		if randomWeapons: randomWeaponsGive()
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
	elif state == PLAYER_CONTROL_1 or state == OPEN_MENU:
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
		
		if currentWeapon == "flame thrower" or currentWeapon == "minigun":
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
	if objectUnderControl and playerControl:
		if weaponStyle == CHARGABLE and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
			energising = True
			energyLevel = 0
			fireWeapon = False
			if currentWeapon == "homing missile" and not showTarget:
				energising = False
	if Sheep.trigger == False:
		Sheep.trigger = True

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
		if timeTravel:
			timeTravelPlay()
			energyLevel = 0
		elif weaponStyle == CHARGABLE and energising:
			fireWeapon = True
		# putable/gun weapons case
		elif (weaponStyle in [PUTABLE, GUN]) and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0 and not currentWeapon == "rope":
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
				if currentWeapon == "girder":
					girder((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
					timeRemaining(5)
					state = nextState
				if currentWeapon == "teleport":
					currentTeam.specialCounter[TELEPORT] -= 1
					currentWeapon = "missile"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					objectUnderControl.pos = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
					timeRemaining(5)
					state = nextState
				if currentWeapon == "airstrike" and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
					fireAirstrike((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
					currentTeam.weaponCounter[weaponDict[currentWeapon]] -= 1
					renderWeaponCount()
					timeRemaining(5)
					state = nextState
				if currentWeapon == "mine strike" and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
					fireMineStrike((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
					currentTeam.weaponCounter[weaponDict[currentWeapon]] -= 1
					renderWeaponCount()
					timeRemaining(5)
					state = nextState
				if currentWeapon == "napalm strike" and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
					fireNapalmStrike((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
					currentTeam.weaponCounter[weaponDict[currentWeapon]] -= 1
					renderWeaponCount()
					timeRemaining(5)
					state = nextState

			if state == PLAYER_CONTROL_1 and currentWeapon == "homing missile":
				Target.x, Target.y = mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y
				showTarget = True
			# cliking in menu
			if state == OPEN_MENU:
				for wRect in wRects:
					if wRect[3]:
						# print(wRect[5])
						if not wRect[5] == 0:
							break
						currentWeapon = weaponDictI[wRect[0]]
						renderWeaponCount()
						weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
						state = PLAYER_CONTROL_1
						wRect[3] = False
						break
				for sRect in sRects:
					if sRect[3] and currentTeam.specialCounter[sRect[0]] > 0:
						# decrease:
						currentTeam.specialCounter[sRect[0]] -= 1
						# check if has special:
						currentTeam.hasSpecial = False
						for i in currentTeam.specialCounter:
							if i > 0:
								currentTeam.hasSpecial = True
								break
						# apply effect:
						if sRect[0] == MOON_GRAVITY:
							# global globalGravity
							globalGravity = 0.1
						elif sRect[0] == DOUBLE_DAMAGE:
							# global damageMult
							damageMult += damageMult
							radiusMult *= 1.5
						elif sRect[0] == AIM_AID:
							# global aimAid
							aimAid = True
						elif sRect[0] == TELEPORT:
							currentWeapon = "teleport"
							weaponStyle = CLICKABLE
							currentTeam.specialCounter[sRect[0]] += 1
							renderWeaponCount(True)
						elif sRect[0] == SWITCH_WORMS:
							if switchingWorms:
								currentTeam.specialCounter[sRect[0]] += 1
							switchingWorms = True
						elif sRect[0] == TIME_TRAVEL:
							if not timeTravel:
								timeTravelInitiate()
						elif sRect[0] == JETPACK:
							objectUnderControl.toggleJetpack()
						state = PLAYER_CONTROL_1
					sRect[3] = False
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)\
			# testing mainly
			if state == PLAYER_CONTROL_1:
				# mouse = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
				# Portal(mouse)
				# HealthPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# WeaponPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# p = UtilityPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# camTrack = w
				pass
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
			# this is the next state after placing all worms
			if state == PLACING_WORMS:
				state = nextState
				renderWeaponCount()
			elif state == PLAYER_CONTROL_1:
				state = OPEN_MENU
				weaponMenuInit()
			elif state == OPEN_MENU:
				state = PLAYER_CONTROL_1
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll up
			if state == OPEN_MENU:
				scrollMenu()
			else:
				# if not camTrack:
					# Cam.pos = Vector((screenWidth/2)/scalingFactor + camPos.x, (screenHeight/2)/scalingFactor + camPos.y)
					# camTrack = Cam
				scalingFactor *= 1.1
				if scalingFactor >= 3: scalingFactor = 3
				# winWidth = int(1280 / scalingFactor)
				# winHeight = int(720 / scalingFactor)
				# win = pygame.Surface((winWidth, winHeight))
				
				# camTarget.x = camTrack.pos.x - winWidth /2
				# camTarget.y = camTrack.pos.y - winHeight /2
				# camPos = vectorCopy(camTarget)
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll down
			if state == OPEN_MENU:
				scrollMenu(False)
			else:
				# if not camTrack:
					# Cam.pos = Vector((screenWidth/2)/scalingFactor + camPos.x, (screenHeight/2)/scalingFactor + camPos.y)
					# camTrack = Cam
				scalingFactor *= 0.9
				if scalingFactor <= 1: scalingFactor = 1
				# winWidth = int(1280 / scalingFactor)
				# winHeight = int(720 / scalingFactor)
				# win = pygame.Surface((winWidth, winHeight))
				
				# camTarget.x = camTrack.pos.x - winWidth /2
				# camTarget.y = camTrack.pos.y - winHeight /2
				# camPos = vectorCopy(camTarget)

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
				if event.key == pygame.K_1:
					currentWeapon = "missile"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_2:
					currentWeapon = "grenade"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_3:
					currentWeapon = "mortar"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_4:
					currentWeapon = "petrol bomb"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_5:
					currentWeapon = "TNT"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_6:
					currentWeapon = "shotgun"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_7:
					currentWeapon = "girder"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_8:
					currentWeapon = "flame thrower"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_9:
					currentWeapon = "sticky bomb"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_0:
					currentWeapon = "minigun"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					renderWeaponCount()
				elif event.key == pygame.K_MINUS:
					currentWeapon = "rope"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
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
				elif state == PLAYER_CONTROL_1 and currentWeapon == "plant seed":
					PlantBomb.venus = not PlantBomb.venus
					if PlantBomb.venus:
						FloatingText(objectUnderControl.pos + Vector(0,-5), "venus fly trap", (20,20,20))
					else:
						FloatingText(objectUnderControl.pos + Vector(0,-5), "plant mode", (20,20,20))
				elif state == PLAYER_CONTROL_1 and weaponStyle == CHARGABLE and not currentWeapon == "bunker buster":
					fuseTime += 30
					if fuseTime > 120:
						fuseTime = 30
					string = "delay " + str(fuseTime//30) + " sec"
					FloatingText(objectUnderControl.pos + Vector(0,-5), string, (20,20,20))
				elif state == PLAYER_CONTROL_1 and currentWeapon == "girder":
					girderAngle += 45
					if girderAngle == 180:
						girderSize = 100
					if girderAngle == 360:
						girderSize = 50
						girderAngle = 0
				elif state == PLAYER_CONTROL_1 and switchingWorms:
					switchWorms()
			if event.key == pygame.K_t:
				# Missile(CpuHolder.initialPos, CpuHolder.direction, CpuHolder.energy)
				pass
			if event.key == pygame.K_y:
				# objectUnderControl.cpu = not objectUnderControl.cpu
				pass
			if event.key == pygame.K_PAGEUP or event.key == pygame.K_KP9:
				scrollMenu()
			if event.key == pygame.K_PAGEDOWN or event.key == pygame.K_KP3:
				scrollMenu(False)
			if event.key == pygame.K_F2:
				Worm.healthMode = (Worm.healthMode + 1) % 2
				if Worm.healthMode == 1:
					for worm in PhysObj._worms:
						worm.healthStr = myfont.render(str(worm.health), False, worm.team.color)
			
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
	
	# use edge map scroll
	if playerScrollAble and pygame.mouse.get_focused():
		mousePos = pygame.mouse.get_pos()
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
	if mapClosed:
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
			gameStable = False
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
	for p in PhysObj._reg: p.draw()
	for f in nonPhys: f.draw()
	drawTarget()
	# draw shooting indicator
	if objectUnderControl and state in [PLAYER_CONTROL_1, PLAYER_CONTROL_2, FIRE_MULTIPLE, OPEN_MENU] and objectUnderControl.health > 0:
		objectUnderControl.drawCursor()
		if aimAid and weaponStyle == GUN:
			p1 = vectorCopy(objectUnderControl.pos)
			p2 = point1 + Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle)) * 500
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
	
	if not state in [RESET, GENERATE_TERRAIN, PLACING_WORMS, CHOOSE_STARTER] and drawHealthBar: teamHealthDraw()
	# weapon menu:
	if state == OPEN_MENU:
		weaponMenuStep()
		weaponMenuDraw()
	
	# debug:
	win.blit(myfont.render(str(int(damageThisTurn)), False, (0,0,0)), ((int(10), int(winHeight-6))))
	if state == PLACING_WORMS:
		win.blit(myfont.render(str(len(PhysObj._worms)), False, (0,0,0)), ((int(20), int(winHeight-6))))
	
	# reset actions
	actionMove = False
	
	# screen manegement
	screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
	
	pygame.display.update()
	
pygame.quit()

