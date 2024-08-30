

import pygame
from math import atan2, pi, sin, cos
from typing import List

from common import Entity, GameVariables, point2world, CRITICAL_FALL_VELOCITY, sprites
from common.vector import Vector

from game.map_manager import MapManager, GRD
from game.visual_effects import splash


class PhysObj(Entity):
	''' a physical object '''

	def __init__(self, pos=(0,0), **kwargs) -> None:
		''' initialize '''
		GameVariables().register_physical(self)
		self.acc = Vector(0,0)
		self.vel = Vector(0,0)
		self.pos = Vector(pos[0], pos[1])
		
		self.radius = 4
		self.stable = False
		self.damp = 0.4
		
		self.bounce_before_death = -1
		self.dead = False
		self.color = (255, 0, 0)
		self.is_wind_affected = GameVariables().initial_variables.all_wind_affected
		self.is_boom_affected = True
		self.is_fall_affected = True

		self.health = None

		# colliders, true means colliding with
		self.is_extra_collider = False
		self.is_worm_collider = False
	
	def step(self) -> None:
		self.apply_force()
		
		# velocity
		self.vel += self.acc * GameVariables().dt
		self.limit_vel()
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
				if not self.is_worm_collider and MapManager().worm_col_map.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
				elif not self.is_extra_collider and MapManager().objects_col_map.get_at((int(testPos.x), int(testPos.y))) != (0,0,0):
					response += ppos - testPos
					collision = True
			
			r += pi / 8
		
		magVel = self.vel.getMag()
		
		if collision:
			
			self.on_collision(ppos)
			if magVel > CRITICAL_FALL_VELOCITY and self.is_fall_affected:
				self.damage(magVel * 1.5 * GameVariables().fall_damage_mult, 1)
			self.stable = True
			
			response.normalize()

			fdot = self.vel.dot(response)
			if not self.bounce_before_death == 1:
				
				# damp formula 1 - logarithmic
				# dampening = max(self.damp, self.damp * log(magVel) if magVel > 0.001 else 1)
				# dampening = min(dampening, min(self.damp * 2, 0.9))
				# newVel = ((response * -2 * fdot) + self.vel) * dampening
				
				# legacy formula
				newVel = ((response * -2 * fdot) + self.vel) * self.damp * GameVariables().damp_mult
					
				self.vel = newVel
				# max speed recorded ~ 25
			
			if self.bounce_before_death > 0:
				self.bounce_before_death -= 1
				self.dead = self.bounce_before_death == 0
				
		else:
			self.pos = ppos
			
		# flew out Game._game.map_manager.game_map but not worms !
		if self.pos.y > MapManager().game_map.get_height() - GameVariables().water_level and not self in GameVariables().get_worms():
			splash(self.pos, self.vel)
			angle = self.vel.getAngle()
			if (angle > 2.7 and angle < 3.14) or (angle > 0 and angle < 0.4):
				if self.vel.getMag() > 7:
					self.pos.y = MapManager().game_map.get_height() - GameVariables().water_level - 1
					self.vel.y *= -1
					self.vel.x *= 0.8
			else:
				self.on_out_of_map()
				self.remove_from_game()
				return
		
		if magVel < 0.1: # creates a double jump problem
			self.stable = True
		
		if self.dead:
			self.remove_from_game()
			self.death_response()
		
		self.secondaryStep()
	
	def apply_force(self) -> None:
		# gravity:
		self.acc.y += GameVariables().physics.global_gravity
		if self.is_wind_affected > 0:
			if self.pos.x < - 3 * MapManager().game_map.get_width() or self.pos.x > 4 * MapManager().game_map.get_width():
				return
			self.acc.x += GameVariables().physics.wind * 0.1 * GameVariables().wind_mult * self.is_wind_affected
	
	def move(self, facing: int) -> bool:
		''' move the object one pixel in the facing direction, return True if succeded '''
		dir = facing
		if MapManager().check_free_pos(self.radius, self.pos + Vector(dir, 0)):
			self.pos += Vector(dir, 0) * GameVariables().dt
			return True
		else:
			for i in range(1, 5):
				if MapManager().check_free_pos(self.radius, self.pos + Vector(dir, -i)):
					self.pos += Vector(dir, -i) * GameVariables().dt
					return True
			for i in range(1,5):
				if MapManager().check_free_pos(self.radius, self.pos + Vector(dir, i)):
					self.pos += Vector(dir, i) * GameVariables().dt
					return True
		return False

	def death_response(self):
		pass
	
	def secondaryStep(self):
		pass
	
	def remove_from_game(self) -> None:
		GameVariables().unregister_physical(self)
	
	def damage(self, value, damageType=0):
		pass
	
	def on_collision(self, ppos):
		pass
	
	def on_out_of_map(self):
		pass
	
	def limit_vel(self):
		pass
	
	def draw(self, win: pygame.Surface) -> None:
		pygame.draw.circle(win, self.color, point2world(self.pos), int(self.radius)+1)