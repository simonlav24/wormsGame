
import pygame
from random import uniform, randint, choice
from math import cos, sin, pi

from common import blit_weapon_sprite, ColorType, GameVariables, point2world
from common.vector import *

from entities.physical_entity import PhysObj
from entities.gun_shell import GunShell
from game.visual_effects import EffectManager
from game.world_effects import boom
from game.sfx import Sfx, SfxIndex


class Grenade (PhysObj):
	def __init__(self, pos, direction, energy, weapon_name: str="grenade"):
		super().__init__(pos)
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.color = (0,100,0)
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), weapon_name)
		self.angle = 0

	def death_response(self):
		rad = 30
		if randint(0,50) == 1 or GameVariables().mega_weapon_trigger:
			rad *= 2
		boom(self.pos, rad)

	def step(self):
		super().step()
		self.angle -= self.vel.x * 4 * GameVariables().dt
		self.timer += 1 * GameVariables().dt
		if self.timer >= GameVariables().fuse_time:
			self.dead = True
		self.stable = False

	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))


class StickyBomb (Grenade):
	def __init__(self, pos, direction, energy):
		super().__init__(pos, direction, energy, "sticky bomb")
		self.radius = 2
		self.color = (117,47,7)
		self.damp = 0.5
		self.sticked = False
		self.stick = None
	
	def on_collision(self, ppos):
		super().on_collision(ppos)
		if not self.sticked:
			self.sticked = True
			self.stick = vectorCopy((self.pos + ppos)/2)
		self.vel *= 0
	
	def step(self):
		super().step()
		if self.stick:
			self.pos = self.stick


class HolyGrenade(Grenade):
	def __init__(self, pos, direction, energy):
		super().__init__(pos, direction, energy, "holy grenade")
		self.radius = 3
		self.color = (230, 230, 0)
		self.damp = 0.5
		
	def death_response(self):
		boom(self.pos, 45)
		
	def step(self):
		super().step()
		if self.timer == GameVariables().fuse_time + GameVariables().fps:
			comments = [
				[{'text': "o lord bless this thy "}, {'text': 'hand grenade', 'color': (210,210,0)}],
				[{'text': "blow thine enemy to tiny bits"}],
				[{'text': "feast upon the lambs and sloths and carp"}],
				[{'text': "three shall be the number thou shalt count"}],
				[{'text': "thou shall snuff that"}],
			]
			GameVariables().commentator.comment(choice(comments))


class Banana(Grenade):
	def __init__(self, pos, direction, energy, used = False):
		super().__init__(pos, direction, energy, "banana")
		self.radius = 2
		self.color = (255, 204, 0)
		self.damp = 0.5
		self.used = used

	def on_collision(self, ppos):
		super().on_collision(ppos)
		if self.used:
			self.dead = True

	def death_response(self):
		if self.used:
			boom(self.pos, 40)
			return
		boom(self.pos, 40)
		for i in range(5):
			angle = (i * pi) / 6 + pi / 6
			direction = (cos(angle) * uniform(0.2, 0.6), -sin(angle))
			m = Banana(self.pos, direction, uniform(0.3, 0.8), True)
			m.is_boom_affected = False
			if i == 2:
				GameVariables().cam_track = m

	def step(self):
		super().step()
		if self.used: 
			self.timer = 0


class GasGrenade(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), 'gas grenade')
		self.angle = 0

		self.damp = 0.5
		self.state = "throw"

	def remove_from_game(self):
		super().remove_from_game()
		Sfx().loop_decrease(SfxIndex.GAS_LOOP, 1500)

	def death_response(self):
		boom(self.pos, 20)
		for i in range(40):
			vel = Vector(cos(2 * pi * i / 40), sin(2 * pi * i / 40)) * uniform(1, 1.5)
			EffectManager().add_gas(self.pos, vel)
	
	def step(self):
		super().step()
		GameVariables().game_distable()
		self.angle -= self.vel.x * 4
		self.timer += 1
		if self.state == "throw":
			if self.timer >= GameVariables().fuse_time:
				self.state = "release"
				Sfx().loop_increase(SfxIndex.GAS_LOOP)
		if self.state == "release":
			if self.timer % 3 == 0:
				EffectManager().add_gas(self.pos, vectorUnitRandom())
			if self.timer >= GameVariables().fuse_time + 5 * GameVariables().fps:
				self.dead = True
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2)) 