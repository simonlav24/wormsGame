import PySimpleGUI as sg
import os, sys
import subprocess
from random import choice
import time

def loadImage(num):
	return 'wormsMaps/wMap' + str(num) + '.png'

def grabMapsFrom(path, maps):
	for imageFile in os.listdir(path):
		if imageFile[-4:] != ".png":
			continue
		string = path + "/" + imageFile
		maps.append(string)

maps = []
grabMapsFrom('wormsMaps', maps)
if os.path.exists('wormsMaps/moreMaps'):
	grabMapsFrom('wormsMaps/moreMaps', maps)

def randMap():
	return choice(maps)

def path2map(path):
	if "perlin" in path:
		return path
	return path.split("/")[-1]

def parseRecord():
	os.popen("wormsWinCounter.py")
	

mapChoice = randMap()
image_elem = sg.Image(key="image", filename=mapChoice, size=(600,400))

sg.theme('Reddit')   # Add a touch of color

defaults = {"--worms_per_team": 8, "--initial_health": 100, "--pack_mult": 1}

layout =   [[sg.Text("Simon's worms game launcher", font=('Arial', 10, 'bold'))],
			[sg.Text('Gameplay Mode', font=('Arial', 10, 'bold')),
				sg.Radio('David vs Goliath', "RADIO1", key="--dvg"), sg.Radio('Points', "RADIO1", key="--points_mode"),
				sg.Radio('Targets', "RADIO1", key="--targets"), sg.Radio('Capture the flag', "RADIO1", key="--ctf")],
			[sg.Text('Options', font=('Arial', 10, 'bold')), sg.Checkbox('Used List', key="--used_list"), sg.Checkbox('Warped', key="--warped"), sg.Checkbox('Random', key="--random"), sg.Checkbox('Manual placing', key="--place"), 
				sg.Checkbox('Darkness', key="--darkness")], 
			[sg.Text('            '), sg.Checkbox('Closed map', key="--closed_map"), sg.Checkbox('Forts', key="--forts"), sg.Checkbox('Digging', key="--digging")],
			[sg.Text('             '), sg.Spin([i for i in range(1, 9)], size=(6, 1), initial_value=8, key="--worms_per_team"), sg.Text('Worms per team'), 
				sg.Spin([i for i in range(50,1000,50)], size=(6, 1), initial_value=100, key="--initial_health"), sg.Text('Health'), 
				sg.Spin([i for i in range(1,11)], size=(6, 1), initial_value=1, key="--pack_mult"), sg.Text('Packs')],
			[sg.Text("Perlin noise map generator", font=('Arial', 10, 'bold')), sg.Button('Generate', key="generate")],
			[sg.Text('Game map', font=('Arial', 10, 'bold')), sg.Button('Random', key="random"), sg.Input(key='browse', enable_events=True, visible=False), sg.FileBrowse(target="browse", enable_events=True), sg.Button('Play', key="play")],
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
		image_elem.Update(filename=mapChoice, size=(600,400))
	
	if event == "browse":
		mapChoice = values["browse"]
		image_elem.Update(filename=mapChoice, size=(600,400))
	
	if event == "generate":
		mapChoice = subprocess.check_output("python ./perlinNoise.py -d").decode('utf-8')[:-2]
		image_elem.Update(filename=mapChoice, size=(600,400))
		
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

