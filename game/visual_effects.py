
import pygame
from typing import Any, List, Tuple
from random import randint, uniform, choice
from math import exp, pi, sin, cos

import globals

from common import DARK_COLOR, LIGHT_RADIUS, ColorType, fonts, Entity, SingletonMeta, clamp, GameVariables, point2world
from common.vector import *

from game.map_manager import MapManager

class Effect(Entity):
	''' visual effects '''
	def __init__(self):
		EffectManager().register(self)

class EffectManager(metaclass=SingletonMeta):
	def __init__(self) -> None:
		self.effects_in_play: List[Effect] = []
		self.effects_to_remove: List[Effect] = []

		self.circles_layers: List[List[Tuple[Any]]] = [[], [], []]

		self.dark_mask = pygame.Surface(MapManager().get_map_size(), pygame.SRCALPHA)
		self.is_dark_mode = False
		self.lights: List[Tuple[Vector, int, ColorType]] = []
	
	def register(self, effect: Effect) -> None:
		self.effects_in_play.append(effect)

	def unregister(self, effect: Effect) -> None:
		self.effects_to_remove.append(effect)

	def add_circle_effect(self, layer_num: int, color: ColorType, pos: Vector, radius: float) -> None:
		self.circles_layers[layer_num].append(
			(color,	pos, radius)
		)
	
	def add_light(self, pos: Vector, radius: int, color: ColorType) -> None:
		if not self.is_dark_mode:
			return
		self.lights.append((pos, radius, color))

	def step(self) -> None:
		for effect in self.effects_in_play:
			effect.step()
		for effect in self.effects_to_remove:
			self.effects_in_play.remove(effect)
		self.effects_to_remove.clear()
	
	def draw(self, win: pygame.Surface):
		for effect in self.effects_in_play:
			effect.draw(win)

		for layer in self.circles_layers:
			for circle in layer:
				pygame.draw.circle(win, circle[0], point2world(circle[1]), int(circle[2]))
			layer.clear()

	def get_dark_mask(self, main_obj_pos: Vector) -> pygame.Surface:
		''' render and return dark mask '''
		self.dark_mask.fill(DARK_COLOR)
		pygame.draw.circle(self.dark_mask, (0,0,0,0), main_obj_pos.vec2tupint(), LIGHT_RADIUS)
		for light in self.lights:
			pygame.draw.circle(self.dark_mask, light[3], (light[0], light[1]), light[2])
		self.lights.clear()

class Blast(Effect):
	''' firey effect, emmited by explossions, jetpack etc '''
	_color = [(255,255,255), (255, 222, 3), (255, 109, 10), (254, 153, 35), (242, 74, 1), (93, 91, 86)]
	
	def __init__(self, pos, radius, smoke = 30, moving=0, star=False, color=None):
		super().__init__()
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
			for _ in range(4):
				color = tuple(max(i - 30,0) for i in color)
				self.color.append(color)
		else:
			self.color = Blast._color
			
	def step(self) -> None:
		if randint(0,self.smoke) == 0 and self.rad > 1:
			SmokeParticles._sp.addSmoke(self.pos, Vector())
		self.timeCounter += 0.5 * GameVariables().dt
		self.rad = 1.359 * self.timeCounter * exp(- 0.5 * self.timeCounter) * self.radius
		self.pos.x += (4.0 * GameVariables().physics.wind / self.rad) * GameVariables().dt
		self.pos.y -= (2.0 / self.rad) * GameVariables().dt

		color = self.color[int(clamp(self.timeCounter, 5, 0))]
		EffectManager().lights.append((self.pos[0], self.pos[1], self.rad * 3, (color[0], color[1], color[2], 100) ))
		if self.timeCounter >= 10:
			EffectManager().unregister(self)
			
	def draw(self, win: pygame.Surface) -> None:
		if self.star and self.timeCounter < 1.0:
			points = []
			num = randint(10, 25) // 2
			for i in range(num):
				radius = self.rad * 0.1 if i % 2 == 0 else self.rad * 4
				rand = Vector() if i % 2 == 0 else 5 * vectorUnitRandom()
				radrand = 1.0 if i % 2 == 0 else uniform(0.8,3)
				point = point2world(self.pos + vectorFromAngle((i/num) * 2 * pi, radius + radrand) + rand)
				points.append(point)
			pygame.draw.polygon(win, choice(self.color[0:2]), points)
		
		clamp(self.timeCounter - 1, 5, 0)
		EffectManager().add_circle_effect(0, self.color[int(clamp(self.timeCounter, 5, 0))], self.pos, self.rad)
		EffectManager().add_circle_effect(1, self.color[int(clamp(self.timeCounter - 1, 5, 0))], self.pos + self.rand, self.rad * 0.6)
		EffectManager().add_circle_effect(2, self.color[int(clamp(self.timeCounter - 2, 5, 0))], self.pos + self.rand, self.rad * 0.3)

class FireBlast(Effect):
	''' fire effect, fire color circles changing colors '''
	_color = [(255, 222, 3), (242, 74, 1), (255, 109, 10), (254, 153, 35)]
	
	def __init__(self, pos, radius):
		super().__init__()
		self.pos = vectorCopy(pos) + vectorUnitRandom() * randint(1, 5)
		self.radius = radius
		self.color = choice(self._color)
		
	def step(self) -> None:
		self.pos.y -= (2 - 0.4 * self.radius) * GameVariables().dt
		self.pos.x += GameVariables().physics.wind * GameVariables().dt
		if randint(0, 10) < 3:
			self.radius -= 1 * GameVariables().dt
		if self.radius < 0:
			EffectManager().unregister(self)
			
	def draw(self, win: pygame.Surface) -> None:
		if self.radius == 0:
			win.set_at(point2world(self.pos), self.color)
		EffectManager().add_circle_effect(2, self.color, self.pos, self.radius)

class Explossion(Effect):
	''' explossion effect, creates blast in changing sizes according to radius '''
	def __init__(self, pos, radius):	
		super().__init__()
		self.pos = pos
		self.radius = radius
		self.times = int(radius * 0.35)
		self.timeCounter = 0
		
	def step(self) -> None:
		Blast(self.pos + vectorUnitRandom() * uniform(0,self.radius/2), uniform(10, self.radius*0.7))
		self.timeCounter += 1
		if self.timeCounter == self.times:
			EffectManager().unregister(self)

class FloatingText(Effect): #pos, text, color
	''' floating text effect for damage indication, crate content '''
	def __init__(self, pos, text, color = (255,0,0)):
		super().__init__()
		self.pos = Vector(pos[0], pos[1])
		self.surf = fonts.pixel5.render(str(text), False, color)
		self.timeCounter = 0
		self.phase = uniform(0,2 * pi)
		
	def step(self) -> None:
		self.timeCounter += 1
		self.pos.y -= 0.5
		self.pos.x += 0.25 * sin(0.1 * GameVariables().time_overall + self.phase)
		if self.timeCounter == 50:
			EffectManager().unregister(self)
			
	def draw(self, win: pygame.Surface) -> None:
		win.blit(self.surf, (int(self.pos.x - GameVariables().cam_pos[0] - self.surf.get_size()[0] / 2), int(self.pos.y - GameVariables().cam_pos[1])))

class GasParticles:
	''' smoke manager, calculates and draws smoke'''
	_sp = None
	_particlesRemove = []
	_particles = []
	
	def __init__(self):
		GasParticles._sp = self
		
	def addSmoke(self, pos, vel=None, color=None):
		if not color:
			color = (20, 20, 20)
		radius = randint(8,10)
		pos = tup2vec(pos)
		timeCounter = 0
		if not vel:
			vel = Vector()
		particle = [pos, vel, color, radius, timeCounter]

		GasParticles._particles.append(particle)
			
	def step(self) -> None:
		for particle in GasParticles._particles:
			particle[4] += 1
			if particle[4] % 8 == 0:
				particle[3] -= 1
				if particle[3] <= 0:
					GasParticles._particles.remove(particle)
			particle[1] += Vector(GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * uniform(0.2,1), -0.1)
			particle[0] += particle[1]
			for worm in globals.game_manager.get_worms():
				if distus(particle[0], worm.pos) < (particle[3] + worm.radius) * (particle[3] + worm.radius):
					worm.sicken(1)
					
	def draw(self, win: pygame.Surface) -> None:
		smokeSurf = pygame.Surface((GameVariables().win_width, GameVariables().win_height), pygame.SRCALPHA)
		for particle in GasParticles._particles + GasParticles._particles:
			pygame.draw.circle(smokeSurf, particle[2], point2world(particle[0]), particle[3])
		smokeSurf.set_alpha(100)
		win.blit(smokeSurf, (0,0))

class SmokeParticles(Effect):
	''' smoke manager, calculates and draws smoke'''
	_sp = None
	_particles = []
	_particlesRemove = []
	_sickParticles = []
	
	def __init__(self):
		SmokeParticles._sp = self
		
	def addSmoke(self, pos, vel=None, color=None):
		if not color:
			color = (20, 20, 20)
		radius = randint(8,10)
		pos = tup2vec(pos)
		timeCounter = 0
		if not vel:
			vel = Vector()
		particle = [pos, vel, color, radius, timeCounter]

		SmokeParticles._particles.append(particle)
			
	def step(self) -> None:
		for particle in SmokeParticles._particles:
			particle[4] += 1
			if particle[4] % 5 == 0:
				particle[3] -= 1 * GameVariables().dt
				if particle[3] <= 0:
					SmokeParticles._particlesRemove.append(particle)
			particle[1] += Vector(GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * uniform(0.2,1) * GameVariables().dt, -0.1)
			particle[0] += particle[1] * GameVariables().dt
		for p in SmokeParticles._particlesRemove:
			SmokeParticles._particles.remove(p)
		SmokeParticles._particlesRemove = []

	def draw(self, win: pygame.Surface) -> None:
		smokeSurf = pygame.Surface((GameVariables().win_width, GameVariables().win_height), pygame.SRCALPHA)
		for particle in SmokeParticles._particles + SmokeParticles._sickParticles:
			pygame.draw.circle(smokeSurf, particle[2], point2world(particle[0]), particle[3])
		smokeSurf.set_alpha(100)
		win.blit(smokeSurf, (0,0))

def splash(pos: Vector, vel: Vector) -> None:
	amount = 10 + int(vel.getMag())
	for _ in range(amount):
		vel = vectorUnitRandom()
		vel.y = uniform(-1,0) * vel.getMag() * 10
		vel.x *= vel.getMag() * 0.17
		DropLet(Vector(pos.x, pos.y), vel)

class DropLet(Effect):
	def __init__(self, pos: Vector, vel: Vector):
		super().__init__()
		self.radius = randint(1,2)
		self.pos = pos
		self.vel = vel
		self.acc = Vector()

	def step(self) -> None:
		factor = 2.5# 2.5 if self.water else 1
		self.acc.y += GameVariables().physics.global_gravity * factor

		self.vel += self.acc * GameVariables().dt
		self.pos += self.vel * GameVariables().dt

		self.acc *= 0

		if self.pos.y > MapManager().get_map_height():
			EffectManager().unregister(self)

	def draw(self, win: pygame.Surface) -> None:
		color = GameVariables().water_color[1]
		pygame.draw.circle(win, color, point2world(self.pos), self.radius)

