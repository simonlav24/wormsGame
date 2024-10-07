

from abc import ABC
from typing import List, Tuple, Any
from enum import Enum

import pygame

from common import GameVariables, fonts, GameGlobals
from common.vector import *

class Gui:
    def __init__(self):
        self.toaster = Toaster()
        self.focusElement = None
        self.menus: List[StackPanel] = []
        self.animators: List[AnimatorBase] = []
        self.event_que = []
    
    def showCursor(self, cursor, element):
        self.focusElement = element
        pygame.mouse.set_cursor(cursor)
    
    def listen(self) -> Tuple[Any, Any]:
        if len(self.event_que) > 0:
            event = self.event_que.pop(0)
            return event, self.get_values()
        return (None, None)

    def notify_event(self, event):
        self.event_que.append(event)

    def get_values(self):
        ''' check for gui events '''
        event = None
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

MENU_ELEMENT = -1
MENU_MENU   = 0
MENU_BUTTON = 1
MENU_UPDOWN = 2
MENU_TOGGLE = 3
MENU_COMBOS = 4
MENU_TEXT   = 5
MENU_DIV	= 6
MENU_DRAGIMAGE	= 7
MENU_INPUT	= 8
MENU_LOADBAR = 9
MENU_SURF = 10
MENU_IMAGE = 11

HORIZONTAL = 0
VERTICAL = 1

WHITE = (255,255,255,255)
BLACK = (0,0,0,255)

def mouseInWin():
    mouse = pygame.mouse.get_pos()
    return Vector(mouse[0] / GameGlobals().scale_factor, mouse[1] / GameGlobals().scale_factor)

class StackPanel:
    _buttonColor = (82,65,60)
    _textElementColor = (62,45,40)
    _toggleColor = (0,255,0)
    _selectedColor = (0,180,0)
    _subButtonColor = (182,165,160)
    _subSelectColor = (255,255,255)
    _dragging = False
    _offsetDrag = Vector()
    
    def __init__(self, pos=None, size=None, name="", orientation=VERTICAL, margin=1, register=False, customSize=None):
        self.pos = Vector()
        if pos:
            self.pos = tup2vec(pos)
        self.size = Vector()
        if size:
            self.size = tup2vec(size)
        self.name = name
        self.elements = []
        self.orientation = orientation
        self.focused = True
        self.event = None
        self.margin = margin # distance between elements
        self.type = MENU_MENU
        self.menu = None
        self.customSize = customSize
        self.offset = None
        self.gui: Gui = None
    
    def handle_pygame_event(self, event):
        for element in self.elements:
            element.handle_pygame_event(event)

    def getSuperPos(self):
        if self.menu:
            return self.menu.getSuperPos() + self.pos
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

    def addElement(self, newElement):
        newElement.menu = self
        self.elements.append(newElement)
        self.recalculate()
        
    def recalculate(self):
        numElements = len(self.elements)
        customSizedElements = [i for i in self.elements if i.customSize]
        CustomSizedPortion = sum(i.customSize for i in customSizedElements)
        emptySpace = self.size[self.orientation] - CustomSizedPortion - (numElements - 1) * self.margin
        if numElements - len(customSizedElements) != 0:
            sizePerElem = emptySpace / (numElements - len(customSizedElements))
        accSize = 0
        for element in self.elements:
            element.size[0] = self.size[0]
            element.size[1] = self.size[1]
            if element.customSize:
                element.size[self.orientation] = element.customSize
            else:
                element.size[self.orientation] = sizePerElem

            element.pos[self.orientation] = accSize
            accSize += element.size[self.orientation] + self.margin
        for element in self.elements:
            if element.type == MENU_MENU:
                element.recalculate()
            if element.type == MENU_DRAGIMAGE:
                element.setImage(element.imagePath)
    
    def getValues(self):
        values = {}
        for element in self.elements:
            values[element.key] = element.value
        return values
    
    def step(self):
        if not self.focused:
            return
        updated = False
        event = None
        for element in self.elements:
            result = element.step()
            if result:
                updated = True
                event = result
        self.event = event
        return event
    
    def update(self):
        pass
            
    def draw(self, win: pygame.Surface) -> None:
        for element in self.elements:
            element.draw(win)
    
    def insert(self, element):
        self.addElement(element)
        return element

class MenuElement(ABC):
    def __init__(self, *args, **kwargs):
        self.pos = kwargs.get('pos', Vector())
        self.size = kwargs.get('size', Vector())
        self.name = kwargs.get('name', "element")
        self.customSize = kwargs.get('customSize', None)
        self.color = StackPanel._buttonColor
        self.selected = False
        self.key = kwargs.get('key', 'key')
        self.value = kwargs.get('value', 'value')
        self.menu = None
        self.type = MENU_ELEMENT
        self.surf = None
        self.tooltip = kwargs.get('tool_tip', None)
        self.cursor = pygame.SYSTEM_CURSOR_ARROW
        self.highlight_value = 0.0
        self.gui: Gui = None
    
    def set_gui(self, gui: Gui):
        self.gui = gui
    
    def handle_pygame_event(self, event):
        pass

    def get_values(self):
        return {self.key: self.value}

    def getSuperPos(self):
        return self.menu.getSuperPos()
        
    def setIndex(self, num):
        self.index = num
    
    def renderSurf(self, text=None):
        if text == "":
            text="input"
        if text:
            self.text = text
        self.surf = fonts.pixel5.render(self.text, True, WHITE)
        
    def drawRect(self, win: pygame.Surface) -> None:
        buttonPos = self.getSuperPos() + self.pos
        color = [self.color[i] * (1 - self.highlight_value) + StackPanel._selectedColor[i] * self.highlight_value for i in range(3)]
        pygame.draw.rect(win, color, (buttonPos, self.size))
    
    def drawText(self, win: pygame.Surface) -> None:
        buttonPos = self.getSuperPos() + self.pos
        if self.surf:
            win.blit(self.surf, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2, buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))
    
    def drawHighLight(self):
        buttonPos = self.getSuperPos() + self.pos

    def step(self):
        pass

    def selection_check(self):
        ''' check if mouse on button '''
        mousePos = mouseInWin()
        buttonPos = self.getSuperPos() + self.pos
        posInButton = mousePos - buttonPos
        if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
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
        self.drawRect(win)
        self.drawText(win)

class MenuElementText(MenuElement):
    def __init__(self, text='text', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.renderSurf(self.text)
        self.color = StackPanel._textElementColor

class MenuElementButton(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get('text', "Bu")
        self.surf = None
        self.renderSurf(self.text)
        self.type = MENU_BUTTON
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
        return None
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
    
class MenuElementUpDown(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get('text', "")
        self.showValue = kwargs.get('showValue', False)
        self.mode = 0
        if self.showValue:
            self.renderSurf(str(self.value))
        else:
            self.renderSurf(self.text)
        self.type = MENU_UPDOWN
        self.limitMin = kwargs.get('limitMin', False)
        self.limitMax = kwargs.get('limitMax', False)
        self.limMin = kwargs.get('limMin', 0)
        self.limMax = kwargs.get('limMax', 100)
        self.values = kwargs.get('values', None)
        self.stepSize = kwargs.get('stepSize', 1)
        self.generate_event: bool = kwargs.get('generate_event', False)
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.advance()
                if self.generate_event:
                    self.gui.notify_event(self.key)

    def get_values(self):
        event = self.key if self.generate_event else None
        return {self.key: self.value}

    def advance(self):
        if self.values:
            current = self.values.index(self.value)
            current = (current + 1) % len(self.values)
            self.value = self.values[current]
            return
        pot = self.value + self.mode * self.stepSize
        if self.limitMin and pot < self.limMin:
            pot = self.limMin
        if self.limitMax and pot > self.limMax:
            pot = self.limMax
        self.value = pot
    
    def step(self):
        mousePos = mouseInWin()
        buttonPos = self.getSuperPos() + self.pos
        posInButton = mousePos - buttonPos
        if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
            self.selected = True
            if posInButton[1] > posInButton[0] * (self.size[1] / self.size[0]):
                self.mode = -1
            else:
                self.mode = 1
            if self.showValue:
                self.renderSurf(str(self.value))
        else:
            self.selected = False
        self.highlight_check()
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        buttonPos = self.getSuperPos() + self.pos
        border = 1
        arrowSize = self.size[1] // 2
        rightColor = StackPanel._subSelectColor if self.selected and self.mode == 1 else StackPanel._subButtonColor
        leftColor = StackPanel._subSelectColor if self.selected and not self.mode == 1 else StackPanel._subButtonColor
        pygame.draw.polygon(win, rightColor, [(buttonPos[0] + self.size[0] - arrowSize, buttonPos[1] + border), (buttonPos[0] + self.size[0] - border - 1, buttonPos[1] + border), (buttonPos[0] + self.size[0] - border - 1, buttonPos[1] + arrowSize)])
        pygame.draw.polygon(win, leftColor, [(buttonPos[0] + border ,buttonPos[1] + self.size[1] - arrowSize), (buttonPos[0] + border, buttonPos[1] + self.size[1] - border - 1), (buttonPos[0] + arrowSize, buttonPos[1] + self.size[1] - border - 1)])

class MenuElementToggle(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = MENU_TOGGLE
        self.border = 1
        self.cursor = pygame.SYSTEM_CURSOR_HAND
        self.text = kwargs.get('text', "toggle")
        self.renderSurf(self.text)
    
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
        buttonPos = self.getSuperPos() + self.pos
        if self.value:
            pygame.draw.rect(win, StackPanel._toggleColor, ((buttonPos[0] + self.border, buttonPos[1] + self.border), (self.size[0] - 2 * self.border, self.size[1] - 2 * self.border)))
        self.drawText(win)

class MenuElementComboSwitch(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surf = None
        self.currentIndex = 0
        self.type = MENU_COMBOS
        self.items = kwargs.get('items', [])
        self.text = kwargs.get('text', 'combo')
        if self.items:
            self.setItems(self.items)
            self.setCurrentItem(self.text)
        self.forward = False
        self.mapping = {}
    
    def get_values(self):
        return {self.key: self.value}
    
    def setItems(self, strings, mapping={}):
        self.items = []
        self.mapping = mapping
        for string in strings:
            stringToRender = string
            if string in self.mapping.keys():
                stringToRender = self.mapping[string]
            surf = fonts.pixel5.render(stringToRender, True, WHITE)
            self.items.append((string, surf))
        self.value = self.items[self.currentIndex][0]
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.advance()

    def renderSurf(self, string):
        return
    
    def setCurrentItem(self, item):
        for i, it in enumerate(self.items):
            if it[0] == item:
                self.currentIndex = i
                break
        self.value = self.items[self.currentIndex][0]
    
    def step(self):
        mousePos = mouseInWin()
        buttonPos = self.getSuperPos() + self.pos
        posInButton = (mousePos[0] - buttonPos[0], mousePos[1] - buttonPos[1])
        if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
            self.selected = True
            self.highlight_value = self.highlight_value + (1 - self.highlight_value) * 0.3
            # if self.tooltip: 
            #     Gui._instance.toaster.showToolTip(self)
            # Gui._instance.showCursor(pygame.SYSTEM_CURSOR_HAND, self)
            if posInButton[0] > self.size[0] // 2:
                self.forward = True
            else:
                self.forward = False
            return self
        else:
            self.selected = False
            self.highlight_value = self.highlight_value + (0 - self.highlight_value) * 0.3
        return None
    
    def advance(self):
        addition = 1 if self.forward else -1
        self.currentIndex = (self.currentIndex + addition) % len(self.items)
        self.value = self.items[self.currentIndex][0]
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        buttonPos = self.getSuperPos() + self.pos
        surf = self.items[self.currentIndex][1]
        win.blit(surf, (buttonPos[0] + self.size[0]/2 - surf.get_width()/2, buttonPos[1] + self.size[1]/2 - surf.get_height()/2))
        arrowBorder = 3
        arrowSize = self.size[1]
        polygonRight = [Vector(self.size[0] - arrowSize / 2, arrowBorder), Vector(self.size[0] - arrowBorder, self.size[1] / 2), Vector(self.size[0] - arrowSize / 2, self.size[1] - arrowBorder)]
        polygonLeft = [Vector(arrowSize / 2, arrowBorder), Vector(arrowBorder, self.size[1] / 2), Vector(arrowSize / 2, self.size[1] - arrowBorder)]
        rightColor = StackPanel._subSelectColor if self.selected and self.forward else StackPanel._subButtonColor
        leftColor = StackPanel._subSelectColor if self.selected and not self.forward else StackPanel._subButtonColor
        pygame.draw.polygon(win, rightColor, [buttonPos + i for i in polygonRight])
        pygame.draw.polygon(win, leftColor, [buttonPos + i for i in polygonLeft])

class MenuElementImage(MenuElementButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = MENU_IMAGE
        self.imageSurf = None
        self.tooltip = None
    
    def setImage(self, image, rect=None, background=None):
        self.imageSurf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        if background:
            self.imageSurf.fill(background)
        self.imageSurf.blit(image, (0, 0), rect)
    
    def get_values(self):
        return {self.key: self.value}

    def draw(self, win: pygame.Surface) -> None:
        buttonPos = self.getSuperPos() + self.pos
        win.blit(self.imageSurf, (buttonPos[0], buttonPos[1]))

class MenuElementDragImage(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image = kwargs.get('image')
        self.type = MENU_DRAGIMAGE
        self.imageSurf = None
        self.imagePath = None
        self.setImage(image)
        self.dragDx = 0
        self.draggable = True
    
    def setImage(self, path):
        if path is None:
            return
        if self.size[0] < 0 or self.size[1] < 0:
            return
        self.surf = pygame.Surface(self.size, pygame.SRCALPHA)
        self.imagePath = path
        self.value = path
        self.imageSurf = pygame.image.load(path).convert()
        ratio = self.imageSurf.get_width() / self.imageSurf.get_height()
        imageSize = (self.size[1] * ratio, self.size[1])
        self.imageSurf = pygame.transform.smoothscale(self.imageSurf, (imageSize[0], imageSize[1]))
        self.imageSurf.set_colorkey((0,0,0))
        self.dragDx = - self.imageSurf.get_width() // 2
        self.recalculateImage()
    
    def draw(self, win: pygame.Surface) -> None:
        buttonPos = self.getSuperPos() + self.pos
        win.blit(self.surf, buttonPos)
        pygame.draw.rect(win, StackPanel._buttonColor, (buttonPos, self.surf.get_size()), 2)
    
    def get_values(self):
        return {self.key: self.value}

    def recalculateImage(self):
        self.surf.fill((0,0,0,0))
        self.surf.blit(self.imageSurf, (self.size[0] // 2  + self.dragDx, 0))
    
    def step(self):
        mousePos = mouseInWin()
        buttonPos = self.getSuperPos() + self.pos
        posInButton = (mousePos[0] - buttonPos[0], mousePos[1] - buttonPos[1])
        if self.draggable:
            if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
                if pygame.mouse.get_pressed()[0]:
                    vel = pygame.mouse.get_rel()
                    if abs(vel[0]) > 100:
                        return
                    self.dragDx += vel[0] / GameGlobals().scale_factor
                    if self.imageSurf.get_width() < self.size[0]:
                        return
                    if self.dragDx > -self.size[0] // 2:
                        self.dragDx = -self.size[0] // 2
                    elif self.dragDx < -self.imageSurf.get_width() + self.size[0] // 2:
                        self.dragDx = -self.imageSurf.get_width() + self.size[0] // 2

                    self.recalculateImage()

class MenuElementSurf(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = MENU_SURF
        self.surf = None

    def set_surf(self, surf):
        self.surf = surf
    
    def draw(self, win: pygame.Surface) -> None:
        buttonPos = self.getSuperPos() + self.pos
        win.blit(self.surf, buttonPos)
        pygame.draw.rect(win, StackPanel._buttonColor, (buttonPos, self.surf.get_size()), 2)

class InputMode(Enum):
    IDLE = 0
    EDIT = 1

class MenuElementInput(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = InputMode.IDLE
        self.inputText = ""
        self.oldInputText = ""
        self.value = self.inputText
        self.default_value = kwargs.get('default_value', '')
        self.type = MENU_INPUT
        self.text = kwargs.get('text', '')
        self.surf = None
        self.renderSurf(self.text)
        self.cursorSpeed = GameVariables().fps // 4
        self.showCursor = False
        self.timer = 0
        self.cursorText = fonts.pixel5.render("|", True, (255,255,255))
        self.cursor = pygame.SYSTEM_CURSOR_IBEAM
        self.evaluatedType = kwargs.get('evaluatedType', 'str')
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.selected:
                self.mode = InputMode.EDIT
            else:
                self.mode = InputMode.IDLE
        
        if event.type == pygame.KEYDOWN:
            if self.mode == InputMode.EDIT:
                self.processKey(event)

    def processKey(self, event):
        if event.key == pygame.K_BACKSPACE and len(self.inputText) > 0:
            self.inputText = self.inputText[:-1]
        elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
            self.mode = InputMode.IDLE
        else:
            self.inputText += event.unicode
        self.value = self.inputText
    
    def get_values(self):
        value = self.value
        if self.evaluatedType == 'int':
            if self.value == '':
                self.value = self.default_value
            value = int(self.value)
        return {self.key: value}
    
    def step(self):
        if self.mode == InputMode.EDIT:
            self.timer += 1
            if self.timer >= self.cursorSpeed:
                self.showCursor = not self.showCursor
                self.timer = 0
            if self.inputText != self.oldInputText:
                render_text = self.inputText
                if render_text == '':
                    render_text = self.text
                self.surf = fonts.pixel5.render(render_text, True, WHITE)
                self.oldInputText = self.inputText
        mousePos = mouseInWin()
        buttonPos = self.getSuperPos() + self.pos
        posInButton = (mousePos[0] - buttonPos[0], mousePos[1] - buttonPos[1])
        if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
            # if self.tooltip:
            #     Gui._instance.toaster.showToolTip(self)
            # Gui._instance.showCursor(self.cursor, self)
            self.selected = True
            return self
        else:
            self.selected = False
        return None
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        buttonPos = self.getSuperPos() + self.pos

        if self.mode == InputMode.EDIT and self.showCursor:
            win.blit(self.cursorText, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2 + self.surf.get_width(), buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))

class MenuElementLoadBar(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = MENU_LOADBAR
        self.barColor = (255,255,0)
        self.value = 0
        self.maxValue = 100
        self.direction = 1
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        buttonPos = self.getSuperPos() + self.pos
        # calculate size
        if self.maxValue == 0:
            print("division by zero error")
            return
        size = Vector(self.size[0] * (self.value / self.maxValue), self.size[1])

        # draw bar left to right direction
        if self.direction == 1:
            pygame.draw.rect(win, StackPanel._textElementColor, (buttonPos, self.size), 2)
            pygame.draw.rect(win, self.barColor, (buttonPos + Vector(2,2), size - Vector(4,4)))
        # draw bar right to left direction
        else:
            pygame.draw.rect(win, StackPanel._textElementColor, (buttonPos + Vector(self.size[0] - size[0], 0), size), 2)
            pygame.draw.rect(win, self.barColor, (buttonPos + Vector(self.size[0] - size[0] + 2, 2), size - Vector(4,4)))

class AnimatorBase:
    def __init__(self) -> None:
        self.is_done = False
    
    def step(self) -> None:
        pass

    def finish(self) -> None:
        self.is_done = True

class MenuAnimator(AnimatorBase):
    def __init__(self, menu, posStart, posEnd, trigger=None, args=None, ease="inout", end_return = False):
        super().__init__()
        self.posStart = posStart
        self.posEnd = posEnd
        self.timer = 0
        self.fullTime = GameVariables().fps * 1
        self.trigger = trigger
        self.args = args
        self.initial_menu_pos = menu.pos
        self.end_return = end_return
        
        self.menu = menu
        self.ease = ease
        # set first positions
        menu.pos = posStart
    
    def easeIn(self, t):
        return t * t
    
    def easeOut(self, t):
        return 1 - (1 - t) * (1 - t)
    
    def easeInOut(self, t):
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - (2 * (1 - t)) * (1 - t)
    
    def step(self):
        super().step()
        if self.ease == "in":
            ease = self.easeOut(self.timer / self.fullTime)
        elif self.ease == "out":
            ease = self.easeIn(self.timer / self.fullTime)
        elif self.ease == "inout":
            ease = self.easeInOut(self.timer / self.fullTime)
        self.menu.pos = self.posEnd * ease + (1 - ease) * self.posStart
        self.timer += 1
        if self.timer > self.fullTime:
            self.finish()
    
    def finish(self):
        super().finish()
        self.menu.pos = self.posEnd
        if self.end_return:
            self.menu.pos = self.initial_menu_pos
        if self.trigger:
            if self.args:
                self.trigger(*self.args)
            else:
                self.trigger()

class ElementAnimator:
    def __init__(self, element, start, end, duration = -1, timeOffset=0):
        self.element = element
        self.start = start
        self.end = end
        self.timer = -timeOffset
        self.fullTime = duration
        if self.fullTime == -1:
            self.duration = GameVariables().fps * 1
        self.is_done = False
        
    def step(self):
        self.timer += 1
        if self.timer < 0:
            return
        self.element.value = self.start + (self.end - self.start) * (self.timer / self.fullTime)
        if self.timer > self.fullTime:
            self.element.value = self.end
            self.is_done = True

class Toaster:
    def __init__(self):
        self.toastSurf = None
        self.timer = 0
        self.toastState = "none"
        self.toastPos = Vector(0,0)

        self.tooltipSurf = None
        self.tooltipElement = None
    
    def showToolTip(self, element):
        textSurf = fonts.pixel5.render(element.tooltip, True, (255,255,255), (0,0,0))
        self.tooltipSurf = pygame.Surface((textSurf.get_width() + 2, textSurf.get_height() + 2))
        self.tooltipSurf.fill((0,0,0))
        self.tooltipSurf.blit(textSurf, (1,1))
        self.tooltipElement = element
    
    def hideToolTip(self):
        self.tooltipSurf = None
    
    def toast(self, text):
        textSurf = fonts.pixel5.render(text, True, (255,255,255), (0,0,0))
        self.toastSurf = pygame.Surface((textSurf.get_width() + 2, textSurf.get_height() + 2))
        self.toastSurf.fill((0,0,0))
        self.toastSurf.blit(textSurf, (1,1))

        self.toastPos = Vector(win.get_width() // 2 - self.toastSurf.get_width() // 2, win.get_height())
        self.toastState = "opening"
    
    def step(self):
        # toast
        if self.toastState == "opening":
            self.toastPos.y -= 1
            if self.toastPos.y <= win.get_height() - 10 - self.toastSurf.get_height():
                self.toastState = "showing"
                self.timer = 0
        elif self.toastState == "showing":
            self.timer += 1
            if self.timer >= GameVariables().fps * 2:
                self.toastState = "closing"
        elif self.toastState == "closing":
            self.toastPos.y += 1
            if self.toastPos.y >= win.get_height():
                self.toastState = "none"
                self.toastSurf = None
                self.timer = 0

        # tooltip
        if self.tooltipElement:
            if not self.tooltipElement.selected:
                self.hideToolTip()
                self.tooltipElement = None
    
    def draw(self, win: pygame.Surface) -> None:
        # toast
        if self.toastSurf:
            win.blit(self.toastSurf, self.toastPos)

        # tooltip
        if self.tooltipSurf:
            mousePos = mouseInWin()
            win.blit(self.tooltipSurf, mousePos + Vector(5,5))