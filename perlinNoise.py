from math import fabs, sqrt, cos, sin, pi, floor, ceil, exp
from random import uniform, randint, choice
import pygame
import argparse
import datetime
import os



################################################################################

def perlin1D(count, seedArray, octaves, bias):
	output = []
	for x in range(count):
		noise = 0
		scale = 1
		scaleAcc = 0
		for o in range(octaves):
			pitch = count >> o
			sample1 = (x // pitch) * pitch
			sample2 = (sample1 + pitch) % count
			
			blend = (x - sample1)/pitch
			sample = (1 - blend) * seedArray[sample1] + blend * seedArray[sample2]
			noise += sample * scale
			scaleAcc += scale
			scale /= bias
		output.append(noise / scaleAcc)
	return output

def perlin2D(width, height, seedArray, octaves, bias):
	output = [0] * width * height
	average = 0
	for x in range(width):
		for y in range(height):
			noise = 0
			scaleAcc = 0
			scale = 1
			for o in range(octaves):
				pitch = width >> o
				sampleX1 = (x // pitch) * pitch
				sampleY1 = (y // pitch) * pitch
				
				sampleX2 = (sampleX1 + pitch) % width
				sampleY2 = (sampleY1 + pitch) % width
				
				blendX = (x - sampleX1)/pitch
				blendY = (y - sampleY1)/pitch
				
				# print(sampleY1 * width + sampleX1)
				# print(sampleY2 * width + sampleX1)
				sampleT = (1 - blendX) * seedArray[sampleY1 * width + sampleX1] + blendX * seedArray[sampleY1 * width + sampleX2]
				sampleB = (1 - blendX) * seedArray[sampleY2 * width + sampleX1] + blendX * seedArray[sampleY2 * width + sampleX2]
				
				scaleAcc += scale
				noise += (blendY * (sampleB - sampleT) + sampleT) * scale
				scale /= bias
			output[y * width + x] = noise / scaleAcc
			average += noise / scaleAcc
	return (output, average / (width * height))

def generatePerlinNoise(width, height):
	noiseSeed2D = [uniform(0,1) for i in range(noiseWid * noiseHei)]
	octaveCount = 7
	bias = 1.2
	
	perlin, avrg = perlin2D(noiseWid, noiseHei, noiseSeed2D, octaveCount, bias)
	
	surf = pygame.Surface((width, height))
	
	for x in range(noiseWid):
		for y in range(noiseHei):
			pixel = perlin[y * noiseWid + x]
			if pixel < avrg: surf.set_at((x,y), (255,255,255))
			if pixel >= avrg: surf.set_at((x,y), (0,0,0))
	
	return surf

def random_bw(minimum=0, maximum=255):
	color = randint(minimum, maximum)
	return (color, color, color)

def threshold(surf, avrg):
	for x in range(surf.get_width()):
		for y in range(surf.get_height()):
			pixel = surf.get_at((x, y))[0]
			if pixel < avrg: surf.set_at((x,y), (255,255,255))
			if pixel >= avrg: surf.set_at((x,y), (0,0,0))

def generateNoise(width, height):
	ratio = height / width
	pool = randint(20, 50)
	size = (pool, int(pool * ratio))
	noise_org = pygame.Surface(size)
	for y in range(size[1]):
		for x in range(size[0]):
			noise_org.set_at((x,y), random_bw())
			if x == 0:
				noise_org.set_at((x,y), random_bw(128,255))
			if x == size[0] - 1:
				noise_org.set_at((x,y), random_bw(128,255))
			if y == 0:
				noise_org.set_at((x,y), random_bw(128,255))
			if y in [size[1] - 1, size[1] - 2]:
				noise_org.set_at((x,y), random_bw(0,128))
	
	pygame.draw.circle(noise_org, (255, 255, 255), (randint(5, size[0] - 5), randint(5, size[0] - 5)), size[1] //2 - randint(2,6))
	surf = pygame.transform.smoothscale(noise_org, (winWidth, winHeight))
	threshold(surf, randint(100, 128))
	return surf

################################################################################ Main Loop

if __name__ == "__main__":

	parser = argparse.ArgumentParser()

	parser.add_argument("-d", "--dump", action='store_true', help='generate image and quit')
	parser.add_argument("-t", "--type", default="noise", help="noise type", type=str)
	
	args = parser.parse_args()
	
	winWidth = 800
	winHeight = 300
	
	pygame.init()
	
	win = pygame.display.set_mode((winWidth,winHeight))

	if args.type == "perlin":
		noise = generatePerlinNoise(winWidth, winHeight)
	elif args.type == "noise":
		noise = generateNoise(winWidth, winHeight)
	win.blit(noise, (0,0))

	run = True
	while run:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
	
			if event.type == pygame.KEYDOWN:
				#key pressed once:
				if event.key == pygame.K_x:
					if args.type == "perlin":
						noise = generatePerlinNoise(winWidth, winHeight)
					elif args.type == "noise":
						noise = generateNoise(winWidth, winHeight)
					win.blit(noise, (0,0))
		keys = pygame.key.get_pressed()
		if keys[pygame.K_ESCAPE]:
			run = False
		
		if args.dump:
			break
		pygame.display.update()
	
	x = datetime.datetime.now()
	if not os.path.exists("wormsMaps/PerlinMaps"):
		os.mkdir("wormsMaps/PerlinMaps")
		
	imageString = "wormsMaps/PerlinMaps/perlin" + str(x.day) + str(x.month) + str(x.year % 100) + str(x.hour) + str(x.minute) + ".png"
	pygame.image.save(win, imageString)
	print(imageString)
	pygame.quit()














