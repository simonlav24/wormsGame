
from random import uniform, randint
from math import cos, sin, atan2
from typing import Tuple

import pygame

from common.vector import Vector, distus, vectorUnitRandom
from common import sprites, GameVariables, Sickness

from game.map_manager import MapManager, GRD, SKY, SKY_COL
from game.visual_effects import splash, Blast
from game.world_effects import boom
from entities.fire import Fire
from entities.gun_shell import GunShell
from weapons.bubble import Bubble
from weapons.long_bow import LongBow, Icicle, FireBall
from weapons.plants import RazorLeaf
from weapons.spear import Spear
from weapons.earth_spike import EarthSpike, calc_earth_spike_pos
from game.sfx import Sfx, SfxIndex


def fire_gun_generic(**kwargs) -> Tuple[Vector, Vector, int]:
	''' return pos, direction '''
	return (
		kwargs.get('pos'),
		kwargs.get('direction')
	)


def fire_long_bow(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	w = LongBow(pos + direction * 5, direction, LongBow._sleep)
	w.ignore = kwargs.get('shooter')
	return w

def fire_flame_thrower(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	offset = uniform(1, 2)
	f = Fire(pos + direction * 5)
	f.vel = direction * offset * 2.4

def fire_bubble_gun(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	w = Bubble(MapManager().get_closest_pos_available(pos, 3.5), direction, uniform(0.5, 0.9))
	w.ignore = kwargs.get('shooter')

def fire_icicle(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	w = Icicle(pos + direction * 5, direction)
	w.ignore = kwargs.get('shooter')
	return w

def fire_fire_ball(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	w = FireBall(pos + direction * 5, direction)
	w.ignore = kwargs.get('shooter')
	return w

def fire_razor_leaf(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	RazorLeaf(pos + direction * 10, direction)

def fire_spear(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	w = Spear(pos, direction, kwargs.get('energy') * 0.95, kwargs.get('shooter'))
	return w

def fire_earth_spike(*args, **kwargs):
	pos = calc_earth_spike_pos()
	if pos is not None:
		EarthSpike(pos)

def fire_shotgun(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	GunShell(pos + Vector(0, -4), direction=direction)
	for t in range(5, 500):
		test_pos = pos + direction * t
		GameVariables().add_extra(test_pos, (255, 204, 102), 3)
		
		if test_pos.y >= MapManager().game_map.get_height() - GameVariables().water_level:
			splash(test_pos, Vector(10,0))
			break
		if test_pos.x >= MapManager().game_map.get_width() or test_pos.y >= MapManager().game_map.get_height() or test_pos.x < 0 or test_pos.y < 0:
			continue

		at = (int(test_pos.x), int(test_pos.y))
		if MapManager().game_map.get_at(at) == GRD or MapManager().worm_col_map.get_at(at) != SKY_COL or MapManager().objects_col_map.get_at(at) != SKY_COL:
			if MapManager().worm_col_map.get_at(at) != SKY_COL:
				MapManager().stain(test_pos, sprites.blood, sprites.blood.get_size(), False)
			boom(test_pos, kwargs.get('power', 15))
			break

def fire_minigun(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	angle = atan2(direction[1], direction[0])
	angle += uniform(-0.2, 0.2)
	direction[0], direction[1] = cos(angle), sin(angle)
	fire_shotgun(pos=pos, direction=direction, power=randint(7,9))


def fire_gamma_gun(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	hitted = []
	normal = Vector(-direction.y, direction.x).normalize()
	for t in range(5,500):
		test_pos = pos + direction * t + normal * 1.5 * sin(t * 0.6) * (t + 1)/70
		GameVariables().add_extra(test_pos, (0,255,255), 10)
		
		if test_pos.x >= MapManager().game_map.get_width() or test_pos.y >= MapManager().game_map.get_height() or test_pos.x < 0 or test_pos.y < 0:
			continue
		# if hits worm:
		for worm in GameVariables().get_worms():
			if distus(test_pos, worm.pos) < worm.radius * worm.radius and not worm in hitted:
				worm.damage(int(10 / GameVariables().damage_mult) + 1)
				# might cause virus
				if randint(0,20) == 1:
					worm.sicken(Sickness.VIRUS)
				else:
					worm.sicken()
				hitted.append(worm)
		# if hits plant:
		for plant in GameVariables().get_plants():
			if distus(test_pos, plant.pos + plant.direction * 25) <= 625:
				plant.mutate()
		for target in GameVariables().get_targets():
			if distus(test_pos, target.pos) < target.radius * target.radius:
				target.explode()

# todo: optimize
def fire_laser(*args, **kwargs):
	pos, direction = fire_gun_generic(**kwargs)
	hit = False
	color = (254, 153, 35)
	square = [Vector(1,5), Vector(1,-5), Vector(-10,-5), Vector(-10,5)]
	for i in square:
		i.rotate(direction.getAngle())
	
	for t in range(5,500):
		test_pos = pos + direction * t
		
		if test_pos.x >= MapManager().game_map.get_width() or test_pos.y >= MapManager().game_map.get_height() or test_pos.x < 0 or test_pos.y < 0:
			GameVariables().layers_circles[0].append((color, pos, 5))
			GameVariables().layers_circles[0].append((color, test_pos, 5))
			GameVariables().layers_lines.append((color, pos, test_pos, 10, 1))
			continue
			
		# if hits worm:
		for worm in GameVariables().get_worms():
			if worm == kwargs.get('shooter'):
				continue
			if distus(test_pos, worm.pos) < (worm.radius + 2) * (worm.radius + 2):
				if randint(0, 1) == 1:
					Blast(test_pos + vectorUnitRandom(), randint(5,9), 20)
				GameVariables().layers_circles[0].append((color, pos + direction * 5, 5))
				GameVariables().layers_circles[0].append((color, test_pos, 5))
				GameVariables().layers_lines.append((color, pos + direction * 5, test_pos, 10, 1))
				
				boom(worm.pos + Vector(randint(-1, 1),randint(-1, 1)), 2, False, False, True)

				hit = True
				break
		# if hits can:
		for can in GameVariables().get_exploding_props():
			if distus(test_pos, can.pos) < (can.radius + 1) * (can.radius + 1):
				can.damage(10)
				# hit = True
				break
		if hit:
			break
		
		if MapManager().game_map.get_at((int(test_pos.x), int(test_pos.y))) == GRD:
			if randint(0, 1) == 1:
				Blast(test_pos + vectorUnitRandom(), randint(5, 9), 20)
			GameVariables().layers_circles[0].append((color, pos + direction * 5, 5))
			GameVariables().layers_circles[0].append((color, test_pos, 5))
			GameVariables().layers_lines.append((color, pos + direction * 5, test_pos, 10, 1))
			points = []
			for i in square:
				points.append((test_pos + i).vec2tupint())
			
			pygame.draw.polygon(MapManager().game_map, SKY, points)
			pygame.draw.polygon(MapManager().ground_map, SKY, points)
			break
