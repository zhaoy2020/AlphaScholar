import reflex as rx 

from ..templates import web_structure


@rx.page("/")
@web_structure
def index() -> rx.Component:
    '''Index page'''

    return rx.box(
            rx.vstack(
                rx.heading("Welcome to AlphaScholar!", size="9"),
                rx.text("Get started by editing ", size="5"),
                rx.link(
                    rx.button("Check out our docs!"),
                    href="https://reflex.dev/docs/getting-started/introduction/",
                    is_external=True,
                ),

                spacing="5",
                align="center",
                justify="center",
                
                width='100%',
            ),
            width='80%',
        )
