
import pygame
from typing import List
from math import cos, pi, sin, radians
from random import uniform, randint, choice

from common import GameVariables, point2world, ColorType
from common.vector import *

from entities.physical_entity import PhysObj
from game.visual_effects import Blast

class Debrie (PhysObj):
	''' debrie resulting from explossions '''
	
	def __init__(self, pos: Vector, blast: float, colors: List[ColorType], bounces=2, firey=True):
		super().__init__(pos)
		GameVariables().get_debries().append(self)
		self.vel = Vector(cos(uniform(0,1) * 2 *pi), sin(uniform(0,1) * 2 *pi)) * blast
		self.pos = Vector(pos[0], pos[1])
		
		self.is_boom_affected = False
		self.bounce_before_death = bounces
		self.color = choice(colors)
		self.radius = 1
		self.damp = 0.2
		
		width = randint(1,3)
		height = randint(1,3)
		point = Vector(width/2, height/2)
		
		self.rect = [point, Vector(point.x, -point.y), -point, -Vector(point.x, -point.y)]
		self.angle = 0
		
		self.firey = randint(0, 5) == 0 and firey
		self.sound_collision = False
	
	def apply_force(self):
		factor = 1.5
		self.acc.y += GameVariables().physics.global_gravity * factor
	
	def step(self):
		super().step()
		self.angle -= self.vel.x * 2
		if self.firey:
			Blast(self.pos, randint(3,6), 150)
			# Blast(self.pos + vectorUnitRandom() * randint(0,4) + vector_from_angle(-radians(self.angle)-pi/2) * 8, randint(3,6), 150)
	
	def on_collision(self, ppos):
		super().on_collision(ppos)
		self.firey = False
	
	def draw(self, win: pygame.Surface):
		points = [point2world(self.pos + rotateVector(i, -self.angle)) for i in self.rect]
		pygame.draw.polygon(win, self.color, points)
