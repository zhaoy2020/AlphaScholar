import reflex as rx 


def navbar_link(text: str, url: str) -> rx.Component:
    '''A helper function to create a navbar link component.'''
    
    return rx.link(rx.text(text, size="5", weight="medium", color='black'), href=url)


def menu() -> rx.Component:
    '''The menu component for the navbar.'''

    return rx.hstack(
                rx.hstack(
                    rx.image(
                        src=rx.asset('AlphaScholar.png'),
                        width="3em",
                        height="auto",
                        border_radius="25%",
                    ),
                    rx.heading("AlphaScholar", size="7", weight="bold"),
                    align_items="center",
                ),
                rx.spacer(),
                rx.hstack(
                    navbar_link("Home", "/#"),
                    navbar_link("Tracker", "/tracker"),
                    navbar_link("Reader", "/reader"),
                    navbar_link("Assistant", "/assistant"),
                    navbar_link("About", "/about"),
                    spacing="5",
                ),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.icon_button(rx.icon("user"), size="2", radius="full")
                    ),
                    rx.menu.content(
                        rx.menu.item(rx.link('Log in', href='/login')),
                        rx.menu.item("Settings"),
                        rx.menu.item("Earnings"),
                        rx.menu.separator(),
                        rx.menu.item("Log out"),
                    ),
                    justify="end",
                ),
                justify="between",
                align_items="center",
            )


def navbar() -> rx.Component:
    return rx.box(
        rx.color_mode.button(position="bottom-right"),
        rx.desktop_only(menu()),
        rx.mobile_and_tablet(menu()),

        bg='#4b2e83',
        # padding="1em",
        # position="fixed",
        # top="0px",
        # z_index="1000",
        # width="100%",
        # height="80px",
        align="center",
        justify="center",
    )