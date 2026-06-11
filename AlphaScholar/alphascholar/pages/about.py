import reflex as rx 
from ..templates import web_structure


@rx.page('/about')
@web_structure
def about() -> rx.Component:
    '''The about page.'''

    return rx.box(
        rx.vstack(
            rx.heading("About AlphaScholar", size="9"),
            rx.text("AlphaScholar is a tool to help you keep track of your research progress and summarize your research progress.", size="5"),

            spacing="5",
            align="center",
            justify="center",
            
            wdith="100%",
            min_hight='100vh',
        ),
        
        width="80%",
        align="center",
        justify="center",
    )