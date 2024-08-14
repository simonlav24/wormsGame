
import pygame
from typing import List
from math import cos, pi, sin, radians
from random import uniform, randint, choice

from GameVariables import GameVariables, point2world
from PhysicalEntity import PhysObj
from Constants import ColorType
from vector import *
from Effects import Blast

class Debrie (PhysObj):
	''' debrie resulting from explossions '''
	_debries = []
	
	def __init__(self, pos, blast, colors: List[ColorType], bounces=2, firey=True):
		Debrie._debries.append(self)
		self.initialize()
		self.vel = Vector(cos(uniform(0,1) * 2 *pi), sin(uniform(0,1) * 2 *pi)) * blast
		self.pos = Vector(pos[0], pos[1])
		
		self.boomAffected = False
		self.bounceBeforeDeath = bounces
		self.color = choice(colors)
		self.radius = 1
		self.damp = 0.2
		
		width = randint(1,3)
		height = randint(1,3)
		point = Vector(width/2, height/2)
		
		self.rect = [point, Vector(point.x, -point.y), -point, -Vector(point.x, -point.y)]
		self.angle = 0
		
		self.firey = randint(0, 5) == 0 and firey
	
	def applyForce(self):
		factor = 1
		self.acc.y += GameVariables().physics.global_gravity * factor
	
	def secondaryStep(self):
		self.angle -= self.vel.x * 2
		if self.firey:
			Blast(self.pos + vectorUnitRandom() * randint(0,4) + vectorFromAngle(-radians(self.angle)-pi/2) * 8, randint(3,6), 150)
	
	def collisionRespone(self, ppos):
		self.firey = False
	
	def draw(self, win: pygame.Surface):
		points = [point2world(self.pos + rotateVector(i, -self.angle)) for i in self.rect]
		pygame.draw.polygon(win, self.color, points)