

import pygame
from abc import ABC

from common import GameVariables, fonts, GameGlobals
from common.vector import *

class Gui:
    def __init__(self):
        self.toaster = Toaster()
        self.focusElement = None
        self.menus = []
        self.animators = []
        self.event_que = []
    
    def showCursor(self, cursor, element):
        self.focusElement = element
        pygame.mouse.set_cursor(cursor)
    
    def get_event_values(self):
        ''' check for gui events '''
        event = None
        values = {}
        for menu in self.menus:
            menu_event, menu_values = menu.get_event_values()
            if menu_event is not None:
                event = menu_event
            values |= menu_values
        return event, values

    def handle_pygame_event(self, event):
        for menu in self.menus:
            menu.handle_pygame_event(event)
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     for inp in MenuElementInput._reg:
        #         inp.mode = "fixed"
        #     if event.button == 1:
        #         for menu in StackPanel._reg:
        #             if menu.event:
        #                 menu.processInternalEvents()
        #                 handleMenuEvents(menu.event)
        # if event.type == pygame.KEYDOWN:
        #     for inp in MenuElementInput._reg:
        #         if inp.mode == "editing":
        #             inp.processKey(event)
        #             break

    def step(self):
        for menu in self.menus:
            menu.step()
        for animation in self.animators:
            animation.step()

        # if self.focusElement:
            # if not self.focusElement.selected:
                # pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                # self.focusElement = None
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
    
    def handle_pygame_event(self, event):
        for element in self.elements:
            element.handle_pygame_event(event)

    def getSuperPos(self):
        if self.menu:
            return self.menu.getSuperPos() + self.pos
        return self.pos
    
    def get_event_values(self):
        event = None
        values = {}
        for element in self.elements:
            element_event, element_values = element.get_event_values()
            if element_event is not None:
                event = element_event
            values |= element_values
        return event, values

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
        
    def evaluate(self, dic):
        for element in self.elements:
            element.evaluate(dic)
    
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
        self.animation_offset = 0
    
    def handle_pygame_event(self, event):
        pass

    def get_event_values(self):
        return None, {self.key: self.value}

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
    
    def evaluate(self, dic):
        dic[self.key] = self.value
    
    def drawRect(self, win: pygame.Surface) -> None:
        buttonPos = self.getSuperPos() + self.pos
        color = [self.color[i] * (1 - self.animation_offset) + StackPanel._selectedColor[i] * self.animation_offset for i in range(3)]
        pygame.draw.rect(win, color, (buttonPos, self.size))
    
    def drawText(self, win: pygame.Surface) -> None:
        buttonPos = self.getSuperPos() + self.pos
        if self.surf:
            win.blit(self.surf, (buttonPos[0] + self.size[0]/2 - self.surf.get_width()/2, buttonPos[1] + self.size[1]/2 - self.surf.get_height()/2))
    
    def drawHighLight(self):
        buttonPos = self.getSuperPos() + self.pos

    def step(self):
        pass
    
    def draw(self, win: pygame.Surface) -> None:
        self.drawRect(win)
        self.drawText(win)

class MenuElementText(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get('text', 'text')
        self.renderSurf(self.text)
        self.color = StackPanel._textElementColor


class MenuElementButton(MenuElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get('text', "Bu")
        self.surf = None
        self.renderSurf(self.text)
        self.type = MENU_BUTTON
        self.mouseInButton = False
        self.cursor = pygame.SYSTEM_CURSOR_HAND
        self.event = None
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.event = self.key
    
    def get_event_values(self):
        if self.event is not None:
            event = self.event
            self.event = None
            return event, {}
        return None, {}

    def step(self):
        mousePos = mouseInWin()
        buttonPos = self.getSuperPos() + self.pos
        posInButton = mousePos - buttonPos
        if posInButton[0] >= 0 and posInButton[0] < self.size[0] and posInButton[1] >= 0 and posInButton[1] < self.size[1]:
            # if not self.mouseInButton:
                # mouse enters button
                # if self.tooltip:
                    # Gui._instance.toaster.showToolTip(self)
                # Gui._instance.showCursor(self.cursor, self)
            self.mouseInButton = True
            self.selected = True
            self.animation_offset = self.animation_offset + (1 - self.animation_offset) * 0.3
            return self
        else:
            self.mouseInButton = False
            self.selected = False
            self.animation_offset = self.animation_offset + (0 - self.animation_offset) * 0.3
        return None
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
    
class MenuElementUpDown(MenuElementButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = kwargs.get('text', "")
        self.showValue = True
        self.mode = 0
        self.renderSurf(str(self.value))
        self.type = MENU_UPDOWN
        self.limitMin = kwargs.get('limitMin', False)
        self.limitMax = kwargs.get('limitMax', False)
        self.limMin = kwargs.get('limMin', 0)
        self.limMax = kwargs.get('limMax', 100)
        self.values = kwargs.get('values', None)
        self.stepSize = kwargs.get('stepSize', 1)
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.advance()

    def get_event_values(self):
        return None, {self.key: self.value}

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
            self.animation_offset = self.animation_offset + (1 - self.animation_offset) * 0.3
            # if self.tooltip:
                # Gui._instance.toaster.showToolTip(self)
            # Gui._instance.showCursor(pygame.SYSTEM_CURSOR_HAND, self)
            if posInButton[1] > posInButton[0] * (self.size[1] / self.size[0]): # need replacement
                self.mode = -1
            else:
                self.mode = 1
            if self.showValue:
                self.renderSurf(str(self.value))
            return self
        else:
            self.selected = False
            self.animation_offset = self.animation_offset + (0 - self.animation_offset) * 0.3
        return None
    
    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        buttonPos = self.getSuperPos() + self.pos
        border = 1
        arrowSize = self.size[1] // 2
        rightColor = StackPanel._subSelectColor if self.selected and self.mode == 1 else StackPanel._subButtonColor
        leftColor = StackPanel._subSelectColor if self.selected and not self.mode == 1 else StackPanel._subButtonColor
        pygame.draw.polygon(win, rightColor, [(buttonPos[0] + self.size[0] - arrowSize, buttonPos[1] + border), (buttonPos[0] + self.size[0] - border - 1, buttonPos[1] + border), (buttonPos[0] + self.size[0] - border - 1, buttonPos[1] + arrowSize)])
        pygame.draw.polygon(win, leftColor, [(buttonPos[0] + border ,buttonPos[1] + self.size[1] - arrowSize), (buttonPos[0] + border, buttonPos[1] + self.size[1] - border - 1), (buttonPos[0] + arrowSize, buttonPos[1] + self.size[1] - border - 1)])


class MenuElementToggle(MenuElementButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = MENU_TOGGLE
        self.border = 1
        self.cursor = pygame.SYSTEM_CURSOR_HAND
    
    def handle_pygame_event(self, event):
        super().handle_pygame_event(event)
        if self.selected:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.value = not self.value

    def get_event_values(self):
        return None, {self.key: self.value}

    def draw(self, win: pygame.Surface) -> None:
        super().draw(win)
        buttonPos = self.getSuperPos() + self.pos
        if self.value:
            pygame.draw.rect(win, StackPanel._toggleColor, ((buttonPos[0] + self.border, buttonPos[1] + self.border), (self.size[0] - 2 * self.border, self.size[1] - 2 * self.border)))
        self.drawText(win)

class MenuElementComboSwitch(MenuElementButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.surf = None
        self.currentIndex = 0
        self.type = MENU_COMBOS
        self.items = kwargs.get('items', [])
        if self.items:
            self.setItems(self.items)
            self.setCurrentItem(self.text)
        self.forward = False
        self.mapping = {}
    
    def get_event_values(self):
        return None, {self.key: self.value}
    
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
            self.animation_offset = self.animation_offset + (1 - self.animation_offset) * 0.3
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
            self.animation_offset = self.animation_offset + (0 - self.animation_offset) * 0.3
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
    
    def get_event_values(self):
        return None, {self.key: self.value}

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
    
    def get_event_values(self):
        return None, {self.key: self.value}

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

class MenuElementInput(MenuElementButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = "fixed"
        self.inputText = ""
        self.oldInputText = ""
        self.value = self.inputText
        self.type = MENU_INPUT
        self.surf = None
        self.cursorSpeed = GameVariables().fps // 4
        self.showCursor = False
        self.timer = 0
        self.cursorText = fonts.pixel5.render("|", True, (255,255,255))
        self.cursor = pygame.SYSTEM_CURSOR_IBEAM
        self.evaluatedType = kwargs.get('evaluatedType', 'str')
    
    def processKey(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.inputText = self.inputText[:-1]
        else:
            self.inputText += event.unicode
        self.value = self.inputText
    
    def evaluate(self, dic):
        if self.evaluatedType == 'str':
            dic[self.key] = self.value
        if self.evaluatedType == 'int':
            if self.value == '':
                return
            dic[self.key] = int(self.value)
    
    def step(self):
        if self.mode == "editing":
            self.timer += 1
            if self.timer >= self.cursorSpeed:
                self.showCursor = not self.showCursor
                self.timer = 0
            if self.inputText != self.oldInputText:
                self.renderSurf(self.inputText)
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

        if self.mode == "editing" and self.showCursor:
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

class MenuAnimator:
    def __init__(self, menu, posStart, posEnd, trigger=None, args=None, ease="inout"):
        self.posStart = posStart
        self.posEnd = posEnd
        self.timer = 0
        self.fullTime = GameVariables().fps * 1
        self.trigger = trigger
        self.args = args
        # set first positions
        self.menu = menu
        self.ease = ease
        menu.pos = posStart
        self.is_done = False
    
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
        self.menu.pos = self.posEnd
        if self.trigger:
            if self.args:
                self.trigger(*self.args)
            else:
                self.trigger()
        self.is_done = True

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