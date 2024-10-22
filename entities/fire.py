import pygame
from random import uniform, randint
from math import sin

from common import GameVariables
from common.vector import *
from entities import PhysObj
from game.visual_effects import FireBlast, EffectManager
from game.world_effects import boom


class Fire(PhysObj):
	def __init__(self, pos, delay = 0):
		super().__init__(pos)
		GameVariables().get_debries().append(self)
		self.pos = Vector(pos[0], pos[1])
		self.damp = 0
		self.red = 255
		self.yellow = 106
		self.phase = uniform(0, 2)
		self.radius = 2
		self.is_wind_affected = 1
		self.life = randint(50, 70)
		self.fallen = False
		self.delay = delay
		self.timer = 0
		self.is_worm_collider = True

	def remove_from_game(self) -> None:
		super().remove_from_game()

	def on_collision(self, ppos):		
		self.fallen = True

	def step(self):
		super().step()
		self.stable = False
		if randint(0, 10) < 3:
			FireBlast(self.pos + vectorUnitRandom(), randint(self.radius, 4))
		if randint(0, 50) < 1:
			EffectManager().add_smoke(self.pos)
		self.timer += 1 * GameVariables().dt
		if self.fallen:
			self.life -= 1

		EffectManager().add_light(vectorCopy(self.pos), 20, (0, 0, 0, 0))
		if self.life == 0:
			self.remove_from_game()
			return
		if randint(0,1) == 1 and self.timer > self.delay:
			boom(self.pos + Vector(randint(-1, 1), randint(-1, 1)), 3, False, False, True)

	def draw(self, win: pygame.Surface):
		radius = 1
		if self.life > 20:
			radius += 1
		if self.life > 10:
			radius += 1
		self.yellow = int(sin(0.3 * GameVariables().time_overall + self.phase) * ((255 - 106) / 4) + 255 - ((255 - 106) / 2))
		pygame.draw.circle(win, (self.red, self.yellow, 69), (int(self.pos.x - GameVariables().cam_pos[0]), int(self.pos.y - GameVariables().cam_pos[1])), radius)
