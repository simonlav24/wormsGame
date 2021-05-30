from math import fabs, sqrt, cos, sin, pi, floor, ceil, exp
from random import uniform, randint, choice
import pygame
import argparse
import datetime

parser = argparse.ArgumentParser()

parser.add_argument("-d", "--dump", action='store_true', help='generate image and quit')

args = parser.parse_args()

winWidth = 800
winHeight = 300
noiseWid = winWidth
noiseHei = winWidth

pygame.init()
if not args.dump:
	
	fpsClock = pygame.time.Clock()

win = pygame.display.set_mode((winWidth,winHeight))

################################################################################

noiseSeed = [uniform(0,1) for i in range(winWidth)]
noiseSeed2D = [uniform(0,1) for i in range(noiseWid * noiseHei)]
# print(len(noiseSeed2D))
perlinNoise = []

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

def perlin2Do(width, height, seedArray, octaves, bias):
	output = [0] * width * height
	for y in range(height):
		xoff = 0
		perlin1d = perlin1D(width, [uniform(0,1) for i in range(height)], 7, 1.5)
		for x in range(width):
			r = perlin1d[xoff] * 255
			output[x + y * width] = (r,r,r)
			xoff += 1
			
	return (output, 0.5)

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

def regenerate():
	global perlin, avrg, octaveCount, bias
	perlin, avrg = perlin2D(noiseWid, noiseHei, noiseSeed2D, octaveCount, bias)
	# print(avrg)
	

octaveCount = 7
bias = 1.2

perlin = []
avrg = 0

regenerate()

################################################################################ Main Loop
run = True
while run:
	if not args.dump: fpsClock.tick(3)
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False

		if event.type == pygame.KEYDOWN:
			#key pressed once:
			if event.key == pygame.K_x:
				bias = uniform(1.2, 2.2)
				octaveCount = randint(6,7)
				noiseSeed2D = [uniform(0,1) for i in range(noiseWid * noiseHei)]
				regenerate()
			if event.key == pygame.K_l:
				bias += 0.1
				regenerate()
			if event.key == pygame.K_k:
				bias -= 0.1
				regenerate()
	keys = pygame.key.get_pressed()
	if keys[pygame.K_ESCAPE]:
		run = False
	
	# draw:
	# win.fill((255,255,255))
	
	
	# print(perlin)
	# print(hh)
	
	# perlin = perlin1D(winWidth, noiseSeed, octaveCount, 1.8)
	# for x, y in enumerate(perlin):
		# pygame.draw.line(win, (0,0,0), (x, 0), (x, y * winHeight))
	
	
	# for x in range(winWidth):
		# for y in range(winHeight):
			# pixel = perlin[y * winWidth + x]
			# win.set_at((x,y), pixel)
	
	
	for x in range(noiseWid):
		for y in range(noiseHei):
			pixel = perlin[y * noiseWid + x]
			if pixel < avrg: win.set_at((x,y), (255,255,255))
			if pixel >= avrg: win.set_at((x,y), (0,0,0))
	
	if args.dump:
		break
	pygame.display.update()
	
x = datetime.datetime.now()
imageString = "wormsMaps/PerlinMaps/perlin" + str(x.day) + str(x.month) + str(x.year % 100) + str(x.hour) + str(x.minute) + ".png"
pygame.image.save(win, imageString)
print(imageString)
pygame.quit()














