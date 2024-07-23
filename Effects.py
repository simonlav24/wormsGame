
import pygame
from vector import *


import globals
from random import randint, uniform, choice
from math import exp, pi, sin, cos


class Effect:
	''' visual effects '''
	...


class Blast(Effect):
	''' firey effect, emmited by explossions, jetpack etc '''
	_color = [(255,255,255), (255, 222, 3), (255, 109, 10), (254, 153, 35), (242, 74, 1), (93, 91, 86)]
	
	def __init__(self, pos, radius, smoke = 30, moving=0, star=False, color=None):
		globals.game_manager.nonPhys.append(self)
		self.timeCounter = 0
		self.pos = pos + vectorUnitRandom() * moving
		self.radius = radius
		self.rad = 0
		self.timeCounter = 0
		self.smoke = smoke
		self.rand = vectorUnitRandom() * randint(1, int(self.radius / 2))
		self.star = star
		if color:
			self.color = [(255,255,255), color]
			for i in range(4):
				color = tuple(max(i - 30,0) for i in color)
				self.color.append(color)
		else:
			self.color = Blast._color
			
	def step(self):
		if randint(0,self.smoke) == 0 and self.rad > 1:
			SmokeParticles._sp.addSmoke(self.pos, Vector())
		self.timeCounter += 0.5 * globals.game_manager.dt
		self.rad = 1.359 * self.timeCounter * exp(- 0.5 * self.timeCounter) * self.radius
		self.pos.x += (4.0 * globals.game_manager.wind / self.rad) * globals.game_manager.dt
		self.pos.y -= (2.0 / self.rad) * globals.game_manager.dt
		if globals.game_manager.darkness:
			color = self.color[int(max(min(self.timeCounter, 5), 0))]
			globals.game_manager.lights.append((self.pos[0], self.pos[1], self.rad * 3, (color[0], color[1], color[2], 100) ))
		if self.timeCounter >= 10:
			globals.game_manager.nonPhysToRemove.append(self)
			
	def draw(self):
		if self.star and self.timeCounter < 1.0:
			points = []
			num = randint(10, 25) // 2
			for i in range(num):
				radius = self.rad * 0.1 if i % 2 == 0 else self.rad * 4
				rand = Vector() if i % 2 == 0 else 5 * vectorUnitRandom()
				radrand = 1.0 if i % 2 == 0 else uniform(0.8,3)
				point = globals.game_manager.point_to_world(self.pos + vectorFromAngle((i/num) * 2 * pi, radius + radrand) + rand)
				points.append(point)
			pygame.draw.polygon(globals.game_manager.win, choice(self.color[0:2]), points)
		globals.game_manager.layersCircles[0].append((self.color[int(max(min(self.timeCounter, 5), 0))], self.pos, self.rad))
		globals.game_manager.layersCircles[1].append((self.color[int(max(min(self.timeCounter-1, 5), 0))], self.pos + self.rand, self.rad*0.6))
		globals.game_manager.layersCircles[2].append((self.color[int(max(min(self.timeCounter-2, 5), 0))], self.pos + self.rand, self.rad*0.3))


class FireBlast(Effect):
	''' fire effect, fire color circles changing colors '''
	_color = [(255, 222, 3), (242, 74, 1), (255, 109, 10), (254, 153, 35)]
	
	def __init__(self, pos, radius):
		self.pos = vectorCopy(pos) + vectorUnitRandom() * randint(1, 5)
		self.radius = radius
		globals.game_manager.nonPhys.append(self)
		self.color = choice(self._color)
		
	def step(self):
		self.pos.y -= (2 - 0.4 * self.radius) * globals.game_manager.dt
		self.pos.x += globals.game_manager.wind * globals.game_manager.dt
		if randint(0, 10) < 3:
			self.radius -= 1 * globals.game_manager.dt
		if self.radius < 0:
			globals.game_manager.nonPhysToRemove.append(self)
			
	def draw(self):
		if self.radius == 0:
			globals.game_manager.win.set_at(globals.game_manager.point_to_world(self.pos), self.color)
		globals.game_manager.layersCircles[2].append((self.color, self.pos, self.radius))


class Explossion(Effect):
	''' explossion effect, creates blast in changing sizes according to radius '''
	def __init__(self, pos, radius):	
		globals.game_manager.nonPhys.append(self)
		self.pos = pos
		self.radius = radius
		self.times = int(radius * 0.35)
		self.timeCounter = 0
		
	def step(self):
		Blast(self.pos + vectorUnitRandom() * uniform(0,self.radius/2), uniform(10, self.radius*0.7))
		self.timeCounter += 1
		if self.timeCounter == self.times:
			globals.game_manager.nonPhysToRemove.append(self)
			
	def draw(self):
		pass


class FloatingText(Effect): #pos, text, color
	''' floating text effect for damage indication, crate content '''
	def __init__(self, pos, text, color = (255,0,0)):
		globals.game_manager.nonPhys.append(self)
		self.pos = Vector(pos[0], pos[1])
		self.surf = globals.pixelFont5.render(str(text), False, color)
		self.timeCounter = 0
		self.phase = uniform(0,2*pi)
		
	def step(self):
		self.timeCounter += 1
		self.pos.y -= 0.5
		self.pos.x += 0.25 * sin(0.1 * globals.time_manager.timeOverall + self.phase)
		if self.timeCounter == 50:
			globals.game_manager.nonPhysToRemove.append(self)
			
	def draw(self):
		globals.game_manager.win.blit(self.surf , (int(self.pos.x - globals.game_manager.camPos.x - self.surf.get_size()[0]/2), int(self.pos.y - globals.game_manager.camPos.y)))
		

class SmokeParticles(Effect):
	''' smoke manager, calculates and draws smoke'''
	_sp = None
	_particles = []
	_particlesRemove = []
	_sickParticles = []
	
	def __init__(self):
		SmokeParticles._sp = self
		
	def addSmoke(self, pos, vel=None, color=None, sick=0):
		if not color:
			color = (20, 20, 20)
		radius = randint(8,10)
		pos = tup2vec(pos)
		timeCounter = 0
		if not vel:
			vel = Vector()
		particle = [pos, vel, color, radius, timeCounter]
		if sick == 0:
			SmokeParticles._particles.append(particle)
		else:
			particle[3] = randint(8,18)
			particle.append(sick)
			SmokeParticles._sickParticles.append(particle)
			
	def step(self):
		for particle in SmokeParticles._particles:
			particle[4] += 1
			if particle[4] % 5 == 0:
				particle[3] -= 1 * globals.game_manager.dt
				if particle[3] <= 0:
					SmokeParticles._particlesRemove.append(particle)
			particle[1] += Vector(globals.game_manager.wind * 0.1 * globals.game_manager.windMult * uniform(0.2,1) * globals.game_manager.dt, -0.1)
			particle[0] += particle[1] * globals.game_manager.dt
		for p in SmokeParticles._particlesRemove:
			SmokeParticles._particles.remove(p)
		SmokeParticles._particlesRemove = []

		for particle in SmokeParticles._sickParticles:
			particle[4] += 1
			if particle[4] % 8 == 0:
				particle[3] -= 1
				if particle[3] <= 0:
					SmokeParticles._sickParticles.remove(particle)
			particle[1] += Vector(globals.game_manager.wind * 0.1 * globals.game_manager.windMult * uniform(0.2,1), -0.1)
			particle[0] += particle[1]
			for worm in globals.game_manager.get_worms():
				if distus(particle[0], worm.pos) < (particle[3] + worm.radius) * (particle[3] + worm.radius):
					worm.sicken(particle[5])
					
	def draw(self):
		smokeSurf = pygame.Surface(globals.game_manager.win.get_size(), pygame.SRCALPHA)
		for particle in SmokeParticles._particles + SmokeParticles._sickParticles:
			pygame.draw.circle(smokeSurf, particle[2], globals.game_manager.point_to_world(particle[0]), particle[3])
		smokeSurf.set_alpha(100)
		globals.game_manager.win.blit(smokeSurf, (0,0))