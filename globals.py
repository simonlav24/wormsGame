
import pygame

win = None
winWidth = 0
winHeight = 0
scalingFactor = 0

class HaloFont:
    def __init__(self, font):
        self.fontObject = font
    def render(self, text, antialiasing, color, halo=(0,0,0)):
        haloSurf = self.fontObject.render(text, antialiasing, halo)
        textSurf = self.fontObject.render(text, antialiasing, color)
        surf = pygame.Surface((textSurf.get_width() + 2, textSurf.get_height() + 2), pygame.SRCALPHA)
        surf.blit(haloSurf, (0,1))
        surf.blit(haloSurf, (1,0))
        surf.blit(haloSurf, (1,2))
        surf.blit(haloSurf, (2,1))
        surf.blit(textSurf, (1,1))
        return surf

def globalsInit():
    global fpsClock, fps, pixelFont5, pixelFont5halo, pixelFont10, screenWidth, screenHeight, scalingFactor, winWidth, winHeight, win, screen
    global scalingMax, scalingMin

    pygame.init()

    fpsClock = pygame.time.Clock()
    fps = 30
        
    # pygame.font.init()
    pixelFont5 = pygame.font.Font("fonts\pixelFont.ttf", 5)
    pixelFont5halo = HaloFont(pixelFont5)
    pixelFont10 = pygame.font.Font("fonts\pixelFont.ttf", 10)

    screenWidth = 1920
    screenHeight = 1080
    
    scalingFactor = 3
    scalingMax = 3
    scalingMin = 1
    
    winWidth = int(screenWidth / scalingFactor)
    winHeight = int(screenHeight / scalingFactor)
    win = pygame.Surface((winWidth, winHeight))
    
    pygame.display.set_caption("Simon's Worms")
    screen = pygame.display.set_mode((screenWidth,screenHeight), pygame.DOUBLEBUF | pygame.NOFRAME)

def exitGame():
    pygame.quit()
    quit(0)