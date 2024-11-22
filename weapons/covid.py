

import pygame

from common import GameVariables, point2world, sprites, Sickness
from common.vector import *

from weapons.missiles import SeekerBase
from game.sfx import Sfx, SfxIndex


class Covid19(SeekerBase):
	def __init__(self, pos: Vector, immune_team_name: str):
		super().__init__(pos, Vector(), 5)
		self.timer = 12 * GameVariables().fps
		self.target = Vector()
		self.worm_target = None
		self.unreachable = []
		self.bitten = []
		for worm in GameVariables().get_worms():
			if worm.get_team_data().team_name == immune_team_name:
				self.bitten.append(worm)
		Sfx().loop_increase(SfxIndex.BAT_LOOP)
	
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
				self.worm_target = worm
	
	def death_response(self):
		super().death_response()
		Sfx().loop_decrease(SfxIndex.BAT_LOOP, 150, True)

	def hit_response(self):
		self.bitten.append(self.worm_target)
		self.target = Vector()
		# sting
		if not self.worm_target:
			return
		self.worm_target.vel.y -= 2
		if self.worm_target.vel.y < -3:
			self.worm_target.vel.y = 3
		if self.pos.x > self.worm_target.pos.x:
			self.worm_target.vel.x -= 2
		else:
			self.worm_target.vel.x += 2
		self.worm_target.damage(10)
		self.worm_target.sicken(Sickness.VIRUS)
		self.worm_target = None
	
	def draw(self, win: pygame.Surface):
		frame = GameVariables().time_overall // 2 % 5
		win.blit(sprites.sprite_atlas, point2world(self.pos - Vector(8, 8)), ((frame * 16, 32), (16, 16)) )