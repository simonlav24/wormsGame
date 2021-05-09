import PySimpleGUI as sg
import os, sys
import subprocess
from random import choice

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
	return path.split("/")[-1]

mapChoice = randMap()
image_elem = sg.Image(key="image", filename=mapChoice, size=(700,500))

sg.theme('Reddit')   # Add a touch of color

defaults = {"--worms_per_team": 8, "--initial_health": 100, "--pack_mult": 1}

layout = [  [sg.Text("Simon's worms game options")],
			[sg.Checkbox('Forts', key="--forts"), sg.Checkbox('Points', key="--points_mode"), sg.Checkbox('Used List', key="--used_list"), sg.Checkbox('David vs Goliath', key="--dvg"), 
				sg.Checkbox('Digging', key="--digging"), sg.Checkbox('Darkness', key="--darkness"), sg.Checkbox('Closed map', key="--closed_map")], 
			[sg.Checkbox('Capture the flag', key="--ctf"), sg.Checkbox('Targets', key="--targets"), sg.Checkbox('Warped', key="--warped"), sg.Checkbox('Random', key="--random"), sg.Checkbox('Manual placing', key="--place")],
			[sg.Spin([i for i in range(1, 9)], initial_value=8, key="--worms_per_team"), sg.Text('Worms per team'), 
				sg.Spin([i for i in range(50,1000,50)], initial_value=100, key="--initial_health"), sg.Text('Health'), 
				sg.Spin([i for i in range(1,11)], initial_value=1, key="--pack_mult"), sg.Text('Packs')],
			[sg.Text('Game map'), sg.Button('Random', key="random"), sg.Input(key='browse', enable_events=True, visible=False), sg.FileBrowse(target="browse", enable_events=True), sg.Button('Play', key="play")],
			[image_elem] ]

# Create the Window
window = sg.Window('Worms Launcher', layout)

boolParamsLen = len(layout[1]) + len(layout[2])
intParamsLen = len(layout[3])/2


layoutbools1 = 1
layoutbools2 = 2
layoutparams = 3

while True:
	event, values = window.read()
	if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
		break
	
	# print(event, values)
	# print('You entered ', values[0])
	if event == "random":
		mapChoice = randMap()
		image_elem.Update(filename=mapChoice, size=(700,500))
	
	if event == "browse":
		mapChoice = values["browse"]
		image_elem.Update(filename=mapChoice, size=(700,500))
		
		
	if event == "play":
		prog = "worms.py " if os.path.exists("./worms.py") else "main.py "
		string = prog + "-map " + path2map(mapChoice) + " "
		for i, key in enumerate(values):
			if i < boolParamsLen:
				if values[key] == True:
					string += str(key) + " "
			elif i < boolParamsLen + intParamsLen:
				if defaults[key] != values[key]:
					string += str(key) + " " + str(values[key]) + " "
		window.close()
		os.system(string)
		sys.exit()
	window.Refresh()
	
window.close()

