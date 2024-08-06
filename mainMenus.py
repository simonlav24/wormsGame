from math import exp
import pygame, os, datetime, ast
import globals
from random import randint, choice, uniform
from perlinNoise import generateNoise
from vector import *
from menuGui import *
from Constants import *
if not os.path.exists("graphObject.py"):
	print("fetching graphObject")
	import urllib.request
	with urllib.request.urlopen('https://raw.githubusercontent.com/simonlav24/Graph-plotter/master/graphObject.py') as f:
		text = f.read().decode('utf-8')
		with open("graphObject.py", "w+") as graphpy:
			graphpy.write(text)
import graphObject
import tkinter
from tkinter.filedialog import askopenfile
import xml.etree.ElementTree as ET

from GameConfig import *



trueFalse = ["-f", "-dig", "-dark", "-used", "-closed", "-warped", "-rg", "-place", "-art"]
feelIndex = randint(0, len(feels) - 1)
debug = False

def initGui():
	Gui(globals.win, globals.pixelFont5, globals.scalingFactor, globals.fps)

def updateWin(win, scalingFactor):
	Gui._instance.updateWindow(win)
	Gui._instance.scalingFactor = scalingFactor

def perlinNoise1D(count, seed, octaves, bias):
	output = []
	for x in range(count):
		noise = 0.0
		scaleAcc = 0.0
		scale = 1.0
		
		for o in range(octaves):
			pitch = count >> o
			sample1 = (x // pitch) * pitch
			sample2 = (sample1 + pitch) % count
			blend = (x - sample1) / pitch
			sample = (1 - blend) * seed[int(sample1)] + blend * seed[int(sample2)]
			scaleAcc += scale
			noise += sample * scale
			scale = scale / bias
		output.append(noise / scaleAcc)
	return output

def renderMountains(dims, color):
	mount = pygame.Surface(dims, pygame.SRCALPHA)
	mount.fill((0,0,0,0))
	
	noiseSeed = []
	
	for i in range(dims[0]):
		noiseSeed.append(uniform(0,1))
	noiseSeed[0] = 0.5
	surface = perlinNoise1D(dims[0], noiseSeed, 7, 2) # 8 , 2.0
	
	for x in range(0,dims[0]):
		for y in range(0,dims[1]):
			if y >= surface[x] * dims[1]:
				mount.set_at((x,y), color)

	return mount

def renderCloud(colors=[(224, 233, 232), (192, 204, 220)]):
	c1 = colors[0]
	c2 = colors[1]
	surf = pygame.Surface((170, 70), pygame.SRCALPHA)
	circles = []
	leng = randint(15,30)
	space = 5
	gpos = (20, 40) 
	for i in range(leng):
		pos = Vector(gpos[0] + i * space, gpos[1]) + vectorUnitRandom() * uniform(0, 10)
		radius = max(20 * (exp(-(1/(5*leng)) * ((pos[0]-gpos[0])/space -leng/2)**2)), 5) * uniform(0.8,1.2)
		circles.append((pos, radius))
	circles.sort(key=lambda x: x[0][0])
	for c in circles:
		pygame.draw.circle(surf, c2, c[0], c[1])
	for c in circles:
		pygame.draw.circle(surf, c1, c[0] - Vector(1,1) * 0.7 * 0.2 * c[1], c[1] * 0.8)
	for i in range(0,len(circles),int(len(circles)/4)):
		pygame.draw.circle(surf, c2, circles[i][0], circles[i][1])
	for i in range(0,len(circles),int(len(circles)/8)):
		pygame.draw.circle(surf, c1, circles[i][0] - Vector(1,1) * 0.8 * 0.2 * circles[i][1], circles[i][1] * 0.8)
	
	return surf

def spriteIndex2rect(index):
	return (index % 8) * 16, (index // 8) * 16, 16, 16

class BackGround:
	_bg = None
	def __init__(self):
		BackGround._bg = self
		self.feelIndex = feelIndex
		self.recreate()
		self.cloudsPos = [i * (globals.winWidth + 170)/3 for i in range(3)]
		self.animationStep = 0 # in
		self.fireworks = None
	def recreate(self):
		feel = feels[self.feelIndex]
		self.imageMountain = renderMountains((180, 110), feel[3])
		self.imageMountain2 = renderMountains((180, 150), feel[2])
		colorRect = pygame.Surface((2,2))
		pygame.draw.line(colorRect, feel[0], (0,0), (2,0))
		pygame.draw.line(colorRect, feel[1], (0,1), (2,1))
		self.imageSky = pygame.transform.smoothscale(colorRect, (globals.winWidth, globals.winHeight))
		self.clouds = [renderCloud() for i in range(3)]
	def step(self):
		if self.fireworks:
			pass
	def draw(self):
		globals.win.blit(self.imageSky, (0,0))
		x = 0
		while x < globals.winWidth:
			globals.win.blit(self.imageMountain, (x, globals.winWidth - self.imageMountain.get_height()))
			globals.win.blit(self.imageMountain2, (x, globals.winWidth - self.imageMountain.get_height()))
			x += self.imageMountain.get_width()
		for i, c in enumerate(self.clouds):
			self.cloudsPos[i] = self.cloudsPos[i] + 0.1
			if self.cloudsPos[i] > globals.winWidth:
				self.cloudsPos[i] = -170
			globals.win.blit(c, (self.cloudsPos[i] ,globals.winHeight // 2))

class MainMenu:
	_mm = None
	_picture = None
	_maps = None
	def __init__(self):
		self.gameParameters = None
		self.run = True
		MainMenu._mm = self

	def initializeEndGameMenu(self, parameters):
		endMenu = Menu(name="endMenu", pos=[globals.winWidth//2  - globals.winWidth//4, (globals.winHeight - 160)//2], size=[globals.winWidth // 2, 160], register=True)
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
			ElementAnimator(bar, 0, parameters["teams"][team][1], duration = globals.fps, timeOffset=2 * globals.fps)

		endMenu.insert(MENU_BUTTON, key="continue", text="continue")
	
	def initializeWeaponMenu(self, zero=False):
		wepMenu = Menu(orientation=VERTICAL, name="weapons", pos=[40, (globals.winHeight - 180)//2], size=[globals.winWidth - 80, 180], register=True)
		
		weapons = ET.parse('weapons.xml').getroot()[0]
		weaponCount = len(weapons)
		weaponSprites = pygame.image.load("./assets/sprites.png")
		weaponIndex = 0
		indexOffset = 72

		categDict = {"MISSILES": MISSILES, "GRENADES": GRENADES, "GUNS": GUNS, "FIREY": FIREY, "BOMBS": BOMBS, "TOOLS": TOOLS,
						"AIRSTRIKE": AIRSTRIKE, "LEGENDARY": LEGENDARY}

		items = ["-1"] + [str(i) for i in range(11)]
		mapping = {"-1":"inf"}

		while weaponIndex < weaponCount:
			sub = Menu(orientation=HORIZONTAL, customSize=16)
			for j in range(6):
				pic = MenuElementImage()
				pic.customSize = 16
				bgColor = categDict[weapons[weaponIndex].attrib["category"]]
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
		mainMenu = Menu(name="menu", pos=[40, (globals.winHeight - 196)//2], size=[globals.winWidth - 80, 196], register=True)
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
			('cool down', 'option_cool_down', True),
			('artifacts', 'option_artifacts', True),
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
		bgMenu = Menu(pos=[globals.winWidth - 20, globals.winHeight - 20], size=[20, 20], register=True)
		bgMenu.insert(MENU_UPDOWN, text="bg", key="feel_index", value=feelIndex, values=[i for i in range(len(feels))], showValue=False)

	def initializeRecordMenu(self):
		# clear graphs
		graphObject.Graph._reg.clear()

		recordMenu = Menu(name="record menu", pos=[globals.winWidth//2  - globals.winWidth//4, (globals.winHeight - 180)//2], size=[globals.winWidth // 2, 180], register=True)
		recordMenu.insert(MENU_TEXT, text="worms game records", customSize=15)
		b = recordMenu.insert(MENU_SURF)
		recordMenu.insert(MENU_BUTTON, key="back", text="back", customSize=15)
	
		graph = graphObject.Graph(b.getSuperPos(), b.size, globals.pixelFont5, False)
		graph._reg[0].draw()
		b.setSurf(graph.surf)

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
		graph.setCam(Vector(pos[0]*5, -pos[1]*5)) # arbitrary '5' that works for some reason
	
	def updateWeaponSets(self):
		weaponSetCombo = getElementByName("weapon_combo")
		weaponsSets = ['default']
		if os.path.exists("./assets/weaponsSets"):
			for file in os.listdir("./assets/weaponsSets"):
				weaponsSets.append(file.split(".")[0])
		weaponSetCombo.setItems(weaponsSets)

	def handleMainMenu(self, event):
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
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, Menu._reg[0].pos + Vector(0, -globals.winHeight), trigger=playOnPress)
		if key == "continue":
			self.initializeMenuOptions()
			MenuAnimator(Menu._reg[1], Menu._reg[1].pos + Vector(0, -globals.winHeight), Menu._reg[1].pos)
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, Menu._reg[0].pos + Vector(0, globals.winHeight), trigger=continueOnPress)
			# remove the end menu
			# Menu._reg.pop(0)
		if key == "scoreboard":
			# create the scoreboard menu
			self.initializeRecordMenu()
			# animate record menu in
			MenuAnimator(Menu._reg[-1], Menu._reg[-1].pos + Vector(0, globals.winHeight), Menu._reg[-1].pos)
			# animate main menu out
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, Menu._reg[0].pos + Vector(0, -globals.winHeight))
		if key == "back":
			# animate record menu out
			MenuAnimator(Menu._reg[-1], Menu._reg[-1].pos, Menu._reg[-1].pos + Vector(0, globals.winHeight))
			# animate main menu in
			endPos = Menu._reg[0].pos + Vector(0, globals.winHeight)
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, endPos, trigger=menuPop)
			self.updateWeaponSets()
		if key == "weaponssetup":
			# create the weapons menu
			self.initializeWeaponMenu()
			# animate weapons menu in
			MenuAnimator(Menu._reg[-1], Menu._reg[-1].pos + Vector(0, globals.winHeight), Menu._reg[-1].pos)
			# animate main menu out
			MenuAnimator(Menu._reg[0], Menu._reg[0].pos, Menu._reg[0].pos + Vector(0, -globals.winHeight))
		if key == "defaultweapons":
			wepmenu = getMenubyName("weapons")
			Menu._reg.remove(wepmenu)
			self.initializeWeaponMenu()
		if key == "zeroweapons":
			wepmenu = getMenubyName("weapons")
			Menu._reg.remove(wepmenu)
			self.initializeWeaponMenu(zero=True)
		if key == "saveweapons":
			wepmenu = getMenubyName("weapons")
			values = {}
			wepmenu.evaluate(values)
			saveWeaponsXml(values, values["filename"])
			Gui._instance.toaster.toast("weapons set " + values["filename"] + " saved")
		if key == "exit":
			exit(0)

class PauseMenu:
	_pm = None
	def __init__(self):
		self.run = True
		PauseMenu._pm = self
	def initializePauseMenu(self, args):
		pauseMenu = Menu(name="endMenu", pos=[globals.winWidth//2  - globals.winWidth//4, 40], size=[globals.winWidth // 2, 160], register=True)
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
		pauseMenu.pos = Vector(globals.winWidth//2 - pauseMenu.size[0]//2, globals.winHeight//2 - pauseMenu.size[1]//2)

	def handlePauseMenu(self, event):
		key = event.key
		if key == "resume":
			self.run = False
		if key == "toMainMenu":
			self.run = False
			self.result[0] = 1

def grabMapsFrom(paths):
	maps = []
	for path in paths:
		if not os.path.isdir(path):
			continue
		for imageFile in os.listdir(path):
			if imageFile[-4:] != ".png":
				continue
			string = path + "/" + imageFile
			string = os.path.abspath(string)
			maps.append(string)
	return maps

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
	graphObject.Graph._reg.clear()

def playOnPress():
	values = evaluateMenuForm()

	# create default config
	game_config = GameConfig()
	game_config = GameConfig.model_validate(values)

	MainMenu._mm.gameParameters = game_config
	MainMenu._mm.run = False

def drawRecordGraph():
	if MainMenu._mm.graphteams is None:
		return
	for key in MainMenu._mm.graphteams.keys():
		graphObject.Graph._reg[0].drawGraph2(MainMenu._mm.graphtime, MainMenu._mm.graphteams[key][1], ast.literal_eval(MainMenu._mm.graphteams[key][0]))

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
	graphObject.Graph._reg.clear()

	BackGround()
	MainMenu()
	MainMenu._maps = grabMapsFrom(['wormsMaps', 'wormsMaps/moreMaps'])
	
	if fromGameParameters is None:
		MainMenu._mm.initializeMenuOptions()
		endPos = Menu._reg[0].pos
		MenuAnimator(Menu._reg[0], endPos + Vector(0, globals.winHeight), endPos)
	else:
		MainMenu._mm.initializeEndGameMenu(fromGameParameters)
		endPos = Menu._reg[0].pos
		MenuAnimator(Menu._reg[0], endPos + Vector(0, globals.winHeight), endPos)

	while MainMenu._mm.run:
		for event in pygame.event.get():
			mousePos = pygame.mouse.get_pos()
			for g in graphObject.Graph._reg:
				g.handleGraphEvent(event, Vector(mousePos[0] // globals.scalingFactor, mousePos[1] // globals.scalingFactor))
			handleEvents(event, MainMenu._mm.handleMainMenu)
			if event.type == pygame.QUIT:
				globals.exitGame()

		# step
		BackGround._bg.step()
		
		Gui._instance.step()
		
		for g in graphObject.Graph._reg:
			mousePos = pygame.mouse.get_pos()
			g.step(Vector(mousePos[0] // globals.scalingFactor, mousePos[1] // globals.scalingFactor))

		# draw
		BackGround._bg.draw()

		Gui._instance.draw()

		for g in graphObject.Graph._reg:
			g.draw()
			drawRecordGraph()

		globals.screen.blit(pygame.transform.scale(globals.win, globals.screen.get_rect().size), (0,0))
		globals.fpsClock.tick(globals.fps)
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
			handleEvents(event, PauseMenu._pm.handlePauseMenu)
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
		globals.fpsClock.tick(globals.fps)
	pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
	clearMenu()
	return