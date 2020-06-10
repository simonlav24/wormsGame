from math import pi, cos, sin, atan2, sqrt, exp, degrees
from random import uniform, randint, choice, shuffle
from vector import *
import pygame
from pygame import gfxdraw
pygame.init()

fpsClock = pygame.time.Clock()

pygame.font.init()
myfont = pygame.font.Font("fonts\pixelFont.ttf", 5)
myfontbigger = pygame.font.Font("fonts\pixelFont.ttf", 10)

### TO DO LIST
# https://worms2d.info/Weapons_(Worms_Unlimited)
# balloon/jetpack
# something electrical
# hamburger ?
# termites
# time travel utility based on actions and weapon
#
# problem with worm switch, cant switch weapons in menu sometimes work

scalingFactor = 3
winWidth = int(1280 / scalingFactor)
winHeight = int(720 / scalingFactor)
win = pygame.Surface((winWidth, winHeight))

screenWidth = int(winWidth * scalingFactor)
screenHeight = int(winHeight * scalingFactor)
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
	
	MISSILES = (255, 255, 255)
	GRENADES = (204, 255, 204)
	GUNS = (255, 204, 153)
	FIREY = (255, 204, 204)
	LEGENDARY = (255, 255, 102)
	MISC = (224, 224, 235)
	AIRSTRIKE = (204, 255, 255)

# Game parameters
turnTime = 40 
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

# Multipliers
damageMult = 0.8
fallDamageMult = 1
windMult = 1.5
radiusMult = 1

################################################################################ Map
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
	
def makeBoundary():
	for i in range(mapHeight):
		map[i * mapWidth + 0] = GRD
		map[i * mapWidth + mapWidth-1] = GRD

def makeLowBoundary():
	for i in range(mapWidth):
		map[(mapHeight - 1) * mapWidth + i] = GRD

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
	radius *= radiusMult
	global camTrack
	boomPos = Vector(pos[0], pos[1])
	# ground delete
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
			d = Debrie(pos, radius/5)
			d.radius = choice([1,2])

def drawWindIndicator():
	pygame.draw.line(win, (100,100,255), (20, 15), (int(20 + wind * 20),15))
	pygame.draw.line(win, (0,0,255), (20, 10), (20,20))

def giveGoodPlace():
	goodPlace = False
	counter = 0###
	if not diggingMatch:
		while not goodPlace:
			counter += 1
			goodPlace = True
			place = Vector(randint(6, mapWidth - 6), randint(6, mapHeight - 6))
			# check circle around
			if isGroundAround(place):
				goodPlace = False
			if  not goodPlace:
				continue
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
			place = Vector(randint(6, mapWidth - 6), randint(6, mapHeight - 50))
			goodPlace = True
			for worm in PhysObj._worms:
				if dist(worm.pos, place) < 75:
					goodPlace = False
					break
				if  not goodPlace:
					continue
		
	# if counter >= 7090:
		# print("above 7090:", counter)
	return place

def placePetrolCan(quantity = 1):
	noPlace = []
	
	for times in range(quantity):
		place = giveGoodPlace()
		PetrolCan((place.x, place.y - 2))

def placeMines(quantity = 1):
	noPlace = []
	
	for times in range(quantity):
		place = giveGoodPlace()
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

def clamp(value, upper, lower):
	if value > upper:
		value = upper
	if value < lower:
		value = lower
	return value

def color2str(color):
	if color == RED:
		return "red"
	elif color == YELLOW:
		return "yellow"
	elif color == GREEN:
		return "green"
	elif color == BLUE:
		return "blue"

def sign(x):
	if x > 0:
		return 1
	elif x < 0:
		return -1
	return 0
imageMountain = pygame.image.load("mountain.png").convert_alpha()
imageMountain2 = pygame.image.load("mountain2.png").convert_alpha()
imageSky = pygame.transform.scale(pygame.image.load("sky.png"), (winWidth, winHeight))
imageCloud = pygame.image.load("cloud.png").convert_alpha()

def drawBackGround(surf, parallax):
	width = surf.get_width()
	height = surf.get_height()
	offset = (camPos.x/parallax)//width
	for i in range(4):
		x = int(-camPos.x/parallax) + int(int(offset) * width + i * width)
		y =  int(mapHeight - height) - int(camPos.y) - int((int(mapHeight - winHeight) - int(camPos.y))/parallax)
		win.blit(surf, (x, y))

def point2world(point):
	return (int(point[0]) - int(camPos[0]), int(point[1]) - int(camPos[1]))
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
	global state, nextState
	if state == PLAYER_CONTROL_1:
		state = WAIT_STABLE
	elif state == PLAYER_CONTROL_2:
		state = nextState
	elif state == FIRE_MULTIPLE:
		state = PLAYER_CONTROL_2
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
		self.windAffected = False
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
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), int(self.radius)+1)

class Debrie (PhysObj):
	def __init__(self, pos, blast):
		self.initialize()
		self.vel = Vector(cos(uniform(0,1) * 2 *pi), sin(uniform(0,1) * 2 *pi)) * blast
		self.pos = Vector(pos[0],pos[1])
		
		self.boomAffected = False
		self.bounceBeforeDeath = 2
		self.color = (62,201,83)
		self.radius = 1
		self.damp = 0.5
	def applyForce(self):
		# gravity:
		self.acc.y += globalGravity * 2.5
	def draw(self):
		pygame.draw.circle(win, self.color, (int(self.pos.x - camPos.x), int(self.pos.y - camPos.y)), int(self.radius))

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
	def __init__(self, pos, name=None, team=None):
		self._worms.append(self)
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.color = (255, 206, 167)
		self.radius = 3.5
		self.damp = 0.2
		self.facing = RIGHT
		self.shootAngle = 0
		self.shootAcc = 0
		self.shootVel = 0
		self.health = initialHealth
		self.team = team
		self.teamColor = team.color
		self.sick = False
		self.gravity = DOWN
		if name:
			self.nameStr = name
		else:
			self.nameStr = randomNames.pop()
		self.name = myfont.render(self.nameStr, False, self.teamColor)
		self.score = 0
	def applyForce(self):
		# gravity:
		if self.gravity == DOWN:
			self.acc.y += globalGravity
		else:# up
			self.acc.y -= globalGravity
	def drawCursor(self):
		shootVec = self.pos + Vector((cos(self.shootAngle) * 20) ,sin(self.shootAngle) * 20)
		pygame.draw.circle(win, (255,255,255), (int(shootVec.x) - int(camPos.x), int(shootVec.y) - int(camPos.y)), 2)
	def sicken(self):
		self.sick = True
		self.color = (128, 189,66)
	def damage(self, value):
		if self.health > 0: # if alive
			dmg = int(value * damageMult)
			if dmg < 1:
				dmg = 1
			if dmg > self.health:
				dmg = self.health
			
			FloatingText(self.pos.vec2tup(), str(dmg))
			self.health -= dmg
			global damageThisTurn
			if not self == objectUnderControl:
				if not sentring and not self in objectUnderControl.team.worms:
					damageThisTurn += dmg
			if self.health < 0:
				self.health = 0
	def move(self):
		if not objectUnderControl == self or not self.health > 0:
			return
		dir = self.facing
		if self.checkFreePos(self.pos + Vector(dir, 0)):
			self.pos += Vector(dir, 0)
			return
		else:
			for i in range(1,5):
				if self.checkFreePos(self.pos + Vector(dir, -i)):
					self.pos += Vector(dir, -i)
					return
			for i in range(1,5):
				if self.checkFreePos(self.pos + Vector(dir, i)):
					self.pos += Vector(dir, i)
					return
	def checkFreePos(self, pos):
		r = 0
		while r < 2 * pi:
			testPos = Vector((self.radius) * cos(r) + pos.x, (self.radius) * sin(r) + pos.y)
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
	def draw(self):
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), int(self.radius)+1)
		win.blit(self.name , ((int(self.pos.x) - int(camPos.x) - int(self.name.get_size()[0]/2)), (int(self.pos.y) - int(camPos.y) - 21)))
		if self.health > 0 and drawHealthBar:
			self.drawHealth()
	def __str__(self):
		return self.nameStr
	def __repr__(self):
		return str(self)
	def destroy(self):
		global state, nextState, teams
		if self in self._worms:
			self._worms.remove(self)
			self.team.worms.remove(self)
			if objectUnderControl == self:
				# self died and is objectUnderControl
				if state == FIRE_MULTIPLE:
					nextState = WAIT_STABLE
				state = nextState
				timeRemaining(5)
	def drawHealth(self):
		pygame.draw.rect(win, (220,220,220),(int(self.pos.x) -10 -int(camPos.x), int(self.pos.y) -15 -int(camPos.y), 20,3))
		value = 20 * min(self.health/initialHealth, 1)
		if value < 1:
			value = 1
		pygame.draw.rect(win, (0,220,0),(int(self.pos.x) -10 -int(camPos.x), int(self.pos.y) -15 -int(camPos.y), int(value),3))
	def secondaryStep(self):
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
		
		self.shootVel = clamp(self.shootVel + self.shootAcc, 0.1, -0.1)
		self.shootAngle += self.shootVel * self.facing
		if self.facing == RIGHT:
			self.shootAngle = clamp(self.shootAngle, pi/2, -pi/2)
		elif self.facing == LEFT:
			self.shootAngle = clamp(self.shootAngle, pi + pi/2, pi/2)

		global state, nextState
		if self.health <= 0:
			self.color = (167,167,167)
			self.destroy()
		# check if on map:
		if self.pos.y >= mapHeight: #if true than worm is out of map
			global damageThisTurn
			if not self == objectUnderControl:
				if not sentring and not self in objectUnderControl.team.worms:
					damageThisTurn += self.health
			self.health = 0
			self.destroy()
			self._reg.remove(self)
		if self.pos.y < 0:
			self.gravity = DOWN
		if actionMove or actionMove:
			self.move()
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
		self.pos = Vector(pos[0], pos[1])
		self.damp = 0
		self.color = (255,106,69)
		self.radius = 2
		self.windAffected = True
		self.life = randint(50,70)
		self.fallen = False
		self.delay = delay
		self.timer = 0
	def collisionRespone(self, ppos):
		self.fallen = True
	def secondaryStep(self):
		self.timer += 1
		if self.fallen:
			self.life -= 1
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
		pygame.draw.circle(win, self.color, (int(self.pos.x - camPos.x), int(self.pos.y - camPos.y)), radius)

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
		if self.timer == 120:
			self.dead = True
	def deathResponse(self):
		global camTrack, grenadeThrown, grenadeTimer
		boom(self.pos, 40)
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -2) - int(camPos.x),int(self.pos.y -4) - int(camPos.y) , 3,8))

shotCount = 0
def fireShotgun(start, direction, power=15):#6
	if power == 15 and randint(0,100) == 1:
		power = 30
	hit = False
	for t in range(5,500):
		testPos = start + direction * t
		extra.append((testPos.x, testPos.y, (255,255,0), 3))
		
		if testPos.x >= mapWidth or testPos.y >= mapHeight or testPos.x < 0 or testPos.y < 0:
			break
		# if hits worm:
		for worm in PhysObj._worms:
			if dist(testPos, worm.pos) < worm.radius:
				boom(testPos, power)
				worm.vel += direction*2
				hit = True
			
		if hit:
			break
		
		# if hits map:
		# if map[int(testPos.y) * mapWidth + int(testPos.x)] == GRD:
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
	def __init__(self, pos = (0,0)):
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
		self._reg.remove(self)
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
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), int(self.radius)+1)
		# pygame.draw.circle(win, (52,66,71,10), (int(self.pos.x - camPos.x), int(self.pos.y - camPos.y)), 35)
		if not self.activated:
			pygame.draw.circle(win, (222,63,49), (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), 1)
		else:
			if self.timer % 2 == 0:
				pygame.draw.circle(win, (222,63,49), (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), 1)

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
	def __init__(self, pos):
		PhysObj._reg.append(self)
		self.color = (102, 255, 127, 100)
		self.radius = randint(8,18)
		self.pos = tup2vec(pos)
		self.acc = Vector(0,0)
		self.vel = Vector(0,0)
		self.stable = False
		self.boomAffected = False
		self.time = 0
	def draw(self):
		pygame.gfxdraw.filled_circle(win, int(self.pos.x - camPos.x), int(self.pos.y - camPos.y), self.radius, self.color)
	def step(self):
		self.time += 1
		if self.time % 8 == 0:
			self.radius -= 1
			if self.radius == 0:
				PhysObj._reg.remove(self)
				del self
				return
		self.acc.x = wind * 0.1 * windMult * uniform(0.2,1)
		self.acc.y = -0.1
		self.vel += self.acc
		self.pos += self.vel
		for worm in PhysObj._worms:
			if dist(self.pos, worm.pos) < self.radius + worm.radius:
				worm.sicken()

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
		# if worm.health > 100:
			# worm.health = 100
		worm.sick = False
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
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -5) - int(camPos.x),int(self.pos.y -5) - int(camPos.y) , 10,10))
		win.blit(self.surf, (int(self.pos.x) - int(camPos.x)-1, int(self.pos.y) - int(camPos.y)-2))
	def effect(self, worm):
		effect = choice([MOON_GRAVITY, DOUBLE_DAMAGE, AIM_AID, TELEPORT, SWITCH_WORMS, TIME_TRAVEL])
		if effect == MOON_GRAVITY:
			FloatingText(self.pos, "moon gravity", (0,200,200))
		elif effect == DOUBLE_DAMAGE:
			FloatingText(self.pos, "double damage", (0,200,200))
		elif effect == AIM_AID:
			FloatingText(self.pos, "aim aid", (0,200,200))
		elif effect == TELEPORT:
			FloatingText(self.pos, "teleport", (0,200,200))
		elif effect == SWITCH_WORMS:
			FloatingText(self.pos, "switch worms", (0,200,200))
		elif effect == TIME_TRAVEL:
			FloatingText(self.pos, "time travel", (0,200,200))
		worm.team.hasSpecial = True
		worm.team.specialCounter[effect] += 1

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
	def draw(self):
		pygame.draw.rect(win, self.color, (int(self.pos.x -5) - int(camPos.x),int(self.pos.y -5) - int(camPos.y) , 10,10))
		win.blit(self.surf, (int(self.pos.x) - int(camPos.x)-2, int(self.pos.y) - int(camPos.y)-2))
	def effect(self, worm):
		effect = choice(["banana", "holy grenade", "earthquake", "gemino mine", "sentry gun", "bee hive", "vortex grenade", "buster strike"])
		FloatingText(self.pos, effect, (0,200,200))
		worm.team.weaponCounter[weaponDict[effect]] += 1

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

def fireBusterStrike(pos):
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
			break
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
		win.blit(surf , (int(self.pos.x - camPos.x - surf.get_size()[0]/2), int(self.pos.y - camPos.y - surf.get_size()[1]/2)))

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

class ClusterRand(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,100,0)
		self.damp = 0.5
		self.timer = 0
		self.activate = False
	def deathResponse(self):
		# for i in range(12):
			# fireShotgun(self.pos, Vector(cos((i/12) * pi), sin((i/12) * pi)))
		pass
	def secondaryStep(self):
		self.timer += 1
		if self.timer == 70:
			self.activate = True
			self.boomAffected = False
		if self.activate:
			if self.timer % 3 == 0:
				fireShotgun(self.pos, vectorUnitRandom())
			if self.timer == 150:
				self.dead = True
		
class Cluster(Grenade):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0,100,0)
		self.damp = 0.5
		self.timer = 0
		self.activate = False
	def deathResponse(self):
		# for i in range(12):
			# fireShotgun(self.pos, Vector(cos((i/12) * pi), sin((i/12) * pi)))
		pass
	def secondaryStep(self):
		self.timer += 1
		if self.timer == 70:
			self.activate = True
			self.boomAffected = False
		if self.activate:
			if self.timer % 2 == 0:
				# boom(self.pos, randint(15, 50))
				# fireShotgun(self.pos, Vector(cos(self.timer/2), sin(self.timer/2)))
				# Missile(self.pos, vectorUnitRandom(), 1)
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
	def __init__(self, pos, radius = 5, direction = -1):
		PhysObj._reg.append(self)
		self.pos = Vector(pos[0], pos[1])
		if direction == -1:
			self.direction = uniform(0, 2*pi)
		else:
			self.direction = direction
		self.stable = False
		self.boomAffected = False
		self.radius = radius
		self.time = 0
		self.green = 170
	def step(self):
		self.pos += vectorFromAngle(self.direction + uniform(-1,1))
		if randint(1,100) <= 2:
			Plant(self.pos, self.radius, self.direction + choice([pi/3, -pi/3]))
		self.time += 1
		if self.time % 10 == 0:
			self.radius -= 1
		self.green += randint(-5,5)
		if self.green > 255:
			self.green = 255
		if self.green < 0:
			self.green = 0
		pygame.draw.circle(map, GRD, (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		pygame.draw.circle(ground, (0,self.green,0), (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		
		if self.radius == 0:
			PhysObj._reg.remove(self)
			del self
	def draw(self):
		pass

class PlantBomb(PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (204, 204, 0)
		self.bounceBeforeDeath = 1
		self.damp = 0.5
	def deathResponse(self):
		for i in range(randint(4,5)):
			Plant(self.pos)

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
			if self.timer <= 0 and self.target:
				fireMiniGun(self.pos, self.target.pos - self.pos)
				self.shots -= 1
				if self.shots == 0:
					self.firing = False
					self.shots = 10
					self.timer = 20
					self.timesFired -= 1
					if self.timesFired == 0:
						self.health = 0

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
		point1 = self.pos + vectorFromAngle(-5*pi/4, self.radius+2)
		point3 = self.pos + vectorFromAngle(pi/4, self.radius+2)
		pygame.draw.lines(win, self.color, False, [point2world(point1), point2world(self.pos), point2world(point3)], 3)
		pygame.draw.rect(win, (0, 51, 0), (point2world((self.pos.x - 3, self.pos.y - 2)), (6, 4)) )
		pygame.draw.circle(win, self.teamColor, point2world(self.pos + Vector(2,0)), 1)
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
			self.angle += uniform(-1,1)
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
		self.windAffected = False
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
		boom(self.pos, 30)
		
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
		self.timer += 1
		if self.timer == fuseTime:
			self.electrifying = True
		if self.timer >= fuseTime + self.lifespan:
			self.dead = True
		if self.electrifying:
			self.stable = False
			for worm in PhysObj._worms:
				if dist(self.pos, worm.pos) < 100 and not worm in self.worms:
					self.worms.append(worm)
				if dist(self.pos, worm.pos) >= 100 and worm in self.worms:
					self.worms.remove(worm)
			if len(self.worms) == 0:
				self.emptyCounter += 1
				if self.emptyCounter == 30:
					self.dead = True
			else:
				self.emptyCounter = 0
		for worm in self.worms:
			if randint(1,100) < 5:
				worm.damage(randint(1,8))
				worm.vel -= Vector(sign(self.pos.x - worm.pos.x)*uniform(0.8,2.2), uniform(0.8,2.2))
			if worm.health <= 0:
				self.worms.remove(worm)
		
	
	def draw(self):
		pygame.draw.circle(win, self.color, (int(self.pos.x) - int(camPos.x), int(self.pos.y) - int(camPos.y)), int(self.radius)+1)
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
		nonPhys.append(self)
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
			nonPhys.remove(self)
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
def timeTravelRecord():
	timeTravelPositions.append(objectUnderControl.pos.vec2tup())
def timeTravelPlay():
	global timeTravel, time, timeTravelList
	time = timeTravelList["time in turn"]
	timeTravel = False
	timeTravelList["weapon"] = currentWeapon
	timeTravelList["weaponOrigin"] = vectorCopy(objectUnderControl.pos)
	timeTravelList["energy"] = energyLevel
	timeTravelList["weaponDir"] = Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle))
	objectUnderControl.pos = timeTravelList["initial pos"]
	TimeAgent()
def timeTravelReset():
	global timeTravelPositions, timeTravelList, timeTravelFire
	timeTravelFire = False
	timeTravelPositions = []
	timeTravelList = {}
	
################################################################################ Create World

maps = []
for i in range(1,58):
	string = "wormsMaps/wMap" + str(i) + ".png"
	maps.append((string, 512))
maps.append(("wormsMaps/wMapbig1.png", 1000))
maps.append(("wormsMaps/wMapbig2.png", 800))

def createWorld():
	global mapClosed
	# imageFile = ("lastWormsGround.png", 512)
	imageChoice = choice(maps)
	imageChoice = maps[26 - 1]
	
	if imageChoice in [maps[i] for i in [19-1, 26-1, 40-1, 41-1]]: mapClosed = True
	imageFile, heightNorm = imageChoice
	
	global mapImage
	mapImage = pygame.image.load(imageFile)
	
	if not diggingMatch: createMapImage(heightNorm)
	else: mapImage = None; createMapDigging()
		
	placePetrolCan(randint(2,3))
	placeMines(randint(2,3))
	randomLegendary(1)
	if diggingMatch: moreDigging()
	renderLand()

# drawHealthBar = False
# randomPlace = False
# mapClosed = True
# diggingMatch = True
wormsPerTeam = 8

################################################################################ Weapons setup

weapons = []
if True:
	weapons.append(("dummy", -1, 0, (0,0,0)))
	weapons.append(("missile", CHARGABLE, -1, MISSILES))
	weapons.append(("gravity missile", CHARGABLE, 10, MISSILES))
	weapons.append(("bunker buster", CHARGABLE, 2, MISSILES))
	weapons.append(("homing missile", CHARGABLE, 2, MISSILES))
	weapons.append(("grenade", CHARGABLE, 10, GRENADES))
	weapons.append(("mortar", CHARGABLE, 3, GRENADES))
	weapons.append(("sticky bomb", CHARGABLE, 3, GRENADES))
	weapons.append(("gas grenade", CHARGABLE, 5, GRENADES))
	weapons.append(("electric grenade", CHARGABLE, 3, GRENADES))
	weapons.append(("shotgun", GUN, 15, GUNS))
	weapons.append(("minigun", GUN, 6, GUNS))
	weapons.append(("gamma gun", GUN, 6, GUNS))
	weapons.append(("petrol bomb", CHARGABLE, 5, FIREY))
	weapons.append(("flame thrower", PUTABLE, 5, FIREY))
	weapons.append(("mine", PUTABLE, 5, GRENADES))
	weapons.append(("TNT", PUTABLE, 1, GRENADES))
	weapons.append(("baseball", PUTABLE, 3, MISC))
	weapons.append(("girder", CLICKABLE, -1, MISC))
	weapons.append(("plant seed", CHARGABLE, 2, MISC))
	weapons.append(("sentry gun", PUTABLE, 0, MISC))
	weapons.append(("airstrike", CLICKABLE, 1, AIRSTRIKE))
	weapons.append(("napalm strike", CLICKABLE, 1, AIRSTRIKE))
	weapons.append(("mine strike", CLICKABLE, 1, AIRSTRIKE))
	weapons.append(("holy grenade", CHARGABLE, 0, LEGENDARY))
	weapons.append(("banana", CHARGABLE, 0, LEGENDARY))
	weapons.append(("earthquake", PUTABLE, 0, LEGENDARY))
	weapons.append(("gemino mine", CHARGABLE, 0, LEGENDARY))
	weapons.append(("bee hive", CHARGABLE, 0, LEGENDARY))
	weapons.append(("vortex grenade", CHARGABLE, 0, LEGENDARY))
	weapons.append(("buster strike", CLICKABLE, 0, LEGENDARY))

weaponDict = {}
weaponDictI = {}
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
		
	if timeTravelFire:
		decrease = False
		weaponOrigin = timeTravelList["weaponOrigin"]
		energy = timeTravelList["energy"]
		weaponDir = timeTravelList["weaponDir"]
		
	# if currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0: return
		
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
		decrease = True
		if state == PLAYER_CONTROL_1:
			shotCount = 2 #this means 3 shots
		fireShotgun(weaponOrigin, weaponDir)
		if not shotCount == 0:
			shotCount -= 1
			nextState = FIRE_MULTIPLE
		else:
			decrease = True
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
		decrease = True
		if state == PLAYER_CONTROL_1:
			shotCount = 1 #this means 2 shots
		fireGammaGun(weaponOrigin, weaponDir)
		if not shotCount == 0:
			shotCount -= 1
			nextState = FIRE_MULTIPLE
		else:
			decrease = True
	elif weapon == "holy grenade":
		w = HolyGrenade(weaponOrigin, weaponDir, energy)
	elif weapon == "banana":
		w = Banana(weaponOrigin, weaponDir, energy)
	elif weapon == "cluster":
		w = Cluster(weaponOrigin, weaponDir, energy)
	elif weapon == "earthquake":
		Earthquake()
	elif weapon == "gemino mine":
		w = Gemino(weaponOrigin, weaponDir, energy)
	elif weapon == "plant seed":
		w = PlantBomb(weaponOrigin, weaponDir, energy)
	elif weapon == "sentry gun":
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
	elif weapon == "drill missile":
		w = DrillMissile(weaponOrigin, weaponDir, energy)
	elif weapon == "vortex grenade":
		w = VortexGrenade(weaponOrigin, weaponDir, energy)
	
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
for i in range(1,len(weaponDict)):
	index = i
	textSurf = myfont.render(weaponDictI[i], False, (0,0,0))
	rect = (winWidth - 100 + 2, 2 + i * 10 - 10, 100 - 4 ,8)
	selected = False
	color = weapons[i][3]
	wRects.append( [index, textSurf, rect, selected, color] )
specialStr = ["moon gravity", "double damage", "aim aid", "teleport", "switch worms", "time travel"]
sRects = []
for i in range(len(specialStr)):
	textSurf = myfont.render(specialStr[i], False, (0,0,0))
	rect = (winWidth - 200, 2 + i * 10, 100 - 4, 8)
	selected = False
	sRects.append( [i, textSurf, rect, selected] )

################################################################################ Teams
class Team:
	def __init__(self, namesList, color):
		self.nameList = namesList
		self.color = color
		self.weaponCounter = basicSet.copy()
		self.specialCounter = [0] * len(specialStr)
		self.hasSpecial = False
		self.worms = []
	def __len__(self):
		return len(self.worms)
	def addWorm(self, pos):
		if len(self.nameList) > 0:
			self.worms.append(Worm(pos, self.nameList.pop(0), self))
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

blues = Team(["red lion", "commercial", "swan", "brewers", "fred", "sparrow", "eithan", "red"], BLUE)
reds = Team(["fix delux r", "vamp b", "birdie", "lordie", "pinkie", "katie", "angie", "miya"], RED)
greens = Team(["blair", "major", "thatcher", "chellenge", "george", "mark", "mercury", "philip"], GREEN)
yellows = Team(["colan", "GT", "jettets", "chevan", "jonie", "murph", "silvia", "flur"], YELLOW)

# choose playing teams here
teams = [blues, reds, yellows, greens]
shuffle(teams)
totalTeams = len(teams)

currentTeam = choice(teams)
teamChoser = randint(0,3) % totalTeams
roundCounter = 0
mostDamage = (0,None)
damageThisTurn = 0

nWormsPerTeam = 0
teamsInfo = []
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
	elif currentWeapon == "switch worms":
		currentWeaponSurf = myfont.render(currentWeapon + " " + str(currentTeam.specialCounter[SWITCH_WORMS]), False, (0,0,0))
	
def calculateTeamHealth():
	global teamsInfo
	teamsInfo = []
	maxHealth = nWormsPerTeam * initialHealth
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
	global deploying, sentring, deployPacks

	# reset special effects:
	global globalGravity
	globalGravity = 0.2
	global damageMult
	global radiusMult
	damageMult = 0.8
	radiusMult = 1
	global aimAid, switchingWorms, timeTravel
	aimAid = False
	if timeTravel:
		timeTravelReset()
	if switchingWorms:
		if currentWeapon == "switch worms":
			currentWeapon = "missile"
			weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
		switchingWorms = False
		currentTeam.specialCounter[SWITCH_WORMS] -= 1
	
	# update damage:
	if damageThisTurn > mostDamage[0]:
		mostDamage = (damageThisTurn, objectUnderControl.nameStr)
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
				print("team", color2str(team.color), "won!")
				file = open('wormsRecord.txt', 'a')
				file.write("time taken: " + '{:6}'.format(str(int(timeOverall/30))) + " winner: " + '{:10}'.format(color2str(team.color)) \
					 + "most damage: " + '{:6}'.format(int(mostDamage[0])) +" by " + '{:6}'.format(mostDamage[1]) + "\n")
				file.close()
				run = False
				return
	
	roundCounter += 1
	# deploy pack:
	if deployPacks:
		if roundCounter % totalTeams == 0 and not deploying:
			deploying = True
			roundCounter -= 1
			nextState = WAIT_STABLE
			w = deployPack(choice([HEALTH_PACK,UTILITY_PACK, WEAPON_PACK]))
			# print("deploy")
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
			# print("shoot")
			sentring = True
			roundCounter -= 1
			nextState = WAIT_STABLE
			return
			
	deploying = False
	sentring = False
	
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
		if worm.sick and worm.health > 5:
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
	global objectUnderControl, camTrack, switchingWorms
	currentWorm = currentTeam.worms.index(objectUnderControl)
	totalWorms = len(currentTeam.worms)
	currentWorm = (currentWorm + 1) % totalWorms
	objectUnderControl = currentTeam.worms[currentWorm]
	camTrack = objectUnderControl
	switchingWorms = True

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
	counter = 0
	for i in range(wormsPerTeam * len(teams)):
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
	return (rect[0], rect[1] - y, rect[2], rect[3])
	
def weaponMenuStep():
	mousePos = pygame.mouse.get_pos()
	mousePos = (mousePos[0]/scalingFactor, mousePos[1]/scalingFactor)
	for wRect in wRects:
		if mousePos[0] > wRect[2][0] and mousePos[0] < wRect[2][0] + wRect[2][2] and mousePos[1] > wRect[2][1] - menuOffset and mousePos[1] < wRect[2][1] + wRect[2][3] - menuOffset:
			wRect[3] = True
		else:
			wRect[3] = False
	if not currentTeam.hasSpecial:
		return
	for sRect in sRects:
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
		if i[3]:# selected
			# pass
			pygame.draw.rect(win, (255,0,0), rectOffset(i[2], menuOffset))
		else:
			pygame.draw.rect(win, i[4], rectOffset(i[2], menuOffset))
		# text
		win.blit(i[1], ((i[2][0] +1, i[2][1] +1 - menuOffset)))
		# amount
		if currentTeam.weaponCounter[i[0]] >= 0:
			win.blit(myfont.render(str(currentTeam.weaponCounter[i[0]]), False, (0,0,0)), ((winWidth - 20, i[2][1] +1 - menuOffset)))
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
	file.write(str(switchingWorms) + "\n")
	
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
			
def randomLegendary(amount):
	if unlimitedMode: return
	for i in range(amount):
		for team in teams:
			effect = choice(["holy grenade", "gemino mine", "bee hive"])
			team.weaponCounter[weaponDict[effect]] += 1
			
def suddenDeath():
	for worm in PhysObj._worms:
		worm.sicken()
		if not worm.health == 1:
			worm.health = worm.health // 2

def moreDigging():
	for team in teams:
		team.weaponCounter[weaponDict["minigun"]] += 5
		team.weaponCounter[weaponDict["bunker buster"]] += 3
################################################################################ State machine

# states:
RESET = 0; GENERATE_TERRAIN = 1; PLACING_WORMS = 2; CHOOSE_STARTER = 3; PLAYER_CONTROL_1 = 4
PLAYER_CONTROL_2 = 5; WAIT_STABLE = 6; FIRE_MULTIPLE = 7; OPEN_MENU = 8

state = RESET
nextState = RESET

gameStable = False
playerScrollAble = False
playerControl = False
playerControlPlacing = False
playerShootAble = False
gameStableCounter = 0
tempDamage = 0

def stateMachine():
	global state, nextState, gameStable, playerControl, playerControlPlacing, playerShootAble, playerScrollAble
	global objectUnderControl, camTrack, gameStable, gameStableCounter, shotCount, fireWeapon, currentWeapon
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
		
		nextState = PLAYER_CONTROL_2
		if currentWeapon == "shotgun":
			if not shotCount == 0:
				nextState = FIRE_MULTIPLE
		
		if currentWeapon == "flame thrower" or currentWeapon == "minigun":
			fireWeapon = True
			if not shotCount == 0:
				nextState = FIRE_MULTIPLE

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

namesFile = open("names.txt", "r")
randomNames = namesFile.read().splitlines()
shuffle(randomNames)

namesCustom = ["eithan", "almog", "berry", "simon", "dor", "evgeny", "ted", "shahaf", "nakar", "dan", "yoni", "asi"]
namesCustom2 = ["Cenzor", "aliza", "naomi", "phathi", "yohai", "yulia", "rom", "lidia", "acasha", "ziv", "mario", "hagar"]
# makeRandomTeams(4, 3, namesCustom)

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
				if currentWeapon == "buster strike" and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
					fireBusterStrike((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
					currentTeam.weaponCounter[weaponDict[currentWeapon]] -= 1
					renderWeaponCount()
					timeRemaining(5)
					state = nextState
				if currentWeapon == "teleport":
					currentTeam.specialCounter[TELEPORT] -= 1
					currentWeapon = "missile"
					weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
					objectUnderControl.pos = Vector(mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y)
					timeRemaining(5)
					state = nextState
			
			if state == PLAYER_CONTROL_1 and currentWeapon == "homing missile":
				Target.x, Target.y = mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y
				showTarget = True
			# cliking in menu
			if state == OPEN_MENU:
				for wRect in wRects:
					if wRect[3]:
						currentWeapon = weaponDictI[wRect[0]]
						renderWeaponCount()
						weaponStyle = weaponStyleTup[weaponDict[currentWeapon]]
						state = PLAYER_CONTROL_1
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
							currentWeapon = "switch worms"
							weaponStyle = PUTABLE
							currentTeam.specialCounter[sRect[0]] += 1
							renderWeaponCount(True)
						elif sRect[0] == TIME_TRAVEL:
							if not timeTravel:
								timeTravelInitiate()
						state = PLAYER_CONTROL_1
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)\
			# testing mainly
			if state == PLAYER_CONTROL_1:
				# HealthPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# WeaponPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# Bee((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y), uniform(0,2*pi))
				# Plant((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# SentryGun((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y), currentTeam.color)
				# UtilityPack((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# w = deployPack(WEAPON_PACK)
				# v = Vortex((mousePos[0]/scalingFactor + camPos.x, mousePos[1]/scalingFactor + camPos.y))
				# if not timeTravel: timeTravelInitiate()
				# camTrack = w
				pass
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
			# this is the next state after placing all worms
			if state == PLACING_WORMS:
				state = nextState
				renderWeaponCount()
			elif state == PLAYER_CONTROL_1:
				state = OPEN_MENU
			elif state == OPEN_MENU:
				state = PLAYER_CONTROL_1
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll up
			menuOffset -= 50
			if menuOffset < 0:
				menuOffset = 0
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll down
			menuOffset += 50
			if menuOffset > 70:
				menuOffset = 70
		# key press
		if event.type == pygame.KEYDOWN:
			# controll worm
			if objectUnderControl and playerControl:
				if event.key == pygame.K_RETURN:
					# jump
					if objectUnderControl.stable and objectUnderControl.health > 0:
						objectUnderControl.vel += Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle)) * 3
						objectUnderControl.stable = False
				# fire on key press
				if event.key == pygame.K_SPACE:
					if weaponStyle == CHARGABLE and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
						energising = True
						energyLevel = 0
						fireWeapon = False
						if currentWeapon == "homing missile" and not showTarget:
							energising = False
				# facing key
				if event.key == pygame.K_RIGHT:
					objectUnderControl.facing = RIGHT
					if objectUnderControl.shootAngle >= pi/2 and objectUnderControl.shootAngle <= (3/2)*pi:
						objectUnderControl.shootAngle = pi - objectUnderControl.shootAngle
					camTrack = objectUnderControl
				if event.key == pygame.K_LEFT:
					objectUnderControl.facing = LEFT
					if objectUnderControl.shootAngle >= -pi/2 and objectUnderControl.shootAngle <= pi/2:
						objectUnderControl.shootAngle = pi - objectUnderControl.shootAngle
					camTrack = objectUnderControl
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
			# randomize wind
			if event.key == pygame.K_w:
				wind = uniform(-1,1)
			if event.key == pygame.K_l:
				loadGame()
			if event.key == pygame.K_p:
				pause = not pause
			if event.key == pygame.K_TAB:
				if state == PLAYER_CONTROL_1 and weaponStyle == CHARGABLE and not currentWeapon == "bunker buster":
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
				elif state == PLAYER_CONTROL_1 and currentWeapon == "bunker buster":
					BunkerBuster.mode = not BunkerBuster.mode
					if BunkerBuster.mode:
						FloatingText(objectUnderControl.pos + Vector(0,-5), "drill mode", (20,20,20))
					else:
						FloatingText(objectUnderControl.pos + Vector(0,-5), "rocket mode", (20,20,20))
			if event.key == pygame.K_s:
				suddenDeath()
			if event.key == pygame.K_t:
				print("timeTravel:", timeTravel)
				print("lenght of positions:", len(timeTravelPositions))
				print("length os set:", len(timeTravelList))
		# key release
		if event.type == pygame.KEYUP:
			# fire release
			if event.key == pygame.K_SPACE and playerShootAble:
				if timeTravel:
					timeTravelPlay()
					energyLevel = 0
				elif weaponStyle == CHARGABLE and energising:
					fireWeapon = True
				elif currentWeapon == "switch worms" and currentTeam.specialCounter[SWITCH_WORMS] > 0:
					switchWorms()
				elif (weaponStyle in [PUTABLE, GUN]) and playerShootAble and not currentTeam.weaponCounter[weaponDict[currentWeapon]] == 0:
					fireWeapon = True
					playerShootAble = False
				energising = False
				
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
			energyLevel += 0.05
			if energyLevel >= 1:
				if timeTravel:
					timeTravelPlay()
					energyLevel = 0
					energising = False
				else:
					energyLevel = 1
					fireWeapon = True
	if pause: continue

	# set camera target
	if camTrack:
		camTarget.x = camTrack.pos.x - winWidth /2
		camTarget.y = camTrack.pos.y - winHeight /2
		camPos += (camTarget - camPos) * 0.2
	
	# use edge map scroll
	if playerScrollAble:
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
	
	# advance timer
	timeOverall += 1
	if timeOverall % 30 == 0:
		if not state in [PLACING_WORMS]:
			timeStep()
			
	cloud_maneger()
	for cloud in Cloud._reg: cloud.step()
		
	# draw:
	# win.fill(SKY_CYAN)
	win.blit(imageSky, (0,0))
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
			point1 = vectorCopy(objectUnderControl.pos)
			point2 = point1 + Vector(cos(objectUnderControl.shootAngle), sin(objectUnderControl.shootAngle)) * 500
			pygame.draw.line(win, (0,0,255), (int(point1.x) - int(camPos.x), int(point1.y) - int(camPos.y)), (int(point2.x) - int(camPos.x), int(point2.y) - int(camPos.y)))
		i = 0
		while i < 20 * energyLevel:
			cPos = vectorCopy(objectUnderControl.pos)
			angle = objectUnderControl.shootAngle
			pygame.draw.line(win, (0,0,0), (int(cPos[0] - camPos.x), int(cPos[1] - camPos.y)), ((int(cPos[0] + cos(angle) * i - camPos.x), int(cPos[1] + sin(angle) * i - camPos.y))))
			i += 1
	if currentWeapon == "girder" and state == PLAYER_CONTROL_1: drawGirderHint()
	drawExtra()
	
	# HUD
	drawWindIndicator()
	timeDraw()
	win.blit(currentWeaponSurf, ((int(25), int(8))))
	
	if not state in [RESET, GENERATE_TERRAIN, PLACING_WORMS, CHOOSE_STARTER] and drawHealthBar: teamHealthDraw()
	# weapon menu:
	if state == OPEN_MENU:
		weaponMenuStep()
		weaponMenuDraw()
	
	# debug:
	# win.blit(myfont.render(str(state), False, (0,0,0)), ((int(1), int(winHeight-6))))
	win.blit(myfont.render(str(int(damageThisTurn)), False, (0,0,0)), ((int(10), int(winHeight-6))))
	if state == PLACING_WORMS:
		win.blit(myfont.render(str(len(PhysObj._worms)), False, (0,0,0)), ((int(20), int(winHeight-6))))
	# if gameStable:
		# win.blit(myfont.render("s", False, (0,0,0)), ((int(10), int(winHeight-6))))
	
	# reset actions
	actionMove = False
	
	# screen manegement
	screen.blit(pygame.transform.scale(win, screen.get_rect().size), (0,0))
	
	pygame.display.update()
	
pygame.quit()

