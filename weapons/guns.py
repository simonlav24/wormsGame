
from random import uniform, randint
from math import cos, sin, atan2

import pygame

from common.vector import Vector, distus, vectorUnitRandom
from common import sprites, GameVariables

from game.map_manager import MapManager, GRD, SKY
from game.visual_effects import splash, Blast
from game.world_effects import boom
from entities import Fire, Worm
from entities.gun_shell import GunShell
from weapons.bubble import Bubble
from weapons.long_bow import LongBow, Icicle, FireBall
from weapons.plants import RazorLeaf
from weapons.spear import Spear
from weapons.earth_spike import EarthSpike, calc_earth_spike_pos

from entities.shooting_target import ShootingTarget
from entities.props import PetrolCan
from weapons.plants import Venus


def fireLongBow(pos: Vector, direction: Vector, power: int=15):
	w = LongBow(pos + direction * 5, direction, LongBow._sleep)
	w.ignore = Worm.player
	return w

def fireFlameThrower(pos: Vector, direction: Vector, power: int=0):
	offset = uniform(1, 2)
	f = Fire(pos + direction * 5)
	f.vel = direction * offset * 2.4

def fireBubbleGun(pos: Vector, direction: Vector, power: int=15):
	w = Bubble(MapManager().get_closest_pos_available(pos, 3.5), direction, uniform(0.5, 0.9))
	w.ignore = Worm.player

def fireIcicle(pos: Vector, direction: Vector, power: int=15):
	w = Icicle(pos + direction * 5, direction)
	w.ignore = Worm.player
	return w

def fireFireBall(pos: Vector, direction: Vector, power: int=15):
	w = FireBall(pos + direction * 5, direction)
	w.ignore = Worm.player
	return w

def fireRazorLeaf(pos: Vector, direction: Vector, power: int=15):
	RazorLeaf(pos + direction * 10, direction)

def fireSpear(pos: Vector, direction: Vector, power: int=15):
	w = Spear(pos, direction, power * 0.95)
	return w

def fireEarthSpike(pos: Vector, direction: Vector, power: int=15):
	pos = calc_earth_spike_pos()
	if pos is not None:
		EarthSpike(pos)

def fireShotgun(pos: Vector, direction: Vector, power: int=15):
	GunShell(pos + Vector(0, -4), direction=direction)
	for t in range(5,500):
		testPos = pos + direction * t
		GameVariables().add_extra(testPos, (255, 204, 102), 3)
		
		if testPos.y >= MapManager().game_map.get_height() - GameVariables().water_level:
			splash(testPos, Vector(10,0))
			break
		if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue

		at = (int(testPos.x), int(testPos.y))
		if MapManager().game_map.get_at(at) == GRD or MapManager().worm_col_map.get_at(at) != (0,0,0) or MapManager().objects_col_map.get_at(at) != (0,0,0):
			if MapManager().worm_col_map.get_at(at) != (0,0,0):
				MapManager().stain(testPos, sprites.blood, sprites.blood.get_size(), False)
			boom(testPos, power)
			break

def fireMiniGun(pos: Vector, direction: Vector, power: int=0):#0
	angle = atan2(direction[1], direction[0])
	angle += uniform(-0.2, 0.2)
	direction[0], direction[1] = cos(angle), sin(angle)
	fireShotgun(pos, direction, randint(7,9))


def fireGammaGun(pos: Vector, direction: Vector, power: int=15):
	hitted = []
	normal = Vector(-direction.y, direction.x).normalize()
	for t in range(5,500):
		testPos = pos + direction * t + normal * 1.5 * sin(t * 0.6) * (t + 1)/70
		GameVariables().add_extra(testPos, (0,255,255), 10)
		
		if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			continue
		# if hits worm:
		for worm in GameVariables().get_worms():
			if distus(testPos, worm.pos) < worm.radius * worm.radius and not worm in hitted:
				worm.damage(int(10 / GameVariables().damage_mult) + 1)
				if randint(0,20) == 1:
					worm.sicken(2)
				else:
					worm.sicken()
				hitted.append(worm)
		# if hits plant:
		for plant in Venus._reg:
			if distus(testPos, plant.pos + plant.direction * 25) <= 625:
				plant.mutate()
		for target in ShootingTarget._reg:
			if distus(testPos, target.pos) < target.radius * target.radius:
				target.explode()


def fireLaser(pos: Vector, direction: Vector, power: int=15):
	hit = False
	color = (254, 153, 35)
	square = [Vector(1,5), Vector(1,-5), Vector(-10,-5), Vector(-10,5)]
	for i in square:
		i.rotate(direction.getAngle())
	
	for t in range(5,500):
		testPos = pos + direction * t
		# extra.append((testPos.x, testPos.y, (255,0,0), 3))
		
		if testPos.x >= MapManager().game_map.get_width() or testPos.y >= MapManager().game_map.get_height() or testPos.x < 0 or testPos.y < 0:
			GameVariables().layers_circles[0].append((color, pos, 5))
			GameVariables().layers_circles[0].append((color, testPos, 5))
			GameVariables().layers_lines.append((color, pos, testPos, 10, 1))
			continue
			
		# if hits worm:
		for worm in GameVariables().get_worms():
			if worm == Worm.player:
				continue
			if distus(testPos, worm.pos) < (worm.radius + 2) * (worm.radius + 2):
				if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
				GameVariables().layers_circles[0].append((color, pos + direction * 5, 5))
				GameVariables().layers_circles[0].append((color, testPos, 5))
				GameVariables().layers_lines.append((color, pos + direction * 5, testPos, 10, 1))
				
				boom(worm.pos + Vector(randint(-1,1),randint(-1,1)), 2, False, False, True)
				# worm.damage(randint(1,5))
				# worm.vel += direction*2 + vectorUnitRandom()
				hit = True
				break
		# if hits can:
		for can in PetrolCan._cans:
			if distus(testPos, can.pos) < (can.radius + 1) * (can.radius + 1):
				can.damage(10)
				# hit = True
				break
		if hit:
			break
		
		# if hits MapManager().game_map:
		if MapManager().game_map.get_at((int(testPos.x), int(testPos.y))) == GRD:
			if randint(0,1) == 1: Blast(testPos + vectorUnitRandom(), randint(5,9), 20)
			GameVariables().layers_circles[0].append((color, pos + direction * 5, 5))
			GameVariables().layers_circles[0].append((color, testPos, 5))
			GameVariables().layers_lines.append((color, pos + direction * 5, testPos, 10, 1))
			points = []
			for i in square:
				points.append((testPos + i).vec2tupint())
			
			pygame.draw.polygon(MapManager().game_map, SKY, points)
			pygame.draw.polygon(MapManager().ground_map, SKY, points)
			break