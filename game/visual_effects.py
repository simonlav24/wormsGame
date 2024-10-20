
from typing import Any, List, Tuple
from random import randint, uniform, choice, shuffle
from math import exp, pi, sin, cos

import pygame
import pygame.gfxdraw

from common import DARK_COLOR, LIGHT_RADIUS, ColorType, fonts, Entity, SingletonMeta, clamp, GameVariables, point2world, Sickness, GAS_COLOR, GameGlobals
from common.vector import *

from game.map_manager import MapManager

# particle: pos, vel, color, life
ParticleType = Tuple[Vector, Vector, ColorType, int]

class Effect(Entity):
	''' visual effects '''
	def __init__(self):
		EffectManager().register(self)

class EffectManager(metaclass=SingletonMeta):
	def __init__(self) -> None:
		self.effects_in_play: List[Effect] = []
		self.effects_to_remove: List[Effect] = []

		self.circles_layers: List[List[Tuple[Any]]] = [[], [], []]

		self.dark_mask = pygame.Surface((GameGlobals().screen_width, GameGlobals().screen_height), pygame.SRCALPHA)
		self.is_dark_mode = False
		self.lights: List[Tuple[Vector, int, ColorType]] = []

		self.smoke_particles = SmokeParticles()
		self.gas_particles = GasParticles()
		self.particles: List[ParticleType] = []
	
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

		for particle in self.particles:
			acc = Vector(GameVariables().physics.wind * 0.05, GameVariables().physics.global_gravity * 0.5)
			particle[1] = particle[1] + acc
			particle[0] = particle[0] + particle[1] * 0.5
			particle[3] -= 1
		self.particles = [particle for particle in self.particles if particle[3] > 0]

		self.smoke_particles.step()
		self.gas_particles.step()
	
	def draw(self, win: pygame.Surface):
		for particle in self.particles:
			radius = min(int(particle[3] * 2 / GameGlobals().fps), 2)
			pos = point2world(particle[0])
			pygame.gfxdraw.filled_circle(win, pos[0], pos[1], radius, (*particle[2], 100))

		for effect in self.effects_in_play:
			effect.draw(win)

		self.smoke_particles.draw(win)
		self.gas_particles.draw(win)

		for layer in self.circles_layers:
			for circle in layer:
				pygame.draw.circle(win, circle[0], point2world(circle[1]), int(circle[2]))
			layer.clear()

	def get_dark_mask(self, main_obj_pos: Vector) -> pygame.Surface:
		''' render and return dark mask '''
		self.dark_mask.fill(DARK_COLOR)
		pygame.draw.circle(self.dark_mask, (0,0,0,0), point2world(main_obj_pos), LIGHT_RADIUS)
		for light in self.lights:
			pygame.draw.circle(self.dark_mask, light[2], point2world((light[0][0], light[0][1])), light[1])
		self.lights.clear()


		# self.dark_mask.fill(DARK_COLOR)
		# pygame.draw.circle(self.dark_mask, (0,0,0,0), main_obj_pos.vec2tupint(), LIGHT_RADIUS)
		# for light in self.lights:
		# 	pygame.draw.circle(self.dark_mask, light[2], (light[0][0], light[0][1]), light[1])
		# self.lights.clear()
		return self.dark_mask
	
	def add_smoke(self, pos: Vector, vel: Vector=None, color: ColorType=None):
		self.smoke_particles.add_smoke(pos, vel, color)

	def add_gas(self, pos: Vector, vel: Vector=None, sickness: Sickness=Sickness.SICK):
		self.gas_particles.add_gas(pos, vel, sickness)

	def create_particle(self, pos: Vector, vel: Vector, color: Vector):
		life = randint(GameGlobals().fps, 2 * GameGlobals().fps)
		particle = [pos, vel, color, life]
		self.particles.append(particle)

class Blast(Effect):
	''' firey effect, emmited by explossions, jetpack etc '''
	_color = [(255,255,255), (255, 222, 3), (255, 109, 10), (254, 153, 35), (242, 74, 1), (93, 91, 86)]
	
	def __init__(self, pos, radius, smoke = 30, moving=0, star=False, color=None):
		super().__init__()
		self.time_counter = 0
		self.pos = pos + vectorUnitRandom() * moving
		self.radius = radius
		self.rad = 0
		self.time_counter = 0
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
			EffectManager().add_smoke(self.pos, Vector())
		self.time_counter += 0.5 * GameVariables().dt
		self.rad = 1.359 * self.time_counter * exp(- 0.5 * self.time_counter) * self.radius
		self.pos.x += (4.0 * GameVariables().physics.wind / self.rad) * GameVariables().dt
		self.pos.y -= (2.0 / self.rad) * GameVariables().dt

		color = self.color[int(clamp(self.time_counter, 5, 0))]
		EffectManager().add_light(self.pos, self.rad * 3, (color[0], color[1], color[2], 100))
		if self.time_counter >= 10:
			EffectManager().unregister(self)
			
	def draw(self, win: pygame.Surface) -> None:
		if self.star and self.time_counter < 1.0:
			points = []
			num = randint(10, 25) // 2
			for i in range(num):
				radius = self.rad * 0.1 if i % 2 == 0 else self.rad * 4
				rand = Vector() if i % 2 == 0 else 5 * vectorUnitRandom()
				radrand = 1.0 if i % 2 == 0 else uniform(0.8,3)
				point = point2world(self.pos + vector_from_angle((i/num) * 2 * pi, radius + radrand) + rand)
				points.append(point)
			pygame.draw.polygon(win, choice(self.color[0:2]), points)
		
		clamp(self.time_counter - 1, 5, 0)
		EffectManager().add_circle_effect(0, self.color[int(clamp(self.time_counter, 5, 0))], self.pos, self.rad)
		EffectManager().add_circle_effect(1, self.color[int(clamp(self.time_counter - 1, 5, 0))], self.pos + self.rand, self.rad * 0.6)
		EffectManager().add_circle_effect(2, self.color[int(clamp(self.time_counter - 2, 5, 0))], self.pos + self.rand, self.rad * 0.3)

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
		self.time_counter = 0
		
	def step(self) -> None:
		Blast(self.pos + vectorUnitRandom() * uniform(0,self.radius/2), uniform(10, self.radius*0.7))
		self.time_counter += 1
		if self.time_counter == self.times:
			EffectManager().unregister(self)

class FloatingText(Effect): #pos, text, color
	''' floating text effect for damage indication, crate content '''
	def __init__(self, pos, text, color = (255,0,0)):
		super().__init__()
		self.pos = Vector(pos[0], pos[1])
		self.surf = fonts.pixel5.render(str(text), False, color)
		self.time_counter = 0
		self.phase = uniform(0,2 * pi)
		
	def step(self) -> None:
		self.time_counter += 1
		self.pos.y -= 0.5
		self.pos.x += 0.25 * sin(0.1 * GameVariables().time_overall + self.phase)
		if self.time_counter == 50:
			EffectManager().unregister(self)
			
	def draw(self, win: pygame.Surface) -> None:
		win.blit(self.surf, (int(self.pos.x - GameVariables().cam_pos[0] - self.surf.get_size()[0] / 2), int(self.pos.y - GameVariables().cam_pos[1])))

class SmokeParticles(Effect):
	''' smoke manager, calculates and draws smoke'''
	
	def __init__(self):
		self.particles = []
		self.particles_remove = []

	def add_smoke(self, pos, vel=None, color=None):
		if not color:
			color = (20, 20, 20)
		radius = randint(8,10)
		pos = tup2vec(pos)
		time_counter = 0
		if not vel:
			vel = Vector()
		particle = [pos, vel, color, radius, time_counter]

		self.particles.append(particle)
			
	def step(self) -> None:
		for particle in self.particles:
			particle[4] += 1
			if particle[4] % 5 == 0:
				particle[3] -= 1 * GameVariables().dt
				if particle[3] <= 0:
					self.particles_remove.append(particle)
			particle[1] += Vector(GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * uniform(0.2,1) * GameVariables().dt, -0.1)
			particle[0] += particle[1] * GameVariables().dt
		for p in self.particles_remove:
			self.particles.remove(p)
		self.particles_remove = []

	def draw(self, win: pygame.Surface) -> None:
		if len(self.particles) == 0:
			return
		smokeSurf = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height), pygame.SRCALPHA)
		for particle in self.particles:
			pygame.draw.circle(smokeSurf, particle[2], point2world(particle[0]), particle[3])
		smokeSurf.set_alpha(100)
		win.blit(smokeSurf, (0,0))

GAS_POS = 0
GAS_VEL = 1
GAS_RADIUS = 2
GAS_TIME = 3
GAS_SICK = 4

class GasParticles:
	''' smoke manager, calculates and draws smoke'''	
	def __init__(self):
		self.particles = []
		self.particles_remove = []
		
	def add_gas(self, pos, vel=None, sickness: Sickness=Sickness.SICK):
		radius = randint(8,10)
		pos = tup2vec(pos)
		time_counter = 0
		if not vel:
			vel = Vector()
		particle = [pos, vel, radius, time_counter, sickness]

		self.particles.append(particle)
			
	def step(self) -> None:
		for particle in self.particles:
			particle[GAS_TIME] += 1
			if particle[GAS_TIME] % 8 == 0:
				particle[GAS_RADIUS] -= 1
				if particle[GAS_RADIUS] <= 0:
					self.particles_remove.append(particle)
			particle[GAS_VEL] += Vector(GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * uniform(0.2, 1), -0.1)
			particle[GAS_POS] += particle[GAS_VEL]
			for worm in GameVariables().get_worms():
				if distus(particle[GAS_POS], worm.pos) < (particle[GAS_RADIUS] + worm.radius) * (particle[GAS_RADIUS] + worm.radius):
					worm.sicken(particle[GAS_SICK])
		for particle in self.particles_remove:
			self.particles.remove(particle)
		self.particles_remove.clear()

	def draw(self, win: pygame.Surface) -> None:
		if len(self.particles) == 0:
			return
		smokeSurf = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height), pygame.SRCALPHA)
		for particle in self.particles:
			pygame.draw.circle(smokeSurf, GAS_COLOR, point2world(particle[GAS_POS]), particle[GAS_RADIUS])
		smokeSurf.set_alpha(100)
		win.blit(smokeSurf, (0, 0))

def splash(pos: Vector, vel: Vector) -> None:
	amount = 10 + int(vel.getMag())
	for i in range(2):
		for _ in range(amount):
			x = vel.x * 0.5 * uniform(0.5, 1.5) + uniform(-4, 4)
			y = -abs(vel.getMag() * uniform(0.8, 1.2))
			if i == 1:
				y = y * uniform(0, 0.9)
			velocity = Vector(x, y) * 0.7
			DropLet(Vector(pos.x, pos.y), velocity)
	

class DropLet(Effect):
	def __init__(self, pos: Vector, vel: Vector):
		super().__init__()
		self.radius = randint(1,2)
		self.pos = pos
		self.vel = vel
		self.acc = Vector()

	def step(self) -> None:
		factor = 2.5
		self.acc.y += GameVariables().physics.global_gravity * factor

		self.vel += self.acc * GameVariables().dt
		self.pos += self.vel * GameVariables().dt

		self.acc *= 0
		GameVariables().game_distable()
		if self.pos.y > MapManager().get_map_height():
			EffectManager().unregister(self)

	def draw(self, win: pygame.Surface) -> None:
		color = GameVariables().water_color[1]
		pygame.draw.circle(win, color, point2world(self.pos), self.radius)

class FireWork:
	def __init__(self, pos, color):
		GameVariables().register_non_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.blasts = []
		
		self.timer = 0
		blastNum = 20
		for i in range(blastNum):
			self.blasts.append([vectorCopy(self.pos), vector_from_angle(i * 2 * pi / blastNum, 7 + uniform(-1,1))])

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
		if self.timer > 0.9 * GameVariables().fps:
			GameVariables().unregister_non_physical(self)
	
	def draw(self, win: pygame.Surface):
		pass

class Frost:
	def __init__(self, pos):
		self.pos = pos.integer()
		self.visited = []
		self.next = []
		self.timer = GameVariables().fps * randint(2, 6)
		if not MapManager().is_ground_at(self.pos):
			return
		GameVariables().register_non_physical(self)
	
	def step(self):
		color = MapManager().ground_map.get_at(self.pos)
		r = color[0] + (256 - color[0]) // 2
		g = color[1] + (256 - color[1]) // 2
		b = color[2] + int((256 - color[2]) * 0.8)
		newColor = (r, g, b)
		MapManager().ground_map.set_at(self.pos, newColor)
		self.visited.append(vectorCopy(self.pos))
		directions = [Vector(1,0), Vector(0,1), Vector(-1,0), Vector(0,-1)]
		shuffle(directions)
		
		while len(directions) > 0:
			direction = directions.pop(0)
			checkPos = self.pos + direction
			if MapManager().is_ground_at(checkPos) and not checkPos in self.visited:
				self.next.append(checkPos)
		if len(self.next) == 0:
			GameVariables().unregister_non_physical(self)
			return
		self.pos = choice(self.next)
		self.next.remove(self.pos)
		
		self.timer -= 1
		if self.timer <= 0:
			GameVariables().unregister_non_physical(self)
	
	def draw(self, win: pygame.Surface):
		pass