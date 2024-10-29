''' main entry point '''

import traceback
from typing import Dict

import pygame
import pygame.gfxdraw

from common import GameGlobals
import common.constants

from rooms.room import Room, Rooms
from rooms.room_main_menu import MainMenuRoom
from rooms.room_pause import PauseRoom
from rooms.splash_screen import SplashScreenRoom
from rooms.room_game import GameRoom


wip = '''
	still in progress:
		holding mjolnir
		refactor bubble
		team creation screen
		pressing 0 to cycle legendaries
	'''

def main():
	print(wip)
	pygame.init()
	fps_clock = pygame.time.Clock()
	GameGlobals().win_width = int(GameGlobals().screen_width / GameGlobals().scale_factor)
	GameGlobals().win_height = int(GameGlobals().screen_height / GameGlobals().scale_factor)

	GameGlobals().win = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height))

	pygame.display.set_caption("Simon's Worms")
	screen = pygame.display.set_mode((GameGlobals().screen_width, GameGlobals().screen_height), pygame.DOUBLEBUF)
	GameGlobals().screen = screen

	common.constants.initialize()

	# room enum to room class converter
	rooms_creation_dict = {
		Rooms.MAIN_MENU: MainMenuRoom,
		Rooms.GAME_ROOM: GameRoom,
		Rooms.PAUSE_MENU: PauseRoom,
	}

	# current active rooms
	rooms_dict: Dict[Rooms, Room] = {}

	current_room = SplashScreenRoom()
	rooms_dict[Rooms.MAIN_MENU] = current_room

	done = False
	while not done:
		try:
			# handle events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					done = True
				current_room.handle_pygame_event(event)
		
			# step
			current_room.step()

			# draw
			current_room.draw(GameGlobals().win)

			if current_room.is_ready_to_switch():
				# switch room
				switch = current_room.switch
				current_room.switch = None
				if switch.craete_new_room:
					new_room = rooms_creation_dict[switch.next_room](input=switch.room_input)
					rooms_dict[switch.next_room] = new_room
					current_room = new_room
				else:
					if switch.next_room == Rooms.EXIT:
						done = True
						break
					existing_room = rooms_dict[switch.next_room]
					current_room = existing_room
					current_room.on_resume(input=switch.room_input)
				
		except Exception:
			print(traceback.format_exc())

		pygame.transform.scale(GameGlobals().win, screen.get_rect().size, screen)
		pygame.display.update()

		fps_clock.tick(GameGlobals().fps)

	pygame.quit()


if __name__ == "__main__":
	main()
	
