


import pygame
import pygame.gfxdraw

from common import *
from common.vector import Vector

from rooms.room import Room, Rooms, SwitchRoom
from rooms.room_pause import PauseRoomInfo

from game.time_manager import TimeManager
from game.map_manager import MapManager
from game.visual_effects import FloatingText
from game.team_manager import TeamManager
from game.world_effects import Earthquake

from entities.worm import Worm

from weapons.weapon_manager import WeaponManager
from weapons.weapon import WeaponCategory, WeaponStyle
from weapons.missiles import DrillMissile
from weapons.long_bow import LongBow

from game.game_manager import Game


def on_key_press_right():
	GameVariables().player.turn(RIGHT)

def on_key_press_left():
	GameVariables().player.turn(LEFT)

def on_key_press_space():
	# release worm_tool
	if GameVariables().game_state == GameState.PLAYER_RETREAT:
		worm_tool = GameVariables().player.get_tool()
		if worm_tool is not None:
			worm_tool.release()

def on_key_press_tab():
	if WeaponManager().current_weapon.name == "drill missile":
		DrillMissile.mode = not DrillMissile.mode
		if DrillMissile.mode:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "drill mode", (20,20,20))
		else:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "rocket mode", (20,20,20))
		WeaponManager().render_weapon_count()
	elif WeaponManager().current_weapon.name == "long bow":
		LongBow._sleep = not LongBow._sleep
		if LongBow._sleep:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "sleeping", (20,20,20))
		else:
			FloatingText(GameVariables().player.pos + Vector(0,-5), "regular", (20,20,20))
	elif WeaponManager().current_weapon.name == "girder":
		GameVariables().girder_angle += 45
		if GameVariables().girder_angle == 180:
			GameVariables().girder_size = 100
		if GameVariables().girder_angle == 360:
			GameVariables().girder_size = 50
			GameVariables().girder_angle = 0
	elif WeaponManager().current_weapon.is_fused:
		GameVariables().fuse_time += GameVariables().fps
		if GameVariables().fuse_time > GameVariables().fps * 4:
			GameVariables().fuse_time = GameVariables().fps
		string = "delay " + str(GameVariables().fuse_time // GameVariables().fps) + " sec"
		FloatingText(GameVariables().player.pos + Vector(0, -5), string, (20, 20, 20))
		WeaponManager().render_weapon_count()
	elif WeaponManager().current_weapon.category == WeaponCategory.AIRSTRIKE:
		GameVariables().airstrike_direction *= -1
 
def on_key_press_test():
	''' test '''
	GameVariables().debug_print()
	# print(WeaponManager().weapon_director.actors)

def on_key_press_enter():
	# jump
	if GameVariables().player.stable and GameVariables().player.health > 0:
		GameVariables().player.vel += GameVariables().player.get_shooting_direction() * JUMP_VELOCITY
		GameVariables().player.stable = False


class GameRoom(Room):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		config = kwargs.get('input')
		self.game_manager = Game(config)

		# refactor these
		damage_this_turn = GameVariables().stats.get_stats()['damage_this_turn']
		self.damage_text = (damage_this_turn, fonts.pixel5_halo.render(str(int(damage_this_turn)), False, GameVariables().initial_variables.hud_color))
	
	def handle_pygame_event(self, event) -> None:
		''' handle pygame events in game '''
		super().handle_pygame_event(event)
		is_handled = self.game_manager.handle_event(event)
		if is_handled:
			return
		GameVariables().handle_event(event)
		if event.type == pygame.QUIT:
			self.switch = SwitchRoom(Rooms.EXIT, False, None)
			return
		# mouse click event
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # left click (main)
			pass

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2: # middle click (tests)
			pass
		
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: # right click (secondary)
			if GameVariables().game_state == GameState.PLAYER_PLAY:
				if self.game_manager.radial_weapon_menu is None:
					if WeaponManager().can_switch_weapon():
						self.game_manager.weapon_menu_init()
				else:
					self.game_manager.radial_weapon_menu = None
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # scroll down
			if not self.game_manager.radial_weapon_menu:
				GameGlobals().scale_factor *= 1.1
				GameGlobals().scale_factor = GameGlobals().scale_factor
				GameGlobals().scale_factor = min(GameGlobals().scale_factor, GameGlobals().scale_range[1])
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # scroll up
			if not self.game_manager.radial_weapon_menu:
				GameGlobals().scale_factor *= 0.9
				GameGlobals().scale_factor = GameGlobals().scale_factor
				GameGlobals().scale_factor = max(GameGlobals().scale_factor, GameGlobals().scale_range[0])

		# key press
		if event.type == pygame.KEYDOWN:
			# controll worm, jump and facing
				if GameVariables().player is not None and GameVariables().is_player_in_control():
					if event.key == pygame.K_RETURN:
						on_key_press_enter()
					if event.key == pygame.K_RIGHT:
						on_key_press_right()
					if event.key == pygame.K_LEFT:
						on_key_press_left()
				# fire on key press
				if event.key == pygame.K_SPACE:
					on_key_press_space()
				# weapon change by keyboard
				# misc
				if event.key == pygame.K_ESCAPE:
					# switch to pause menu
					pause_info = PauseRoomInfo(
						teams_score=TeamManager().get_info(),
						round_count=GameVariables().game_round_count
						)
					self.switch = SwitchRoom(Rooms.PAUSE_MENU, True, pause_info)
				if event.key == pygame.K_TAB:
					on_key_press_tab()
				if event.key == pygame.K_t:
					on_key_press_test()
				if event.key == pygame.K_F2:
					Worm.healthMode = (Worm.healthMode + 1) % 2
					if Worm.healthMode == 1:
						for worm in GameVariables().get_worms():
							worm.healthStr = fonts.pixel5.render(str(worm.health), False, worm.team.color)
				if event.key == pygame.K_F3:
					MapManager().draw_ground_secondary = not MapManager().draw_ground_secondary
				if event.key == pygame.K_m:
					pass
					# TimeSlow()
				if event.key in [pygame.K_RCTRL, pygame.K_LCTRL]:
					GameGlobals().scale_factor = GameGlobals().scale_range[1]
					if GameVariables().cam_track is None:
						GameVariables().cam_track = GameVariables().player

				self.game_manager.cheat_code += event.unicode
				if event.key == pygame.K_EQUALS:
					self.game_manager.cheat_activate(self.game_manager.cheat_code)
					self.game_manager.cheat_code = ""

	def step(self):
		''' game step '''

		GameVariables().state_machine.step()
		if GameVariables().game_end:
			self.switch = SwitchRoom(Rooms.MAIN_MENU, False, GameVariables().game_record)
			return

		if GameVariables().game_state in [GameState.RESET]:
			return

		# edge map scroll
		if pygame.mouse.get_focused():
			mouse_pos = pygame.mouse.get_pos()
			scroll = Vector()
			if mouse_pos[0] < EDGE_BORDER:
				scroll.x -= MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if mouse_pos[0] > GameGlobals().screen_width - EDGE_BORDER:
				scroll.x += MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if mouse_pos[1] < EDGE_BORDER:
				scroll.y -= MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if mouse_pos[1] > GameGlobals().screen_height - EDGE_BORDER:
				scroll.y += MAP_SCROLL_SPEED * (2.5 - GameGlobals().scale_factor / 2)
			if scroll != Vector():
				GameVariables().cam_track = Camera(GameVariables().cam_pos + Vector(GameGlobals().win_width, GameGlobals().win_height)/2 + scroll)
		
		# handle scale:
		old_size = (GameGlobals().win_width, GameGlobals().win_height)
		GameGlobals().win_width += (GameGlobals().screen_width / GameGlobals().scale_factor - GameGlobals().win_width) * 0.2
		GameGlobals().win_height += (GameGlobals().screen_height / GameGlobals().scale_factor - GameGlobals().win_height) * 0.2
		GameGlobals().win_width = int(GameGlobals().win_width)
		GameGlobals().win_height = int(GameGlobals().win_height)

		if old_size != (GameGlobals().win_width, GameGlobals().win_height):
			GameGlobals().win = pygame.Surface((GameGlobals().win_width, GameGlobals().win_height))
		
		# handle position:
		if GameVariables().cam_track:
			GameVariables().cam_pos += (
				(
					GameVariables().cam_track.pos - Vector(int(GameGlobals().screen_width / GameGlobals().scale_factor),
					int(GameGlobals().screen_height / GameGlobals().scale_factor)) / 2
				) - GameVariables().cam_pos
			) * 0.2

		# constraints:
		if GameVariables().cam_pos[1] < 0:
			GameVariables().cam_pos[1] = 0
		if GameVariables().cam_pos[1] >= MapManager().game_map.get_height() - GameGlobals().win_height:
			GameVariables().cam_pos[1] = MapManager().game_map.get_height() - GameGlobals().win_height


		if Earthquake.earthquake > 0:
			Earthquake.quake()
		
		self.game_manager.step()
		GameVariables().game_stable = True

		GameVariables().step_physicals()
		GameVariables().step_non_physicals()
		GameVariables().step()

		# step effects
		EffectManager().step()
		
		# step weapon manager
		WeaponManager().step()

		# step time manager
		TimeManager().step()
		GameVariables().hud.step()
		TeamManager().step()

		# step background
		self.game_manager.background.step()
		
		# step game mode
		GameVariables().game_mode.step()

		# camera for wait to stable:
		if GameVariables().game_state == GameState.WAIT_STABLE and GameVariables().time_overall % 20 == 0:
			for worm in GameVariables().get_worms():
				if worm.stable:
					continue
				GameVariables().cam_track = worm
				break
				
		# menu step
		if self.game_manager.radial_weapon_menu:
			self.game_manager.radial_weapon_menu.step()

		GameVariables().commentator.step()
	
	def draw(self, win: pygame.Surface) -> None:
		''' draw game '''
		super().draw(win)

		if GameVariables().game_state == GameState.RESET:
			return

		# draw background
		self.game_manager.background.draw(win)

		# draw map
		MapManager().draw_land(win)

		# draw objects
		for p in GameVariables().get_physicals(): 
			p.draw(win)
		
		GameVariables().draw_non_physicals(win)

		# draw effects
		EffectManager().draw(win)

		# draw top layer of background
		self.game_manager.background.draw_secondary(win)
		
		# draw shooting indicator
		if GameVariables().player is not None and GameVariables().game_state in [GameState.PLAYER_PLAY, GameState.PLAYER_RETREAT] and GameVariables().player.health > 0:
			GameVariables().player.draw_cursor(win)
			# draw aim aid
			if GameVariables().aim_aid and WeaponManager().current_weapon.style == WeaponStyle.GUN:
				p1 = vectorCopy(GameVariables().player.pos)
				p2 = p1 + GameVariables().player.get_shooting_direction() * 500
				pygame.draw.line(win, (255,0,0), point2world(p1), point2world(p2))

		# draw weapon indicators
		WeaponManager().draw_weapon_hint(win)

		# draw extra
		GameVariables().draw_extra(win)
		GameVariables().draw_layers(win)
		
		# draw game play mode
		GameVariables().game_mode.draw(win)

		# draw HUD
		GameVariables().hud.draw(win)
		TimeManager().draw(win)
		GameVariables().commentator.draw(win)
		WeaponManager().draw(win)
		
		# draw health bar
		TeamManager().draw(win)
		
		# weapon menu:
		if self.game_manager.radial_weapon_menu:
			self.game_manager.radial_weapon_menu.draw(win)
		
		# debug:
		damage_this_turn = GameVariables().stats.get_stats()['damage_this_turn']
		if self.damage_text[0] != damage_this_turn:
			self.damage_text = (damage_this_turn, fonts.pixel5_halo.render(str(int(damage_this_turn)), False, GameVariables().initial_variables.hud_color))
		win.blit(self.damage_text[1], ((int(5), int(GameGlobals().win_height -5 -self.damage_text[1].get_height()))))
