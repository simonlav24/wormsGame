
import pygame

class Room:
    def __init__(self, *args, **kwargs) -> None:
        ...

    def handle_pygame_event(self, event) -> None:
        ...

    def step(self) -> None:
        ...

    def draw(self, win: pygame.Surface) -> None:
        ...



