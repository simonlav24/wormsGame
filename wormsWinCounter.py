import os
import xml.etree.ElementTree as ET
import ast
if os.path.exists("graph.py"):
	import graph
else:
	print("fetching graph")
	import urllib.request
	with urllib.request.urlopen('https://raw.githubusercontent.com/simonlav24/Graph-plotter/master/graph.py') as f:
		text = f.read().decode('utf-8')
		with open("graph.py", "w+") as graphpy:
			graphpy.write(text)
	import graph

def countWin():
	if not os.path.exists("wormsRecord.xml"):
		return
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
	
teams, count = countWin()
time = [i for i in range(count)]

y_average = 0
for key in teams.keys():
	y_average += teams[key][1][-1]
y_average /= len(teams)

x = time[-1]

def step():
	pass
	
def draw():
	for key in teams.keys():
		graph.drawGraph2(time, teams[key][1], ast.literal_eval(teams[key][0]))
		
graph.setZoom(25)
graph.setCam((x, y_average))
graph.mainLoop(step, draw)