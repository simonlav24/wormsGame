
from random import randint, uniform

import pygame

from common import GameVariables, point2world, blit_weapon_sprite, RIGHT, LEFT
from common.vector import *
from common.drawing_utilities import draw_lightning

from game.world_effects import boom
from entities import PhysObj, Worm
from entities.gun_shell import GunShell

from weapons.raon import Raon
from weapons.green_shell import GreenShell
from weapons.sentry_gun import SentryGun


class ElectricGrenade(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		GameVariables().move_to_back_physical(self)
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
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
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "electric grenade")
		self.angle = 0
	
	def death_response(self):
		rad = 20
		boom(self.pos, rad)
		for sentry in self.sentries:
			sentry.electrified = False
	
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		self.timer += 1
		if self.timer == GameVariables().fuse_time:
			self.electrifying = True
		if self.timer >= GameVariables().fuse_time + self.lifespan:
			self.dead = True
		if self.electrifying:
			self.stable = False
			self.worms = []
			self.raons = []
			self.shells = []
			for worm in GameVariables().get_worms():
				if distus(self.pos, worm.pos) < 10000:
					self.worms.append(worm)
			# for raon in Raon._raons:
			# 	if distus(self.pos, raon.pos) < 10000:
			# 		self.raons.append(raon)
			for shell in GreenShell._shells:
				if distus(self.pos, shell.pos) < 10000:
					self.shells.append(shell)
			# for sentry in SentryGun._sentries:
			# 	if distus(self.pos, sentry.pos) < 10000:
			# 		sentry.electrified = True
			# 		if sentry not in self.sentries:
			# 			self.sentries.append(sentry)
			# 	else:
			# 		sentry.electrified = False
			if len(self.worms) == 0 and len(self.raons) == 0:
				self.emptyCounter += 1
				if self.emptyCounter == GameVariables().fps:
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
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		for worm in self.worms:
			draw_lightning(win, self.pos, worm.pos)
		for raon in self.raons:
			draw_lightning(win, self.pos, raon.pos)
		for shell in self.shells:
			draw_lightning(win, self.pos, shell.pos)
		for sentry in self.sentries:
			if sentry.electrified:
				draw_lightning(win, self.pos, sentry.pos)


class ElectroBoom(PhysObj):
	def __init__(self, pos, direction, energy, immune_team_name: str):
		super().__init__(pos)
		GameVariables().move_to_back_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		GunShell(self.pos, index=1, direction=direction)
		self.radius = 2
		self.color = (120, 230, 230)
		self.damp = 0.6
		self.timer = 0
		self.worms = []
		self.network = []
		self.used = []
		self.electrifying = False
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "electro boom")
		self.angle = 0
		self.immune_team_name = immune_team_name
	
	def secondaryStep(self):
		self.angle -= self.vel.x*4
		self.stable = False
		self.timer += 1
		if self.timer == GameVariables().fuse_time:
			self.electrifying = True
			self.calculate()
		if self.timer == GameVariables().fuse_time + GameVariables().fps * 2:
			for net in self.network:
				for worm in net[1]:
					boom(worm.pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
				boom(net[0].pos + vectorUnitRandom() * uniform(1,5), randint(10,16) )
			boom(self.pos + vectorUnitRandom() * uniform(1,5), randint(10,16))
			self.dead = True
	
	def calculate(self):
		for worm in GameVariables().get_worms():
			if worm.get_team_data().team_name == self.immune_team_name:
				continue
			if dist(self.pos, worm.pos) < 150:
				self.worms.append(worm)
		for selfWorm in self.worms:
			net = []
			for worm in GameVariables().get_worms():
				if worm == selfWorm or worm in self.used or worm in self.worms or worm in GameVariables().player.team.worms:
					continue
				if dist(selfWorm.pos, worm.pos) < 150 and not worm in self.worms:
					net.append(worm)
					self.used.append(worm)
			self.network.append((selfWorm, net))
	
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
		
		for worm in self.worms:
			draw_lightning(win, self.pos, worm.pos, (250, 250, 21))
		for net in self.network:
			for worm in net[1]:
				draw_lightning(win, net[0].pos, worm.pos, (250, 250, 21))