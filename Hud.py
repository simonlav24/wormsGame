
import pygame

import globals
from Constants import *


class HealthBar:
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
		if globals.game_manager.diggingMatch:
			HealthBar.drawBar = False
	def calculateInit(self):
		self.maxHealth = globals.team_manager.nWormsPerTeam * globals.game_manager.initialHealth
		if globals.game_manager.gameMode == DAVID_AND_GOLIATH:
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
			pygame.draw.rect(globals.game_manager.win, (220,220,220), (int(globals.winWidth - (HealthBar.width + 10)), 10 + i * 3, HealthBar.width, 2))
			
			# health:
			value = min(self.teamHealthMod[i] / self.maxHealth, 1) * HealthBar.width
			if value < 1 and value > 0:
				value = 1
			if not value <= 0:
				pygame.draw.rect(globals.game_manager.win, globals.team_manager.teams[i].color, (int(globals.winWidth - (HealthBar.width + 10)), 10 + i * 3, int(value), 2))
			
			# points:
			if not HealthBar.drawPoints:
				continue
			if maxPoints == 0:
				continue
			value = (globals.team_manager.teams[i].points / maxPoints) * HealthBar.width
			if value < 1 and value > 0:
				value = 1
			if not value == 0:
				pygame.draw.rect(globals.game_manager.win, (220,220,220), (int(globals.winWidth - (HealthBar.width + 10)) - 1 - int(value), int(10+i*3), int(value), 2))
			if globals.game_manager.gameMode == CAPTURE_THE_FLAG:
				if globals.team_manager.teams[i].flagHolder:
					pygame.draw.circle(globals.game_manager.win, (220,0,0), (int(globals.winWidth - (HealthBar.width + 10)) - 1 - int(value) - 4, int(10+i*3) + 1) , 2)