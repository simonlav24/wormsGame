
from random import uniform

from common.vector import Vector

from entities import Fire






def fireFlameThrower(pos: Vector, direction: Vector, power: int=0):
	offset = uniform(1, 2)
	f = Fire(pos + direction * 5)
	f.vel = direction * offset * 2.4
