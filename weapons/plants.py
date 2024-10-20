

from enum import Enum
from random import randint, choice, uniform
from math import pi, sin, sqrt, degrees, copysign

import pygame

from common import GameVariables, point2world, sprites, GameState, blit_weapon_sprite, RIGHT, LEFT, EntityWorm, PlantMode
from common.vector import *

from game.map_manager import MapManager, GRD
from game.visual_effects import EffectManager
from game.world_effects import boom
from entities import PhysObj, Debrie, Worm
from weapons.mine import Mine
from entities.gun_shell import GunShell
from entities.worm import DamageType

def generate_leaf(pos, direction, color) -> None:
	''' draw procedural leaf on the map '''
	points = []
	width = max(0.3, uniform(0,1))
	length = 1 + uniform(0,1)
	for i in range(10):
		x = (i/10) * length
		y = 0.5 * width * sin(2 * (1/length) * pi * x)
		points.append(Vector(x, y))
	for i in range(10):
		x = (1 - (i/10)) * length
		y = - width * sqrt(1 - ((2/length) * (x - length/2))**2)
		points.append(Vector(x, y))
	if randint(0,1) == 0:
		points = [Vector(-i.x, i.y) for i in points]
	size = uniform(4, 7)
	points = [pos + i.rotate(direction) * size for i in points]
	pygame.draw.polygon(MapManager().game_map, GRD, points)
	pygame.draw.polygon(MapManager().ground_map, color, points)

class Venus:
	grow = -1
	catch = 0
	idle = 1
	hold = 2
	release = 3
	def __init__(self, pos, angle = -1):
		GameVariables().register_non_physical(self)
		GameVariables().get_plants().append(self)
		self.pos = pos
		self.offset = Vector(25, 0)
		
		if angle == -1:
			self.direction = vectorUnitRandom()
		else:
			self.direction = vector_from_angle(angle)
		self.angle = self.direction.getAngle()
		self.d1 = self.direction.normal()
		self.d2 = self.d1 * -1
		
		self.snap = 0
		self.gap = 0
		
		self.mode = Venus.grow
		self.timer = 0
		self.scale = 0
		self.explossive = False
		self.opening = -pi/2 + uniform(0, 0.8)
		self.mutant = False
		self.desired = None

		self.p1 = Vector()
		self.p2 = Vector()
		
		self.surf = pygame.Surface((48, 16), pygame.SRCALPHA)
		self.surf.blit(sprites.sprite_atlas, (0,0), (0, 64, 48, 16))
	
	def step(self):
		self.gap = 5*(self.snap + pi/2)/(pi/2)
		self.d1 = self.direction.normal()
		self.d2 = self.d1 * -1
		self.p1 = self.pos + self.d1 * self.gap
		self.p2 = self.pos + self.d2 * self.gap
		
		if self.mode == Venus.grow:
			# check if can eat a worm from here on first round:
			if GameVariables().game_turn_count == 0 and GameVariables().game_state in [GameState.PLAYER_PLAY] and self.scale == 0:
				pos = self.pos + self.direction * 25
				for worm in GameVariables().get_worms():
					if distus(worm.pos, pos) <= 625:
						self.remove_from_game()
						return
			
			self.scale += 0.1
			if self.scale >= 1:
					
				self.scale = 1
				self.mode = Venus.hold
				MapManager().game_map.set_at(self.pos.vec2tupint(), GRD)
			GameVariables().game_distable()
			return
		
		self.angle = self.direction.getAngle()
		self.timer += 1
		if self.desired:
			current = self.direction.getAngle()
					
			if self.desired - current > pi:
				self.desired -= 2*pi
			if current - self.desired > pi:
				self.desired += 2*pi
			
			current += (self.desired - current) * 0.2
			self.direction.setAngle(current)
		
		if self.mode == Venus.idle:
			pos = self.pos + self.direction * 25
						
			if self.mutant:
				maxDist = 640000
				closest = None
				for worm in GameVariables().get_worms():
					distance = distus(worm.pos, self.pos)
					if distance < maxDist and distance < 6400:
						maxDist = distance
						closest = worm
				if closest:
					self.desired = (closest.pos - self.pos).getAngle()

			# iterate physicals
			for entity in GameVariables().get_physicals():
				if entity in GameVariables().get_debries():
					continue

				if distus(entity.pos, pos) <= 625:
					self.mode = Venus.catch
					if entity in GameVariables().get_worms():
						worm: EntityWorm = entity

						# if PLANT_MASTER in worm.team.artifacts:
						# 	continue
						worm.damage(100, damage_type=DamageType.PLANT, kill=True)
						name = worm.name_str
						color = worm.get_team_data().color
						comments = [
							[{'text': 'yummy'}],
							[{'text': name, 'color': color}, {'text': ' was delicious'}],
							[{'text': name, 'color': color}, {'text': ' is good protein'}],
							[{'text': name, 'color': color}, {'text': ' is some serious gourmet s**t'}],
						]
						GameVariables().commentator.comment(choice(comments))
					else:
						self.explossive = True
						entity.remove_from_game()
					break

		elif self.mode == Venus.catch:
			GameVariables().game_distable()
			self.snap += 0.5
			if self.snap >= 0:
				self.snap = 0
				self.mode = Venus.hold
				self.timer = 0
		elif self.mode == Venus.hold:
			GameVariables().game_distable()
			if self.timer == 1 * GameVariables().fps:
				self.mode = Venus.release
				if self.explossive:
					self.explossive = False
					for _ in range(randint(6, 14)):
						EffectManager().add_smoke(self.pos + self.direction * 25 + vectorUnitRandom() * randint(3,10))
		elif self.mode == Venus.release:
			GameVariables().game_distable()
			self.snap -= 0.1
			if self.snap <= self.opening:
				self.snap = self.opening
				self.mode = Venus.idle
		
		# check if self is destroyed
		if MapManager().is_on_map(self.pos.vec2tupint()):
			if not MapManager().game_map.get_at(self.pos.vec2tupint()) == GRD:
				self.remove_from_game()
				
				gs = GunShell(vectorCopy(self.pos))
				gs.angle = self.angle - self.snap
				gs.surf = self.surf
				gs = GunShell(vectorCopy(self.pos))
				gs.angle = self.angle + self.snap
				gs.surf = self.surf
				return
		else:
			self.remove_from_game()
			return
		if self.pos.y >= MapManager().game_map.get_height() - GameVariables().water_level:
			self.remove_from_game()
			return
	
	def rotate(self, angle: float):
		self.direction.rotate(angle)

	def mutate(self):
		if self.mutant:
			return
		self.mutant = True
		self.surf.fill((0, 125, 255, 100), special_flags=pygame.BLEND_MULT)
	
	def remove_from_game(self):
		GameVariables().unregister_non_physical(self)
		GameVariables().get_plants().remove(self)

	def draw(self, win: pygame.Surface):
		if self.scale < 1:
			if self.scale == 0:
				return
			image = pygame.transform.scale(self.surf, (tup2vec(self.surf.get_size()) * self.scale).vec2tupint())
		else: image = self.surf

		rotated_image = pygame.transform.rotate(image, -degrees(self.angle - self.snap))
		rotated_offset = rotateVector(self.offset, self.angle - self.snap)
		rect = rotated_image.get_rect(center=(self.p2 + rotated_offset).vec2tupint())
		win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))
		MapManager().objects_col_map.blit(rotated_image, tup2vec(rect) + self.direction*-25*(1-self.scale))
		
		rotated_image = pygame.transform.rotate(pygame.transform.flip(image, False, True), -degrees(self.angle + self.snap))
		rotated_offset = rotateVector(self.offset, self.angle + self.snap)
		rect = rotated_image.get_rect(center=(self.p1 + rotated_offset).vec2tupint())
		win.blit(rotated_image, point2world(tup2vec(rect) + self.direction*-25*(1-self.scale)))
		MapManager().objects_col_map.blit(rotated_image, tup2vec(rect) + self.direction*-25*(1-self.scale))


class GrowingPlant:
	''' growing plant that sprouts from the ground '''
	def __init__(self, pos, radius = 5, angle = -1, mode: PlantMode=PlantMode.NONE):
		GameVariables().register_non_physical(self)
		self.pos = Vector(pos[0], pos[1])
		if angle == -1:
			self.angle = uniform(0, 2 * pi)
		else:
			self.angle = angle
		self.stable = False
		self.is_boom_affected = False
		self.radius = radius
		self.time_counter = 0
		self.green = 135
		self.mode = mode

	def step(self):
		self.pos += vector_from_angle(self.angle + uniform(-1,1))
		if randint(1,100) <= 2 and not self.mode == PlantMode.VENUS:
			GrowingPlant(self.pos, self.radius, self.angle + choice([pi/3, -pi/3]), self.mode)
		self.time_counter += 1
		if self.time_counter % 10 == 0:
			self.radius -= 1
		self.green += randint(-5,5)
		if self.green > 255:
			self.green = 255
		if self.green < 0:
			self.green = 0
		pygame.draw.circle(MapManager().game_map, GRD, (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		pygame.draw.circle(MapManager().ground_map, (55,self.green,40), (int(self.pos[0]), int(self.pos[1])), int(self.radius))
		if randint(0, 100) <= 10:
			generate_leaf(self.pos, self.angle + 90, (55,self.green,40))
		if self.radius == 0:
			GameVariables().unregister_non_physical(self)
			if self.mode == PlantMode.VENUS:
				pygame.draw.circle(MapManager().game_map, GRD, (int(self.pos[0]), int(self.pos[1])), 3)
				pygame.draw.circle(MapManager().ground_map, (55,self.green,40), (int(self.pos[0]), int(self.pos[1])), 3)
				Venus(self.pos, self.angle)
			if self.mode == PlantMode.MINE:
				Mine(self.pos, GameVariables().fps * 2)

	def draw(self, win: pygame.Surface):
		pass


class MagicBeanGrow:
	def __init__(self, pos: Vector, vel: Vector):
		GameVariables().register_non_physical(self)
		if vel.getMag() < 0.1:
			vel = Vector(0, -1)
		self.vel = vel
		self.pos = pos
		self.p1 = pos
		self.p2 = pos
		self.p3 = pos
		self.timer = 0
		self.green1 = 135
		self.green2 = 135
		self.green3 = 135
		self.face = 0
		GameVariables().player_can_move = False
	
	def regreen(self, value):
		value += randint(-5,5)
		if value > 255:
			value = 255
		if value < 0:
			value = 0
		return value
	
	def step(self):
		self.timer += 1
		GameVariables().game_distable()
		self.pos += 1.5 * self.vel
		if pygame.key.get_pressed()[pygame.K_LEFT]:
			self.vel.rotate(-0.1)
			self.face = RIGHT
		elif pygame.key.get_pressed()[pygame.K_RIGHT]:
			self.vel.rotate(0.1)
			self.face = LEFT

		self.vel.rotate(0.02 * copysign(1,(sin(0.05 * self.timer))))
		
		growRadius = -0.02 * self.timer + 4
		pygame.draw.circle(MapManager().game_map, GRD, self.p1, growRadius)
		pygame.draw.circle(MapManager().game_map, GRD, self.p2, growRadius)
		pygame.draw.circle(MapManager().game_map, GRD, self.p3, growRadius)
		pygame.draw.circle(MapManager().ground_map, (55,self.green1,40), self.p1, growRadius)
		pygame.draw.circle(MapManager().ground_map, (55,self.green2,40), self.p2, growRadius)
		pygame.draw.circle(MapManager().ground_map, (55,self.green3,40), self.p3, growRadius)

		self.green1 = self.regreen(self.green1)
		self.green2 = self.regreen(self.green2)
		self.green3 = self.regreen(self.green3)

		growRadius = -0.055 * self.timer + 9

		if randint(0, 100) < 10:
			generate_leaf(self.p1, self.vel.getNormal().getAngle(), (55, self.green1, 40))

		self.p1 = self.pos + growRadius * sin(self.timer * 0.1) * self.vel.getNormal()
		self.p2 = self.pos + growRadius * sin(self.timer * 0.1 + 2*pi/3) * self.vel.getNormal()
		self.p3 = self.pos + growRadius * sin(self.timer * 0.1 + 4*pi/3) * self.vel.getNormal()

		if self.timer >= 5 * GameVariables().fps:
			GameVariables().unregister_non_physical(self)
			GameVariables().player_can_move = True
	
	def draw(self, win: pygame.Surface):
		pass


class PlantSeed(PhysObj):
	''' a seed that turn into a plant of some kind on impact '''
	def __init__(self, pos, direction, energy, mode: PlantMode=PlantMode.NONE):
		super().__init__(pos)
		self.pos = Vector(pos[0], pos[1])
		self.vel = Vector(direction[0], direction[1]) * energy * 10
		self.radius = 2
		self.color = (204, 204, 0)
		self.damp = 0.5
		self.mode = mode
		self.is_worm_collider = True
		self.surf = pygame.Surface((16, 16), pygame.SRCALPHA)
		blit_weapon_sprite(self.surf, (0,0), "venus fly trap")
		self.angle = 0
	
	def step(self):
		super().step()
		self.angle -= self.vel.x * 4
	
	def on_collision(self, ppos):
		response = MapManager().get_normal(ppos, self.vel, self.radius, False, True)
		self.remove_from_game()
		
		if self.mode == PlantMode.NONE:
			for _ in range(randint(4,5)):
				GrowingPlant(ppos)
		elif self.mode == PlantMode.VENUS:
			GrowingPlant(ppos, 5, response.getAngle(), PlantMode.VENUS)
		elif self.mode == PlantMode.BEAN:
			w = MagicBeanGrow(ppos, normalize(response))
			GameVariables().cam_track = w
		elif self.mode == PlantMode.MINE:
			for _ in range(randint(2,3)):
				GrowingPlant(ppos, 5, -1, PlantMode.MINE)
		
	def draw(self, win: pygame.Surface):
		angle = 45 * round(self.angle / 45)
		surf = pygame.transform.rotate(self.surf, angle)
		win.blit(surf , point2world(self.pos - tup2vec(surf.get_size())/2))


class RazorLeaf(PhysObj):
	def __init__(self, pos, direction):
		super().__init__(pos)
		self.radius = 2
		self.color = (55, randint(100, 200), 40)
		self.pos = pos
		self.direction = direction
		self.vel += vectorUnitRandom() * 1
		self.timer = 0
		
		points = []
		width = max(0.3, uniform(0,1))
		length = 1 + uniform(0,1)
		for i in range(10):
			x = (i / 10) * length
			y = 0.5 * width * sin(2 * (1 / length) * pi * x)
			points.append(Vector(x, y))
		for i in range(10):
			x = (1 - (i / 10)) * length
			y = - width * sqrt(1 - ((2 / length) * (x - length / 2)) ** 2)
			points.append(Vector(x, y))
		if randint(0,1) == 0:
			points = [Vector(-i.x, i.y) for i in points]
		size = uniform(4, 7)
		angle = uniform(0, 2 * pi)
		self.points = [i.rotate(angle) * size for i in points]
	
	def limit_vel(self):
		self.vel.limit(15)
	
	def step(self):
		super().step()
		self.timer += 1
		if self.timer >= GameVariables().fps * 6:
			self.remove_from_game()
	
	def apply_force(self):
		self.acc = vectorCopy(self.direction) * 0.8
	
	def on_collision(self, ppos):
		boom(ppos, 7)
		self.remove_from_game()
	
	def draw(self, win: pygame.Surface):
		pygame.draw.polygon(win, self.color, [point2world(self.pos + i) for i in self.points])