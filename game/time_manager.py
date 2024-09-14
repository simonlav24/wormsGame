
import pygame

from common import GameVariables, fonts, GameState, SingletonMeta



class TimeManager(metaclass=SingletonMeta):
	''' manages time overall measuring, turn time counting '''

	def __init__(self):
		self.turnTime = 45
		self.retreatTime = 5
		self.wormDieTime = 3

		# second counter
		self.time_counter: int = self.turnTime
		self.generate_time_surf()
	
	def generate_time_surf(self):
		self.timeSurf = (self.time_counter, fonts.pixel5_halo.render(str(self.time_counter), False, GameVariables().initial_variables.hud_color))
	
	def step(self):
		GameVariables().time_overall += 1
		if GameVariables().time_overall % GameVariables().fps == 0:
			self.timeStep()
	
	def timeStep(self):
		''' one second has passed '''
		if self.time_counter == 0:
			self.on_timer()
		
		if not self.time_counter <= 0:
			self.time_counter -= 1
	
	def on_timer(self):
		if GameVariables().game_state == GameState.PLAYER_PLAY:
			GameVariables().game_state = GameState.WAIT_STABLE
			
		elif GameVariables().game_state == GameState.PLAYER_RETREAT:
			GameVariables().game_state = GameVariables().game_next_state
			
	def draw(self, win: pygame.Surface):
		if self.timeSurf[0] != self.time_counter:
			self.generate_time_surf()
		win.blit(self.timeSurf[1] , ((5, 5)))
	
	def time_reset(self):
		self.time_counter = self.turnTime + 1
	
	def time_remaining(self, amount):
		self.time_counter = amount
	
	def time_remaining_etreat(self):
		self.time_remaining(self.retreatTime)
	
	def time_remaining_die(self):
		self.time_remaining(self.wormDieTime)
