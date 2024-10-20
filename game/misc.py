
import os
import pygame
from common import GameVariables

class Anim:
    ''' renders animation into frames '''
    def __init__(self):
        GameVariables().register_non_physical(self)
        num = -1
        for folder in os.listdir("./anims"):
            if not os.path.isdir("./anims/" + folder):
                continue
            try:
                folderNum = int(folder)
            except:
                continue
            num = max(num, folderNum)
        self.folder = "./anims/" + str(num + 1)
        # create folder
        if not os.path.isdir(self.folder):
            os.mkdir(self.folder)
        self.time = 0
        print("record Start")
    
    def step(self):
        pass
    
    def draw(self, win: pygame.Surface):
        pygame.image.save(win, self.folder + "/" + str(self.time).zfill(3) + ".png")
        self.time += 1
        if self.time == 5 * GameVariables().fps:
            GameVariables().unregister_non_physical(self)
            print("record End")
    

class TimeSlow:
	def __init__(self):
		GameVariables().register_non_physical(self)
		self.time = 0
		self.state = "slow"
	def step(self):
		self.time += 1
		if self.state == "slow":
			GameVariables().dt *= 0.9
			if GameVariables().dt < 0.1:
				self.state = "fast"
		elif self.state == "fast":
			GameVariables().dt *= 1.1
			if GameVariables().dt > 1:
				GameVariables().dt = 1
				GameVariables().unregister_non_physical(self)
	def draw(self, win: pygame.Surface):
		pass