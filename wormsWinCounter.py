import os
import xml.etree.ElementTree as ET
import ast
import pygame
if os.path.exists("graphObject.py"):
	import graphObject
else:
	print("fetching graph")
	import urllib.request
	with urllib.request.urlopen('https://raw.githubusercontent.com/simonlav24/Graph-plotter/master/graphObject.py') as f:
		text = f.read().decode('utf-8')
		with open("graphObject.py", "w+") as graphpy:
			graphpy.write(text)
	import graphObject
from vector import *

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

if __name__ == "__main__":

	teams, count = countWin()
	time = [i for i in range(count)]

	y_average = 0
	for key in teams.keys():
		y_average += teams[key][1][-1]
	y_average /= len(teams)

	x = time[-1]

	pygame.init()
	win = pygame.Surface((1280 // 3, 720 // 3))
	screen = pygame.display.set_mode((1280, 720))

	graph = graphObject.Graph(Vector(20,20), Vector(1280 // 3,720 // 3), pygame.font.Font("fonts/pixelFont.ttf", 5), False)

	run = True
	while run:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			graph.handleGraphEvent(event, mousePosition=Vector(pygame.mouse.get_pos()[0] // 3, pygame.mouse.get_pos()[1] // 3))
		
		if pygame.key.get_pressed()[pygame.K_ESCAPE]:
			run = False

		graph.step(mousePosition=Vector(pygame.mouse.get_pos()[0] // 3, pygame.mouse.get_pos()[1] // 3))
		graph.draw()

		for key in teams.keys():
			graph.drawGraph2(time, teams[key][1], ast.literal_eval(teams[key][0]))

		win.fill((255,255,255))
		graph.blitToScreen(win)

		screen.blit(pygame.transform.scale(win, screen.get_size()), (0,0))

		pygame.display.flip()

# def step():
# 	pass
	
# def draw():
# 	for key in teams.keys():
# 		graphObject.drawGraph2(time, teams[key][1], ast.literal_eval(teams[key][0]))

# graphObject.setWinSize((1280//3, 720//3))
# graphObject.setFont("pixelFont.ttf", 5)
# graphObject.setZoom(25)
# graphObject.setCam((x, y_average))
# graphObject.mainLoop(step, draw)