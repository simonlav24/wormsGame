''' gui module for pygame '''

from abc import ABC
from typing import List, Tuple, Any, Protocol
from enum import Enum

import pygame

from common import GameVariables, fonts, GameGlobals
from common.vector import Vector, tup2vec

class Gui:
    def __init__(self):
        self.toaster = Toaster()
        self.menus: List[StackPanel] = []
        self.animators: List[AnimatorBase] = []
        self.event_que = []
    
    def show_cursor(self, cursor, element):
        pygame.mouse.set_cursor(cursor)
    
    def listen(self) -> Tuple[Any, Any]:
        if len(self.event_que) > 0:
            event = self.event_que.pop(0)
            return event, self.get_values()
        return (None, None)

    def notify_event(self, event):
        self.event_que.append(event)

    def get_super_pos(self) -> Vector:
        return Vector()

    def get_values(self):
        ''' check for gui events '''
        values = {}
        for menu in self.menus:
            menu_values = menu.get_values()
            values |= menu_values
        return values

    def handle_pygame_event(self, event):
        for menu in self.menus:
            menu.handle_pygame_event(event)

    def insert(self, menu):
        menu.set_gui(self)
        self.menus.append(menu)

    def step(self):
        for menu in self.menus:
            menu.step()
        for animation in self.animators:
            animation.step()
        self.animators = [animator for animator in self.animators if not animator.is_done]

        self.toaster.step()
    
    def draw(self, win: pygame.Surface) -> None:
        for menu in self.menus:
            menu.draw(win)
        self.toaster.draw(win)

HORIZONTAL = 0
VERTICAL = 1

WHITE = (255,255,255,255)
BLACK = (0,0,0,255)

BUTTON_COLOR = (82,65,60)
TEXT_ELEMENT_COLOR = (62,45,40)
TOGGLE_COLOR = (0,255,0)
SELECTED_COLOR = (0,180,0)
SUB_BUTTON_COLOR = (182,165,160)
SUB_SELECTED_COLOR = (255,255,255)

def mouse_in_win():
    mouse = pygame.mouse.get_pos()
    return Vector(mouse[0] / GameGlobals().scale_factor, mouse[1] / GameGlobals().scale_factor)

class IParent:
    def notify_event(self, event) -> None:
        ...

    def get_super_pos(self) -> Vector:
        ...

class GuiElement(ABC):
    def __init__(self, *args, **kwargs):
        self.pos = kwargs.get('pos', Vector())
        self.size = kwargs.get('size', Vector())
        self.name = kwargs.get('name', "element")
        self.custom_size = kwargs.get('custom_size', None)
        self.color = BUTTON_COLOR
        self.selected = False
        self.key = kwargs.get('key', 'key')
        self.value = kwargs.get('value', 'value')
        self.parent: IParent = None
        self.surf = None
        self.tooltip = kwargs.get('tool_tip', None)
        self.cursor = pygame.SYSTEM_CURSOR_ARROW
        self.highlight_value = 0.0
        self.gui: Gui = None
    
    def recalculate(self):
        pass

    def set_gui(self, gui: Gui):
        self.gui = gui
    
    def handle_pygame_event(self, event):
        pass

    def get_values(self):
        return {self.key: self.value}

    def get_super_pos(self) -> Vector:
        return self.parent.get_super_pos()

    def render_surf(self, text=None):
        if text == "":
            text="input"
        if text:
            self.text = text
        self.surf = fonts.pixel5.render(self.text, True, WHITE)
        
    def draw_rect(self, win: pygame.Surface) -> None:
        button_pos = self.get_super_pos() + self.pos
        color = [self.color[i] * (1 - self.highlight_value) + SELECTED_COLOR[i] * self.highlight_value for i in range(3)]
        pygame.draw.rect(win, color, (button_pos, self.size))
    
    def draw_text(self, win: pygame.Surface) -> None:
        button_pos = self.get_super_pos() + self.pos
        if self.surf:
            win.blit(self.surf, (button_pos[0] + self.size[0]/2 - self.surf.get_width()/2, button_pos[1] + self.size[1]/2 - self.surf.get_height()/2))
    
    def step(self):
        pass

    def selection_check(self):
        ''' check if mouse on button '''
        mouse_pos = mouse_in_win()
        button_pos = self.get_super_pos() + self.pos
        pos_in_button = mouse_pos - button_pos
        if pos_in_button[0] >= 0 and pos_in_button[0] < self.size[0] and pos_in_button[1] >= 0 and pos_in_button[1] < self.size[1]:
            self.selected = True
        else:
            self.selected = False

    def highlight_check(self):
        ''' if selected, modify highlight_value '''
        if self.selected:
            self.highlight_value = self.highlight_value + (1 - self.highlight_value) * 0.3
        else:
            self.highlight_value = self.highlight_value + (0 - self.highlight_value) * 0.3
    
    def draw(self, win: pygame.Surface) -> None:
        self.draw_rect(win)
        self.draw_text(win)
    
    def notify_event(self, event) -> None:
        self.parent.notify_event(event)

class StackPanel(GuiElement):
    def __init__(self, pos=None, size=None, name="", orientation=VERTICAL, margin=1, custom_size=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pos = Vector()
        if pos:
            self.pos = tup2vec(pos)
        self.size = Vector()
        if size:
            self.size = tup2vec(size)
        self.name = name
        self.elements: List[GuiElement] = []
        self.orientation = orientation
        self.event = None
        self.margin = margin # distance between elements
        self.custom_size = custom_size
        self.offset = None
        self.gui: Gui = None
    
    def handle_pygame_event(self, event):
        for element in self.elements:
            element.handle_pygame_event(event)

    def get_super_pos(self):
        if self.parent:
            return self.parent.get_super_pos() + self.pos
        return self.pos
    
    def set_gui(self, gui: Gui):
        self.gui = gui
        for element in self.elements:
            element.set_gui(gui)

    def get_values(self):
        values = {}
        for element in self.elements:
            element_values = element.get_values()
            values |= element_values
        return values

    def add_element(self, new_element: GuiElement):
        new_element.parent = self
        self.elements.append(new_element)
        self.recalculate()
        
    def recalculate(self):
        num_elements = len(self.elements)
        custom_sized_elements = [i for i in self.elements if i.custom_size]
        custom_sized_portion = sum(i.custom_size for i in custom_sized_elements)
        empty_space = self.size[self.orientation] - custom_sized_portion - (num_elements - 1) * self.margin
        size_per_element = 0
        if num_elements - len(custom_sized_elements) != 0:
            size_per_element = empty_space / (num_elements - len(custom_sized_elements))
        acc_size = 0
        for element in self.elements:
            element.size[0] = self.size[0]
            element.size[1] = self.size[1]
            if element.custom_size:
                element.size[self.orientation] = element.custom_size
            else:
                element.size[self.orientation] = size_per_element

            element.pos[self.orientation] = acc_size
            acc_size += element.size[self.orientation] + self.margin
        for element in self.elements:
            element.recalculate()
        
    def step(self):
        for element in self.elements:
            element.step()
    
    def update(self):
        pass
            
    def draw(self, win: pygame.Surface) -> None:
        for element in self.elements:
            element.draw(win)
    
    def insert(self, element: GuiElement):
        self.add_element(element)
        return element

class Text(GuiElement):
    def __init__(self, text='text', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.render_surf(self.text)
        self.color = TEXT_ELEMENT_COLOR

class Button(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get('text', "Bu")
        self.surf = None
        self.render_surf(self.text)
        self.cursor = pygame.SYSTEM_CURSOR_HAND
        self.event = None
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.event = self.key
                self.gui.notify_event(self.event)
    
    def get_values(self):
        return {}

    def step(self):
        self.selection_check()
        self.highlight_check()
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
    
class UpDown(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get('text', "")
        # show value = true: the value of the updown will be rendered. False: the text will be renderd
        self.show_value = kwargs.get('show_value', True)
        self.mode = 0
        self.mapping = kwargs.get('mapping', {})
        if self.show_value:
            self.render_surf(str(self.mapping.get(self.value, self.value)))
        else:
            self.render_surf(self.text)
        self.limit_min = kwargs.get('limit_min', False)
        self.limit_max = kwargs.get('limit_max', False)
        self.lim_min = kwargs.get('lim_min', 0)
        self.lim_max = kwargs.get('lim_max', 100)
        self.values = kwargs.get('values', None)
        self.step_size = kwargs.get('step_size', 1)
        self.generate_event: bool = kwargs.get('generate_event', False)
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.advance()
                if self.generate_event:
                    self.gui.notify_event(self.key)

    def get_values(self):
        return {self.key: self.value}

    def update_value(self, value):
        self.value = value
        self.render_surf(str(self.mapping.get(self.value, self.value)))

    def advance(self):
        if self.values:
            current = self.values.index(self.value)
            current = (current + 1) % len(self.values)
            self.value = self.values[current]
            return
        pot = self.value + self.mode * self.step_size
        if self.limit_min and pot < self.lim_min:
            pot = self.lim_min
        if self.limit_max and pot > self.lim_max:
            pot = self.lim_max
        self.update_value(pot)
        
    
    def step(self):
        self.selection_check()
        self.highlight_check()
        mouse_pos = mouse_in_win()
        button_pos = self.get_super_pos() + self.pos
        pos_in_button = mouse_pos - button_pos
        if self.selected:
            if pos_in_button[1] > pos_in_button[0] * (self.size[1] / self.size[0]):
                self.mode = -1
            else:
                self.mode = 1
        else:
            self.selected = False
        self.highlight_check()
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        button_pos = self.get_super_pos() + self.pos
        border = 1
        arrow_size = self.size[1] // 2
        right_color = SUB_SELECTED_COLOR if self.selected and self.mode == 1 else SUB_BUTTON_COLOR
        left_color = SUB_SELECTED_COLOR if self.selected and not self.mode == 1 else SUB_BUTTON_COLOR
        pygame.draw.polygon(win, right_color, [(button_pos[0] + self.size[0] - arrow_size, button_pos[1] + border), (button_pos[0] + self.size[0] - border - 1, button_pos[1] + border), (button_pos[0] + self.size[0] - border - 1, button_pos[1] + arrow_size)])
        pygame.draw.polygon(win, left_color, [(button_pos[0] + border ,button_pos[1] + self.size[1] - arrow_size), (button_pos[0] + border, button_pos[1] + self.size[1] - border - 1), (button_pos[0] + arrow_size, button_pos[1] + self.size[1] - border - 1)])

class Toggle(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border = 1
        self.cursor = pygame.SYSTEM_CURSOR_HAND
        self.text = kwargs.get('text', "toggle")
        self.render_surf(self.text)
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.value = not self.value

    def get_values(self):
        return {self.key: self.value}
    
    def step(self):
        super().step()
        self.selection_check()
        self.highlight_check()

    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        button_pos = self.get_super_pos() + self.pos
        if self.value:
            pygame.draw.rect(win, TOGGLE_COLOR, ((button_pos[0] + self.border, button_pos[1] + self.border), (self.size[0] - 2 * self.border, self.size[1] - 2 * self.border)))
        self.draw_text(win)

class ComboSwitch(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surf = None
        self.current_index = 0
        self.items = kwargs.get('items', [])
        self.text = kwargs.get('text', 'combo')
        if self.items:
            self.set_items(self.items, kwargs.get('mapping', None))
            self.set_current_item(self.text)
        self.forward = False
    
    def get_values(self):
        return {self.key: self.value}
    
    def set_items(self, strings, mapping=None):
        self.items = []
        self.mapping = {} if mapping is None else mapping
        for string in strings:
            string_to_render = string
            if string in self.mapping.keys():
                string_to_render = self.mapping[string]
            surf = fonts.pixel5.render(string_to_render, True, WHITE)
            self.items.append((string, surf))
        self.value = self.items[self.current_index][0]
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.advance()

    def render_surf(self, text):
        return
    
    def set_current_item(self, item):
        for i, it in enumerate(self.items):
            if it[0] == item:
                self.current_index = i
                break
        self.value = self.items[self.current_index][0]
    
    def step(self):
        mouse_pos = mouse_in_win()
        button_pos = self.get_super_pos() + self.pos
        pos_in_button = (mouse_pos[0] - button_pos[0], mouse_pos[1] - button_pos[1])
        if pos_in_button[0] >= 0 and pos_in_button[0] < self.size[0] and pos_in_button[1] >= 0 and pos_in_button[1] < self.size[1]:
            self.selected = True
            self.highlight_value = self.highlight_value + (1 - self.highlight_value) * 0.3
            if pos_in_button[0] > self.size[0] // 2:
                self.forward = True
            else:
                self.forward = False
            return self
        
        self.selected = False
        self.highlight_value = self.highlight_value + (0 - self.highlight_value) * 0.3
        return None
    
    def advance(self):
        addition = 1 if self.forward else -1
        self.current_index = (self.current_index + addition) % len(self.items)
        self.value = self.items[self.current_index][0]
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        button_pos = self.get_super_pos() + self.pos
        surf = self.items[self.current_index][1]
        win.blit(surf, (button_pos[0] + self.size[0]/2 - surf.get_width()/2, button_pos[1] + self.size[1]/2 - surf.get_height()/2))
        arrow_border = 3
        arrow_size = self.size[1]
        polygon_right = [Vector(self.size[0] - arrow_size / 2, arrow_border), Vector(self.size[0] - arrow_border, self.size[1] / 2), Vector(self.size[0] - arrow_size / 2, self.size[1] - arrow_border)]
        polygon_left = [Vector(arrow_size / 2, arrow_border), Vector(arrow_border, self.size[1] / 2), Vector(arrow_size / 2, self.size[1] - arrow_border)]
        right_color = SUB_SELECTED_COLOR if self.selected and self.forward else SUB_BUTTON_COLOR
        left_color = SUB_SELECTED_COLOR if self.selected and not self.forward else SUB_BUTTON_COLOR
        pygame.draw.polygon(win, right_color, [button_pos + i for i in polygon_right])
        pygame.draw.polygon(win, left_color, [button_pos + i for i in polygon_left])

class ImageButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_surf = None
        self.tooltip = None
    
    def set_image(self, image, rect=None, background=None):
        self.image_surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        if background:
            self.image_surf.fill(background)
        self.image_surf.blit(image, (0, 0), rect)
    
    def get_values(self):
        return {self.key: self.value}

    def draw(self, win: pygame.Surface) -> None:
        button_pos = self.get_super_pos() + self.pos
        win.blit(self.image_surf, (button_pos[0], button_pos[1]))

class ImageDrag(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image = kwargs.get('image')
        self.image_surf = None
        self.image_path = None
        self.set_image(image)
        self.drag_dx = 0
        self.dragging = False
        self.mouse_last: Vector = None
    
    def recalculate(self):
        self.set_image(self.image_path)
    
    def set_image(self, path):
        if path is None:
            return
        if self.size[0] < 0 or self.size[1] < 0:
            return
        self.surf = pygame.Surface(self.size, pygame.SRCALPHA)
        self.image_path = path
        self.value = path
        self.image_surf = pygame.image.load(path).convert()
        ratio = self.image_surf.get_width() / self.image_surf.get_height()
        image_size = (self.size[1] * ratio, self.size[1])
        self.image_surf = pygame.transform.smoothscale(self.image_surf, (image_size[0], image_size[1]))
        self.image_surf.set_colorkey((0,0,0))
        self.drag_dx = - self.image_surf.get_width() // 2
        self.recalc_image()
    
    def draw(self, win: pygame.Surface) -> None:
        button_pos = self.get_super_pos() + self.pos
        win.blit(self.surf, button_pos)
        pygame.draw.rect(win, BUTTON_COLOR, (button_pos, self.surf.get_size()), 2)
    
    def get_values(self):
        return {self.key: self.value}

    def recalc_image(self):
        self.surf.fill((0,0,0,0))
        self.surf.blit(self.image_surf, (self.size[0] // 2  + self.drag_dx, 0))

    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.dragging = True
                self.mouse_last = mouse_in_win()
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

    def step(self):
        self.selection_check()
        if self.dragging:
            mouse_pos = mouse_in_win()
            mouse_delta = mouse_pos - self.mouse_last
            self.mouse_last = mouse_pos

            self.drag_dx += mouse_delta[0]
            if self.drag_dx > -self.size[0] // 2:
                self.drag_dx = -self.size[0] // 2
            elif self.drag_dx < -self.image_surf.get_width() + self.size[0] // 2:
                self.drag_dx = -self.image_surf.get_width() + self.size[0] // 2
            self.recalc_image()

class SurfElement(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surf = None

    def set_surf(self, surf):
        self.surf = surf
    
    def draw(self, win: pygame.Surface) -> None:
        button_pos = self.get_super_pos() + self.pos
        win.blit(self.surf, button_pos)
        pygame.draw.rect(win, BUTTON_COLOR, (button_pos, self.surf.get_size()), 2)

class InputMode(Enum):
    IDLE = 0
    EDIT = 1

class Input(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = InputMode.IDLE
        self.input_text = ""
        self.old_input_text = ""
        self.value = self.input_text
        self.default_value = kwargs.get('default_value', '')
        self.text = kwargs.get('text', '')
        self.surf = None
        self.render_surf(self.text)
        self.cursor_speed = GameVariables().fps // 4
        self.show_cursor = False
        self.timer = 0
        self.cursor_surf = fonts.pixel5.render("|", True, (255,255,255))
        self.cursor = pygame.SYSTEM_CURSOR_IBEAM
        self.eval_type = kwargs.get('eval_type', 'str')
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.selected:
                self.mode = InputMode.EDIT
            else:
                self.mode = InputMode.IDLE
        
        if event.type == pygame.KEYDOWN:
            if self.mode == InputMode.EDIT:
                self.process_key(event)

    def process_key(self, event):
        if event.key == pygame.K_BACKSPACE and len(self.input_text) > 0:
            self.input_text = self.input_text[:-1]
        elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
            self.mode = InputMode.IDLE
        else:
            self.input_text += event.unicode
        self.value = self.input_text
    
    def get_values(self):
        value = self.value
        if self.eval_type == 'int':
            if self.value == '':
                self.value = self.default_value
            value = int(self.value)
        return {self.key: value}
    
    def step(self):
        if self.mode == InputMode.EDIT:
            self.timer += 1
            if self.timer >= self.cursor_speed:
                self.show_cursor = not self.show_cursor
                self.timer = 0
            if self.input_text != self.old_input_text:
                render_text = self.input_text
                if render_text == '':
                    render_text = self.text
                self.surf = fonts.pixel5.render(render_text, True, WHITE)
                self.old_input_text = self.input_text
        mouse_pos = mouse_in_win()
        button_pos = self.get_super_pos() + self.pos
        pos_in_button = (mouse_pos[0] - button_pos[0], mouse_pos[1] - button_pos[1])
        if pos_in_button[0] >= 0 and pos_in_button[0] < self.size[0] and pos_in_button[1] >= 0 and pos_in_button[1] < self.size[1]:
            self.selected = True
            return self
        self.selected = False
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        button_pos = self.get_super_pos() + self.pos

        if self.mode == InputMode.EDIT and self.show_cursor:
            win.blit(self.cursor_surf, (button_pos[0] + self.size[0]/2 - self.surf.get_width()/2 + self.surf.get_width(), button_pos[1] + self.size[1]/2 - self.surf.get_height()/2))

class LoadBar(GuiElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bar_color = kwargs.get('color', (255,255,0))
        self.value = kwargs.get('value', 0)
        self.max_value = kwargs.get('max_value', 100)
        self.direction = 1
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        button_pos = self.get_super_pos() + self.pos
        # calculate size
        if self.max_value == 0:
            print("division by zero error")
            return
        size = Vector(self.size[0] * (self.value / self.max_value), self.size[1])

        # draw bar left to right direction
        if self.direction == 1:
            pygame.draw.rect(win, TEXT_ELEMENT_COLOR, (button_pos, self.size), 2)
            pygame.draw.rect(win, self.bar_color, (button_pos + Vector(2,2), size - Vector(4,4)))
        # draw bar right to left direction
        else:
            pygame.draw.rect(win, TEXT_ELEMENT_COLOR, (button_pos + Vector(self.size[0] - size[0], 0), size), 2)
            pygame.draw.rect(win, self.bar_color, (button_pos + Vector(self.size[0] - size[0] + 2, 2), size - Vector(4,4)))

class AnimatorBase:
    def __init__(self) -> None:
        self.is_done = False
    
    def step(self) -> None:
        pass

    def finish(self) -> None:
        self.is_done = True

class MenuAnimator(AnimatorBase):
    def __init__(self, menu, pos_start, pos_end, trigger=None, args=None, ease="inout", end_return = False):
        super().__init__()
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.timer = 0
        self.full_time = GameVariables().fps * 1
        self.trigger = trigger
        self.args = args
        self.initial_menu_pos = menu.pos
        self.end_return = end_return
        
        self.menu = menu
        self.ease = ease
        # set first positions
        menu.pos = pos_start
    
    def ease_in(self, t):
        return t * t
    
    def ease_out(self, t):
        return 1 - (1 - t) * (1 - t)
    
    def ease_in_out(self, t):
        if t < 0.5:
            return 2 * t * t
        return 1 - (2 * (1 - t)) * (1 - t)
    
    def step(self):
        super().step()
        if self.ease == "in":
            ease = self.ease_out(self.timer / self.full_time)
        elif self.ease == "out":
            ease = self.ease_in(self.timer / self.full_time)
        elif self.ease == "inout":
            ease = self.ease_in_out(self.timer / self.full_time)
        self.menu.pos = self.pos_end * ease + (1 - ease) * self.pos_start
        self.timer += 1
        if self.timer > self.full_time:
            self.finish()
    
    def finish(self):
        super().finish()
        self.menu.pos = self.pos_end
        if self.end_return:
            self.menu.pos = self.initial_menu_pos
        if self.trigger:
            if self.args:
                self.trigger(*self.args)
            else:
                self.trigger()

class ElementAnimator:
    def __init__(self, element, start, end, duration = -1, time_offset=0):
        self.element = element
        self.start = start
        self.end = end
        self.timer = -time_offset
        self.full_time = duration
        if self.full_time == -1:
            self.duration = GameVariables().fps * 1
        self.is_done = False
        
    def step(self):
        self.timer += 1
        if self.timer < 0:
            return
        self.element.value = self.start + (self.end - self.start) * (self.timer / self.full_time)
        if self.timer > self.full_time:
            self.element.value = self.end
            self.is_done = True

class Toaster:
    def __init__(self):
        self.toast_surf = None
        self.timer = 0
        self.toase_state = "none"
        self.toast_pos = Vector(0,0)

        self.tooltip_surf = None
        self.tooltip_element = None
    
    def show_tooltip(self, element):
        text_surf = fonts.pixel5.render(element.tooltip, True, (255,255,255), (0,0,0))
        self.tooltip_surf = pygame.Surface((text_surf.get_width() + 2, text_surf.get_height() + 2))
        self.tooltip_surf.fill((0,0,0))
        self.tooltip_surf.blit(text_surf, (1,1))
        self.tooltip_element = element
    
    def hide_tool_tip(self):
        self.tooltip_surf = None
    
    def toast(self, text):
        text_surf = fonts.pixel5.render(text, True, (255,255,255), (0,0,0))
        self.toast_surf = pygame.Surface((text_surf.get_width() + 2, text_surf.get_height() + 2))
        self.toast_surf.fill((0,0,0))
        self.toast_surf.blit(text_surf, (1,1))

        self.toast_pos = Vector(win.get_width() // 2 - self.toast_surf.get_width() // 2, win.get_height())
        self.toase_state = "opening"
    
    def step(self):
        # toast
        if self.toase_state == "opening":
            self.toast_pos.y -= 1
            if self.toast_pos.y <= win.get_height() - 10 - self.toast_surf.get_height():
                self.toase_state = "showing"
                self.timer = 0
        elif self.toase_state == "showing":
            self.timer += 1
            if self.timer >= GameVariables().fps * 2:
                self.toase_state = "closing"
        elif self.toase_state == "closing":
            self.toast_pos.y += 1
            if self.toast_pos.y >= win.get_height():
                self.toase_state = "none"
                self.toast_surf = None
                self.timer = 0

        # tooltip
        if self.tooltip_element:
            if not self.tooltip_element.selected:
                self.hide_tool_tip()
                self.tooltip_element = None
    
    def draw(self, win: pygame.Surface) -> None:
        # toast
        if self.toast_surf:
            win.blit(self.toast_surf, self.toast_pos)

        # tooltip
        if self.tooltip_surf:
            mouse_pos = mouse_in_win()
            win.blit(self.tooltip_surf, mouse_pos + Vector(5,5))
