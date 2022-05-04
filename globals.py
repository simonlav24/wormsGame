
import pygame

win = None
winWidth = 0
winHeight = 0
scalingFactor = 0

def globalsInit():
    global fpsClock, fps, pixelFont5, pixelFont10, screenWidth, screenHeight, scalingFactor, winWidth, winHeight, win, screen

    pygame.init()

    fpsClock = pygame.time.Clock()
    fps = 30
        
    # pygame.font.init()
    pixelFont5 = pygame.font.Font("fonts\pixelFont.ttf", 5)
    pixelFont10 = pygame.font.Font("fonts\pixelFont.ttf", 10)

    screenWidth = 1280
    screenHeight = 720
    scalingFactor = 3
    winWidth = int(screenWidth / scalingFactor)
    winHeight = int(screenHeight / scalingFactor)
    win = pygame.Surface((winWidth, winHeight))
        
    pygame.display.set_caption("Simon's Worms")
    screen = pygame.display.set_mode((screenWidth,screenHeight), pygame.DOUBLEBUF | pygame.NOFRAME)

def exitGame():
    pygame.quit()
    quit(0)