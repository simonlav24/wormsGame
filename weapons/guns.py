
from random import uniform

from common.vector import Vector

from game.map_manager import MapManager
from entities import Fire, Worm
from weapons.bubble import Bubble
from weapons.long_bow import LongBow, Icicle, FireBall
from weapons.plants import RazorLeaf
from weapons.spear import Spear
from weapons.earth_spike import EarthSpike, calc_earth_spike_pos


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

