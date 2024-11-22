
from random import randint, choice

import pygame

from common import GameVariables, point2world, blit_weapon_sprite, draw_target
from common.vector import *

from game.world_effects import boom
from game.visual_effects import Blast, FireWork
from game.sfx import Sfx, SfxIndex


class FireWorkRockets:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.objects = []
		self.state = "tag"
		self.timer = 0
		self.picked = 0
		self.pos = None
	
	def step(self):
		if self.state == "thrusting":
			self.timer += 1
			if self.timer > 1.5 * GameVariables().fps:
				self.state = "exploding"
			for obj in self.objects:
				obj.acc += Vector(0, -0.34)
				Blast(obj.pos + Vector(0, obj.radius * 1.5) + vectorUnitRandom() * 2, randint(5, 8), 80)
		elif self.state == "exploding":
			for obj in self.objects:
				FireWork(obj.pos, GameVariables().player.get_team_data().color)
				boom(obj.pos, 22)
			self.done()
	
	def done(self):
		GameVariables().unregister_non_physical(self)
		Sfx().loop_decrease(SfxIndex.THRUST_LOOP, 100)
	
	def fire(self):
		"""return true if fired"""
		if self.state == "tag":
			candidates = []
			for obj in GameVariables().get_physicals():
				if obj == GameVariables().player or obj in self.objects:
					continue
				if distus(obj.pos, GameVariables().player.pos) < 15*15:
					candidates.append(obj)
			# take the closest
			if len(candidates) > 0:
				candidates.sort(key = lambda x: distus(x.pos, GameVariables().player.pos))
				self.objects.append(candidates[0])
			self.picked += 1
			if self.picked >= 3:
				self.state = "ready"
		elif self.state == "ready":
			Sfx().loop_increase(SfxIndex.THRUST_LOOP)
			self.state = "thrusting"
			for obj in self.objects:
				obj.vel += Vector(randint(-3,3), -2)
			if len(self.objects) > 0:
				GameVariables().cam_track = choice(self.objects)
			return True
		return False
	
	def draw(self, win: pygame.Surface):
		if self.state in ["tag"]:
			for obj in GameVariables().get_physicals():
				if obj == GameVariables().player or obj in self.objects:
					continue
				if distus(obj.pos, GameVariables().player.pos) < 15*15:
					draw_target(win, obj.pos)
		
		for obj in self.objects:
			blit_weapon_sprite(win, point2world(obj.pos - Vector(8,8)), "fireworks")


def fire_firework(*args, **kwargs):
	obj = kwargs.get('shooted_object', None)
	if obj is None:
		obj = FireWorkRockets()
		return obj
	obj.fire()
	return obj
