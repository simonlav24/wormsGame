
from typing import List, Dict, Any
from random import choice

from common.vector import Vector
from common import SingletonMeta, Entity
from common.constants import ColorType


class ToManyUnhandeledEventsException(Exception):
    ''' too many unhandeled events exception '''

class Event:
    ''' game event '''
    def __init__(self) -> None:
        self.is_done = False
    
    def done(self) -> None:
        self.is_done = True


class EventComment(Event):
    ''' event for commenting '''
    def __init__(self, text_dict: List[Dict[str, Any]]) -> None:
        super().__init__()
        self.text_dict = text_dict
    
    @staticmethod
    def post_choice_event(choices: List[str], text: str, color: ColorType):
        comment = choice(choices)
        text_dict = [
            {'text': comment[0]},
            {'text': text, 'color': color},
            {'text': comment[1]},
        ]
        GameEvents().post(EventComment(text_dict))


class EventWormDamage(Event):
    def __init__(self, worm: Entity, damage: int) -> None:
        super().__init__()
        self.worm = worm
        self.damage = damage


class GameEvents(metaclass=SingletonMeta):
    ''' event manager class '''
    def __init__(self) -> None:
        self._events: List[Event] = []

    def get_events(self) -> List[Event]:
        ''' return undone events '''
        self._events = [event for event in self._events if not event.is_done]
        return self._events

    def post(self, event: Event):
        self._events.append(event)
        if len(self._events) > 100:
            raise ToManyUnhandeledEventsException('above 100 events')