import PySimpleGUI as sg
import os, sys, subprocess
import xml.etree.ElementTree as ET
import xml.dom.minidom
from random import choice, randint

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
	if not os.path.exists("wormsRecord.xml"):
		sg.popup('no record yet')
		return
	os.popen("wormsWinCounter.py")

def saveTeam(values):
	data = ET.Element("data")
	
	for t in range(4):
		teamKey = "team" + str(t)
		colorKey = "teamColor" + str(t)
		team = ET.SubElement(data, "team", name=values[teamKey], color=values[colorKey])
		for w in range(8):
			wormKey = "worm" + str(t) + str(w)
			worm = ET.SubElement(team, "worm", name=values[wormKey])

	pretty = xml.dom.minidom.parseString(ET.tostring(data, encoding='unicode')).toprettyxml(indent='    ')
	if os.path.exists("wormsTeamsOld.xml"):
		os.remove("wormsTeamsOld.xml")
	os.rename("wormsTeams.xml", "wormsTeamsOld.xml")
	with open("wormsTeams.xml", 'w+') as output:
		output.write(pretty)
	sg.popup('worms team saved')

fnt_bold = ('Arial', 10, 'bold')

mapChoice = randMap()
image_elem = sg.Image(key="image", filename=mapChoice, size=(600,400))

sg.theme('Reddit')

defaults = {"--worms_per_team": 8, "--initial_health": 100, "--pack_mult": 1, "-ratio": ""}

tab1_layout =   [[sg.Text("Simon's worms game launcher", font=fnt_bold)],
			[sg.Text('Gameplay Mode', font=fnt_bold),
				sg.Radio('Battle', "RADIO1", key="battleMode", default=True), sg.Radio('Points', "RADIO1", key="pointsMode2"),
				sg.Radio('Targets', "RADIO1", key="targetsMode3"), sg.Radio('Capture the flag', "RADIO1", key="captureTheFlagMode4")],
			[sg.Text('                          '), sg.Radio('Terminator', "RADIO1", key="terminatorMode5"), sg.Radio('David vs Goliath', "RADIO1", key="davidVGoliathMode1"), sg.Radio('Arena', "RADIO1", key="arenaMode6")],
			[sg.Text('Options', font=fnt_bold), sg.Checkbox('Cooldown', key="--used_list", default=True), sg.Checkbox('Artifacts', key="--artifacts", default=True),sg.Text('Random'), sg.Combo(['Complete', 'In Team'], key='--random'), sg.Checkbox('Manual placing', key="--place"), 
				], 
			[sg.Text('            '), sg.Checkbox('Closed map', key="--closed_map"), sg.Checkbox('Forts', key="--forts"), sg.Checkbox('Digging', key="--digging"), sg.Checkbox('Darkness', key="--darkness"), sg.Checkbox('Warped', key="--warped")],
			[sg.Text('             '), sg.Spin([i for i in range(1, 9)], size=(6, 1), initial_value=8, key="--worms_per_team"), sg.Text('Worms per team'), 
				sg.Spin([i for i in range(50,1000,50)], size=(6, 1), initial_value=100, key="--initial_health"), sg.Text('Health'), 
				sg.Spin([i for i in range(1,11)], size=(6, 1), initial_value=1, key="--pack_mult"), sg.Text('Packs')],
			[sg.Text('            '), sg.Checkbox('Sudden death after', key='suddenDeath', enable_events=True, default=True), sg.Spin([i for i in range(0,50,1)], size=(6, 1), initial_value=16, key="suddenDeathRounds", disabled=False), 
				sg.Text('rounds'), sg.Checkbox('Water level rising', key='tsunami', disabled=False), sg.Checkbox('Plague', key='plague', disabled=False)],
			[sg.Text("Perlin noise map generator", font=fnt_bold), sg.Button('Generate', key="generate")],
			[sg.Text('Game map', font=fnt_bold), sg.Button('Random', key="random"), sg.Input(key='browse', enable_events=True, visible=False), sg.FileBrowse(target="browse", enable_events=True), sg.Button('Play', key="play"),
				sg.Checkbox('Ground color', key="-rg"), sg.Input("", key="-ratio", size=(6,1)), sg.Text('Custom ratio')],
			[image_elem], 
			[sg.Button('Score Record', key="record"), sg.Button('About', key="about")]]

# parse teams
tab2_layout = [[]]

for j, teamsData in enumerate(ET.parse('wormsTeams.xml').getroot()):
	layout_teamName = [[sg.Input(teamsData.attrib["name"], size=(15,1), key = "team"+str(j), font=fnt_bold)],
						[sg.Input(teamsData.attrib["color"], size=(15,1), key = "teamColor"+str(j))]]
	for i, team in enumerate(teamsData):
		keyStr = "worm" + str(j) + str(i)
		layout_teamName.append([sg.Input( team.attrib["name"], key=keyStr, size=(15,1))])
	tab2_layout[0].append(sg.Column(layout_teamName))

tab2_layout.append([sg.Button('Save Teams', key="save_team")])

tab3_layout = []

layout = [[sg.TabGroup([[sg.Tab('Gameplay', tab1_layout), sg.Tab('Team edit', tab2_layout), sg.Tab('Settings', tab3_layout)]])]]

# Create the Window
window = sg.Window('Worms Launcher', layout, grab_anywhere=True)

# popup winners
if len(sys.argv) > 1 and os.path.exists('wormsRecord.xml'):
	winners = ET.parse('wormsRecord.xml').getroot()
	sg.popup('Team ' + winners[-1].attrib["winner"] + " won!",
		'Most damage: ' + winners[-1].attrib["mostDamage"] + " by " + winners[-1].attrib["damager"], title="Worms game results")
	popupWin = False
	

while True:
	event, values = window.read()
	if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
		break
	
	if event == "suddenDeath":
		window.FindElement('suddenDeathRounds').Update(disabled = not values["suddenDeath"])
		window.FindElement('tsunami').Update(disabled = not values["suddenDeath"])
		window.FindElement('plague').Update(disabled = not values["suddenDeath"])
	
	if event == "random":
		mapChoice = randMap()
		image_elem.Update(filename=mapChoice, size=(600,400))
	
	if event == "browse":
		mapChoice = os.path.abspath(values["browse"])
		image_elem.Update(filename=mapChoice, size=(600,400))
	
	if event == "generate":
		mapChoice = subprocess.check_output("python ./perlinNoise.py -d").decode('utf-8')[:-2]
		image_elem.Update(filename=mapChoice, size=(600,400))
		
	if event == "record":
		parseRecord()
		
	if event == "save_team":
		saveTeam(values)
	
	if event == "about":
		sg.popup('This game was developed by Simon Labunsky', 'For educational purposes and fun', 'Enjoy', title="About")
	
	if event == "play":
		starter = ""
		if os.path.exists("main.py"):
			starter = "main.py"
		else:
			starter = "worms.py"
		string = starter + " -map " + path2map(mapChoice) + " "
		
		for key in values.keys():
			
			if key == "--random":
				if values["--random"] == "Complete":
					string += " " + key + " 1 "
				elif values["--random"] == "In Team":
					string += " " + key + " 2 "
				continue
			if key in ["suddenDeath", "suddenDeathRounds", "tsunami", "plague", "battleMode"]:
				continue
			if "Mode" in str(key) and values[key]:
				string += "--game_mode " + key[-1] + " "
				continue
			if key in defaults.keys():
				if values[key] != defaults[key]:
					string += key + " " + str(values[key]) + " "
			elif values[key] == True:
				string += key + " "
		if values["suddenDeath"]:
			suddenDeathRounds = values["suddenDeathRounds"]
			if suddenDeathRounds == 0:
				suddenDeathRounds = randint(2, 14)
			string += " --sudden_death " + str(suddenDeathRounds)
			if values["tsunami"]:	
				string += " --sudden_death_tsunami"
			if values["plague"]:	
				string += " --sudden_death_plague"

		window.close()
		# print(string)
		subprocess.Popen(string, shell=True)
		sys.exit()
		
	window.Refresh()
	
	
window.close()

