
import pygame
from math import cos, pi, sin, radians, degrees
from random import uniform, randint, choice

from common.vector import *
from common import GameVariables, Entity, sprites, SHOCK_RADIUS, point2world

from game.map_manager import MapManager, SKY
from game.visual_effects import Blast, Explossion
from entities import PhysObj
from entities import Debrie

def boom(pos, radius, debries = True, gravity = False, fire = False):
	if not fire: radius *= GameVariables().boom_radius_mult
	boomPos = Vector(pos[0], pos[1])
	# sample Game._game.map_manager.ground_map colors:
	if debries:
		colors = []
		for _ in range(10):
			sample = (pos + vectorUnitRandom() * uniform(0,radius)).vec2tupint()
			if MapManager().is_on_map(sample):
				color = MapManager().ground_map.get_at(sample)
				if not color == SKY:
					colors.append(color)
		if len(colors) == 0:
			colors = Blast._color

	# Game._game.map_manager.ground_map delete
	if not fire:
		Explossion(pos, radius * 1.2)
		if radius > 25:
			Earthquake(int(0.3 * GameVariables().fps), True, min(0.5, 0.02 * radius - 0.3))
		
	# draw burn:
	MapManager().stain(pos, sprites.hole, (int(radius*4),int(radius*4)), True)
	
	pygame.draw.circle(MapManager().game_map, SKY, pos.vec2tupint(), int(radius))
	pygame.draw.circle(MapManager().ground_map, SKY, pos.vec2tupint(), int(radius))
	if not fire:
		pygame.draw.circle(MapManager().ground_secondary, SKY, pos.vec2tupint(), int(radius * 0.7))
	
	listToCheck = GameVariables().get_physicals() if not fire else GameVariables().get_worms()
	
	for p in listToCheck:
		if not p.is_boom_affected:
			continue
		
		totalRadius = radius * SHOCK_RADIUS
		if distus(p.pos, boomPos) < totalRadius * totalRadius:
			distance = dist(p.pos, boomPos)
			# shockwave
			direction = (p.pos - boomPos).normalize()
			p.vel += direction * - 0.5 * (1 / SHOCK_RADIUS) * (distance - radius * SHOCK_RADIUS) * 1.3
			p.stable = False
			# damage
			if p.health:
				if p.health > 0:
					dmg = - (1 / SHOCK_RADIUS)*(distance - radius * SHOCK_RADIUS) * 1.2
					p.damage(dmg)
			if p in GameVariables().get_worms():
				if gravity:
					p.gravity = p.gravity * -1
				if not fire:
					GameVariables().cam_track = p
	if debries:
		for _ in range(int(radius)):
			d = Debrie(pos, radius / 5, colors, 2, radius > 25)
			d.radius = choice([2, 1])



class Earthquake(Entity):
	earthquake = 0
	def __init__(self, timer = 7 * GameVariables().fps, decorative = False, strength = 1):
		GameVariables().register_non_physical(self)
		self.timer = timer
		self.stable = False
		self.is_boom_affected = False
		Earthquake.earthquake = strength
		self.decorative = decorative

	def step(self):
		if not self.decorative:
			# shake objects
			for obj in GameVariables().get_physicals():
				if obj == self:
					continue
				if randint(0,5) == 1:
					obj.vel += Vector(randint(-1,1), -uniform(0,1))
			
		self.timer -= 1 * GameVariables().dt
		if self.timer <= 0:
			GameVariables().unregister_non_physical(self)
			Earthquake.earthquake = 0


class Tornado:
	def __init__(self, pos: Vector, facing: int):
		GameVariables().register_non_physical(self)
		self.width = 30
		self.facing = facing
		self.pos = pos + Vector(4 + self.width / 2, 0) * facing
		amount = MapManager().game_map.get_height() // 10
		self.points = [Vector(0, 10 * i) for i in range(amount)]
		self.swirles = []
		self.sizes = [self.width + randint(0,20) for i in self.points]
		for _ in self.points:
			xRadius = 0
			yRadius = 0
			theta = uniform(0, 2 * pi)
			self.swirles.append([xRadius, yRadius, theta])
		self.timer = 0
		self.speed = 2
		self.radius = 0
	
	def step(self):
		GameVariables().game_distable()
		if self.timer < 2 * GameVariables().fps:
			for i, swirl in enumerate(self.swirles):
				swirl[0] = min(self.timer, self.sizes[i])
				swirl[1] = min(self.timer / 3, 10)
		self.pos.x += self.speed * self.facing
		for swirl in self.swirles:
			swirl[2] += 0.1 * uniform(0.8, 1.2)
		rect = (Vector(self.pos.x - self.width / 2, 0), Vector(self.width, MapManager().game_map.get_height()))
		for obj in GameVariables().get_physicals():
			if obj.pos.x > rect[0][0] and obj.pos.x <= rect[0][0] + rect[1][0]:
				if obj.vel.y > -2:
					obj.acc.y += -0.5
				obj.acc.x += 0.5 * sin(self.timer/6)
		if self.timer >= GameVariables().fps * 10 and len(self.swirles) > 0:
			self.swirles.pop(-1)
			if len(self.swirles) == 0:
				GameVariables().unregister_non_physical(self)
		self.timer += 1
	
	def draw(self, win: pygame.Surface):
		for i, swirl in enumerate(self.swirles):
			five = [point2world(Vector(swirl[0] * cos(swirl[2] + t/5) + self.pos.x, 10 * i + swirl[1] * sin(swirl[2] + t/5))) for t in range(5)]
			pygame.draw.lines(win, (255,255,255), False, five)