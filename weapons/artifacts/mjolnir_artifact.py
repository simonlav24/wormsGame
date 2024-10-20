
from math import degrees, atan2, pi, cos, sin
from typing import List
from random import randint, uniform

import pygame

from common import GameVariables, sprites, point2world, EntityWorm, draw_lightning, seek, LEFT
from common.vector import tup2vec, Vector, distus, vectorCopy

from game.world_effects import boom
from game.map_manager import MapManager, GRD
from game.team_manager import TeamManager
from weapons.artifacts.deployable_artifact import DeployableArtifact
from entities import PhysObj

class MjolnirArtifact(DeployableArtifact):
	
	def set_surf(self):
		self.surf = pygame.Surface((16,16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0,112,16,16))
	
	def comment_creation(self):
		GameVariables().commentator.comment([{'text': "a gift from the gods"}])
	
	def comment_pick(self):
		return ("", " is worthy to wield mjolnir!")
	
	def step(self):
		super().step()
		if self.vel.getMag() > 1:
			self.angle = -degrees(self.vel.getAngle()) - 90
	
	def on_collision(self, ppos):
		vel = self.vel.getMag()
		if vel > 4:
			boom(self.pos, max(20, 2 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(sprites.image_mjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size()) / 2))




class MjolnirThrow(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		GameVariables().move_to_back_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.damp = 0.3
		self.rotating = True
		self.angle = 0
		self.stableCount = 0
		self.worms = []

	def step(self):
		super().step()
		if self.vel.getMag() > 1:
			self.rotating = True
		else:
			self.rotating = False
		if self.rotating:
			self.angle = -degrees(self.vel.getAngle()) - 90
		
		if self.stable:
			self.stableCount += 1
		else:
			self.stableCount = 0
		if self.stableCount > 20:
			self.remove_from_game()
			self.returnToWorm()
		
		# electrocute
		self.worms: List[EntityWorm] = []
		for worm in GameVariables().get_worms():
			if worm in TeamManager().current_team.worms:
				continue
			if distus(self.pos, worm.pos) < 10000:
				self.worms.append(worm)
		
		for worm in self.worms:
			if randint(1,100) < 5:
				worm.damage(randint(1,8))
				a = lambda x : 1 if x >= 0 else -1
				worm.vel -= Vector(a(self.pos.x - worm.pos.x) * uniform(1.2,2.2), uniform(1.2,3.2))
			if worm.health <= 0:
				self.worms.remove(worm)
		
		GameVariables().game_distable()
	def returnToWorm(self):
		MjolnirReturn(self.pos, self.angle)
	def on_collision(self, ppos):
		vel = self.vel.getMag()
		# print(vel, vel * 4)
		if vel > 4:
			boom(self.pos, max(20, 4 * self.vel.getMag()))
		elif vel < 1:
			self.vel *= 0
	def on_out_of_map(self):
		self.returnToWorm()
	def draw(self, win: pygame.Surface):
		for worm in self.worms:
			draw_lightning(win, self.pos, worm.pos)
		surf = pygame.transform.rotate(sprites.image_mjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirReturn:
	def __init__(self, pos, angle):
		GameVariables().register_non_physical(self)
		self.pos = Vector(pos[0], pos[1])
		self.acc = Vector()
		self.vel = Vector()
		self.angle = angle
		GameVariables().cam_track = self
		self.speedLimit = 8
	def step(self):
		self.acc = seek(self, GameVariables().player.pos, self.speedLimit, 1)
		
		self.vel += self.acc
		self.vel.limit(self.speedLimit)
		self.pos += self.vel
		
		self.angle += (0 - self.angle) * 0.1
		GameVariables().game_distable()
		if distus(self.pos, GameVariables().player.pos) < GameVariables().player.radius * GameVariables().player.radius * 2:
			GameVariables().unregister_non_physical(self)
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(sprites.image_mjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size()) / 2))


class MjolnirFly(PhysObj):
	flying = False
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 3
		self.damp = 0.3
		self.rotating = True
		self.angle = 0
		MjolnirFly.flying = True
	def step(self):
		super().step()
		if self.vel.getMag() > 1:
			self.rotating = True
		else:
			self.rotating = False
		if self.rotating:
			self.angle = -degrees(self.vel.getAngle()) - 90
			
		GameVariables().player.pos = vectorCopy(self.pos)
		GameVariables().player.vel = Vector()
	def on_collision(self, ppos):
		# colission with world:
		response = Vector(0,0)
		angle = atan2(self.vel.y, self.vel.x)
		r = angle - pi#- pi/2
		while r < angle + pi:#+ pi/2:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() - GameVariables().water_level or testPos.x < 0:
				if GameVariables().config.option_closed_map:
					response += ppos - testPos
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				r += pi /8
				continue
			
			if MapManager().game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
			
			r += pi /8
		
		self.remove_from_game()
		response.normalize()
		pos = self.pos + response * (GameVariables().player.radius + 2)
		GameVariables().player.pos = pos
		
	def remove_from_game(self):
		GameVariables().unregister_physical(self)
		MjolnirFly.flying = False
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(sprites.image_mjolnir, self.angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))

class MjolnirStrike:
	def __init__(self):
		self.pos = GameVariables().player.pos
		GameVariables().register_non_physical(self)
		self.stage = 0
		self.timer = 0
		self.angle = 0
		self.worms = []
		self.facing = GameVariables().player.facing
		GameVariables().player.is_boom_affected = False
		self.radius = 0
	def step(self):
		self.pos = GameVariables().player.pos
		self.facing = GameVariables().player.facing
		if self.stage == 0:
			self.angle += 1
			if self.timer >= GameVariables().fps * 4:
				self.stage = 1
				self.timer = 0
			# electrocute:
			self.worms: List[EntityWorm] = []
			for worm in GameVariables().get_worms():
				if worm in TeamManager().current_team.worms:
					continue
				if self.pos.x - 60 < worm.pos.x and worm.pos.x < self.pos.x + 60 and worm.pos.y <= self.pos.y:
					self.worms.append(worm)
					
			for worm in self.worms:
				if randint(1,100) < 5:
					worm.damage(randint(1,8))
					a = lambda x : 1 if x >= 0 else -1
					worm.vel -= Vector(a(self.pos.x - worm.pos.x) * uniform(1.2,2.2), uniform(1.2,3.2))
				if worm.health <= 0:
					self.worms.remove(worm)
		elif self.stage == 1:
			self.angle += -30
			if self.timer >= GameVariables().fps * 0.25:
				boom(self.pos, 40)
				GameVariables().unregister_non_physical(self)
				GameVariables().player.is_boom_affected = True
		self.timer += 1
		GameVariables().game_distable()
	def draw(self, win: pygame.Surface):
		surf = pygame.transform.rotate(sprites.image_mjolnir, self.angle)
		surf = pygame.transform.flip(surf, self.facing == LEFT, False)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2 + Vector(0, -5)))
		draw_lightning(win, Vector(self.pos.x, 0), self.pos)
		for worm in self.worms:
			draw_lightning(win, Vector(self.pos.x, randint(0, int(self.pos.y))), worm.pos)