
import pygame
from math import cos, pi, sin, radians, degrees
from random import uniform, randint, choice

import globals

from common.vector import *
from common import GameVariables, Entity, sprites, SHOCK_RADIUS

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
	
	listToCheck = PhysObj._reg if not fire else PhysObj._worms
	
	for p in listToCheck:
		if not p.boomAffected:
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
			if p in PhysObj._worms:
				if gravity:
					p.gravity = p.gravity * -1
				if not fire:
					GameVariables().cam_track = p
	if debries:
		for _ in range(int(radius)):
			d = Debrie(pos, radius/5, colors, 2, radius > 25)
			d.radius = choice([2,1])


class Earthquake(Entity):
	earthquake = 0
	def __init__(self, timer = 7 * GameVariables().fps, decorative = False, strength = 1):
		self.timer = timer
		GameVariables().register_non_physical(self)
		self.stable = False
		self.boomAffected = False
		Earthquake.earthquake = strength
		self.decorative = decorative

	def step(self):
		if not self.decorative:
			# shake objects
			for obj in PhysObj._reg:
				if obj == self:
					continue
				if randint(0,5) == 1:
					obj.vel += Vector(randint(-1,1), -uniform(0,1))
			
		self.timer -= 1 * GameVariables().dt
		if self.timer <= 0:
			GameVariables().unregister_non_physical(self)
			Earthquake.earthquake = 0