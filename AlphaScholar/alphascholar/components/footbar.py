import reflex as rx 


def footbar() -> rx.Component:
    '''The footer component.'''
    
    return rx.container(
        rx.text("© 2026 AlphaScholar. All rights reserved."),
    )