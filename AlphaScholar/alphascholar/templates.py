import reflex as rx 

from typing import Callable

from .components.navbar import navbar
from .components.footbar import footbar


def web_structure(page: Callable[[], rx.Component]) -> rx.Component:
    '''The web structure of the app.'''
    
    
    return rx.vstack(
        navbar(),
        page(),
        footbar(),

        spacing="1",
        align_items='center',
    )