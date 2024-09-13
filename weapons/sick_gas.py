

import pygame
from random import randint, uniform
from common import GameVariables, point2world, Sickness, ColorType
from common.vector import *

class GasParticles:
	''' smoke manager, calculates and draws smoke'''
	_sp = None
	_particlesRemove = []
	_particles = []
	
	def __init__(self):
		GasParticles._sp = self
		
	def addSmoke(self, pos, vel=None, color: ColorType=None, sickness: Sickness=Sickness.SICK):
		if not color:
			color = (20, 20, 20)
		radius = randint(8,10)
		pos = tup2vec(pos)
		time_counter = 0
		if not vel:
			vel = Vector()
		particle = [pos, vel, color, radius, time_counter, sickness]

		GasParticles._particles.append(particle)
			
	def step(self) -> None:
		for particle in GasParticles._particles:
			particle[4] += 1
			if particle[4] % 8 == 0:
				particle[3] -= 1
				if particle[3] <= 0:
					GasParticles._particles.remove(particle)
			particle[1] += Vector(GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * uniform(0.2, 1), -0.1)
			particle[0] += particle[1]
			for worm in GameVariables().get_worms():
				if distus(particle[0], worm.pos) < (particle[3] + worm.radius) * (particle[3] + worm.radius):
					worm.sicken(particle[5])
					
	def draw(self, win: pygame.Surface) -> None:
		if len(GasParticles._particles) == 0:
			return
		smokeSurf = pygame.Surface((GameVariables().win_width, GameVariables().win_height), pygame.SRCALPHA)
		for particle in GasParticles._particles + GasParticles._particles:
			pygame.draw.circle(smokeSurf, particle[2], point2world(particle[0]), particle[3])
		smokeSurf.set_alpha(100)
		win.blit(smokeSurf, (0, 0))

