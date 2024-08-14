

import pygame
from math import atan2, pi, sin, cos
from typing import List

from common import Entity, GameVariables, point2world, CRITICAL_FALL_VELOCITY, sprites
from common.vector import Vector

from game.map_manager import MapManager, GRD
from game.visual_effects import splash

# todo: to remove all _regs

class PhysObj(Entity):
	''' a physical object '''
	_reg: List['PhysObj'] = []
	_toRemove = []
	_worms = []
	_mines = []
	def initialize(self):
		PhysObj._reg.append(self)
		self.vel = Vector(0,0)
		self.acc = Vector(0,0)
		
		self.stable = False
		self.damp = 0.4
		
		self.bounceBeforeDeath = -1
		self.dead = False
		self.color = (255,0,0)
		self.windAffected = GameVariables().initial_variables.all_wind_affected
		self.boomAffected = True
		self.fallAffected = True
		self.health = None
		self.extraCollider = False
		self.wormCollider = False
	
	def __init__(self, pos):
		self.initialize()
		self.pos = Vector(pos[0],pos[1])
		
		self.radius = 4
	
	def step(self):
		self.applyForce()
		
		# velocity
		self.vel += self.acc * GameVariables().dt
		self.limitVel()
		# position
		ppos = self.pos + self.vel * GameVariables().dt
		
		# reset forces
		self.acc *= 0
		self.stable = False
		
		angle = atan2(self.vel.y, self.vel.x)
		response = Vector(0,0)
		collision = False
		
		# colission with world:
		r = angle - pi
		while r < angle + pi:
			testPos = Vector((self.radius) * cos(r) + ppos.x, (self.radius) * sin(r) + ppos.y)
			if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() - GameVariables().water_level or testPos.x < 0:
				if GameVariables().config.option_closed_map:
					response += ppos - testPos
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
					continue
			if testPos.y < 0:
				if MapManager().is_ground_at((int(testPos.x), 0)):
					response += ppos - testPos
					collision = True
					r += pi /8
					continue
				else:
					r += pi /8
				continue
			
			# collission with Game._game.map_manager.game_map:
			if MapManager().game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
				response += ppos - testPos
				collision = True
				r += pi /8; continue

			else:
				if not self.wormCollider and MapManager().worm_col_map.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
				elif not self.extraCollider and MapManager().objects_col_map.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
			
			r += pi / 8
		
		magVel = self.vel.getMag()
		
		if collision:
			
			self.collisionRespone(ppos)
			if magVel > CRITICAL_FALL_VELOCITY and self.fallAffected:
				self.damage(magVel * 1.5 * GameVariables().fall_damage_mult, 1)
				# blood
				if self in PhysObj._worms:
					MapManager().stain(self.pos, sprites.blood, sprites.blood.get_size(), False)
			self.stable = True
			
			response.normalize()
			#addExtra(self.pos + 5 * response, (0,0,0), 1)
			fdot = self.vel.dot(response)
			if not self.bounceBeforeDeath == 1:
				
				# damp formula 1 - logarithmic
				# dampening = max(self.damp, self.damp * log(magVel) if magVel > 0.001 else 1)
				# dampening = min(dampening, min(self.damp * 2, 0.9))
				# newVel = ((response * -2 * fdot) + self.vel) * dampening
				
				# legacy formula
				newVel = ((response * -2 * fdot) + self.vel) * self.damp * GameVariables().damp_mult
					
				self.vel = newVel
				# max speed recorded ~ 25
			
			if self.bounceBeforeDeath > 0:
				self.bounceBeforeDeath -= 1
				self.dead = self.bounceBeforeDeath == 0
				
		else:
			self.pos = ppos
			
		# flew out Game._game.map_manager.game_map but not worms !
		if self.pos.y > MapManager().game_map.get_height() - GameVariables().water_level and not self in self._worms:
			splash(self.pos, self.vel)
			angle = self.vel.getAngle()
			if (angle > 2.7 and angle < 3.14) or (angle > 0 and angle < 0.4):
				if self.vel.getMag() > 7:
					self.pos.y = MapManager().game_map.get_height() - GameVariables().water_level - 1
					self.vel.y *= -1
					self.vel.x *= 0.8
			else:
				self.outOfMapResponse()
				self.removeFromGame()
				return
		
		if magVel < 0.1: # creates a double jump problem
			self.stable = True
		
		self.secondaryStep()
		
		if self.dead:
			self.removeFromGame()
			self.deathResponse()
	def applyForce(self):
		# gravity:
		self.acc.y += GameVariables().physics.global_gravity
		if self.windAffected > 0:
			if self.pos.x < - 3 * MapManager().game_map.get_width() or self.pos.x > 4 * MapManager().game_map.get_width():
				return
			self.acc.x += GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * self.windAffected
	def deathResponse(self):
		pass
	def secondaryStep(self):
		pass
	def removeFromGame(self):
		PhysObj._toRemove.append(self)
	def damage(self, value, damageType=0):
		pass
	def collisionRespone(self, ppos):
		pass
	def outOfMapResponse(self):
		pass
	def limitVel(self):
		pass
	def draw(self, win: pygame.Surface):
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)