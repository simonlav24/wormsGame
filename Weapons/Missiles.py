

import pygame
from typing import List
from math import cos, pi, sin, radians, degrees
from random import uniform, randint, choice

from common import blit_weapon_sprite, ColorType, GameVariables, point2world
from common.vector import *

from entities.physical_entity import PhysObj
from game.world_effects import boom
from game.visual_effects import Blast
from game.map_manager import MapManager, GRD, SKY

class Missile (PhysObj):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255,255,0)
		self.bounceBeforeDeath = 1
		self.windAffected = 1
		self.boomRadius = 28
		self.megaBoom = False or GameVariables().mega_weapon_trigger
		if randint(0,50) == 1:
			self.megaBoom = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "missile")
	def deathResponse(self):
		if self.megaBoom:
			self.boomRadius *= 2
		boom(self.pos, self.boomRadius)
	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), randint(5,8), 30, 3)


class GravityMissile(Missile):
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255,255,0)
		self.bounceBeforeDeath = 1
		self.windAffected = 1
		self.boomRadius = 28
		self.megaBoom = False or GameVariables().mega_weapon_trigger
		if randint(0,50) == 1:
			self.megaBoom = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "gravity missile")

	def deathResponse(self):
		boom(self.pos, self.boomRadius, True, True)
		
	def applyForce(self):
		# gravity:
		self.acc.y -= GameVariables().physics.global_gravity
		self.acc.x += GameVariables().physics.wind * 0.1 * GameVariables().wind_mult
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2, 5)
		if self.pos.y < 0:
			self.removeFromGame()


class DrillMissile(PhysObj):
	mode = False #True = drill
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.lastPos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 7
		self.color = (102, 51, 0)
		self.boomRadius = 30
		self.boomAffected = False
		
		self.drillVel = None
		self.inGround = False
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "drill missile")

	def step(self):
		self.applyForce()
		
		# velocity
		if self.inGround:
			if self.mode:
				self.vel = self.drillVel
				self.vel.setMag(2)
			else:
				self.vel += self.acc * GameVariables().dt
				self.vel.limit(5)
		else:
			self.vel += self.acc * GameVariables().dt
		
		# position
		ppos = self.pos + self.vel * GameVariables().dt
		
		# reset forces
		self.acc *= 0
		self.stable = False
		
		collision = False
		# colission with world:
		direction = self.vel.getDir()
		
		checkPos = (self.pos + direction*self.radius).vec2tupint()
		if not(checkPos[0] >= MapManager().game_map.get_width() or checkPos[0] < 0 or checkPos[1] >= MapManager().game_map.get_height() or checkPos[1] < 0):
			if MapManager().game_map.get_at(checkPos) == GRD:
				self.inGround = True
				self.drillVel = vectorCopy(self.vel)
		if self.inGround:
			self.timer += 1 * GameVariables().dt
					
		checkPos = (self.pos + direction*(self.radius + 2)).vec2tupint()
		if not(checkPos[0] >= MapManager().game_map.get_width() or checkPos[0] < 0 or checkPos[1] >= MapManager().game_map.get_height() or checkPos[1] < 0):
			if not MapManager().game_map.get_at(checkPos) == GRD and self.inGround:
				self.dead = True
				
		if self.timer >= GameVariables().fps * 2:
			self.dead = True
			
		self.lastPos.x, self.lastPos.y = self.pos.x, self.pos.y
		self.pos = ppos
		
		if self.inGround:
			boom(self.pos, self.radius, False)
		self.lineOut((self.lastPos.vec2tupint(), self.pos.vec2tupint()))
		
		# flew out MapManager().game_map but not worms !
		if self.pos.y > MapManager().game_map.get_height():
			self.removeFromGame()
			return
		if self.inGround and self.pos.y <= 0:
			self.dead = True

		if self.vel.getMag() < 0.1:
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self.removeFromGame()
			self.deathResponse()

	def lineOut(self,line):
		pygame.draw.line(MapManager().game_map, SKY, line[0], line[1], self.radius * 2)
		pygame.draw.line(MapManager().ground_map, SKY, line[0], line[1], self.radius * 2)

	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size()) / 2))

	def deathResponse(self):
		boom(self.pos, 23)



class HomingMissile(PhysObj):
	Target = Vector()
	showTarget = False
	def __init__(self, pos, direction, energy):
		self.initialize()
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0, 51, 204)
		self.bounceBeforeDeath = 1
		self.windAffected = 1
		self.boomRadius = 30
		self.activated = False
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "homing missile")

	def applyForce(self):
		# gravity:
		if self.activated:
			desired = HomingMissile.Target - self.pos
			desired.setMag(50)
			self.acc = desired - self.vel
			self.acc.limit(1)
		else:
			self.acc.y += GameVariables().physics.global_gravity
	
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom() * 2 - 10 * normalize(self.vel), 5)
		self.timer += 1
		if self.timer == 20:
			self.activated = True
		if self.timer == 20 + GameVariables().fps * 5:
			self.activated = False
	
	def limitVel(self):
		self.vel.limit(15)
	
	def outOfMapResponse(self):
		HomingMissile.showTarget = False
	
	def collisionRespone(self, ppos):
		HomingMissile.showTarget = False
		boom(ppos, self.boomRadius)
	
	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))