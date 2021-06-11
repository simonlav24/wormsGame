import PySimpleGUI as sg
import os, sys
import subprocess
from random import choice
import time

def loadImage(num):
	return 'wormsMaps/wMap' + str(num) + '.png'

maps = []
for imageFile in os.listdir('wormsMaps'):
	if imageFile[-4:] != ".png":
		continue
	string = "wormsMaps/" + imageFile
	maps.append(string)

def randMap():
	return choice(maps)

def path2map(path):
	if "perlin" in path:
		return path
	return path.split("/")[-1]

def parseRecord():
	os.popen("wormsWinCounter.py")
	

mapChoice = randMap()
image_elem = sg.Image(key="image", filename=mapChoice, size=(700,500))

sg.theme('Reddit')   # Add a touch of color

defaults = {"--worms_per_team": 8, "--initial_health": 100, "--pack_mult": 1}

layout =   [[sg.Text("Simon's worms game options")],
			[sg.Text('Gameplay Mode'), 
				sg.Checkbox('Forts', key="--forts"), sg.Checkbox('Capture the flag', key="--ctf"), sg.Checkbox('Points', key="--points_mode"), sg.Checkbox('Targets', key="--targets"), sg.Checkbox('David vs Goliath', key="--dvg"), 
				sg.Checkbox('Digging', key="--digging")], 
			[sg.Text('Options'), sg.Checkbox('Used List', key="--used_list"), sg.Checkbox('Warped', key="--warped"), sg.Checkbox('Random', key="--random"), sg.Checkbox('Manual placing', key="--place"), 
				sg.Checkbox('Darkness', key="--darkness"), sg.Checkbox('Closed map', key="--closed_map")],
			[sg.Spin([i for i in range(1, 9)], size=(6, 1), initial_value=8, key="--worms_per_team"), sg.Text('Worms per team'), 
				sg.Spin([i for i in range(50,1000,50)], size=(6, 1), initial_value=100, key="--initial_health"), sg.Text('Health'), 
				sg.Spin([i for i in range(1,11)], size=(6, 1), initial_value=1, key="--pack_mult"), sg.Text('Packs')],
			[sg.Text("Perlin noise map generator"), sg.Button('Generate', key="generate")],
			[sg.Text('Game map'), sg.Button('Random', key="random"), sg.Input(key='browse', enable_events=True, visible=False), sg.FileBrowse(target="browse", enable_events=True), sg.Button('Play', key="play")],
			[image_elem], 
			[sg.Button('Score Record', key="record")]]

# Create the Window
window = sg.Window('Worms Launcher', layout, grab_anywhere=True)


while True:
	event, values = window.read()
	if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
		break
	
	if event == "random":
		mapChoice = randMap()
		image_elem.Update(filename=mapChoice, size=(700,500))
	
	if event == "browse":
		mapChoice = values["browse"]
		image_elem.Update(filename=mapChoice, size=(700,500))
	
	if event == "generate":
		mapChoice = subprocess.check_output("python ./perlinNoise.py -d").decode('utf-8')[:-2]
		image_elem.Update(filename=mapChoice, size=(700,500))
		
	if event == "record":
		parseRecord()
		
		
	if event == "play":
		starter = ""
		if os.path.exists("main.py"):
			starter = "main.py"
		else:
			starter = "worms.py"
		string = starter + " -map " + path2map(mapChoice) + " "
		
		for key in values.keys():
			if key in defaults.keys():
				if values[key] != defaults[key]:
					string += key + " " + str(values[key]) + " "
			elif values[key] == True:
				string += key + " "
		print(string)

		window.close()
		subprocess.Popen(string, shell=True)
		sys.exit()
		
	window.Refresh()
	
window.close()

