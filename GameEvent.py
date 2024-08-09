
from typing import List
from Common import SingletonMeta

class Event:
    ''' game event '''


class EventComment(Event):
    ''' event for commenting '''
    def __init__(self, text) -> None:
        self.text = text


class GameEvents(metaclass=SingletonMeta):
    ''' event manager class '''
    def __init__(self) -> None:
        self.events: List[Event] = []

    def get_events(self) -> List[Event]:
        return self.events

    def post(self, event: Event):
        self.events.append(event)