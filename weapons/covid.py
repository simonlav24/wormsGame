

import pygame

from common import GameVariables, point2world, sprites, Sickness
from common.vector import *

from weapons.missiles import SeekerBase


class Covid19(SeekerBase):
	def __init__(self, pos: Vector, immune_team_name: str):
		super().__init__(pos, Vector(), 5)
		self.timer = 12 * GameVariables().fps
		self.target = Vector()
		self.wormTarget = None
		self.chum = None
		self.unreachable = []
		self.bitten = []
		for worm in GameVariables().get_worms():
			if worm.get_team_data().team_name == immune_team_name:
				self.bitten.append(worm)
	
	def step(self):
		super().step()
		# find target
		closest = 800
		for worm in GameVariables().get_worms():
			if worm in self.bitten or worm in self.unreachable:
				continue
			distance = dist(worm.pos, self.pos)
			if distance < closest:
				closest = distance
				self.target = worm.pos
				self.wormTarget = worm
	
	def hitResponse(self):
		self.bitten.append(self.wormTarget)
		self.target = Vector()
		# sting
		if not self.wormTarget:
			return
		self.wormTarget.vel.y -= 2
		if self.wormTarget.vel.y < -3:
			self.wormTarget.vel.y = 3
		if self.pos.x > self.wormTarget.pos.x:
			self.wormTarget.vel.x -= 2
		else:
			self.wormTarget.vel.x += 2
		self.wormTarget.damage(10)
		self.wormTarget.sicken(Sickness.VIRUS)
		self.wormTarget = None
	
	def draw(self, win: pygame.Surface):
		frame = GameVariables().time_overall // 2 % 5
		win.blit(sprites.sprite_atlas, point2world(self.pos - Vector(8, 8)), ((frame * 16, 32), (16, 16)) )