
from typing import List, Dict, Any
from random import choice

from Common import SingletonMeta
from Constants import comments_flew, comments_damage, ColorType

class Event:
    ''' game event '''


class EventComment(Event):
    ''' event for commenting '''
    def __init__(self, text_dict: List[Dict[str, Any]]) -> None:
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

class GameEvents(metaclass=SingletonMeta):
    ''' event manager class '''
    def __init__(self) -> None:
        self.events: List[Event] = []

    def get_events(self) -> List[Event]:
        return self.events

    def post(self, event: Event):
        self.events.append(event)