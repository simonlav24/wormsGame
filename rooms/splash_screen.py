
import pygame

from common import GameVariables
from rooms.room import Room, Rooms, SwitchRoom

class SplashScreenRoom(Room):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.splashImage = pygame.image.load("assets/simeGames.png")
		self.timer = 2 * GameVariables().fps
	
	def handle_pygame_event(self, event) -> None:
		super().handle_pygame_event(event)
		if event.type == pygame.QUIT:
			self.end()
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			self.end()

	def end(self):
		self.switch = SwitchRoom(Rooms.MAIN_MENU, True, None)

	def step(self):
		super().step()
		self.timer -= 1
		if self.timer <= 0:
			self.end()
	
	def draw(self, win: pygame.Surface) -> None:
		super().draw(win)
		win.fill((11,126,193))
		win.blit(self.splashImage, ((
			GameVariables().win_width / 2 - self.splashImage.get_width() / 2,
			GameVariables().win_height / 2 - self.splashImage.get_height() / 2
			)))