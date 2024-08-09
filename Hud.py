
import pygame
from random import choice, uniform

import globals
from Constants import *
from vector import *
from GameConfig import GameMode
from GameVariables import GameVariables

HEALTH_BAR_WIDTH = 40

class HealthBar:
	''' team health bar calculations and drawing '''
	_healthBar = None
	drawBar = True
	drawPoints = True
	width = 40
	def __init__(self):
		HealthBar._healthBar = self
		self.mode = 0
		self.teamHealthMod = [0] * globals.team_manager.totalTeams
		self.teamHealthAct = [0] * globals.team_manager.totalTeams
		self.maxHealth = 0
		HealthBar.drawBar = True
		HealthBar.drawPoints = True
		if globals.game_manager.game_config.option_digging:
			HealthBar.drawBar = False
	def calculateInit(self):
		self.maxHealth = globals.team_manager.nWormsPerTeam * globals.game_manager.game_config.worm_initial_health
		if globals.game_manager.gameMode == GameMode.DAVID_AND_GOLIATH:
			self.maxHealth = int(globals.game_manager.initialHealth/(1+0.5*(globals.team_manager.nWormsPerTeam - 1))) * globals.team_manager.nWormsPerTeam
		for i, team in enumerate(globals.team_manager.teams):
			self.teamHealthMod[i] = sum(worm.health for worm in team.worms)
	def step(self):
		for i, team in enumerate(globals.team_manager.teams):
			# calculate teamhealth
			self.teamHealthAct[i] = sum(worm.health for worm in team.worms)
			
			# animate health bar
			self.teamHealthMod[i] += (self.teamHealthAct[i] - self.teamHealthMod[i]) * 0.1
			if int(self.teamHealthMod[i]) == self.teamHealthAct[i]:
				self.teamHealthMod[i] = self.teamHealthAct[i]
	def draw(self):
		if not HealthBar.drawBar: return
		maxPoints = sum(i.points for i in globals.team_manager.teams)
		
		for i, team in enumerate(globals.team_manager.teams):
			pygame.draw.rect(globals.game_manager.win, (220,220,220), (int(GameVariables().win_width - (HealthBar.width + 10)), 10 + i * 3, HealthBar.width, 2))
			
			# health:
			value = min(self.teamHealthMod[i] / self.maxHealth, 1) * HealthBar.width
			if value < 1 and value > 0:
				value = 1
			if not value <= 0:
				pygame.draw.rect(globals.game_manager.win, globals.team_manager.teams[i].color, (int(GameVariables().win_width - (HealthBar.width + 10)), 10 + i * 3, int(value), 2))
			
			# points:
			if not HealthBar.drawPoints:
				continue
			if maxPoints == 0:
				continue
			value = (globals.team_manager.teams[i].points / maxPoints) * HealthBar.width
			if value < 1 and value > 0:
				value = 1
			if not value == 0:
				pygame.draw.rect(globals.game_manager.win, (220,220,220), (int(GameVariables().win_width - (HealthBar.width + 10)) - 1 - int(value), int(10+i*3), int(value), 2))
			if globals.game_manager.gameMode == GameMode.CAPTURE_THE_FLAG:
				if globals.team_manager.teams[i].flagHolder:
					pygame.draw.circle(globals.game_manager.win, (220,0,0), (int(GameVariables().win_width - (HealthBar.width + 10)) - 1 - int(value) - 4, int(10+i*3) + 1) , 2)

class Commentator:
	''' comment pop ups '''
	_com = None
	surf_que = []
	timer = 0 #0-wait, 1-render, 2-show
	WAIT = 0
	PREPARE = 1
	SHOW = 2
	mode = 0
	textSurf = None
	name = None
	stringsDmg = [("", " is no more"), ("", " is an ex-worm"), ("", " bit the dust"), ("", " has been terminated"), ("poor ", ""), ("so long ", ""), ("", " will see you on the other side"), ("", " diededed"), ("", " smells the flower from bellow")]
	stringsFlw = [(""," is swimming with the fishes"), ("there goes ", " again"), ("its bye bye for ", ""), ("", " has drowed"), ("", " swam like a brick"), ("", " has gone to marry a mermaid"), ("", " has divided by zero")]
	CAUSE_DAMAGE = 0
	CAUSE_FLEW = 1
	def __init__(self):
		Commentator._com = self
    
	def step(self):
		if self.mode == Commentator.WAIT:
			if len(self.surf_que) == 0:
				return
			else:
				self.mode = Commentator.PREPARE
		elif self.mode == Commentator.PREPARE:
			self.textSurf = self.surf_que.pop(0)

			self.mode = Commentator.SHOW
			self.timer = 2 * globals.fps + 1 * globals.fps / 2
		elif self.mode == Commentator.SHOW:
			globals.game_manager.win.blit(self.textSurf, (int(GameVariables().win_width/2 - self.textSurf.get_width()/2), 5))
			
			self.timer -= 1
			if self.timer == 0:
				self.mode = Commentator.WAIT
	
	@staticmethod
	def commentDeath(worm, cause):
		if cause == Commentator.CAUSE_DAMAGE:
			strings = choice(Commentator.stringsDmg)
		elif cause == Commentator.CAUSE_FLEW:
			strings = choice(Commentator.stringsFlw)
		output = [
			{'text': strings[0]},
			{'text': worm.nameStr, 'color': worm.team.color},
			{'text': strings[1]},
		]
		Commentator.comment(output)

	@staticmethod
	def comment(strings):
		surfs = []
		for string in strings:
			text = string.get('text')
			color = string.get('color', GameVariables().initial_variables.hud_color)
			surfs.append(globals.pixelFont5halo.render(text, False, color))
		width = sum([i.get_width() for i in surfs])
		surf = pygame.Surface((width, surfs[0].get_height()), pygame.SRCALPHA)
		x = 0
		for s in surfs:
			surf.blit(s, (x, 0))
			x += s.get_width()
		Commentator.surf_que.append(surf)
		

class Toast:
	_toasts = []
	toastCount = 0
	bottom = 0
	middle = 1
	
	def __init__(self, surf, mode=0):
		Toast._toasts.append(self)
		self.surf = surf
		self.time = 0
		self.mode = mode
		if self.mode == Toast.bottom:
			self.anchor = Vector(GameVariables().win_width / 2, GameVariables().win_height)
		else:
			self.anchor = Vector(GameVariables().win_width // 2, GameVariables().win_height // 2) - tup2vec(self.surf.get_size()) / 2
		self.pos = Vector()
		self.state = 0
		Toast.toastCount += 1
		
	def step(self):
		if self.mode == Toast.bottom:
			if self.state == 0:
				self.pos.y -= 3
				if self.pos.y < -self.surf.get_height():
					self.state = 1
			if self.state == 1:
				self.time += 1
				if self.time == globals.fps * 3:
					self.state = 2
			if self.state == 2:
				self.pos.y += 3
				if self.pos.y > 0:
					Toast._toasts.remove(self)
					Toast.toastCount -= 1
		elif self.mode == Toast.middle:
			self.time += 1
			if self.time == globals.fps * 3:
				Toast._toasts.remove(self)
				Toast.toastCount -= 1
			self.pos = uniform(0,2) * vectorUnitRandom()
			
	def draw(self):
		if self.mode == Toast.bottom:
			pygame.gfxdraw.box(globals.game_manager.win, (self.anchor + self.pos - Vector(1,1), tup2vec(self.surf.get_size()) + Vector(2,2)), (255,255,255,200))
		globals.game_manager.win.blit(self.surf, self.anchor + self.pos)
		
	def updateWinPos(self, pos):
		self.anchor[0] = pos[0]
		self.anchor[1] = pos[1]
		

class WindFlag:
	''' hud widget, represents wind speed and direction '''
	_instance = None
	
	def __init__(self):
		WindFlag._instance = self
		self.vertices = [Vector(i * 10, 0) for i in range(5)]
		self.acc = [Vector() for i in range(len(self.vertices))]
		self.vel = [Vector() for i in range(len(self.vertices))]
	
	def step(self):
		for step in range(3):
			# calculate acc
			for i in range(len(self.vertices)):
				if i == 0:
					continue

				displacement1 = dist(self.vertices[i], self.vertices[i-1]) - 10
				displacement2 = 0
				if i != len(self.vertices) - 1:
					displacement2 = dist(self.vertices[i], self.vertices[i+1]) - 10

				acc1 = 0.05 * displacement1 * (self.vertices[i-1] - self.vertices[i]).normalize()
				acc2 = Vector()
				if i != len(self.vertices) - 1:
					acc2 = 0.05 * displacement2 * (self.vertices[i+1] - self.vertices[i]).normalize()

				self.acc[i] += acc1 + acc2
				# gravity
				self.acc[i] += Vector(0, 0.01)
				# wind
				self.acc[i] += Vector(GameVariables().physics.wind * 0.05, 0)
				# turbulence
				self.acc[i] += vectorUnitRandom() * 0.01

			for i in range(len(self.vertices)):
				# calculate vel
				self.vel[i] += self.acc[i]
				self.vel[i] *= 0.99
				self.acc[i] = Vector()
			
				# calculate pos
				self.vertices[i] += self.vel[i]
				
	def draw(self):
		it = 0
		rad = 6
		pos = Vector(25, 18)
		scale = 0.5
		pygame.draw.line(globals.game_manager.win, (204, 102, 0), pos, pos + Vector(0, 40) * scale, 1)
		for i in range(len(self.vertices) - 1):
			# draw alternating lines red and white
			pygame.draw.line(globals.game_manager.win, (255, 255*it, 255*it), self.vertices[i] * scale + pos, self.vertices[i + 1] * scale + pos, rad)
			it = (it + 1) % 2
			rad -= 1