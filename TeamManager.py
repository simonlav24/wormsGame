
import pygame
from typing import List, Any
import xml.etree.ElementTree as ET
from random import choice, shuffle

import globals
from Weapons.WeaponManager import Weapon
from Common import desaturate

class Team:
	def __init__(self, nameList=None, color=(255,0,0), name = ""):
		if nameList:
			self.nameList = nameList
		else:
			self.nameList = []
		self.color = color
		self.weaponCounter = globals.weapon_manager.basic_set.copy()
		self.worms = []
		self.name = name
		self.damage = 0
		self.killCount = 0
		self.points = 0
		self.flagHolder = False
		self.artifacts = []
		self.hatOptions = None
		self.hatSurf = None
	
	def makeHat(self, index):
		self.hatSurf = pygame.Surface((16, 16), pygame.SRCALPHA)
		self.hatSurf.blit(globals.game_manager.sprites, (0,0), (16 * (index % 8),16 * (index // 8),16,16))
		pixels = pygame.PixelArray(self.hatSurf)
		color = desaturate(self.color)
		pixels.replace((101, 101, 101), color)
		pixels.replace((81, 81, 81), tuple(max(i - 30,0) for i in color))
		del pixels
	
	def __len__(self):
		return len(self.worms)

	def get_new_worm_name(self) -> str:
		if len(self.nameList) > 0:
			return self.nameList.pop(0)
	
	def ammo(self, weapon: Weapon, amount: int=None, absolute: bool=False):
		# adding amount of weapon to team
		if amount and not absolute:
			self.weaponCounter[weapon.index] += amount
		elif amount and absolute:
			self.weaponCounter[weapon.index] = amount
		return self.weaponCounter[weapon.index]

class TeamManager:
	def __init__(self):
		globals.team_manager = self

		self.teams: List[Team] = []
		for teamsData in ET.parse('wormsTeams.xml').getroot():
			newTeam = Team()
			newTeam.name = teamsData.attrib["name"]
			newTeam.hatOptions = teamsData.attrib["hat"]
			newTeam.color = tuple([int(i) for i in teamsData.attrib["color"][1:-1].split(",")])
			for team in teamsData:
				if team.tag == "worm":
					newTeam.nameList.append(team.attrib["name"])
			self.teams.append(newTeam)

		# hats
		hatsChosen = []
		for team in self.teams:
			indexChoice = []
			options = team.hatOptions.replace(" ", "").split(",")
			for option in options:
				if "-" in option:
					indexChoice += [i for i in range(int(option.split("-")[0]), int(option.split("-")[1]) + 1)]
				else:
					indexChoice.append(int(option))
			hatChoice = choice([hat for hat in indexChoice if hat not in hatsChosen])
			team.makeHat(hatChoice)
			hatsChosen.append(hatChoice)

		self.totalTeams = len(self.teams)
		self.currentTeam: Team = None
		self.teamChoser = 0
		self.nWormsPerTeam = 0
		shuffle(self.teams)