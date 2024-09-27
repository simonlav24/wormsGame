from math import exp
import pygame, os, datetime, ast
from random import randint, choice, uniform
import tkinter
from tkinter.filedialog import askopenfile
import xml.etree.ElementTree as ET

import globals

from common import GameConfig, GameVariables, fonts, feels
from common.constants import *
from common.game_config import RandomMode, GameMode, SuddenDeathMode
from common.vector import *

from perlinNoise import generateNoise
from gui._menu_gui import *
from game.map_manager import grab_maps
from game.background import BackGround

trueFalse = ["-f", "-dig", "-dark", "-used", "-closed", "-warped", "-rg", "-place", "-art"]
feelIndex = randint(0, len(feels) - 1)
debug = False

def initGui():
	Gui(fonts.pixel5, GameVariables().scale_factor, GameVariables().fps)

def spriteIndex2rect(index):
	return (index % 8) * 16, (index // 8) * 16, 16, 16

class MainMenu:
	_mm = None
	_picture = None
	_maps = None
	def __init__(self):
		self.gameParameters = None
		self.run = True
		MainMenu._mm = self

	def initializeEndGameMenu(self, parameters):
		endMenu = Menu(name="endMenu", pos=[GameVariables().win_width // 2  - GameVariables().win_width//4, (GameVariables().win_height - 160)//2], size=[GameVariables().win_width // 2, 160], register=True)
		endMenu.insert(MENU_TEXT, text="Game Over", customSize=15)
		if "winner" in parameters.keys():
			endMenu.insert(MENU_TEXT, text="team " + parameters["winner"] + " won the game!")
		else:
			endMenu.insert(MENU_TEXT, text="its a tie!")
		if "mostDamage" in parameters.keys():
			endMenu.insert(MENU_TEXT, text="most damage dealt: " + str(parameters["mostDamage"]) + " by " + parameters["damager"], customSize=15)

		maxpoints = max([parameters["teams"][i][1] for i in parameters["teams"]])
		for team in parameters["teams"].keys():
			teamScore = Menu(orientation=HORIZONTAL, customSize=15)
			teamScore.insert(MENU_TEXT, text=team, customSize=50)
			bar = teamScore.insert(MENU_LOADBAR, value = 0, color=parameters["teams"][team][0], maxValue=maxpoints)
			endMenu.addElement(teamScore)
			ElementAnimator(bar, 0, parameters["teams"][team][1], duration = GameVariables().fps, timeOffset=2 * GameVariables().fps)

		endMenu.insert(MENU_BUTTON, key="continue", text="continue")
	
	def initializeWeaponMenu(self, zero=False):
		wepMenu = Menu(orientation=VERTICAL, name="weapons", pos=[40, (GameVariables().win_height - 180)//2], size=[GameVariables().win_width - 80, 180], register=True)
		
		weapons = ET.parse('weapons.xml').getroot()[0]
		weaponCount = len(weapons)
		weaponSprites = pygame.image.load("./assets/sprites.png")
		weaponIndex = 0
		indexOffset = 72

		items = ["-1"] + [str(i) for i in range(11)]
		mapping = {"-1":"inf"}

		while weaponIndex < weaponCount:
			sub = Menu(orientation=HORIZONTAL, customSize=16)
			for j in range(6):
				pic = MenuElementImage()
				pic.customSize = 16
				bgColor = (255, 255, 255)
				pic.setImage(weaponSprites, spriteIndex2rect(weaponIndex + indexOffset), background=bgColor)
				pic.tooltip = weapons[weaponIndex].attrib["name"]

				sub.addElement(pic)
				amount = weapons[weaponIndex].attrib["amount"]
				if zero:
					amount = "0"
				sub.insert(MENU_COMBOS, key=weapons[weaponIndex].attrib["name"], items=items, text=amount, comboMap=mapping)
				weaponIndex += 1
				if weaponIndex >= weaponCount:
					break

			wepMenu.addElement(sub)

		sub = Menu(orientation=HORIZONTAL)
		sub.insert(MENU_TEXT, text="weapon set name:")
		sub.insert(MENU_INPUT, key="filename", text="enter name")
		sub.insert(MENU_BUTTON, key="saveweapons", text="save")
		wepMenu.addElement(sub)

		sub = Menu(orientation=HORIZONTAL)
		sub.insert(MENU_BUTTON, key="back", text="back")
		sub.insert(MENU_BUTTON, key="defaultweapons", text="default")
		sub.insert(MENU_BUTTON, key="zeroweapons", text="zero")
		wepMenu.addElement(sub)

	def initializeMenuOptions(self):
		mainMenu = Menu(name="menu", pos=[40, (GameVariables().win_height - 196)//2], size=[GameVariables().win_width - 80, 196], register=True)
		mainMenu.insert(MENU_BUTTON, key="play", text="play", customSize=16)

		optionsAndPictureMenu = Menu(name="options and picture", orientation=HORIZONTAL)

		# options vertical sub menu
		optionsMenu = Menu(name="options")

		subMode = Menu(orientation=HORIZONTAL, customSize=15)
		subMode.insert(MENU_TEXT, text="game mode")
		subMode.insert(MENU_COMBOS, key="game_mode", text=list(GameMode)[0].value, items=[mode.value for mode in GameMode])
		optionsMenu.addElement(subMode)

		# toggles
		toggles = [
			('cool down', 'option_cool_down', False),
			('artifacts', 'option_artifacts', False),
			('closed map', 'option_closed_map', False),
			('forts', 'option_forts', False),
			('digging', 'option_digging', False),
			('darkness', 'option_darkness', False)
		]
		
		for i in range(0, len(toggles) - 1, 2):
			first = toggles[i]
			second = toggles[i + 1]
			subOpt = Menu(orientation = HORIZONTAL, customSize = 15)
			subOpt.insert(MENU_TOGGLE, key=first[1], text=first[0], value=first[2])
			subOpt.insert(MENU_TOGGLE, key=second[1], text=second[0], value=second[2])
			optionsMenu.addElement(subOpt)

		# counters
		counters = [
			('worms per team', 'worms_per_team', 8, 1, 8, 1),
			('worm health', 'worm_initial_health', 100, 0, 1000, 50),
			('packs', 'deployed_packs', 1, 0, 10, 1)
		]

		for c in counters:
			subOpt = Menu(orientation=HORIZONTAL)
			subOpt.insert(MENU_TEXT, text=c[0])
			subOpt.insert(MENU_UPDOWN, key=c[1], text=c[0], value=c[2], limitMax=True, limitMin=True, limMin=c[3], limMax=c[4], stepSize=c[5])		
			optionsMenu.addElement(subOpt)

		# random turns
		subMode = Menu(orientation=HORIZONTAL)
		subMode.insert(MENU_TEXT, text="random turns")
		subMode.insert(MENU_COMBOS, key="random_mode", items=[mode.value for mode in RandomMode])	
		optionsMenu.addElement(subMode)

		# sudden death
		subMode = Menu(orientation=HORIZONTAL)
		subMode.insert(MENU_TEXT, text="sudden death")
		subMode.insert(MENU_UPDOWN, key="rounds_for_sudden_death", value=16, text="16", limitMin=True, limMin=0, customSize=19)
		subMode.insert(MENU_COMBOS, key="sudden_death_style", items=[style.value for style in SuddenDeathMode])
		optionsMenu.addElement(subMode)

		optionsAndPictureMenu.addElement(optionsMenu)

		# map options vertical sub menu
		mapMenu = Menu(name="map menu", orientation=VERTICAL)
		MainMenu._picture = mapMenu.insert(MENU_DRAGIMAGE, key="map_path", image=choice(MainMenu._maps))

		# map buttons
		subMap = Menu(orientation = HORIZONTAL, customSize=15)
		subMap.insert(MENU_BUTTON, key="random_image", text="random")
		subMap.insert(MENU_BUTTON, key="browse", text="browse")
		subMap.insert(MENU_BUTTON, key="generate", text="generate")

		mapMenu.addElement(subMap)

		# recolor & ratio
		subMap = Menu(orientation = HORIZONTAL, customSize = 15)
		subMap.insert(MENU_TOGGLE, key="is_recolor", text="recolor")
		subMap.insert(MENU_TEXT, text="ratio")
		subMap.insert(MENU_INPUT, key="map_ratio", text="enter ratio", evaluatedType='int')

		mapMenu.addElement(subMap)
		optionsAndPictureMenu.addElement(mapMenu)
		mainMenu.addElement(optionsAndPictureMenu)

		# weapons setup
		subweapons = Menu(orientation=HORIZONTAL, customSize=14)
		subweapons.insert(MENU_BUTTON, key="weapons setup", text="weapons setup")
		weaponsSets = ['default']

		if os.path.exists("./assets/weaponsSets"):
			for file in os.listdir("./assets/weaponsSets"):
				weaponsSets.append(file.split(".")[0])

		subweapons.insert(MENU_TEXT, text="weapons set:")
		subweapons.insert(MENU_COMBOS, name="weapon_combo", key="weapon_set", items=weaponsSets)
		mainMenu.addElement(subweapons)

		subMore = Menu(orientation=HORIZONTAL, customSize=14)
		subMore.insert(MENU_BUTTON, key="scoreboard", text="score board")
		mainMenu.addElement(subMore)
		
		subMore = Menu(orientation=HORIZONTAL, customSize=14)
		subMore.insert(MENU_BUTTON, key="exit", text="exit")
		mainMenu.addElement(subMore)

		# background feel menu
		bgMenu = Menu(pos=[GameVariables().win_width - 20, GameVariables().win_height - 20], size=[20, 20], register=True)
		bgMenu.insert(MENU_UPDOWN, text="bg", key="feel_index", value=feelIndex, values=[i for i in range(len(feels))], showValue=False)

	def initializeRecordMenu(self):
		# clear graphs

		recordMenu = Menu(name="record menu", pos=[GameVariables().win_width//2  - GameVariables().win_width//4, (GameVariables().win_height - 180)//2], size=[GameVariables().win_width // 2, 180], register=True)
		recordMenu.insert(MENU_TEXT, text="worms game records", customSize=15)
		b = recordMenu.insert(MENU_SURF)
		recordMenu.insert(MENU_BUTTON, key="back", text="back", customSize=15)
	
		readRecord = countWin()
		if readRecord is None:
			self.graphteams = None
			return
		
		self.graphteams, self.graphcount = readRecord[0], readRecord[1]
		self.graphtime = [i for i in range(self.graphcount)]
			
		y_average = 0
		for key in self.graphteams.keys():
			y_average += self.graphteams[key][1][-1]
		y_average /= len(self.graphteams)

		x = self.graphtime[-1]

		pos = (x,y_average)
	
	def handleMainMenu(self, event):
		''' handle main menu events '''
		key = event.key
		# print(event.key, event.value)
		if key == "random_image":
			path = choice(MainMenu._maps)
			MainMenu._picture.setImage(path)
		if key == "-feel":
			BackGround._bg.feelIndex = event.value
			BackGround._bg.recreate()
		if key == "browse":
			filepath = browseFile()
			if filepath:
				MainMenu._picture.setImage(filepath)
		if key == "generate":
			width, height = 800, 300
			noise = generateNoise(width, height)
			x = datetime.datetime.now()
			if not os.path.exists("wormsMaps/PerlinMaps"):
				os.mkdir("wormsMaps/PerlinMaps")
			imageString = "wormsMaps/PerlinMaps/perlin" + str(x.day) + str(x.month) + str(x.year % 100) + str(x.hour) + str(x.minute) + ".png"
			pygame.image.save(noise, imageString)
			MainMenu._picture.setImage(imageString)
		if key == "play":
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, Menu._reg[0].pos + Vector(0, -GameVariables().win_height), trigger=playOnPress)
		if key == "continue":
			self.initializeMenuOptions()
			MenuAnimator(Menu._reg[1], Menu._reg[1].pos + Vector(0, -GameVariables().win_height), Menu._reg[1].pos)
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, Menu._reg[0].pos + Vector(0, GameVariables().win_height), trigger=continueOnPress)
			# remove the end menu
			# Menu._reg.pop(0)
		if key == "scoreboard":
			# create the scoreboard menu
			self.initializeRecordMenu()
			# animate record menu in
			MenuAnimator(Menu._reg[-1], Menu._reg[-1].pos + Vector(0, GameVariables().win_height), Menu._reg[-1].pos)
			# animate main menu out
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, Menu._reg[0].pos + Vector(0, -GameVariables().win_height))
		if key == "back":
			# animate record menu out
			MenuAnimator(Menu._reg[-1], Menu._reg[-1].pos, Menu._reg[-1].pos + Vector(0, GameVariables().win_height))
			# animate main menu in
			endPos = Menu._reg[0].pos + Vector(0, GameVariables().win_height)
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, endPos, trigger=menuPop)
			self.updateWeaponSets()
		if key == "exit":
			exit(0)

class PauseMenu:
	_pm = None
	def __init__(self):
		self.run = True
		PauseMenu._pm = self
	def initializePauseMenu(self, args):
		pauseMenu = Menu(name="endMenu", pos=[GameVariables().win_width//2  - GameVariables().win_width//4, 40], size=[GameVariables().win_width // 2, 160], register=True)
		pauseMenu.insert(MENU_TEXT, text="Game paused")

		if "showPoints" in args.keys() and args["showPoints"]:
			maxPoints = max([team.points for team in args["teams"]])
			if maxPoints == 0:
				maxPoints = 1
			for team in args["teams"]:
				teamScore = Menu(orientation=HORIZONTAL, customSize=15)
				teamScore.insert(MENU_TEXT, text=team.name, customSize=50)
				teamScore.insert(MENU_LOADBAR, value = team.points, color=team.color, maxValue=maxPoints)
				pauseMenu.addElement(teamScore)

		if "missions" in args.keys():
			pauseMenu.insert(MENU_TEXT, text="- missions -")
			for mission in args["missions"]:
				pauseMenu.insert(MENU_TEXT, text=mission)

		pauseMenu.insert(MENU_BUTTON, key="resume", text="resume")
		pauseMenu.insert(MENU_BUTTON, key="toMainMenu", text="back to main menu")
		pauseMenu.pos = Vector(GameVariables().win_width//2 - pauseMenu.size[0]//2, GameVariables().win_height//2 - pauseMenu.size[1]//2)

	def handlePauseMenu(self, event):
		key = event.key
		if key == "resume":
			self.run = False
		if key == "toMainMenu":
			self.run = False
			self.result[0] = 1

def saveWeaponsXml(values, filename):
	weaponsStrings = {}
	weapons = ET.parse('weapons.xml').getroot()[0]
	for w in weapons:
		weaponsStrings[w.attrib["name"]] = w.attrib["amount"]

	filename = filename.replace(" ", "_")
	if not os.path.exists("./assets/weaponsSets"):
		os.makedirs("./assets/weaponsSets")
	file = open("./assets/weaponsSets/" + filename + ".xml", "w")
	file.write("<weapons>\n")
	for key in values:
		if key not in weaponsStrings.keys():
			continue
		if values[key] == 0:
			continue
		file.write("\t<weapon name=\"" + key + "\" amount=\"" + str(values[key]) + "\" />\n")
	file.write("</weapons>\n")
	file.close()

def browseFile():
	root = tkinter.Tk()
	root.withdraw()
	file = askopenfile(mode ='r', filetypes =[('Image Files', '*.png')])
	if file is not None: 
		return file.name
	
def evaluateMenuForm():
	outdict = {}
	for menu in Menu._reg:
		menu.evaluate(outdict)
	return outdict

def menuPop():
	Menu._reg.pop()

def playOnPress():
	values = evaluateMenuForm()

	# create default config
	game_config = GameConfig()
	game_config = GameConfig.model_validate(values)

	MainMenu._mm.gameParameters = game_config
	MainMenu._mm.run = False

def countWin():
	if not os.path.exists("wormsRecord.xml"):
		return None
	teams = {}
	
	# find teams:
	for teamsData in ET.parse('wormsTeams.xml').getroot():
		teams[teamsData.attrib["name"]] = [teamsData.attrib["color"], [0]]
	
	count = 1
	for game in ET.parse('wormsRecord.xml').getroot():
		for key in teams.keys():
			if key == game.attrib["winner"]:
				teams[key][1].append(teams[key][1][-1] + 1)
			else:
				teams[key][1].append(teams[key][1][-1])
		count += 1
	return (teams, count)

def continueOnPress():
	Menu._reg.pop(0)

def mainMenu(fromGameParameters=None, toGameParameters=None):

	# clear menus
	Menu._reg.clear()

	background = BackGround(feels[0])
	MainMenu()
	MainMenu._maps = grab_maps(['assets/worms_maps', 'assets/more_maps'])
	
	if fromGameParameters is None:
		MainMenu._mm.initializeMenuOptions()
		endPos = Menu._reg[0].pos
		MenuAnimator(Menu._reg[0], endPos + Vector(0, GameVariables().win_height), endPos)
	else:
		MainMenu._mm.initializeEndGameMenu(fromGameParameters)
		endPos = Menu._reg[0].pos
		MenuAnimator(Menu._reg[0], endPos + Vector(0, GameVariables().win_height), endPos)

	while MainMenu._mm.run:
		for event in pygame.event.get():
			mousePos = pygame.mouse.get_pos()
			handle_pygame_events(event, MainMenu._mm.handleMainMenu)
			if event.type == pygame.QUIT:
				globals.exitGame()

		# step
		background.step()
		
		Gui._instance.step()
		
		# draw
		background.draw(globals.win)

		Gui._instance.draw(globals.win)

		globals.screen.blit(pygame.transform.scale(globals.win, globals.screen.get_rect().size), (0,0))
		globals.fpsClock.tick(GameVariables().fps)
		pygame.display.update()
	
	clearMenu()
	toGameParameters[0] = MainMenu._mm.gameParameters
	return

def pauseMenu(args, result=None):
	PauseMenu()
	PauseMenu._pm.initializePauseMenu(args)
	PauseMenu._pm.result = result
	while PauseMenu._pm.run:
		for event in pygame.event.get():
			handle_pygame_events(event, PauseMenu._pm.handlePauseMenu)
			if event.type == pygame.QUIT:
				globals.exitGame()
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				PauseMenu._pm.run = False

		for menu in Menu._reg:
			menu.step()

		for menu in Menu._reg:
			menu.draw()

		globals.screen.blit(pygame.transform.scale(globals.win, globals.screen.get_rect().size), (0,0))
		pygame.display.update()
		globals.fpsClock.tick(GameVariables().fps)
	pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
	clearMenu()
	return