

import pygame
from math import pi, degrees
from random import uniform, randint

from common import blit_weapon_sprite, GameVariables, point2world, seek, flee
from common.vector import *

from entities.physical_entity import PhysObj
from entities import Debrie
from game.world_effects import boom, sample_colors
from game.visual_effects import Blast
from game.map_manager import MapManager, GRD, SKY
from game.sfx import Sfx, SfxIndex

class Missile (PhysObj):
	def __init__(self, pos, direction, energy, weapon_name="missile"):
		super().__init__(pos)
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (255,255,0)
		self.bounce_before_death = 1
		self.is_wind_affected = 1
		self.boom_radius = 28
		self.megaBoom = False or GameVariables().mega_weapon_trigger
		if randint(0,50) == 1:
			self.megaBoom = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), weapon_name)
	
	def death_response(self):
		if self.megaBoom:
			self.boom_radius *= 2
		boom(self.pos, self.boom_radius)
	
	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))
	
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2 - 10 * normalize(self.vel), randint(5,8), 30, 3)


class GravityMissile(Missile):
	def __init__(self, pos, direction, energy):
		super().__init__(pos, direction, energy, "gravity missile")

	def death_response(self):
		boom(self.pos, self.boom_radius, True, True)
		
	def apply_force(self):
		# gravity:
		self.acc.y -= GameVariables().physics.global_gravity
		self.acc.x += GameVariables().physics.wind * 0.1 * GameVariables().wind_mult
	
	def secondaryStep(self):
		Blast(self.pos + vectorUnitRandom()*2, 5)
		if self.pos.y < 0:
			self.remove_from_game()


class DrillMissile(PhysObj):
	mode = False #True = drill
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = MapManager().get_closest_pos_available(Vector(pos[0], pos[1]), self.radius)
		self.lastPos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 7
		self.color = (102, 51, 0)
		self.boom_radius = 30
		self.is_boom_affected = False
		
		self.drill_vel = None
		self.in_ground = False
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "drill missile")
		self.colors = Blast._color

	def on_drill(self):
		self.in_ground = True
		Sfx().loop_increase(SfxIndex.DRILL_LOOP)


	def step(self):
		self.apply_force()
		
		# velocity
		if self.in_ground:
			if self.mode:
				self.vel = self.drill_vel
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
		
		# colission with world:
		direction = self.vel.getDir()
		
		checkPos = (self.pos + direction * self.radius).vec2tupint()
		if not(checkPos[0] >= MapManager().game_map.get_width() or checkPos[0] < 0 or checkPos[1] >= MapManager().game_map.get_height() or checkPos[1] < 0):
			if MapManager().game_map.get_at(checkPos) == GRD:
				self.on_drill()
				self.drill_vel = vectorCopy(self.vel)
		if self.in_ground:
			self.timer += 1 * GameVariables().dt
					
		checkPos = (self.pos + direction*(self.radius + 2)).vec2tupint()
		if not(checkPos[0] >= MapManager().game_map.get_width() or checkPos[0] < 0 or checkPos[1] >= MapManager().game_map.get_height() or checkPos[1] < 0):
			if not MapManager().game_map.get_at(checkPos) == GRD and self.in_ground:
				self.dead = True
				
		if self.timer >= GameVariables().fps * 2:
			self.dead = True
			
		self.lastPos.x, self.lastPos.y = self.pos.x, self.pos.y
		self.pos = ppos
		
		if self.in_ground:
			colors = sample_colors(self.pos, self.radius, default_if_none=False)
			if len(colors) > 0:
				self.colors = colors

			boom(self.pos, self.radius, fire=True, debries=False)
			for _ in range(randint(1, 5)):
				debrie = Debrie(self.pos - normalize(self.vel) * self.radius + normalize(self.vel).getNormal() * self.radius * uniform(-1, 1), 1.0, colors=self.colors, firey=False)
				debrie.vel = vectorCopy(self.vel * -1) + vectorUnitRandom()
				
		self.line_out((self.lastPos.vec2tupint(), self.pos.vec2tupint()))
		
		# flew out MapManager().game_map but not worms !
		if self.pos.y > MapManager().game_map.get_height():
			self.remove_from_game()
			return
		if self.in_ground and self.pos.y <= 0:
			self.dead = True

		if self.vel.getMag() < 0.1:
			self.stable = True
		
		if self.dead:
			self.remove_from_game()
			self.death_response()

	def remove_from_game(self):
		super().remove_from_game()
		Sfx().loop_decrease(SfxIndex.DRILL_LOOP, fade_out_ms=50, force_stop=True)

	def line_out(self,line):
		pygame.draw.line(MapManager().game_map, SKY, line[0], line[1], self.radius * 2)
		pygame.draw.line(MapManager().ground_map, SKY, line[0], line[1], self.radius * 2)

	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size()) / 2))

	def death_response(self):
		boom(self.pos, 23)



class HomingMissile(PhysObj):
	def __init__(self, pos, direction, energy):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (0, 51, 204)
		self.bounce_before_death = 1
		self.is_wind_affected = 1
		self.boom_radius = 30
		self.activated = False
		self.timer = 0
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "homing missile")

	def apply_force(self):
		# gravity:
		if self.activated:
			desired = GameVariables().point_target - self.pos
			desired.setMag(50)
			self.acc = desired - self.vel
			self.acc.limit(1)
		else:
			self.acc.y += GameVariables().physics.global_gravity
	
	def activate(self, is_activated: bool):
		self.activated = is_activated
		if self.activated:
			Sfx().play(SfxIndex.MINE_ACTIVATE)
			Sfx().loop_increase(SfxIndex.THRUST_LOOP)
		else:
			Sfx().loop_decrease(SfxIndex.THRUST_LOOP, 100)

	def step(self):
		super().step()
		Blast(self.pos + vectorUnitRandom() * 2 - 10 * normalize(self.vel), 5)
		self.timer += 1
		if self.timer == 20:
			self.activate(True)
		if self.timer == 20 + GameVariables().fps * 5:
			self.activate(False)
	
	def remove_from_game(self):
		super().remove_from_game()
		Sfx().loop_decrease(SfxIndex.THRUST_LOOP, 100)

	def limit_vel(self):
		self.vel.limit(15)
	
	def on_collision(self, ppos):
		super().on_collision(ppos)
		boom(ppos, self.boom_radius)
	
	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))


class SeekerBase:
	def __init__(self, pos, direction, energy):
		GameVariables().register_non_physical(self)
		self.pos = vectorCopy(pos)
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.acc = Vector()
		self.maxSpeed = 5
		self.maxForce = 1
		self.color = (255,100,0)
		self.avoid = []
		self.radius = 6

		self.timer = 15 * GameVariables().fps
		self.target = GameVariables().point_target
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "seeker")
	
	def step(self):
		self.timer -= 1
		if self.timer == 0:
			self.death_response()
		GameVariables().game_distable()
		getForce = seek(self, self.target, self.maxSpeed, self.maxForce)
		avoidForce = Vector()
		distance = dist(self.pos, self.target)
		if distance > 30:
			self.avoid = []
			visibility = int(0.1 * distance + 10)
			for i in range(20):
				direction = vector_from_angle((i / 20) * 2 * pi)
				for j in range(visibility):
					test_pos = self.pos + direction * j
					if MapManager().is_ground_at(test_pos.integer()):
						self.avoid.append(test_pos)
		else:
			if MapManager().is_ground_at(self.pos):
				self.hit_response()
				return
			
		if distance < 8:
			self.hit_response()
			return
			
		for i in self.avoid:
			# if dist(self.pos, i) < 50:
			avoidForce += flee(self, i, self.maxSpeed, self.maxForce)
		
		force = avoidForce + getForce
		self.apply_force(force)
		
		self.vel += self.acc
		self.vel.limit(self.maxSpeed)
		
		ppos = self.pos + self.vel
		while MapManager().is_ground_at(ppos.integer()):
			self.vel *= -1
			self.vel.rotate(uniform(-0.5,0.5))
			ppos = self.pos + self.vel
		
		self.pos = ppos
	
	def hit_response(self):
		self.death_response()
	
	def death_response(self):
		boom(self.pos, 30)
		GameVariables().unregister_non_physical(self)
	
	def apply_force(self, force):
		force.limit(self.maxForce)
		self.acc = vectorCopy(force)
	
	def draw(self, win: pygame.Surface):
		angle = -degrees(self.vel.getAngle()) - 90
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))


class Seeker(SeekerBase):
	def step(self):
		super().step()
		Blast(self.pos + vectorUnitRandom() * 2 - 10 * normalize(self.vel), randint(5, 8), 30, 3)